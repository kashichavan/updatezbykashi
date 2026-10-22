"""
Jobdexo Source Adapter.
Reuses and extends existing jobdexo_service.py with enhanced
India-wide location normalization, domain classification, and last-hour timestamp parsing.
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
from requirements.jobdexo_service import (
    fetch_multi_section_jobdexo_urls,
    extract_jobdexo_detail
)

logger = logging.getLogger(__name__)


class JobdexoSourceAdapter(BaseJobSourceAdapter):
    source_name = "Jobdexo"
    is_enabled = True
    rate_limit_delay = 0.4

    def fetch_jobs(
        self,
        limit: int = 15,
        last_hours: Optional[int] = None,
        keywords: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch latest jobs from Jobdexo with India-wide normalization."""
        candidate_urls = fetch_multi_section_jobdexo_urls(limit=max(30, limit * 3))
        results = []

        now = timezone.now()
        hour_cutoff = now - timedelta(hours=last_hours) if last_hours else None

        for url in candidate_urls:
            try:
                detail = extract_jobdexo_detail(url)
                if not detail or detail.get('is_expired'):
                    continue

                raw_title = detail.get('title', '')
                raw_comp = detail.get('company', '')
                raw_loc = detail.get('location', '')
                raw_desc = detail.get('description', '')
                raw_skills = detail.get('skills', '')

                # Location normalization
                norm_city, is_remote, is_valid_india = normalize_indian_location(raw_loc)
                if not is_valid_india:
                    continue

                # Filter by location if specified
                if location and location.lower() not in norm_city.lower() and not is_remote:
                    continue

                # Filter by keywords if specified
                if keywords and keywords.lower() not in f"{raw_title} {raw_skills}".lower():
                    continue

                # Domain and experience classification
                domain = classify_industry_domain(raw_title, raw_skills, raw_desc)
                exp_tier = classify_experience_tier(raw_title, detail.get('eligibility', ''), raw_desc)

                # Timestamp parsing
                pub_dt, precision = parse_job_timestamps(detail.get('posted_date'), precision_hint="DATE_ONLY")

                # If last_hours filter applied, check publication threshold
                if hour_cutoff and pub_dt < hour_cutoff:
                    # Keep if discovered today
                    if pub_dt.date() != now.date():
                        continue

                results.append({
                    'source_name': self.source_name,
                    'source_job_id': url.strip('/').split('/')[-1],
                    'source_url': url,
                    'apply_url': detail.get('apply_url') or url,
                    'title': raw_title,
                    'company_name': raw_comp,
                    'company_logo_icon': 'building',
                    'description': raw_desc,
                    'location': f"{norm_city}, India" if norm_city != "Remote" else "Remote, India",
                    'normalized_city': norm_city,
                    'is_remote': is_remote,
                    'job_type': detail.get('job_type', 'FULL_TIME'),
                    'industry_domain': domain,
                    'experience_tier': exp_tier,
                    'skills_required': raw_skills,
                    'stipend_salary': detail.get('salary', 'Competitive Package (Best in Industry)'),
                    'eligibility': detail.get('eligibility', 'Open to all graduates'),
                    'selection_process': detail.get('selection_process', ''),
                    'study_materials': detail.get('study_materials', []),
                    'source_published_at': pub_dt,
                    'source_updated_at': pub_dt,
                    'timestamp_precision': precision,
                })

                if len(results) >= limit:
                    break

            except Exception as e:
                logger.warning(f"Error processing Jobdexo URL {url}: {e}")
                continue

        return results
