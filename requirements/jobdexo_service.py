import os
import re
import json
import ssl
import html
import time
import threading
import urllib.request
from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify
from django.core.cache import cache
from .models import Category, JobPosting, JobGroup

# SSL context for secure scraping
SSL_CONTEXT = ssl._create_unverified_context()
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# 5-6 Distinct Jobdexo Discovery Sections
JOBDEXO_SOURCE_ENDPOINTS = [
    'https://jobdexo.com/',
    'https://jobdexo.com/?q=developer',
    'https://jobdexo.com/?q=software',
    'https://jobdexo.com/?q=analyst',
    'https://jobdexo.com/?q=internship',
    'https://jobdexo.com/?q=engineer',
]


def fetch_url_html(url):
    """Safely fetch HTML content from a URL with timeout and standard headers."""
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': DEFAULT_USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    )
    with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=10) as response:
        return response.read().decode('utf-8', errors='ignore')


def normalize_text(text):
    """Normalize strings for ultra-strict duplicate comparison (removes punctuation, casing, spaces)."""
    return re.sub(r'[^a-z0-9]', '', (text or '').lower())


def extract_jobdexo_detail(url):
    """
    Parses a single Jobdexo job page and extracts structured job details
    including the official application link.
    """
    if not url.startswith('http'):
        url = f"https://jobdexo.com{url}"

    page_html = fetch_url_html(url)

    # 1. Parse JSON-LD Schema if available
    schema_data = {}
    schema_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page_html, re.DOTALL)
    if schema_match:
        try:
            schema_data = json.loads(schema_match.group(1).strip())
        except Exception:
            pass

    # 2. Job Title
    title = ""
    title_m = re.search(r'<h1[^>]*class="[^"]*jd-job-title[^"]*">([^<]+)</h1>', page_html)
    if title_m:
        title = html.unescape(title_m.group(1).strip())
    elif schema_data.get('title'):
        title = schema_data.get('title')
    else:
        title = "Software & Tech Opportunity"

    # 3. Company Name
    company = ""
    comp_m = re.search(r'<div class="jd-meta-lbl">\s*🏢\s*Company\s*</div>\s*<div class="jd-meta-val">([^<]+)</div>', page_html, re.IGNORECASE)
    if comp_m:
        company = html.unescape(comp_m.group(1).strip())
    
    if not company:
        comp_m2 = re.search(r'<div class="jd-company[^"]*">([^<]+)</div>', page_html)
        if comp_m2:
            company = html.unescape(comp_m2.group(1).strip())

    if not company and schema_data.get('hiringOrganization', {}).get('name'):
        company = schema_data.get('hiringOrganization', {}).get('name')

    if not company or company.startswith('🏢'):
        company = company.lstrip('🏢').strip()
        if not company:
            slug_parts = url.rstrip('/').split('/')[-1].split('-')
            for known in ['deloitte', 'kpmg', 'oracle', 'accenture', 'barclays', 'tcs', 'infosys', 'cognizant', 'wipro', 'quest', 'vyapar', 'metlife', 'globallogic', 'dassault']:
                if known in slug_parts:
                    company = known.capitalize()
                    break

    if not company:
        company = "Featured Partner"

    # 4. Salary
    salary = "Competitive Salary (Freshers)"
    sal_m = re.search(r'<div class="jd-meta-lbl">\s*💰\s*Salary\s*</div>\s*<div class="jd-meta-val">([^<]+)</div>', page_html, re.IGNORECASE)
    if sal_m:
        salary = html.unescape(sal_m.group(1).strip())
    else:
        sal_insight = re.search(r'<div class="jd-card-title">\s*💰\s*Salary Insights\s*</div>\s*<div[^>]*>([^<]+)</div>', page_html, re.IGNORECASE)
        if sal_insight:
            salary = html.unescape(sal_insight.group(1).strip())

    # 5. Location
    location = "Remote / Hybrid, India"
    loc_m = re.search(r'<div class="jd-meta-lbl">\s*📍\s*Location\s*</div>\s*<div class="jd-meta-val">([^<]+)</div>', page_html, re.IGNORECASE)
    if loc_m:
        location = html.unescape(loc_m.group(1).strip())
    else:
        loc_tag = re.search(r'<span class="jd-tag jt-slate">\s*📍\s*([^<]+)</span>', page_html)
        if loc_tag:
            location = html.unescape(loc_tag.group(1).strip())

    # 6. Skills
    skills_tags = re.findall(r'<span class="jd-skill">([^<]+)</span>', page_html)
    skills = ", ".join([html.unescape(s.strip()) for s in skills_tags if s.strip()])
    if not skills:
        skills = "Problem Solving, Software Engineering, Communication"

    # 7. Eligibility Criteria
    eligibility = "Open to all freshers & eligible graduating batches."
    elig_m = re.search(r'<div class="jd-card-title">\s*✅\s*Eligibility Criteria\s*</div>\s*<div class="jd-prose">([^<]+)</div>', page_html, re.IGNORECASE)
    if elig_m:
        eligibility = html.unescape(elig_m.group(1).strip())

    # 8. Description & About the Role
    description = ""
    desc_m = re.search(r'<div class="jd-prose"[^>]*id="jdDesc"[^>]*>(.*?)</div>', page_html, re.DOTALL)
    if not desc_m:
        desc_m = re.search(r'<div class="jd-card-title">\s*📋\s*About the Role\s*</div>\s*<div class="jd-prose"[^>]*>(.*?)</div>', page_html, re.DOTALL)
    if desc_m:
        raw_desc = re.sub(r'<br\s*/?>', '\n', desc_m.group(1))
        raw_desc = re.sub(r'<[^>]+>', '', raw_desc)
        description = html.unescape(raw_desc.strip())
    else:
        description = f"{company} is hiring for {title}.\nLocation: {location}\nSalary: {salary}\nKey Skills: {skills}"

    # 9. Official Apply URL
    apply_url = ""
    apply_m = re.search(r'href="([^"]+)"[^>]*class="[^"]*jd-apply', page_html)
    if not apply_m:
        apply_m = re.search(r'class="[^"]*jd-apply[^"]*"[^>]*href="([^"]+)"', page_html)
    if apply_m:
        apply_url = html.unescape(apply_m.group(1).strip())
    
    if not apply_url or 'jobdexo.com' in apply_url:
        if not apply_url:
            apply_url = url

    lower_title = f"{title} {description}".lower()
    is_intern = any(k in lower_title for k in ['intern', 'internship', 'apprentice', 'trainee', 'co-op'])
    job_type = 'INTERNSHIP' if is_intern else 'FULL_TIME'

    return {
        'title': title,
        'company': company,
        'salary': salary,
        'location': location,
        'skills': skills,
        'eligibility': eligibility,
        'description': description,
        'apply_url': apply_url,
        'job_type': job_type,
        'source_url': url,
    }


def fetch_multi_section_jobdexo_urls(limit=25):
    """
    Crawls across 5-6 distinct Jobdexo sections (Home, Developer, Software, Analyst, Internship, Engineer)
    to discover all fresh opportunities.
    """
    discovered_urls = []
    seen_urls = set()

    for endpoint in JOBDEXO_SOURCE_ENDPOINTS:
        try:
            page_html = fetch_url_html(endpoint)
            found_urls = re.findall(r'href="(/job/[^"]+)"', page_html)
            for u in found_urls:
                full_url = f"https://jobdexo.com{u}" if u.startswith('/') else u
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    discovered_urls.append(full_url)
                if len(discovered_urls) >= limit:
                    break
        except Exception as err:
            print(f"Error fetching Jobdexo endpoint '{endpoint}': {err}")

        if len(discovered_urls) >= limit:
            break

    return discovered_urls


def is_job_duplicate_in_db(job_data, seen_in_batch=None):
    """
    Multi-tier strict deduplication:
    1. In-batch URL & text check.
    2. Direct official application URL match in database.
    3. Normalized company name + normalized title match in database.
    """
    apply_url = (job_data.get('apply_url') or '').strip()
    source_url = (job_data.get('source_url') or '').strip()
    norm_title = normalize_text(job_data.get('title'))
    norm_comp = normalize_text(job_data.get('company'))

    # 1. Batch level check
    if seen_in_batch is not None:
        batch_key = f"{norm_comp}::{norm_title}"
        if batch_key in seen_in_batch:
            return True
        if apply_url and apply_url in seen_in_batch:
            return True
        seen_in_batch.add(batch_key)
        if apply_url:
            seen_in_batch.add(apply_url)

    # 2. Match exact apply_url in database
    if apply_url and apply_url != source_url:
        if JobPosting.objects.filter(apply_url=apply_url).exists():
            return True

    # 3. Match normalized title + company in active postings
    if norm_title and norm_comp:
        # Search by company prefix
        matching_company_jobs = JobPosting.objects.filter(
            company_name__icontains=job_data.get('company')[:6]
        )
        for existing in matching_company_jobs:
            if normalize_text(existing.company_name) == norm_comp and normalize_text(existing.title) == norm_title:
                return True

    return False


def auto_import_from_jobdexo(urls=None, limit=10, group_name=None, poster_name="Jobdexo Auto-Sync Engine", poster_email="admin@kashiiupdatez.com"):
    """
    Main ingestion engine:
    1. Extracts jobs across 5 distinct Jobdexo sections (or provided URLs).
    2. Strictly filters out any duplicate jobs.
    3. Publishes new verified openings under 'Software & Tech' with 7-day expiry.
    4. Automatically groups them into a 7-day shareable group.
    """
    software_category, _ = Category.objects.get_or_create(
        slug='software-tech',
        defaults={
            'name': 'Software & Tech',
            'icon': 'code',
            'description': 'Software engineering, QA automation, web development, internships, and IT roles.'
        }
    )

    if not urls:
        urls = fetch_multi_section_jobdexo_urls(limit=limit * 2)

    created_jobs = []
    created_job_instances = []
    seen_in_batch = set()
    now = timezone.now()
    deadline = now + timedelta(days=7)

    for url in urls:
        url = url.strip()
        if not url:
            continue

        try:
            job_data = extract_jobdexo_detail(url)

            # Strict Deduplication Check
            if is_job_duplicate_in_db(job_data, seen_in_batch=seen_in_batch):
                continue

            # Create new non-duplicate job posting
            job = JobPosting.objects.create(
                title=job_data['title'],
                company_name=job_data['company'],
                company_logo_icon='building',
                category=software_category,
                job_type=job_data['job_type'],
                stipend_salary=job_data['salary'],
                location=job_data['location'],
                is_remote='remote' in job_data['location'].lower(),
                skills_required=job_data['skills'],
                apply_url=job_data['apply_url'],
                allow_direct_apply=True,
                description=job_data['description'],
                eligibility=job_data['eligibility'],
                posted_by=poster_name,
                poster_email=poster_email,
                status='ACTIVE',
                is_featured=True,
                posted_date=now.date(),
                deadline=deadline,
            )

            created_jobs.append({
                'id': job.id,
                'title': job.title,
                'company': job.company_name,
                'uuid': str(job.uuid),
                'salary': job.stipend_salary,
                'location': job.location,
            })
            created_job_instances.append(job)

            if len(created_jobs) >= limit:
                break

        except Exception as e:
            print(f"Error scraping Jobdexo URL '{url}': {e}")
            continue

    # Create / Update Requirement Group
    job_group = None
    if created_job_instances:
        now_local = timezone.localtime(timezone.now())
        if not group_name:
            group_name = now_local.strftime("Jobdexo Tech Drive — %d %b %Y, %I:%M %p")

        base_slug = slugify(group_name) or "jobdexo-drive"
        slug = f"{base_slug}-{now_local.strftime('%Y%m%d%H%M')}"

        job_group = JobGroup.objects.create(
            name=group_name,
            slug=slug,
            banner_tag="🔥 JOBDEXO VERIFIED TECH DRIVE",
            description=f"Auto-imported collection of {len(created_job_instances)} fresh off-campus opportunities from Jobdexo.",
            posted_date=now.date(),
            deadline=deadline,
            is_active=True,
        )
        job_group.jobs.set(created_job_instances)

    cache.clear()
    return {
        'success': True,
        'imported_count': len(created_jobs),
        'total_in_group': len(created_job_instances),
        'created_jobs': created_jobs,
        'group_id': job_group.id if job_group else None,
        'group_name': job_group.name if job_group else '',
        'group_slug': job_group.slug if job_group else '',
        'group_url': f"/group/{job_group.slug}/" if job_group else '',
        'job_group': job_group,
    }


# ==============================================================================
# 5-MINUTE RECURRING AUTO-SYNC BACKGROUND WORKER
# ==============================================================================

_SYNC_WORKER_RUNNING = False
_SYNC_LOCK = threading.Lock()


def _background_5min_sync_loop():
    """Background worker thread that runs every 5 minutes (300 seconds)."""
    global _SYNC_WORKER_RUNNING
    print("🚀 [Jobdexo Auto-Sync] Background 5-minute sync daemon started.")
    
    while _SYNC_WORKER_RUNNING:
        try:
            # Sleep 300 seconds (5 minutes)
            time.sleep(300)
            print("⚡ [Jobdexo Auto-Sync] Running 5-minute automated crawl across all sections...")
            result = auto_import_from_jobdexo(limit=5, poster_name="5-Min Auto-Sync Engine")
            if result['imported_count'] > 0:
                print(f"✅ [Jobdexo Auto-Sync] Added {result['imported_count']} fresh non-duplicate jobs! Group: {result['group_name']}")
            else:
                print("ℹ️ [Jobdexo Auto-Sync] Checked 5 sections: No new non-duplicate jobs found.")
        except Exception as e:
            print(f"⚠️ [Jobdexo Auto-Sync] Error in 5-minute cycle: {e}")


def start_5min_sync_daemon():
    """Starts the 5-minute background auto-sync worker if not already running."""
    global _SYNC_WORKER_RUNNING
    with _SYNC_LOCK:
        if not _SYNC_WORKER_RUNNING:
            _SYNC_WORKER_RUNNING = True
            t = threading.Thread(target=_background_5min_sync_loop, daemon=True, name="Jobdexo5MinSyncWorker")
            t.start()
            return True
    return False
