"""
Public Feeds Source Adapter.
Ingests permitted open job board feeds and public career syndication feeds
with exact publication timestamps.
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
from requirements.skill_extractor import extract_technical_skills

logger = logging.getLogger(__name__)


class PublicFeedsSourceAdapter(BaseJobSourceAdapter):
    source_name = "PublicFeeds"
    is_enabled = True
    rate_limit_delay = 0.5

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

        # Arbeitnow Open Job Board API (Permitted public feed)
        url = "https://www.arbeitnow.com/api/job-board-api"
        res = self.safe_get(url)
        if not res or res.status_code != 200:
            return results

        try:
            data = res.json()
            jobs = data.get('data', [])

            for item in jobs:
                raw_loc = item.get('location', '')
                is_remote_feed = item.get('remote', False)
                
                # Check for India or Remote eligibility
                norm_city, is_remote, is_valid_india = normalize_indian_location(raw_loc)
                if not is_remote_feed and not is_valid_india and 'india' not in raw_loc.lower():
                    continue

                if is_remote_feed:
                    norm_city = "Remote"
                    is_remote = True

                raw_title = item.get('title', '')
                raw_comp = item.get('company_name', 'Tech Enterprise')
                raw_desc = item.get('description', '')
                created_at_val = item.get('created_at')

                pub_dt, precision = parse_job_timestamps(created_at_val, precision_hint="EXACT_TIMESTAMP")

                if hour_cutoff and pub_dt < hour_cutoff:
                    continue

                domain = classify_industry_domain(raw_title, "", raw_desc)
                exp_tier = classify_experience_tier(raw_title, "", raw_desc)
                apply_url = item.get('url', '')

                tags = item.get('tags', [])
                skills_str = extract_technical_skills(
                    title=raw_title,
                    raw_skills=", ".join(tags) if isinstance(tags, list) else str(tags),
                    description=raw_desc,
                    category_slug=domain.lower()
                )

                results.append({
                    'source_name': self.source_name,
                    'source_job_id': item.get('slug') or str(pub_dt.timestamp()),
                    'source_url': apply_url,
                    'apply_url': apply_url,
                    'title': raw_title,
                    'company_name': raw_comp,
                    'company_logo_icon': 'building',
                    'description': raw_desc[:4000] if raw_desc else f"Job opportunity at {raw_comp}.",
                    'location': f"{norm_city}, India" if norm_city != "Remote" else "Remote, India",
                    'normalized_city': norm_city,
                    'is_remote': is_remote,
                    'job_type': 'FULL_TIME',
                    'industry_domain': domain,
                    'experience_tier': exp_tier,
                    'skills_required': skills_str,
                    'stipend_salary': 'Competitive Compensation',
                    'eligibility': 'Open to global and remote engineers',
                    'source_published_at': pub_dt,
                    'source_updated_at': pub_dt,
                    'timestamp_precision': precision,
                })

                if len(results) >= limit:
                    break

        except Exception as e:
            logger.warning(f"Error parsing public feed: {e}")

        return results
