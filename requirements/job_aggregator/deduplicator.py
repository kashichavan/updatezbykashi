"""
Multi-Tier Conservative Job Deduplication and Ingestion Engine.
Prevents duplicate records while preserving source attribution and upgrading data quality.
Includes full-database duplicate sweep and purge mechanism.
"""

import re
import urllib.parse
from datetime import timedelta
from typing import Dict, Any, Tuple, Optional, Set, List
import logging

from django.utils import timezone
from django.db.models import Q

from requirements.models import JobPosting
from requirements.jobdexo_service import (
    get_or_create_standard_categories,
    classify_opportunity_category
)

logger = logging.getLogger(__name__)

# Common Indian & Global Corporate Entity Suffixes to strip during company normalization
COMPANY_LEGAL_SUFFIXES = [
    r'\bprivate\s+limited\b',
    r'\bpvt\s*\.?\s*ltd\s*\.?\b',
    r'\blimited\b',
    r'\bltd\s*\.?\b',
    r'\btechnologies\b',
    r'\btechnology\b',
    r'\bservices\b',
    r'\bsolutions\b',
    r'\bcorporation\b',
    r'\bcorp\s*\.?\b',
    r'\bincorporated\b',
    r'\binc\s*\.?\b',
    r'\bllc\b',
    r'\bllp\b',
    r'\bholding(s)?\b',
    r'\bgroup\b',
    r'\bindia\b',
]

# Common Indian Tech Employer Name Synonyms
COMPANY_SYNONYMS = {
    'tcs': 'tcs',
    'tata consultancy': 'tcs',
    'tata consultancy services': 'tcs',
    'infy': 'infosys',
    'infosys': 'infosys',
    'cts': 'cognizant',
    'cognizant': 'cognizant',
    'wipro': 'wipro',
    'hcl': 'hcl',
}

# Common Job Posting Title Noise (stripped without deleting essential skill names)
TITLE_NOISE_PATTERNS = [
    r'\bimmediate\s+joiner(s)?\b',
    r'\burgent\s+requirement\b',
    r'\bhiring\s+for\b',
    r'\bwalk[\s-]*in\b',
    r'\bwork\s+from\s+home\b',
    r'\bfull[\s-]*time\b',
    r'\bpart[\s-]*time\b',
    r'\bjob\s+opening\b',
    r'\boff[\s-]*campus\b',
    r'\bm[\s/]*f[\s/]*d\b',
]

# Tracking query parameters to strip from apply URLs
TRACKING_QUERY_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'ref', 'refid', 'trackingid', 'position', 'pagenum', 'mid', 'f_tpr',
    'origin', 'source', 'src', 'gh_jid', 'ashby_jid', 'trk'
}


def clean_canonical_job_url(raw_url: str) -> str:
    """
    Strips tracking query parameters and fragments to produce a canonical job URL.
    """
    if not raw_url or not isinstance(raw_url, str):
        return ""
    try:
        parsed = urllib.parse.urlparse(raw_url.strip())
        if not parsed.scheme or not parsed.netloc:
            return raw_url.strip()

        # Parse query params and strip tracking tokens
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        cleaned_pairs = [(k, v) for k, v in query_pairs if k.lower() not in TRACKING_QUERY_PARAMS]
        
        # Sort query pairs for determinism
        cleaned_pairs.sort(key=lambda x: x[0])
        new_query = urllib.parse.urlencode(cleaned_pairs)

        clean_path = parsed.path.rstrip('/')
        return urllib.parse.urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            clean_path,
            '',
            new_query,
            ''
        ))
    except Exception:
        return raw_url.strip().rstrip('/')


def normalize_company_name(comp: str) -> str:
    """
    Normalizes company names by lowercasing, stripping legal corporate suffixes
    and resolving standard synonyms.
    e.g. 'Infosys Limited' -> 'infosys', 'Tata Consultancy Services Pvt. Ltd.' -> 'tata consultancy'
    """
    if not comp:
        return ""
    
    clean = comp.lower().strip()
    
    # Check direct synonym
    if clean in COMPANY_SYNONYMS:
        clean = COMPANY_SYNONYMS[clean]

    # Strip legal entity suffixes
    for suffix in COMPANY_LEGAL_SUFFIXES:
        clean = re.sub(suffix, '', clean, flags=re.IGNORECASE)

    # Clean punctuation and excess whitespace
    clean = re.sub(r'[^a-z0-9\s]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Re-check synonym after stripping
    if clean in COMPANY_SYNONYMS:
        clean = COMPANY_SYNONYMS[clean]

    return clean


def normalize_job_title(title: str) -> str:
    """
    Normalizes job titles by removing parenthetical metadata, hiring noise, and extra whitespace.
    e.g. 'Software Engineer (Immediate Joiner / Bengaluru)' -> 'software engineer'
    """
    if not title:
        return ""
    clean = title.lower().strip()
    for pat in TITLE_NOISE_PATTERNS:
        clean = re.sub(pat, ' ', clean, flags=re.IGNORECASE)
    clean = re.sub(r'[^a-z0-9\s]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def calculate_token_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity index between alphanumeric token sets."""
    tokens1 = set(re.findall(r'[a-z0-9]+', (text1 or '').lower()))
    tokens2 = set(re.findall(r'[a-z0-9]+', (text2 or '').lower()))
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    return len(intersection) / max(len(tokens1), len(tokens2))


def find_existing_job_duplicate(job_data: Dict[str, Any], seen_in_batch: Optional[Set[str]] = None) -> Optional[JobPosting]:
    """
    Multi-tier conservative deduplication across sources:
    Tier 1: (source_name, source_job_id) match
    Tier 2: Canonical source_url / apply_url match
    Tier 3: Exact normalized (company + title + normalized_city)
    Tier 4: Exact normalized (company + title)
    Tier 5: Same base company + Token Jaccard similarity >= 0.70
    """
    source_name = job_data.get('source_name', '').strip()
    source_job_id = str(job_data.get('source_job_id', '')).strip()
    raw_title = job_data.get('title', '').strip()
    raw_comp = job_data.get('company_name', '').strip()
    apply_url = clean_canonical_job_url(job_data.get('apply_url', ''))
    source_url = clean_canonical_job_url(job_data.get('source_url', ''))
    city = job_data.get('normalized_city', 'Bengaluru').strip()

    norm_title = normalize_job_title(raw_title)
    norm_comp = normalize_company_name(raw_comp)

    # 0. In-memory batch duplicate check
    if seen_in_batch is not None:
        batch_key = f"{source_name}::{source_job_id}" if (source_name and source_job_id) else f"{norm_comp}::{norm_title}::{city}"
        if batch_key in seen_in_batch:
            return JobPosting.objects.filter(company_name__iexact=raw_comp, title__iexact=raw_title).first()
        seen_in_batch.add(batch_key)
        if apply_url:
            seen_in_batch.add(apply_url)

    # Tier 1: Source + Source Job ID
    if source_name and source_job_id:
        existing = JobPosting.objects.filter(source_name=source_name, source_job_id=source_job_id).first()
        if existing:
            return existing

    # Tier 2: Canonical Apply URL match (ignoring generic aggregator host)
    if apply_url and 'jobdexo.com' not in apply_url and len(apply_url) > 15:
        existing = JobPosting.objects.filter(
            Q(apply_url__iexact=apply_url) |
            Q(source_url__iexact=apply_url)
        ).first()
        if existing:
            return existing

    if source_url and 'jobdexo.com' not in source_url and len(source_url) > 15:
        existing = JobPosting.objects.filter(
            Q(apply_url__iexact=source_url) |
            Q(source_url__iexact=source_url)
        ).first()
        if existing:
            return existing

    # Tier 3, 4, & 5: Normalized Company + Title matching
    if norm_comp:
        # Candidate search across active jobs
        company_query = Q(company_name__iexact=raw_comp)
        if len(norm_comp) >= 3:
            company_query |= Q(company_name__icontains=norm_comp)

        candidates = JobPosting.objects.filter(company_query)

        for candidate in candidates:
            cand_comp = normalize_company_name(candidate.company_name)
            cand_title = normalize_job_title(candidate.title)
            cand_city = (candidate.normalized_city or '').strip().lower()

            # Exact company + title match
            if cand_comp == norm_comp and cand_title == norm_title:
                return candidate

            # Exact company + title + city match
            if cand_comp == norm_comp and cand_title == norm_title and (not city or not cand_city or city.lower() == cand_city):
                return candidate

            # Token similarity check for identical base company
            if cand_comp == norm_comp:
                sim = calculate_token_similarity(cand_title, norm_title)
                if sim >= 0.70:
                    return candidate

    return None


def merge_or_create_job(job_data: Dict[str, Any], batch_id: str = "") -> Tuple[JobPosting, bool]:
    """
    Ingest a job record idempotently:
    - If duplicate: update last_seen_at and preserve valid higher-quality fields.
    - If new: create JobPosting record with 7-day expiration policy and verified categorization.
    """
    existing = find_existing_job_duplicate(job_data)
    now = timezone.now()

    if existing:
        # Upgrade metadata on existing record without overwriting valid data
        existing.last_seen_at = now
        changed = ['last_seen_at']

        # If new record provides an exact publication timestamp and existing only had date/unknown
        if job_data.get('source_published_at') and existing.timestamp_precision in ['DATE_ONLY', 'UNKNOWN']:
            existing.source_published_at = job_data['source_published_at']
            existing.timestamp_precision = job_data.get('timestamp_precision', 'EXACT_TIMESTAMP')
            changed.extend(['source_published_at', 'timestamp_precision'])

        # Upgrade apply_url if existing had an aggregator redirect link and new has direct link
        new_apply = clean_canonical_job_url(job_data.get('apply_url', ''))
        if new_apply and 'jobdexo.com' in (existing.apply_url or '') and 'jobdexo.com' not in new_apply:
            existing.apply_url = new_apply
            changed.append('apply_url')

        # Upgrade description if existing description was short or placeholder
        new_desc = job_data.get('description', '')
        if len(new_desc) > len(existing.description or ''):
            existing.description = new_desc
            changed.append('description')

        # Upgrade skills if new skills are richer
        new_skills = job_data.get('skills_required', '')
        if len(new_skills) > len(existing.skills_required or ''):
            existing.skills_required = new_skills
            changed.append('skills_required')

        existing.save(update_fields=list(set(changed)))
        return existing, False

    # Create fresh JobPosting record
    cat_map = get_or_create_standard_categories()
    category = classify_opportunity_category(job_data, cat_map)
    domain = job_data.get('industry_domain', 'TECHNICAL')
    job_type = job_data.get('job_type', 'FULL_TIME')

    deadline = now + timedelta(days=7)
    posted_date = job_data.get('posted_date') or now.date()

    job = JobPosting.objects.create(
        title=job_data.get('title', 'Software Engineer'),
        company_name=job_data.get('company_name', 'Top Tech Employer'),
        company_logo_icon=job_data.get('company_logo_icon', 'building'),
        category=category,
        job_type=job_type,
        stipend_salary=job_data.get('stipend_salary', 'Competitive Package (Best in Industry)'),
        location=job_data.get('location', 'Bengaluru, India'),
        is_remote=job_data.get('is_remote', False),
        skills_required=job_data.get('skills_required', 'Problem Solving, Engineering'),
        apply_url=clean_canonical_job_url(job_data.get('apply_url', '')),
        allow_direct_apply=True,
        description=job_data.get('description', ''),
        eligibility=job_data.get('eligibility', 'Open to all graduates and working professionals'),
        selection_process=job_data.get('selection_process', ''),
        study_materials=job_data.get('study_materials', []),
        status='ACTIVE',
        is_featured=job_data.get('is_featured', True),
        posted_date=posted_date,
        deadline=deadline,
        # Multi-source and Last-Hour Fields
        source_name=job_data.get('source_name', 'Aggregator'),
        source_job_id=job_data.get('source_job_id', ''),
        source_url=clean_canonical_job_url(job_data.get('source_url', '')),
        source_published_at=job_data.get('source_published_at', now),
        source_updated_at=job_data.get('source_updated_at'),
        first_seen_at=now,
        last_seen_at=now,
        timestamp_precision=job_data.get('timestamp_precision', 'EXACT_TIMESTAMP'),
        industry_domain=domain,
        experience_tier=job_data.get('experience_tier', 'FRESHER'),
        normalized_city=job_data.get('normalized_city', 'Bengaluru'),
        ingestion_batch_id=batch_id,
    )

    return job, True


def purge_all_database_duplicates(dry_run: bool = False) -> Dict[str, Any]:
    """
    Exhaustive sweep of all JobPosting records in the database to detect,
    merge, and purge cross-source duplicate listings.

    Algorithm:
    1. Fetches all active JobPosting records.
    2. Clusters duplicates using:
       - Canonical apply URL
       - (norm_company, norm_title, city)
       - norm_company with token Jaccard similarity >= 0.70
    3. Within each cluster:
       - Elects the highest quality record as primary 'winner' (longest description, earliest created).
       - Merges metadata (latest last_seen_at, direct apply_url, richest skills).
       - Deletes all other redundant records.
    """
    all_jobs = list(JobPosting.objects.filter(status='ACTIVE').order_by('id'))
    total_scanned = len(all_jobs)

    # Union-Find / Disjoint Set to group duplicate IDs
    parent: Dict[int, int] = {job.id: job.id for job in all_jobs}

    def find_root(i: int) -> int:
        if parent[i] == i:
            return i
        parent[i] = find_root(parent[i])
        return parent[i]

    def union(i: int, j: int):
        root_i = find_root(i)
        root_j = find_root(j)
        if root_i != root_j:
            parent[root_i] = root_j

    # Index lookups
    url_to_id: Dict[str, int] = {}
    comp_title_city_to_id: Dict[str, int] = {}
    company_buckets: Dict[str, List[JobPosting]] = {}

    for job in all_jobs:
        clean_url = clean_canonical_job_url(job.apply_url)
        norm_comp = normalize_company_name(job.company_name)
        norm_title = normalize_job_title(job.title)
        city = (job.normalized_city or '').lower().strip()

        # 1. URL match (ignoring generic aggregator)
        if clean_url and 'jobdexo.com' not in clean_url and len(clean_url) > 15:
            if clean_url in url_to_id:
                union(job.id, url_to_id[clean_url])
            else:
                url_to_id[clean_url] = job.id

        # 2. Company + Title + City match
        if norm_comp and norm_title:
            ctc_key = f"{norm_comp}::{norm_title}::{city}"
            if ctc_key in comp_title_city_to_id:
                union(job.id, comp_title_city_to_id[ctc_key])
            else:
                comp_title_city_to_id[ctc_key] = job.id

            # Also group by company for fuzzy title matching
            company_buckets.setdefault(norm_comp, []).append(job)

    # 3. Fuzzy Title Matching within same company
    for comp, jobs_in_comp in company_buckets.items():
        if len(jobs_in_comp) < 2:
            continue
        n = len(jobs_in_comp)
        for a in range(n):
            for b in range(a + 1, n):
                job_a = jobs_in_comp[a]
                job_b = jobs_in_comp[b]
                if find_root(job_a.id) == find_root(job_b.id):
                    continue
                sim = calculate_token_similarity(job_a.title, job_b.title)
                if sim >= 0.70:
                    union(job_a.id, job_b.id)

    # Group job instances by root ID
    clusters: Dict[int, List[JobPosting]] = {}
    jobs_by_id = {j.id: j for j in all_jobs}

    for job in all_jobs:
        root = find_root(job.id)
        clusters.setdefault(root, []).append(job)

    # Process clusters with > 1 job (duplicates)
    duplicate_clusters = 0
    total_duplicates_found = 0
    records_to_delete: List[int] = []
    primary_records_updated = 0
    details = []

    for root_id, group in clusters.items():
        if len(group) <= 1:
            continue

        duplicate_clusters += 1
        total_duplicates_found += (len(group) - 1)

        # Pick primary winner:
        # Sort key: longer description > earlier created (lower ID) > has direct URL
        def sort_key(j: JobPosting):
            desc_len = len(j.description or '')
            has_direct_url = 1 if ('jobdexo.com' not in (j.apply_url or '')) else 0
            return (has_direct_url, desc_len, -j.id)

        sorted_group = sorted(group, key=sort_key, reverse=True)
        winner = sorted_group[0]
        losers = sorted_group[1:]

        # Merge metadata from losers into winner
        fields_to_update = set()
        for loser in losers:
            # Upgrade last_seen_at
            if loser.last_seen_at and (not winner.last_seen_at or loser.last_seen_at > winner.last_seen_at):
                winner.last_seen_at = loser.last_seen_at
                fields_to_update.add('last_seen_at')

            # Upgrade skills
            if len(loser.skills_required or '') > len(winner.skills_required or ''):
                winner.skills_required = loser.skills_required
                fields_to_update.add('skills_required')

            # Upgrade apply_url if winner is on aggregator and loser has direct source URL
            if 'jobdexo.com' in (winner.apply_url or '') and 'jobdexo.com' not in (loser.apply_url or ''):
                winner.apply_url = loser.apply_url
                fields_to_update.add('apply_url')

            records_to_delete.append(loser.id)

        if fields_to_update and not dry_run:
            winner.save(update_fields=list(fields_to_update))
            primary_records_updated += 1

        details.append({
            'primary_id': winner.id,
            'title': winner.title,
            'company': winner.company_name,
            'duplicate_ids': [l.id for l in losers],
            'duplicate_count': len(losers),
        })

    # Soft-close duplicate records instead of hard-deleting to prevent 404 on shared URLs
    deleted_count = 0
    if records_to_delete and not dry_run:
        deleted_count = JobPosting.objects.filter(id__in=records_to_delete).update(
            status='CLOSED',
            is_featured=False
        )

    logger.info(
        f"[Deduplicator Purge] Scanned: {total_scanned}, "
        f"Duplicate Groups: {duplicate_clusters}, "
        f"Duplicates Closed: {deleted_count} (dry_run={dry_run})"
    )

    return {
        'scanned_total': total_scanned,
        'duplicate_clusters': duplicate_clusters,
        'duplicates_found': total_duplicates_found,
        'duplicates_deleted': deleted_count if not dry_run else 0,
        'primary_records_updated': primary_records_updated,
        'dry_run': dry_run,
        'details': details[:50],  # Return first 50 groups
    }
