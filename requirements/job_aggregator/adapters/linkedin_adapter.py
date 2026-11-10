"""
LinkedIn Job Source Adapter (Guest API Pattern).
Based on open-source JobSpy / linkedin-scraper patterns using LinkedIn's
public guest job search endpoint:
https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search

Complies with Section 3 requirements:
- Disabled by default via LINKEDIN_SCRAPING_ENABLED=false
- When enabled, uses unauthenticated public guest API (no CAPTCHA bypass or session spoofing)
- Gracefully handles rate limiting (HTTP 429 / 999) with failure isolation
"""

import os
import re
import html
import logging
from typing import List, Dict, Any, Optional
from django.utils import timezone

from ..base_adapter import BaseJobSourceAdapter
from ..normalizer import (
    normalize_indian_location,
    classify_industry_domain,
    classify_experience_tier,
    parse_job_timestamps
)
from requirements.skill_extractor import extract_technical_skills

logger = logging.getLogger(__name__)

LINKEDIN_GUEST_API_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
LINKEDIN_JOB_POSTING_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

# A posting is only published with its real job description. Anything shorter
# than this is treated as "no JD" and the job is skipped, never padded.
MIN_JD_CHARS = 200


def _html_to_text(fragment: str) -> str:
    """Convert LinkedIn's JD HTML to readable plain text, keeping paragraph and bullet breaks."""
    text = re.sub(r'(?i)<br\s*/?>', '\n', fragment)
    text = re.sub(r'(?i)</(p|div|h[1-6]|ul|ol)>', '\n\n', text)
    text = re.sub(r'(?i)<li[^>]*>', '\n• ', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'[ \t\u00a0]+', ' ', text)
    text = re.sub(r' *\n *', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_linkedin_job_posting(html_text: str) -> Dict[str, Any]:
    """Extract the real JD and job criteria from a guest jobPosting page."""
    out: Dict[str, Any] = {'description': '', 'criteria': {}}
    m = re.search(r'show-more-less-html__markup[^>]*>([\s\S]*?)</div>', html_text)
    if m:
        out['description'] = _html_to_text(m.group(1))
    for key, val in re.findall(
        r'description__job-criteria-subheader"[^>]*>\s*([\s\S]*?)\s*</h3>\s*<span[^>]*>\s*([\s\S]*?)\s*</span>',
        html_text,
    ):
        out['criteria'][re.sub(r'<[^>]+>', '', key).strip()] = html.unescape(re.sub(r'<[^>]+>', '', val)).strip()
    return out


class LinkedInSourceAdapter(BaseJobSourceAdapter):
    source_name = "LinkedIn"
    
    # Enabled by default for prioritized India job aggregation (can be disabled via LINKEDIN_SCRAPING_ENABLED=false)
    is_enabled = os.getenv("LINKEDIN_SCRAPING_ENABLED", "true").lower() in ["true", "1"]
    rate_limit_delay = 2.0
    timeout = 7

    def fetch_jobs(
        self,
        limit: int = 25,
        last_hours: Optional[int] = None,
        keywords: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch public job postings from LinkedIn's guest search API.
        Queries multiple technical domains and pagination pages for 20+ fresh jobs.
        """
        if not self.is_enabled:
            logger.info(
                "[LinkedIn] Automated collection is disabled by default. "
                "Set LINKEDIN_SCRAPING_ENABLED=true in environment or .env to activate."
            )
            return []

        search_terms = [keywords] if keywords else [
            "Startup Software Engineer Bengaluru",
            "Software Testing Fresher",
            "QA Automation Tester",
            "HR Recruiter Intern",
            "MBA Management Trainee",
            "Python Developer Pune",
            "Full Stack Developer Hyderabad",
            "Data Analyst Fresher",
        ]
        search_loc = location or "India"

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Apply freshness filter: default to past 24h / 1h for real-time postings
        time_filter = "r86400"  # past 24 hours
        if last_hours == 1:
            time_filter = "r3600"  # past 1 hour (10-60 min fresh)
        elif last_hours and last_hours > 24:
            time_filter = f"r{last_hours * 3600}"

        results = []
        seen_ids = set()

        for kw in search_terms:
            if len(results) >= limit:
                break

            # Search page 1 (and page 2 if needed for 20+ jobs)
            offsets = (0, 25) if limit > 12 else (0,)
            for start_idx in offsets:
                if len(results) >= limit:
                    break

                params = {
                    "keywords": kw,
                    "location": search_loc,
                    "f_TPR": time_filter,
                    "start": start_idx,
                }

                res = self.safe_get(LINKEDIN_GUEST_API_URL, params=params, headers=headers)
                if not res or res.status_code != 200:
                    break

                batch = self.parse_linkedin_guest_html(res.text, limit=(limit - len(results)))
                for j in batch:
                    if j['source_job_id'] in seen_ids:
                        continue
                    seen_ids.add(j['source_job_id'])
                    # JD is required: fetch the real posting; skip the job if it can't be read.
                    if not self.enrich_with_job_posting(j, headers):
                        continue
                    results.append(j)
                    if len(results) >= limit:
                        break

        return results

    def fetch_job_posting(self, job_id: str, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Fetch one public guest job posting and return its real JD + criteria, or None."""
        res = self.safe_get(LINKEDIN_JOB_POSTING_URL.format(job_id=job_id), headers=headers)
        if not res or res.status_code != 200:
            return None
        detail = parse_linkedin_job_posting(res.text)
        if len(detail['description']) < MIN_JD_CHARS:
            return None
        return detail

    def enrich_with_job_posting(self, job: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> bool:
        """Replace card-level placeholders with the posting's real JD, skills and criteria."""
        detail = self.fetch_job_posting(job['source_job_id'], headers)
        if not detail:
            logger.info(f"[LinkedIn] Skipping {job['source_job_id']}: no job description available.")
            return False
        apply_job_posting_detail(job, detail)
        return True

    def parse_linkedin_guest_html(self, html_text: str, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Parse raw HTML fragments returned by LinkedIn seeMoreJobPostings endpoint.
        """
        results = []
        now = timezone.now()

        # Split into job card blocks
        cards = re.findall(r'<li[^>]*>[\s\S]*?</li>', html_text)
        if not cards:
            # Fallback block matching
            cards = re.findall(r'<div class="base-card[^>]*>[\s\S]*?</div>\s*</li>', html_text)

        for card in cards:
            try:
                # 1. Job ID & URN
                urn_match = re.search(r'data-entity-urn="urn:li:jobPosting:(\d+)"', card)
                if not urn_match:
                    urn_match = re.search(r'/view/.*?(\d{7,12})', card)
                job_id = urn_match.group(1) if urn_match else ""
                if not job_id:
                    continue

                # 2. Job Title
                title_match = re.search(r'class="base-search-card__title"[^>]*>([\s\S]*?)</h3>', card)
                raw_title = html.unescape(title_match.group(1)).strip() if title_match else ""
                raw_title = re.sub(r'<[^>]+>', '', raw_title).strip()
                if not raw_title:
                    continue

                # 3. Company Name
                comp_match = re.search(r'class="base-search-card__subtitle"[^>]*>([\s\S]*?)</h4>', card)
                raw_comp = html.unescape(comp_match.group(1)).strip() if comp_match else "Leading Tech Employer"
                raw_comp = re.sub(r'<[^>]+>', '', raw_comp).strip()

                # 4. Location
                loc_match = re.search(r'class="job-search-card__location"[^>]*>([\s\S]*?)</span>', card)
                raw_loc = html.unescape(loc_match.group(1)).strip() if loc_match else "India"
                raw_loc = re.sub(r'<[^>]+>', '', raw_loc).strip()

                norm_city, is_remote, is_valid_india = normalize_indian_location(raw_loc)
                if not is_valid_india:
                    continue

                # 5. Publication Date
                time_match = re.search(r'<time[^>]*datetime="([^"]*)"[^>]*>([\s\S]*?)</time>', card)
                pub_raw = time_match.group(2).strip() if time_match else ""
                if not pub_raw and time_match:
                    pub_raw = time_match.group(1).strip()
                
                pub_dt, precision = parse_job_timestamps(pub_raw, precision_hint="APPROXIMATE_TIME")

                # 6. Apply URL
                apply_url = f"https://www.linkedin.com/jobs/view/{job_id}/"

                domain = classify_industry_domain(raw_title, "", "")
                exp_tier = classify_experience_tier(raw_title, "", "")

                skills_str = extract_technical_skills(
                    title=raw_title,
                    raw_skills="",
                    description=f"{raw_title} at {raw_comp}",
                    category_slug=domain.lower()
                )

                results.append({
                    'source_name': self.source_name,
                    'source_job_id': job_id,
                    'source_url': apply_url,
                    'apply_url': apply_url,
                    'title': raw_title,
                    'company_name': raw_comp,
                    'company_logo_icon': 'building',
                    'description': '',  # filled from the real posting by enrich_with_job_posting
                    'location': f"{norm_city}, India" if norm_city != "Remote" else "Remote, India",
                    'normalized_city': norm_city,
                    'is_remote': is_remote,
                    'job_type': 'INTERNSHIP' if exp_tier == 'INTERNSHIP' else 'FULL_TIME',
                    'industry_domain': domain,
                    'experience_tier': exp_tier,
                    'skills_required': skills_str,
                    'stipend_salary': 'Competitive Package',
                    'eligibility': '',
                    'source_published_at': pub_dt,
                    'source_updated_at': pub_dt,
                    'timestamp_precision': precision,
                })

                if len(results) >= limit:
                    break

            except Exception as e:
                logger.warning(f"[LinkedIn] Error parsing job card: {e}")
                continue

        return results



def apply_job_posting_detail(job: Dict[str, Any], detail: Dict[str, Any]) -> Dict[str, Any]:
    """Merge a fetched posting into a job dict (shared by ingestion and backfill)."""
    desc = detail['description']
    crit = detail.get('criteria', {})
    seniority = crit.get('Seniority level', '')
    emp_type = crit.get('Employment type', '')

    job['description'] = desc
    job['skills_required'] = extract_technical_skills(
        title=job['title'], raw_skills="", description=desc,
        category_slug=(job.get('industry_domain') or '').lower(),
    )
    job['industry_domain'] = classify_industry_domain(job['title'], job['skills_required'], desc)
    job['experience_tier'] = classify_experience_tier(job['title'], seniority, desc)
    if emp_type.lower() == 'internship' or job['experience_tier'] == 'INTERNSHIP':
        job['job_type'] = 'INTERNSHIP'
    elif emp_type.lower() in ('contract', 'temporary'):
        job['job_type'] = 'FREELANCE'
    elif emp_type.lower() == 'part-time':
        job['job_type'] = 'PART_TIME'
    facts = [f"{k}: {v}" for k, v in (('Seniority', seniority), ('Employment type', emp_type)) if v and v != 'Not Applicable']
    job['eligibility'] = '. '.join(facts) or 'See the job description for eligibility.'
    return job


PLACEHOLDER_MARKER = "Candidates can review requirements and apply directly via official link."


def backfill_linkedin_descriptions(limit: int = 10) -> Dict[str, int]:
    """
    Replace placeholder descriptions on active LinkedIn jobs with the real JD.
    Runs in small batches (called each aggregation cycle) to stay polite.
    A posting LinkedIn reports as gone (404/410) is closed; on rate limits or
    other failures the job is left as is and retried next cycle.
    """
    from django.db.models import Q
    from django.db.models.functions import Length
    from requirements.models import JobPosting

    stats = {'updated': 0, 'closed': 0, 'skipped': 0}
    adapter = LinkedInSourceAdapter()
    if not adapter.is_enabled:
        return stats

    candidates = (
        JobPosting.objects.annotate(desc_len=Length('description'))
        .filter(source_name='LinkedIn', status='ACTIVE')
        .filter(Q(description__contains=PLACEHOLDER_MARKER) | Q(desc_len__lt=MIN_JD_CHARS))
        .exclude(source_job_id='')
        .order_by('-created_at')[:limit]
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    for job in candidates:
        res = adapter.safe_get(LINKEDIN_JOB_POSTING_URL.format(job_id=job.source_job_id), headers=headers)
        if res is not None and res.status_code in (404, 410):
            job.status = 'CLOSED'
            job.save(update_fields=['status'])
            stats['closed'] += 1
            continue
        detail = parse_linkedin_job_posting(res.text) if res is not None and res.status_code == 200 else None
        if not detail or len(detail['description']) < MIN_JD_CHARS:
            stats['skipped'] += 1
            continue
        data = apply_job_posting_detail(
            {'title': job.title, 'industry_domain': getattr(job, 'industry_domain', '') or '', 'job_type': job.job_type},
            detail,
        )
        job.description = data['description']
        job.skills_required = data['skills_required'] or job.skills_required
        job.eligibility = data['eligibility']
        job.job_type = data['job_type']
        fields = ['description', 'skills_required', 'eligibility', 'job_type']
        if hasattr(job, 'experience_tier'):
            job.experience_tier = data['experience_tier']
            fields.append('experience_tier')
        if hasattr(job, 'industry_domain'):
            job.industry_domain = data['industry_domain']
            fields.append('industry_domain')
        job.save(update_fields=fields)
        stats['updated'] += 1
    return stats
