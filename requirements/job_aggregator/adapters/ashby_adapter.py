"""
Ashby Public Job Board Adapter.
Ingests live official job postings directly from Ashby public job-board APIs
with EXACT ISO timestamps.
"""

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

# Sample permitted Indian startup boards using Ashby public APIs
TARGET_ASHBY_BOARDS = [
    ('retool', 'Retool'),
    ('sentry', 'Sentry'),
    ('temporal', 'Temporal'),
]


class AshbyPublicSourceAdapter(BaseJobSourceAdapter):
    source_name = "Ashby"
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

        for board_token, company_display in TARGET_ASHBY_BOARDS:
            url = f"https://api.ashbyhq.com/posting-api/job-board/{board_token}"
            res = self.safe_get(url)
            if not res or res.status_code != 200:
                continue

            try:
                data = res.json()
                jobs = data.get('jobs', [])

                for item in jobs:
                    raw_loc = item.get('location', '')
                    norm_city, is_remote, is_valid_india = normalize_indian_location(raw_loc)
                    
                    # Check if India location or worldwide remote
                    if not is_valid_india and 'india' not in raw_loc.lower():
                        continue

                    raw_title = item.get('title', '')
                    published_at_str = item.get('publishedAt') or item.get('createdAt')
                    pub_dt, precision = parse_job_timestamps(published_at_str, precision_hint="EXACT_TIMESTAMP")

                    if hour_cutoff and pub_dt < hour_cutoff:
                        continue

                    domain = classify_industry_domain(raw_title, "", "")
                    exp_tier = classify_experience_tier(raw_title, "", "")
                    job_url = item.get('jobUrl') or f"https://jobs.ashbyhq.com/{board_token}/{item.get('id')}"

                    results.append({
                        'source_name': self.source_name,
                        'source_job_id': str(item.get('id')),
                        'source_url': job_url,
                        'apply_url': job_url,
                        'title': raw_title,
                        'company_name': company_display,
                        'company_logo_icon': 'building',
                        'description': item.get('descriptionHtml') or f"Exciting role at {company_display}.",
                        'location': f"{norm_city}, India" if norm_city != "Remote" else "Remote, India",
                        'normalized_city': norm_city,
                        'is_remote': is_remote,
                        'job_type': 'INTERNSHIP' if exp_tier == 'INTERNSHIP' else 'FULL_TIME',
                        'industry_domain': domain,
                        'experience_tier': exp_tier,
                        'skills_required': f"{domain.capitalize()}, Problem Solving",
                        'stipend_salary': 'Competitive Package',
                        'eligibility': 'Open to all matching qualifications',
                        'source_published_at': pub_dt,
                        'source_updated_at': pub_dt,
                        'timestamp_precision': precision,
                    })

                    if len(results) >= limit:
                        return results

            except Exception as e:
                logger.warning(f"Error parsing Ashby board {board_token}: {e}")
                continue

        return results
