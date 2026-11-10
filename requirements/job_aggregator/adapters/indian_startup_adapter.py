"""
Official career-board adapter (source "Startup", code 'S').

Pulls real postings from the public, keyless job-board APIs that employers
publish on their applicant tracking systems:

  Greenhouse       GET boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
  Lever            GET api.lever.co/v0/postings/{slug}?mode=json
  Ashby            GET api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true
  SmartRecruiters  GET api.smartrecruiters.com/v1/companies/{slug}/postings (+ one detail call per job)

Rules:
- Only India-located postings.
- The real job description is required (MIN_JD_CHARS); a posting without one is skipped.
- Nothing is invented: no placeholder descriptions, phone numbers or salaries.
  Salary is shown only when the employer publishes it.
- Boards are processed round-robin a few per run, so each cycle stays light.
"""

import html
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone as dt_timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.utils import timezone

from ..base_adapter import BaseJobSourceAdapter
from ..normalizer import (
    classify_experience_tier,
    classify_industry_domain,
    normalize_indian_location,
    parse_job_timestamps,
)
from requirements.skill_extractor import extract_technical_skills

logger = logging.getLogger(__name__)

BOARDS_FILE = Path(__file__).resolve().parent.parent / "career_boards.json"
MIN_JD_CHARS = 200
SALARY_NOT_DISCLOSED = "Not disclosed"
_CURSOR_KEY = "career_boards_cursor"

INDIA_HINTS = (
    "india", "bengaluru", "bangalore", "mumbai", "pune", "hyderabad", "gurgaon", "gurugram",
    "noida", "chennai", "delhi", "kolkata", "ahmedabad", "jaipur", "kochi", "coimbatore",
    "indore", "chandigarh", "thiruvananthapuram", "trivandrum", "mysore", "mysuru",
)


def load_boards() -> List[Dict[str, str]]:
    try:
        return json.loads(BOARDS_FILE.read_text(encoding="utf-8")).get("boards", [])
    except Exception as e:  # a broken file must never take ingestion down
        logger.warning(f"[CareerBoards] Could not read {BOARDS_FILE.name}: {e}")
        return []


def html_to_text(fragment: str) -> str:
    """Employer JD HTML -> readable text that keeps paragraphs and bullets."""
    if not fragment:
        return ""
    text = html.unescape(fragment)  # Greenhouse double-encodes its HTML
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|h[1-6]|ul|ol|section)>", "\n\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "\n• ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_india_location(raw: str) -> bool:
    raw = (raw or "").lower()
    return any(h in raw for h in INDIA_HINTS)


ELIGIBILITY_HEADINGS = re.compile(
    r"(?im)^\s*(?:•\s*)?(requirements|qualifications|basic qualifications|minimum qualifications|"
    r"what you(?:'|’)ll need|what we(?:'|’)re looking for|who you are|you should have|eligibility|"
    r"skills (?:and|&) experience|must have)\s*:?\s*$"
)


def extract_eligibility(jd: str, limit: int = 600) -> str:
    """Pull the employer's own requirements section out of the JD, if it has one."""
    m = ELIGIBILITY_HEADINGS.search(jd)
    if not m:
        return "See the job description for eligibility."
    section = jd[m.end():].strip()
    section = re.split(r"\n\s*\n(?=[A-Z][^\n]{0,60}:?\s*\n)", section, maxsplit=1)[0]
    return (section[:limit].rsplit("\n", 1)[0] if len(section) > limit else section).strip() or \
        "See the job description for eligibility."


class IndianStartupSourceAdapter(BaseJobSourceAdapter):
    source_name = "Startup"
    is_enabled = os.getenv("CAREER_BOARDS_ENABLED", "true").lower() in ("true", "1")
    rate_limit_delay = 0.5
    timeout = 15

    boards_per_run = int(os.getenv("CAREER_BOARDS_PER_RUN", "4"))
    max_jobs_per_board = int(os.getenv("CAREER_BOARDS_MAX_JOBS_PER_BOARD", "40"))

    # ------------------------------------------------------------------ run
    def fetch_jobs(
        self,
        limit: int = 25,
        last_hours: Optional[int] = None,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not self.is_enabled:
            return []
        boards = load_boards()
        if not boards:
            return []

        # Round-robin: a few boards per cycle; every board is revisited regularly.
        start = (cache.get(_CURSOR_KEY) or 0) % len(boards)
        count = min(self.boards_per_run, len(boards))
        batch = [boards[(start + i) % len(boards)] for i in range(count)]
        cache.set(_CURSOR_KEY, (start + count) % len(boards), None)

        # Boards always return their full current list; postings are deduplicated
        # downstream, so ignore the short "last hour" window used for search sources.
        results: List[Dict[str, Any]] = []
        for board in batch:
            try:
                jobs = self.fetch_board(board, keywords=keywords, location=location)
                results.extend(jobs[: self.max_jobs_per_board])
            except Exception as e:
                logger.warning(f"[CareerBoards] {board.get('company')} ({board.get('ats')}) failed: {e}")
        return results

    def fetch_board(self, board: Dict[str, str], keywords: Optional[str] = None,
                    location: Optional[str] = None) -> List[Dict[str, Any]]:
        fetcher = {
            "greenhouse": self._greenhouse,
            "lever": self._lever,
            "ashby": self._ashby,
            "smartrecruiters": self._smartrecruiters,
        }.get(board.get("ats"))
        if not fetcher:
            return []
        out = []
        for job in fetcher(board):
            if keywords and keywords.lower() not in job["title"].lower():
                continue
            if location and location.lower() not in job["normalized_city"].lower() and not job["is_remote"]:
                continue
            out.append(job)
        return out

    # ------------------------------------------------------------ builders
    def _build(self, board: Dict[str, str], *, ats_key: str, posting_id: str, title: str,
               raw_location: str, jd: str, apply_url: str, published: Any,
               precision: str = "EXACT_TIMESTAMP", employment_type: str = "",
               salary: str = "", eligibility: str = "") -> Optional[Dict[str, Any]]:
        title = (title or "").strip()
        jd = (jd or "").strip()
        if not title or not apply_url or len(jd) < MIN_JD_CHARS:
            return None
        if not is_india_location(raw_location):
            return None
        norm_city, is_remote, _ = normalize_indian_location(raw_location)

        if isinstance(published, datetime):
            pub_dt = published
        else:
            pub_dt, precision = parse_job_timestamps(published, precision_hint=precision)

        domain = classify_industry_domain(title, "", jd)
        exp_tier = classify_experience_tier(title, "", jd)
        emp = (employment_type or "").lower()
        if "intern" in emp or exp_tier == "INTERNSHIP":
            job_type = "INTERNSHIP"
        elif "part" in emp:
            job_type = "PART_TIME"
        elif "contract" in emp or "temporary" in emp or "freelance" in emp:
            job_type = "FREELANCE"
        else:
            job_type = "FULL_TIME"

        return {
            "source_name": self.source_name,
            "source_job_id": f"su_{ats_key}_{board['slug']}_{posting_id}",
            "source_url": apply_url,
            "apply_url": apply_url,
            "title": title[:200],
            "company_name": board["company"][:150],
            "company_logo_icon": "building",
            "description": jd,
            "location": (f"{norm_city}, India" if norm_city != "Remote" else "Remote, India")[:150],
            "normalized_city": norm_city,
            "is_remote": is_remote,
            "job_type": job_type,
            "industry_domain": domain,
            "experience_tier": exp_tier,
            "skills_required": extract_technical_skills(
                title=title, raw_skills="", description=jd, category_slug=domain.lower()
            ),
            "stipend_salary": (salary or SALARY_NOT_DISCLOSED)[:100],
            "eligibility": eligibility or extract_eligibility(jd),
            "selection_process": "As described in the employer's job posting.",
            "source_published_at": pub_dt,
            "source_updated_at": pub_dt,
            "timestamp_precision": precision,
        }

    # ---------------------------------------------------------- greenhouse
    def _greenhouse(self, board: Dict[str, str]) -> List[Dict[str, Any]]:
        res = self.safe_get(f"https://boards-api.greenhouse.io/v1/boards/{board['slug']}/jobs",
                            params={"content": "true"})
        if not res or res.status_code != 200:
            return []
        out = []
        for item in res.json().get("jobs", []):
            loc = (item.get("location") or {}).get("name") or ""
            if not is_india_location(loc):
                offices = " ".join(o.get("name", "") + " " + (o.get("location") or "") for o in item.get("offices") or [])
                loc = offices if is_india_location(offices) else loc
            job = self._build(
                board, ats_key="gh", posting_id=str(item.get("id")), title=item.get("title"),
                raw_location=loc, jd=html_to_text(item.get("content", "")),
                apply_url=item.get("absolute_url") or "",
                published=item.get("first_published") or item.get("updated_at"),
            )
            if job:
                out.append(job)
        return out

    # --------------------------------------------------------------- lever
    def _lever(self, board: Dict[str, str]) -> List[Dict[str, Any]]:
        res = self.safe_get(f"https://api.lever.co/v0/postings/{board['slug']}", params={"mode": "json"})
        if not res or res.status_code != 200 or not isinstance(res.json(), list):
            return []
        out = []
        for item in res.json():
            cats = item.get("categories") or {}
            locs = [cats.get("location") or ""] + list(cats.get("allLocations") or [])
            loc = next((l for l in locs if is_india_location(l)), locs[0])
            if (item.get("country") or "").upper() == "IN" and not is_india_location(loc):
                loc = f"{loc}, India".strip(", ")

            parts = [item.get("openingPlain") or "", item.get("descriptionBodyPlain") or item.get("descriptionPlain") or ""]
            eligibility = ""
            for lst in item.get("lists") or []:
                heading = (lst.get("text") or "").strip()
                body = html_to_text(lst.get("content") or "")
                if body:
                    parts.append(f"{heading}\n{body}" if heading else body)
                    if not eligibility and re.search(r"(?i)require|qualif|need|looking for|who you are|must", heading):
                        eligibility = body[:600]
            parts.append(item.get("additionalPlain") or "")
            jd = "\n\n".join(p.strip() for p in parts if p and p.strip())

            salary = ""
            sr = item.get("salaryRange") or {}
            if sr.get("min") and sr.get("max"):
                salary = f"{sr.get('currency', '')} {sr['min']:,}–{sr['max']:,} {sr.get('interval', '')}".strip()

            created = item.get("createdAt")
            published = datetime.fromtimestamp(created / 1000.0, tz=dt_timezone.utc) if created else None
            job = self._build(
                board, ats_key="lever", posting_id=str(item.get("id")), title=item.get("text"),
                raw_location=loc, jd=jd, apply_url=item.get("hostedUrl") or item.get("applyUrl") or "",
                published=published or timezone.now(),
                precision="EXACT_TIMESTAMP" if published else "CURRENT_TIMESTAMP",
                employment_type=cats.get("commitment") or "", salary=salary, eligibility=eligibility,
            )
            if job:
                out.append(job)
        return out

    # --------------------------------------------------------------- ashby
    def _ashby(self, board: Dict[str, str]) -> List[Dict[str, Any]]:
        res = self.safe_get(f"https://api.ashbyhq.com/posting-api/job-board/{board['slug']}",
                            params={"includeCompensation": "true"})
        if not res or res.status_code != 200:
            return []
        out = []
        for item in res.json().get("jobs", []):
            if item.get("isListed") is False:
                continue
            locs = [item.get("location") or ""] + [s.get("location", "") for s in item.get("secondaryLocations") or []]
            addr = ((item.get("address") or {}).get("postalAddress") or {}).get("addressCountry") or ""
            loc = next((l for l in locs if is_india_location(l)), "")
            if not loc and is_india_location(addr):
                loc = f"{locs[0]}, India".strip(", ")
            comp = item.get("compensation") or {}
            salary = ""
            if item.get("shouldDisplayCompensationOnJobPostings"):
                salary = comp.get("scrapeableCompensationSalarySummary") or comp.get("compensationTierSummary") or ""
            job = self._build(
                board, ats_key="ashby", posting_id=str(item.get("id")), title=item.get("title"),
                raw_location=loc, jd=item.get("descriptionPlain") or html_to_text(item.get("descriptionHtml") or ""),
                apply_url=item.get("jobUrl") or item.get("applyUrl") or "",
                published=item.get("publishedAt"), employment_type=item.get("employmentType") or "",
                salary=salary,
            )
            if job:
                out.append(job)
        return out

    # ----------------------------------------------------- smartrecruiters
    def _smartrecruiters(self, board: Dict[str, str]) -> List[Dict[str, Any]]:
        from requirements.models import JobPosting

        base = f"https://api.smartrecruiters.com/v1/companies/{board['slug']}/postings"
        res = self.safe_get(base, params={"country": "in", "limit": 100})
        if not res or res.status_code != 200:
            return []
        data = res.json()
        if not data.get("totalFound"):  # unknown company returns 200 with 0 results
            return []

        # The list has no JD; one detail call per posting. Skip postings already
        # stored with a real JD so repeat cycles cost almost nothing.
        ids = [str(p.get("id")) for p in data.get("content", [])]
        known = set(
            JobPosting.objects.filter(
                source_name=self.source_name,
                source_job_id__in=[f"su_sr_{board['slug']}_{i}" for i in ids],
            ).exclude(description="").values_list("source_job_id", flat=True)
        )
        out = []
        for p in data.get("content", []):
            if len(out) >= self.max_jobs_per_board:
                break
            if f"su_sr_{board['slug']}_{p.get('id')}" in known:
                continue
            loc_obj = p.get("location") or {}
            if (loc_obj.get("country") or "").lower() != "in":
                continue
            det = self.safe_get(f"{base}/{p.get('id')}")
            if not det or det.status_code != 200:
                continue
            d = det.json()
            sections = (d.get("jobAd") or {}).get("sections") or {}
            jd_parts, qualifications = [], ""
            for key in ("jobDescription", "qualifications", "additionalInformation", "companyDescription"):
                sec = sections.get(key) or {}
                body = html_to_text(sec.get("text") or "")
                if body:
                    jd_parts.append(f"{sec.get('title') or ''}\n{body}".strip())
                    if key == "qualifications":
                        qualifications = body[:600]
            job = self._build(
                board, ats_key="sr", posting_id=str(p.get("id")), title=p.get("name"),
                raw_location=loc_obj.get("fullLocation") or f"{loc_obj.get('city', '')}, India",
                jd="\n\n".join(jd_parts), apply_url=d.get("postingUrl") or d.get("applyUrl") or "",
                published=p.get("releasedDate"),
                employment_type=(p.get("typeOfEmployment") or {}).get("label") or "",
                eligibility=qualifications,
            )
            if job:
                out.append(job)
        return out
