"""
Location, Domain, Experience, and Timestamp Normalization Utilities
for India-Wide Job Aggregation.
"""

import re
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Tuple, Optional
from django.utils import timezone

from .constants import (
    INDIAN_CITY_CANONICAL_MAP,
    TECHNICAL_KEYWORDS,
    NON_TECHNICAL_KEYWORDS,
    EXPERIENCE_KEYWORDS
)


# Strict list of international countries, European / German cities, and foreign hubs
FOREIGN_EXCLUSIVES = [
    'germany', 'deutschland', 'berlin', 'munich', 'münchen', 'frankfurt', 'chemnitz',
    'hamburg', 'cologne', 'köln', 'stuttgart', 'düsseldorf', 'leipzig', 'dortmund',
    'essen', 'bremen', 'dresden', 'hannover', 'nuremberg', 'nürnberg', 'biberach',
    'hofheim', 'bad wurzach', 'austria', 'vienna', 'wien', 'switzerland', 'zurich',
    'zürich', 'geneva', 'united states', 'usa', 'u.s.', 'united kingdom', 'uk', 'london',
    'canada', 'toronto', 'vancouver', 'australia', 'sydney', 'melbourne', 'singapore',
    'france', 'paris', 'netherlands', 'amsterdam', 'dubai', 'uae', 'qatar', 'poland',
    'warsaw', 'ireland', 'dublin', 'spain', 'madrid', 'barcelona', 'italy', 'rome', 'milan',
    'japan', 'tokyo', 'china', 'beijing', 'shanghai', 'malaysia', 'philippines', 'brazil',
    'mexico', 'south africa', 'new zealand', 'auckland', 'russia', 'moscow', 'sweden', 'stockholm',
]


def normalize_indian_location(raw_loc: str) -> Tuple[str, bool, bool]:
    """
    Normalizes a raw location string into:
    (normalized_city, is_remote, is_valid_india)
    
    Guarantees pure Indian jobs only:
    - Rejects foreign locations (e.g. Germany, UK, USA, Singapore, etc.)
    - Maps recognized Indian metro hubs and cities
    - Flags remote opportunities if India-friendly
    """
    if not raw_loc or not str(raw_loc).strip():
        return "Bengaluru", False, True  # Default Indian tech capital

    clean_loc = str(raw_loc).lower().strip()

    # Remote detection
    is_remote = any(w in clean_loc for w in ['remote', 'wfh', 'work from home', 'virtual', 'anywhere'])

    # Strict rejection of explicit foreign locations
    if any(f in clean_loc for f in FOREIGN_EXCLUSIVES):
        return "International", False, False

    # Check for direct canonical Indian city match
    for alias, canonical in INDIAN_CITY_CANONICAL_MAP.items():
        pattern = r'\b' + re.escape(alias) + r'\b'
        if re.search(pattern, clean_loc):
            return canonical, is_remote, True

    if 'india' in clean_loc or 'pan india' in clean_loc:
        return "India (Multiple Cities)", is_remote, True

    if is_remote:
        return "Remote", True, True

    # If location is unknown and does not mention India or Indian city, reject
    return "International", False, False


def classify_industry_domain(title: str = "", skills: str = "", description: str = "") -> str:
    """
    Classify whether a job belongs to TECHNICAL or NON_TECHNICAL domain.
    """
    text = f"{title} {skills} {description}".lower()
    
    # Check title specifically first (higher weight)
    title_lower = (title or "").lower()
    for kw in TECHNICAL_KEYWORDS:
        if kw in title_lower:
            return 'TECHNICAL'
    for kw in NON_TECHNICAL_KEYWORDS:
        if kw in title_lower:
            return 'NON_TECHNICAL'

    # Overlap analysis
    tech_score = sum(1 for kw in TECHNICAL_KEYWORDS if kw in text)
    non_tech_score = sum(1 for kw in NON_TECHNICAL_KEYWORDS if kw in text)

    if non_tech_score > tech_score:
        return 'NON_TECHNICAL'
    return 'TECHNICAL'


def classify_experience_tier(title: str = "", eligibility: str = "", description: str = "") -> str:
    """
    Classify candidate experience requirement:
    INTERNSHIP, FRESHER, EARLY_CAREER, MID_LEVEL, or SENIOR_LEVEL.
    """
    title_lower = (title or '').lower()
    text = f"{title_lower} {eligibility} {description}".lower()

    # 1. Internship check
    for kw in EXPERIENCE_KEYWORDS['INTERNSHIP']:
        if kw in text:
            return 'INTERNSHIP'

    # 2. Senior / Lead check in title
    for kw in EXPERIENCE_KEYWORDS['SENIOR_LEVEL']:
        if kw in title_lower:
            return 'SENIOR_LEVEL'

    # 3. Numeric range check (e.g. 10-13 Yrs, 5-8 Yrs, 0-1 Yrs)
    range_match = re.search(r'(\d+)\s*(?:-|to|–)\s*(\d+)\s*(?:yrs|years?|year)', text)
    if range_match:
        min_yr = int(range_match.group(1))
        max_yr = int(range_match.group(2))
        if min_yr >= 5 or max_yr >= 7:
            return 'SENIOR_LEVEL'
        elif min_yr >= 3 or max_yr >= 5:
            return 'MID_LEVEL'
        elif min_yr >= 1:
            return 'EARLY_CAREER'
        elif min_yr == 0 and max_yr <= 2:
            return 'FRESHER'

    # Single number check (e.g. 8+ Yrs, 5 Yrs)
    single_match = re.search(r'(\d+)\+?\s*(?:yrs|years?|year)', text)
    if single_match:
        val = int(single_match.group(1))
        if val >= 5:
            return 'SENIOR_LEVEL'
        elif val >= 3:
            return 'MID_LEVEL'
        elif val >= 1:
            return 'EARLY_CAREER'
        elif val == 0:
            return 'FRESHER'

    # 4. Fresher signals
    for kw in EXPERIENCE_KEYWORDS['FRESHER']:
        if kw in text:
            return 'FRESHER'

    # 5. Mid level signals
    for kw in EXPERIENCE_KEYWORDS['MID_LEVEL']:
        if kw in text:
            return 'MID_LEVEL'

    # 6. Early career signals
    for kw in EXPERIENCE_KEYWORDS['EARLY_CAREER']:
        if kw in text:
            return 'EARLY_CAREER'

    return 'FRESHER'


def parse_job_timestamps(raw_val, precision_hint: str = "DATE_ONLY") -> Tuple[datetime, str]:
    """
    Parses diverse timestamp formats (ISO-8601, epoch seconds/ms, relative time, date strings)
    into a timezone-aware UTC datetime and standardized precision level:
    - EXACT_TIMESTAMP (hour & minute precision available)
    - APPROXIMATE_TIME (e.g. '15 mins ago', relative estimation)
    - DATE_ONLY (day level)
    - UNKNOWN
    """
    now = timezone.now()

    if isinstance(raw_val, datetime):
        if timezone.is_naive(raw_val):
            return timezone.make_aware(raw_val, dt_timezone.utc), precision_hint
        return raw_val.astimezone(dt_timezone.utc), precision_hint

    if isinstance(raw_val, (int, float)):
        # Epoch timestamp in seconds or milliseconds
        val_sec = raw_val / 1000.0 if raw_val > 1e11 else raw_val
        dt = datetime.fromtimestamp(val_sec, tz=dt_timezone.utc)
        return dt, 'EXACT_TIMESTAMP'

    if not raw_val or not isinstance(raw_val, str):
        return now, 'UNKNOWN'

    raw_str = raw_val.strip()

    # Relative time parsing (e.g. "25 minutes ago", "1 hour ago", "just now", "2d ago")
    rel_lower = raw_str.lower()
    if 'just now' in rel_lower or 'moments ago' in rel_lower:
        return now, 'APPROXIMATE_TIME'

    min_match = re.search(r'(\d+)\s*(m|min|minute)s?\s*ago', rel_lower)
    if min_match:
        minutes = int(min_match.group(1))
        return now - timedelta(minutes=minutes), 'APPROXIMATE_TIME'

    hr_match = re.search(r'(\d+)\s*(h|hr|hour)s?\s*ago', rel_lower)
    if hr_match:
        hours = int(hr_match.group(1))
        return now - timedelta(hours=hours), 'APPROXIMATE_TIME'

    day_match = re.search(r'(\d+)\s*(d|day)s?\s*ago', rel_lower)
    if day_match:
        days = int(day_match.group(1))
        return now - timedelta(days=days), 'DATE_ONLY'

    if 'yesterday' in rel_lower:
        return now - timedelta(days=1), 'DATE_ONLY'

    # ISO 8601 formats (e.g., "2026-10-22T08:30:00Z", "2026-10-22T14:00:00+05:30")
    iso_candidates = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%b %d, %Y",
    ]

    for fmt in iso_candidates:
        try:
            parsed = datetime.strptime(raw_str.replace("Z", "+0000") if fmt.endswith("%z") else raw_str, fmt)
            if timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed, dt_timezone.utc)
            else:
                parsed = parsed.astimezone(dt_timezone.utc)
            
            precision = 'DATE_ONLY' if ('%H' not in fmt) else 'EXACT_TIMESTAMP'
            return parsed, precision
        except (ValueError, TypeError):
            continue

    return now, 'DATE_ONLY'
