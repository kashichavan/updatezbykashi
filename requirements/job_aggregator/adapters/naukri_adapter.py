"""
Naukri Job Source Adapter.
Extracts fresh Indian job postings from Naukri's public search API
using standard RSA PKCS#1 v1.5 request tokens without session cookies or CAPTCHA bypass.

Features:
- Real-time India-wide search (Bangalore, Hyderabad, Pune, Mumbai, Delhi NCR, Remote, etc.)
- Recency sorting ('sort=f', 'jobAge=1' for past 24h / 1h)
- Full extraction: Title, Company, Location, Experience, Salary, Skills, Cleaned JD, Canonical URL
- Graceful rate-limit backoff and failure isolation
"""

import os
import re
import html
import time
import base64
import functools
import secrets
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone as dt_timezone

from ..base_adapter import BaseJobSourceAdapter
from ..normalizer import (
    normalize_indian_location,
    classify_industry_domain,
    classify_experience_tier,
    parse_job_timestamps,
)

logger = logging.getLogger(__name__)

# Standard public RSA key used for Naukri client token generation
NAUKRI_PUBLIC_KEY_B64 = (
    "MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBALrlQ+djR0RjJwBF1xuisHmdFv334MImK6LgzJhmLhN7"
    "B5yuEyaKoasgXQk3+OQglsOaBxEJ0j5PcTL3nbOvt80CAwEAAQ=="
)

NAUKRI_SEARCH_API_URL = "https://www.naukri.com/jobapi/v3/search"


def _read_der_field(data: bytes, i: int):
    """Parse DER length and payload."""
    length = data[i + 1]
    i += 2
    if length & 0x80:
        size = length & 0x7F
        length = int.from_bytes(data[i : i + size], "big")
        i += size
    return data[i : i + length], i + length


@functools.cache
def _get_naukri_rsa_key():
    """Derive RSA modulus and exponent from the public key."""
    key, _ = _read_der_field(base64.b64decode(NAUKRI_PUBLIC_KEY_B64), 0)
    _, i = _read_der_field(key, 0)
    bit_string, _ = _read_der_field(key, i)
    rsa_key, _ = _read_der_field(bit_string[1:], 0)
    modulus, i = _read_der_field(rsa_key, 0)
    exponent, _ = _read_der_field(rsa_key, i)
    return int.from_bytes(modulus, "big"), int.from_bytes(exponent, "big")


def generate_naukri_token(page: str = "srp") -> str:
    """
    Generate Naukri's request token: RSA (PKCS#1 v1.5) encryption of 'v0|<epoch_ms>|121_<page>'.
    """
    try:
        modulus, exponent = _get_naukri_rsa_key()
        size = (modulus.bit_length() + 7) // 8
        message = f"v0|{int(time.time() * 1000)}|121_{page}".encode()
        padding = bytes(secrets.randbelow(255) + 1 for _ in range(size - 3 - len(message)))
        block = b"\x00\x02" + padding + b"\x00" + message
        cipher = pow(int.from_bytes(block, "big"), exponent, modulus)
        return base64.b64encode(cipher.to_bytes(size, "big")).decode()
    except Exception as e:
        logger.warning(f"[Naukri] Could not generate nkparam token: {e}")
        return ""


class NaukriSourceAdapter(BaseJobSourceAdapter):
    source_name = "Naukri"
    is_enabled = os.getenv("NAUKRI_SCRAPING_ENABLED", "true").lower() in ["true", "1"]
    rate_limit_delay = 1.0
    timeout = 10

    def fetch_jobs(
        self,
        limit: int = 20,
        last_hours: Optional[int] = None,
        keywords: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch fresh job postings from Naukri's public job search API.
        """
        if not self.is_enabled:
            logger.info("[Naukri] Adapter is disabled via NAUKRI_SCRAPING_ENABLED=false")
            return []

        search_keyword = keywords or "Software Engineer"
        token = generate_naukri_token("srp")

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "appid": "109",
            "systemid": "Naukri",
            "nkparam": token,
            "Accept": "application/json",
            "Referer": "https://www.naukri.com/",
        }

        params = {
            "noOfResults": min(limit, 50),
            "urlType": "search_by_keyword",
            "searchType": "adv",
            "keyword": search_keyword,
            "pageNo": 1,
            "sort": "f",  # Fresh jobs first
        }

        if location:
            params["location"] = location

        if last_hours:
            # 1 day age filter on Naukri API
            params["jobAge"] = 1

        try:
            res = self.safe_get(NAUKRI_SEARCH_API_URL, params=params, headers=headers)
            if not res or res.status_code != 200:
                logger.info(f"[Naukri] Search API returned status {res.status_code if res else 'None'}. Skipping.")
                return []

            data = res.json()
            raw_details = data.get("jobDetails", [])
            return self.parse_naukri_job_details(raw_details, limit=limit)
        except Exception as e:
            logger.warning(f"[Naukri] Error fetching jobs: {e}")
            return []

    def parse_naukri_job_details(self, job_details: List[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
        """
        Parse raw Naukri job objects into canonical schema dictionaries.
        """
        results = []

        for item in job_details[:limit]:
            try:
                title = html.unescape(item.get("title", "")).strip()
                comp_name = html.unescape(item.get("companyName", "Leading Employer")).strip()
                job_id = str(item.get("jobId", "")).strip()

                if not title or not job_id:
                    continue

                # Location & Placeholders
                raw_location = "Bengaluru, India"
                raw_exp = item.get("experienceText", "")
                raw_salary = "Competitive Package"

                for pl in item.get("placeholders", []):
                    ptype = pl.get("type")
                    label = pl.get("label", "")
                    if ptype == "location" and label:
                        raw_location = label
                    elif ptype == "experience" and label:
                        raw_exp = label
                    elif ptype == "salary" and label:
                        raw_salary = label

                norm_city, is_remote, is_valid_india = normalize_indian_location(raw_location)
                if not is_valid_india:
                    continue

                # Canonical URL
                jd_url = item.get("jdURL", "")
                if jd_url.startswith("/"):
                    apply_url = f"https://www.naukri.com{jd_url}"
                elif jd_url.startswith("http"):
                    apply_url = jd_url
                else:
                    apply_url = f"https://www.naukri.com/job-listings-{job_id}"

                # Skills
                skills_raw = item.get("tagsAndSkills", "")
                skills_list = [s.strip() for s in skills_raw.split(",") if s.strip()] if isinstance(skills_raw, str) else []
                skills_str = ", ".join(skills_list) if skills_list else "Software Engineering, Problem Solving"

                # Description cleanup
                raw_desc = item.get("jobDescription", "")
                clean_desc = re.sub(r'<[^>]+>', ' ', raw_desc)
                clean_desc = html.unescape(re.sub(r'\s+', ' ', clean_desc)).strip()
                if not clean_desc or len(clean_desc) < 30:
                    clean_desc = (
                        f"{title} position at {comp_name}. Experience requirement: {raw_exp}. "
                        f"Key skills required: {skills_str}. Location: {norm_city}. "
                        f"Apply through the official Naukri posting."
                    )

                # Publication Timestamp
                created_date = item.get("createdDate")
                placeholder_label = item.get("footerPlaceholderLabel", "")

                if created_date:
                    pub_dt, precision = parse_job_timestamps(created_date, precision_hint="EXACT_TIMESTAMP")
                elif placeholder_label:
                    pub_dt, precision = parse_job_timestamps(placeholder_label, precision_hint="APPROXIMATE_TIME")
                else:
                    pub_dt, precision = parse_job_timestamps(None, precision_hint="APPROXIMATE_TIME")

                domain = classify_industry_domain(title, skills_str, clean_desc)
                exp_tier = classify_experience_tier(title, raw_exp, clean_desc)

                # Job Type
                job_type = "INTERNSHIP" if "intern" in title.lower() or "intern" in raw_exp.lower() else "FULL_TIME"

                results.append({
                    'source_name': self.source_name,
                    'source_job_id': job_id,
                    'source_url': apply_url,
                    'apply_url': apply_url,
                    'title': title,
                    'company_name': comp_name,
                    'company_logo_icon': 'building',
                    'location': f"{norm_city}, India" if norm_city != "Remote" else "Remote, India",
                    'normalized_city': norm_city,
                    'is_remote': is_remote,
                    'stipend_salary': raw_salary if raw_salary and "not disclosed" not in raw_salary.lower() else "Competitive Package (Best in Industry)",
                    'skills_required': skills_str,
                    'description': clean_desc,
                    'eligibility': f"Experience: {raw_exp}. Open to matching qualifications.",
                    'selection_process': "Online Assessment / Technical Interview Rounds / HR Review",
                    'job_type': job_type,
                    'industry_domain': domain,
                    'experience_tier': exp_tier,
                    'source_published_at': pub_dt,
                    'timestamp_precision': precision,
                    'posted_date': pub_dt.date(),
                    'is_featured': True,
                })

            except Exception as e:
                logger.debug(f"[Naukri] Error parsing job item: {e}")
                continue

        return results
