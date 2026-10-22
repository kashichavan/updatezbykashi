"""
Multi-Tier Conservative Job Deduplication and Ingestion Engine.
Prevents duplicate records while preserving source attribution and upgrading data quality.
"""

import re
import urllib.parse
from datetime import timedelta
from typing import Dict, Any, Tuple, Optional, Set

from django.utils import timezone
from django.db.models import Q

from requirements.models import JobPosting, Category
from requirements.jobdexo_service import canonical_clean_url, normalize_text, get_or_create_standard_categories


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
    Multi-tier conservative deduplication:
    Tier 1: (source_name, source_job_id) match
    Tier 2: Canonical source_url / apply_url match
    Tier 3: Exact normalized (company + title + normalized_city)
    Tier 4: Same company + Token Jaccard similarity >= 0.75
    """
    source_name = job_data.get('source_name', '').strip()
    source_job_id = str(job_data.get('source_job_id', '')).strip()
    raw_title = job_data.get('title', '').strip()
    raw_comp = job_data.get('company_name', '').strip()
    apply_url = canonical_clean_url(job_data.get('apply_url', ''))
    source_url = canonical_clean_url(job_data.get('source_url', ''))
    city = job_data.get('normalized_city', 'Bengaluru').strip()

    norm_title = normalize_text(raw_title)
    norm_comp = normalize_text(raw_comp)

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

    # Tier 2: Canonical Apply URL match
    if apply_url and 'jobdexo.com' not in apply_url:
        existing = JobPosting.objects.filter(apply_url__iexact=apply_url).first()
        if existing:
            return existing

    # Tier 3 & 4: Company + Title matching
    if raw_comp:
        company_matches = JobPosting.objects.filter(
            Q(company_name__iexact=raw_comp) |
            Q(company_name__iexact=raw_comp.replace(' ', '')) |
            Q(company_name__icontains=raw_comp)
        )

        for candidate in company_matches:
            # Exact normalized title match
            if normalize_text(candidate.title) == norm_title:
                return candidate

            # High token similarity for identical company
            similarity = calculate_token_similarity(candidate.title, raw_title)
            if similarity >= 0.75:
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

        # If new record provides an exact publication timestamp and existing only had date
        if job_data.get('source_published_at') and existing.timestamp_precision in ['DATE_ONLY', 'UNKNOWN']:
            existing.source_published_at = job_data['source_published_at']
            existing.timestamp_precision = job_data.get('timestamp_precision', 'EXACT_TIMESTAMP')
            changed.extend(['source_published_at', 'timestamp_precision'])

        # Upgrade apply_url if existing had a redirect or intermediary link
        new_apply = canonical_clean_url(job_data.get('apply_url', ''))
        if new_apply and 'jobdexo.com' in (existing.apply_url or '') and 'jobdexo.com' not in new_apply:
            existing.apply_url = new_apply
            changed.append('apply_url')

        existing.save(update_fields=list(set(changed)))
        return existing, False

    # Create fresh JobPosting record
    cat_map = get_or_create_standard_categories()
    domain = job_data.get('industry_domain', 'TECHNICAL')
    job_type = job_data.get('job_type', 'FULL_TIME')

    if job_type == 'INTERNSHIP':
        category = cat_map.get('internships', cat_map.get('software-engineering'))
    elif domain == 'NON_TECHNICAL':
        category = cat_map.get('non-it', cat_map.get('software-engineering'))
    else:
        # Check for data / AI keywords
        title_lower = (job_data.get('title') or '').lower()
        if any(w in title_lower for w in ['data', 'ai', 'ml', 'analytics', 'machine learning']):
            category = cat_map.get('data-science-ai', cat_map.get('software-engineering'))
        elif any(w in title_lower for w in ['cloud', 'devops', 'aws', 'security']):
            category = cat_map.get('cybersecurity', cat_map.get('software-engineering'))
        else:
            category = cat_map.get('software-engineering')

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
        apply_url=job_data.get('apply_url', ''),
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
        source_url=job_data.get('source_url', ''),
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
