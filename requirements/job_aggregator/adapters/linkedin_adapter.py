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
from datetime import timedelta
from django.utils import timezone

from ..base_adapter import BaseJobSourceAdapter
from ..normalizer import (
    normalize_indian_location,
    classify_industry_domain,
    classify_experience_tier,
    parse_job_timestamps
)

logger = logging.getLogger(__name__)

LINKEDIN_GUEST_API_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


class LinkedInSourceAdapter(BaseJobSourceAdapter):
    source_name = "LinkedIn"
    
    # Disabled by default in compliance with site terms and anti-bot authorization policy
    is_enabled = os.getenv("LINKEDIN_SCRAPING_ENABLED", "false").lower() in ["true", "1"]
    rate_limit_delay = 2.0
    timeout = 7

    def fetch_jobs(
        self,
        limit: int = 15,
        last_hours: Optional[int] = None,
        keywords: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch public job postings from LinkedIn's guest search API.
        """
        if not self.is_enabled:
            logger.info(
                "[LinkedIn] Automated collection is disabled by default. "
                "Set LINKEDIN_SCRAPING_ENABLED=true in environment or .env to activate."
            )
            return []

        search_kw = keywords or "Software Engineer"
        search_loc = location or "India"

        params = {
            "keywords": search_kw,
            "location": search_loc,
            "start": 0,
        }

        # Apply time posted filter if specified
        if last_hours == 1:
            params["f_TPR"] = "r3600"  # past 1 hour
        elif last_hours and last_hours <= 24:
            params["f_TPR"] = "r86400"  # past 24 hours
        elif last_hours and last_hours <= 168:
            params["f_TPR"] = "r604800"  # past 1 week

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        res = self.safe_get(LINKEDIN_GUEST_API_URL, params=params, headers=headers)
        if not res or res.status_code != 200:
            logger.info(f"[LinkedIn] Guest search returned status {res.status_code if res else 'None'}. Skipping.")
            return []

        return self.parse_linkedin_guest_html(res.text, limit=limit)

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

                results.append({
                    'source_name': self.source_name,
                    'source_job_id': job_id,
                    'source_url': apply_url,
                    'apply_url': apply_url,
                    'title': raw_title,
                    'company_name': raw_comp,
                    'company_logo_icon': 'building',
                    'description': f"{raw_title} role at {raw_comp} ({norm_city}). Apply directly on official portal.",
                    'location': f"{norm_city}, India" if norm_city != "Remote" else "Remote, India",
                    'normalized_city': norm_city,
                    'is_remote': is_remote,
                    'job_type': 'INTERNSHIP' if exp_tier == 'INTERNSHIP' else 'FULL_TIME',
                    'industry_domain': domain,
                    'experience_tier': exp_tier,
                    'skills_required': f"{domain.capitalize()}, Problem Solving",
                    'stipend_salary': 'Competitive Package',
                    'eligibility': 'Open to eligible candidates',
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

