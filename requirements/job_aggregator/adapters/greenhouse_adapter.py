"""
Greenhouse Public Job Board Adapter.
Ingests live official job postings directly from public Greenhouse ATS endpoints
of top Indian tech employers and startups with EXACT timestamps.
"""

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
from requirements.skill_extractor import extract_technical_skills

logger = logging.getLogger(__name__)

# Sample permitted Indian startup / tech enterprise boards using Greenhouse public APIs
TARGET_GREENHOUSE_BOARDS = [
    ('razorpay', 'Razorpay'),
    ('postman', 'Postman'),
    ('cred', 'CRED'),
    ('meesho', 'Meesho'),
    ('browserstack', 'BrowserStack'),
]


class GreenhousePublicSourceAdapter(BaseJobSourceAdapter):
    source_name = "Greenhouse"
    is_enabled = True
    rate_limit_delay = 0.3

    def fetch_jobs(
        self,
        limit: int = 15,
        last_hours: Optional[int] = None,
        keywords: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        results = []
        now = timezone.now()
        hour_cutoff = now - timedelta(hours=last_hours) if last_hours else None

        for board_token, company_display in TARGET_GREENHOUSE_BOARDS:
            url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
            res = self.safe_get(url)
            if not res or res.status_code != 200:
                continue

            try:
                data = res.json()
                jobs = data.get('jobs', [])

                for item in jobs:
                    loc_obj = item.get('location') or {}
                    raw_loc = loc_obj.get('name', '')

                    # Location filter: must match India
                    norm_city, is_remote, is_valid_india = normalize_indian_location(raw_loc)
                    if not is_valid_india and 'india' not in raw_loc.lower():
                        continue

                    raw_title = item.get('title', '')
                    raw_content = html.unescape(item.get('content') or '')
                    updated_at_str = item.get('updated_at')

                    # Parse exact publication timestamp
                    pub_dt, precision = parse_job_timestamps(updated_at_str, precision_hint="EXACT_TIMESTAMP")

                    # Last hours filter check
                    if hour_cutoff and pub_dt < hour_cutoff:
                        continue

                    # Keyword filter check
                    if keywords and keywords.lower() not in f"{raw_title} {raw_content}".lower():
                        continue

                    domain = classify_industry_domain(raw_title, "", raw_content)
                    exp_tier = classify_experience_tier(raw_title, "", raw_content)
                    job_url = item.get('absolute_url') or f"https://boards.greenhouse.io/{board_token}/jobs/{item.get('id')}"

                    results.append({
                        'source_name': self.source_name,
                        'source_job_id': str(item.get('id')),
                        'source_url': job_url,
                        'apply_url': job_url,
                        'title': raw_title,
                        'company_name': company_display,
                        'company_logo_icon': 'building',
                        'description': raw_content[:4000] if raw_content else f"Exciting career opportunity at {company_display}.",
                        'location': f"{norm_city}, India" if norm_city != "Remote" else "Remote, India",
                        'normalized_city': norm_city,
                        'is_remote': is_remote,
                        'job_type': 'INTERNSHIP' if exp_tier == 'INTERNSHIP' else 'FULL_TIME',
                        'industry_domain': domain,
                        'experience_tier': exp_tier,
                        'skills_required': extract_technical_skills(
                            title=raw_title,
                            raw_skills="",
                            description=raw_content or f"Exciting career opportunity at {company_display}.",
                            category_slug=domain.lower()
                        ),
                        'stipend_salary': 'Best in Industry (Competitive Startup Package)',
                        'eligibility': 'Open to candidates matching job qualifications',
                        'source_published_at': pub_dt,
                        'source_updated_at': pub_dt,
                        'timestamp_precision': precision,
                    })

                    if len(results) >= limit:
                        return results

            except Exception as e:
                logger.warning(f"Error parsing Greenhouse board {board_token}: {e}")
                continue

        return results
