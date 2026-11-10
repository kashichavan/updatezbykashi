"""
Adzuna adapter: India jobs through Adzuna's official job search API.

    GET https://api.adzuna.com/v1/api/jobs/in/search/{page}?app_id=..&app_key=..

Needs a free key from https://developer.adzuna.com (ADZUNA_APP_ID and
ADZUNA_APP_KEY). Without both it stays off. Adzuna returns a description
preview; applicants follow Adzuna's redirect_url to the full posting, as
Adzuna's terms require (job pages also show "Jobs by Adzuna").
"""
import html
import logging
import os
import re
from typing import Any, Dict, List, Optional

from ..base_adapter import BaseJobSourceAdapter
from ..normalizer import (
    classify_experience_tier,
    classify_industry_domain,
    normalize_indian_location,
    parse_job_timestamps,
)
from requirements.skill_extractor import extract_technical_skills

logger = logging.getLogger(__name__)

ADZUNA_SEARCH_URL = "https://api.adzuna.com/v1/api/jobs/in/search/{page}"
MIN_JD_CHARS = 200
DEFAULT_QUERIES = [
    "software engineer fresher", "software developer", "data analyst", "python developer",
    "java developer", "frontend developer", "qa engineer", "graduate trainee", "internship",
    "business analyst",
]


class AdzunaSourceAdapter(BaseJobSourceAdapter):
    source_name = "Adzuna"
    rate_limit_delay = 1.0
    timeout = 15

    @property
    def app_id(self) -> str:
        return os.getenv("ADZUNA_APP_ID", "").strip()

    @property
    def app_key(self) -> str:
        return os.getenv("ADZUNA_APP_KEY", "").strip()

    @property
    def is_enabled(self) -> bool:  # on only when both credentials are set
        return bool(self.app_id and self.app_key)

    def fetch_jobs(
        self,
        limit: int = 25,
        last_hours: Optional[int] = None,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not self.is_enabled:
            return []
        queries = [keywords] if keywords else DEFAULT_QUERIES
        max_days = max(1, min(30, (last_hours or 48) // 24 or 1))
        results, seen = [], set()

        for q in queries:
            if len(results) >= limit:
                break
            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "results_per_page": min(50, max(10, limit)),
                "what": q,
                "max_days_old": max_days,
                "sort_by": "date",
                "content-type": "application/json",
            }
            if location:
                params["where"] = location
            res = self.safe_get(ADZUNA_SEARCH_URL.format(page=1), params=params)
            if not res or res.status_code != 200:
                if res is not None and res.status_code in (401, 403):
                    logger.warning("[Adzuna] Credentials rejected; check ADZUNA_APP_ID / ADZUNA_APP_KEY.")
                    return results
                continue
            for item in res.json().get("results", []):
                job = self.parse_result(item)
                if job and job["source_job_id"] not in seen:
                    seen.add(job["source_job_id"])
                    results.append(job)
                    if len(results) >= limit:
                        break
        return results

    def parse_result(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        title = re.sub(r"<[^>]+>", "", html.unescape(item.get("title") or "")).strip()
        desc = re.sub(r"<[^>]+>", "", html.unescape(item.get("description") or "")).strip()
        apply_url = item.get("redirect_url") or ""
        job_id = str(item.get("id") or "")
        if not title or not apply_url or not job_id or len(desc) < MIN_JD_CHARS:
            return None

        loc = item.get("location") or {}
        raw_loc = loc.get("display_name") or ", ".join(loc.get("area") or [])
        norm_city, is_remote, is_valid = normalize_indian_location(raw_loc or "India")
        if not is_valid:
            return None

        salary = ""  # only real employer salaries; Adzuna also returns estimates
        if str(item.get("salary_is_predicted", "1")) == "0" and item.get("salary_min"):
            lo, hi = int(item["salary_min"]), int(item.get("salary_max") or item["salary_min"])
            salary = f"₹{lo:,}" if lo == hi else f"₹{lo:,}–₹{hi:,}"

        pub_dt, precision = parse_job_timestamps(item.get("created"), precision_hint="EXACT_TIMESTAMP")
        domain = classify_industry_domain(title, "", desc)
        exp_tier = classify_experience_tier(title, "", desc)
        contract_time = (item.get("contract_time") or "").lower()
        contract_type = (item.get("contract_type") or "").lower()
        if exp_tier == "INTERNSHIP":
            job_type = "INTERNSHIP"
        elif contract_time == "part_time":
            job_type = "PART_TIME"
        elif contract_type == "contract":
            job_type = "FREELANCE"
        else:
            job_type = "FULL_TIME"

        return {
            "source_name": self.source_name,
            "source_job_id": f"adzuna_{job_id}",
            "source_url": apply_url,
            "apply_url": apply_url,
            "title": title[:200],
            "company_name": ((item.get("company") or {}).get("display_name") or "Company not listed")[:150],
            "company_logo_icon": "building",
            "description": desc,
            "location": (f"{norm_city}, India" if norm_city != "Remote" else "Remote, India")[:150],
            "normalized_city": norm_city,
            "is_remote": is_remote,
            "job_type": job_type,
            "industry_domain": domain,
            "experience_tier": exp_tier,
            "skills_required": extract_technical_skills(
                title=title, raw_skills="", description=desc, category_slug=domain.lower()
            ),
            "stipend_salary": salary or "Not disclosed",
            "eligibility": "See the full job posting for eligibility.",
            "selection_process": "As described in the employer's job posting.",
            "source_published_at": pub_dt,
            "source_updated_at": pub_dt,
            "timestamp_precision": precision,
        }
