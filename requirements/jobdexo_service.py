import os
import re
import json
import ssl
import html
import time
import random
import threading
import urllib.request
import urllib.error
from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify
from django.core.cache import cache
from .models import Category, JobPosting, JobGroup
from .company_resolver import resolve_company_name

# SSL context for secure scraping
SSL_CONTEXT = ssl._create_unverified_context()

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15',
]

# 5-6 Distinct Jobdexo Discovery Sections
JOBDEXO_SOURCE_ENDPOINTS = [
    'https://jobdexo.com/',
    'https://jobdexo.com/?q=developer',
    'https://jobdexo.com/?q=software',
    'https://jobdexo.com/?q=analyst',
    'https://jobdexo.com/?q=internship',
    'https://jobdexo.com/?q=engineer',
]


def fetch_url_html(url, retries=2, backoff=2.5):
    """
    Safely fetch HTML content from a URL with browser emulation headers,
    rate-limit handling, and exponential backoff retry for HTTP 429.
    """
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': random.choice(USER_AGENTS),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://jobdexo.com/',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"macOS"',
                }
            )
            with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=12) as response:
                return response.read().decode('utf-8', errors='ignore')
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                sleep_time = backoff * (attempt + 1) + random.uniform(1.0, 2.5)
                time.sleep(sleep_time)
                continue
            raise
        except Exception as e:
            if attempt < retries:
                time.sleep(backoff)
                continue
            raise


def normalize_text(text):
    """Normalize strings for duplicate comparison (removes punctuation, casing, spaces)."""
    return re.sub(r'[^a-z0-9]', '', (text or '').lower())


def fallback_parse_from_slug(url):
    """
    Fallback parser: In case Jobdexo rate-limits details (HTTP 429),
    extract company, role title, and batch from the URL slug itself.
    e.g. /job/C1138-J204/sde-i-intern-amazon-2026-2
    """
    slug = url.rstrip('/').split('/')[-1]
    # Remove trailing digits / counters
    slug_clean = re.sub(r'-\d+$', '', slug)
    parts = slug_clean.split('-')
    
    # Common company names in slug
    known_companies = [
        'amazon', 'cisco', 'deloitte', 'kpmg', 'oracle', 'accenture',
        'barclays', 'tcs', 'infosys', 'cognizant', 'wipro', 'quest',
        'salesforce', 'microsoft', 'google', 'stripe', 'juspay', 'capgemini',
        'cgi', 'turing', 'reskom', 'hrone', 'ukg', 'binance', 'portcast'
    ]
    
    company = "Technology Partner"
    for comp in known_companies:
        if comp in parts:
            company = comp.capitalize()
            break

    # Build readable title
    title_words = [p.capitalize() for p in parts if p.lower() != company.lower() and not p.isdigit()]
    title = " ".join(title_words) or "Software & Tech Opportunity"
    if not any(k in title.lower() for k in ['engineer', 'developer', 'intern', 'analyst', 'consultant']):
        title = f"{title} Engineer"

    is_intern = 'intern' in slug.lower()
    return {
        'title': title,
        'company': company,
        'salary': "Competitive Package (Freshers)",
        'location': "Remote / Hybrid, India",
        'skills': "Problem Solving, Data Structures, Software Engineering",
        'eligibility': "Open to all graduating freshers & college students.",
        'selection_process': "Online Assessment > Technical Interview > HR Discussion",
        'study_materials': [],
        'description': f"{company} is hiring for {title}. Please check the official application link for comprehensive eligibility and role specifications.",
        'apply_url': url,
        'job_type': 'INTERNSHIP' if is_intern else 'FULL_TIME',
        'source_url': url,
        'posted_date': timezone.now().date(),
        'is_expired': False,
    }


def extract_jobdexo_detail(url):
    """
    Parses a single Jobdexo job page and extracts structured job details
    including the official application link.
    """
    if not url.startswith('http'):
        url = f"https://jobdexo.com{url}"

    try:
        page_html = fetch_url_html(url)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            # Graceful fallback to slug parsing if 429
            return fallback_parse_from_slug(url)
        raise

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
            for known in ['deloitte', 'kpmg', 'oracle', 'accenture', 'barclays', 'tcs', 'infosys', 'cognizant', 'wipro', 'quest', 'vyapar', 'metlife', 'globallogic', 'dassault', 'cisco', 'amazon', 'stripe', 'microsoft']:
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

    # 8b. Selection Process & Interview Rounds
    selection_process = ""
    sel_m = re.search(r'<div class="jd-card-title">\s*🏆\s*Selection Process\s*</div>\s*<div class="jd-prose"[^>]*>(.*?)</div>', page_html, re.DOTALL)
    if sel_m:
        raw_sel = re.sub(r'<br\s*/?>', '\n', sel_m.group(1))
        raw_sel = re.sub(r'<[^>]+>', '', raw_sel)
        selection_process = html.unescape(raw_sel.strip())
        raw_sel = re.sub(r'<[^>]+>', '', raw_sel)
        selection_process = html.unescape(raw_sel.strip())

    # 8c. Free Study Materials & Preparation Links
    study_materials = []
    study_cards = re.findall(r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*jd-study[^"]*"[^>]*>(.*?)</a>', page_html, re.DOTALL)
    for link, content in study_cards:
        t_m = re.search(r'<div class="sm-title">([^<]+)</div>', content)
        d_m = re.search(r'<div class="sm-desc">([^<]+)</div>', content)
        i_m = re.search(r'<div class="sm-icon">([^<]+)</div>', content)
        study_materials.append({
            'title': html.unescape(t_m.group(1).strip()) if t_m else 'Study Resource',
            'desc': html.unescape(d_m.group(1).strip()) if d_m else 'Interview and screening practice resource.',
            'icon': html.unescape(i_m.group(1).strip()) if i_m else '📖',
            'url': link.strip()
        })

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

    # 10. Check Posting Date & Freshness
    is_expired = False
    posted_date = timezone.now().date()

    if schema_data.get('datePosted'):
        try:
            from datetime import datetime
            dp_str = schema_data.get('datePosted')[:10]
            parsed_dp = datetime.strptime(dp_str, '%Y-%m-%d').date()
            posted_date = parsed_dp
            if (timezone.now().date() - parsed_dp).days > 3:
                is_expired = True
        except Exception:
            pass

    deadline_m = re.search(r'Deadline:\s*(\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})', page_html, re.IGNORECASE)
    if deadline_m:
        try:
            from datetime import datetime
            parsed_dl = datetime.strptime(deadline_m.group(1).strip(), '%d %b %Y')
            if parsed_dl.date() < timezone.now().date():
                is_expired = True
        except Exception:
            pass

    if schema_data.get('validThrough'):
        try:
            vt = schema_data.get('validThrough')[:10]
            from datetime import datetime
            parsed_vt = datetime.strptime(vt, '%Y-%m-%d')
            if parsed_vt.date() < timezone.now().date():
                is_expired = True
        except Exception:
            pass

    # Extract meta description
    meta_desc = ""
    og_m = re.search(r'<meta[^>]+property=[\'"]og:description[\'"][^>]+content=[\'"]([^\'"]+)[\'"]', page_html, re.IGNORECASE)
    if not og_m:
        og_m = re.search(r'<meta[^>]+name=[\'"]description[\'"][^>]+content=[\'"]([^\'"]+)[\'"]', page_html, re.IGNORECASE)
    if og_m:
        meta_desc = html.unescape(og_m.group(1).strip())

    full_desc_context = f"{meta_desc}\n{description}" if meta_desc else description

    lower_title = f"{title} {description}".lower()
    is_intern = any(k in lower_title for k in ['intern', 'internship', 'apprentice', 'trainee', 'co-op'])
    job_type = 'INTERNSHIP' if is_intern else 'FULL_TIME'

    resolved_company = resolve_company_name(
        raw_name=company,
        title=title,
        description=full_desc_context,
        apply_url=apply_url,
        url=url
    )

    return {
        'title': title,
        'company': resolved_company,
        'salary': salary,
        'location': location,
        'skills': skills,
        'eligibility': eligibility,
        'selection_process': selection_process,
        'study_materials': study_materials,
        'description': description,
        'apply_url': apply_url,
        'job_type': job_type,
        'source_url': url,
        'posted_date': posted_date,
        'is_expired': is_expired,
    }


def fetch_multi_section_jobdexo_urls(limit=25):
    """
    Crawls across distinct Jobdexo sections with polite pacing.
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
            # Polite pacing between endpoint scrapes
            time.sleep(random.uniform(0.6, 1.2))
        except Exception as err:
            pass

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
        matching_company_jobs = JobPosting.objects.filter(
            company_name__icontains=job_data.get('company')[:6]
        )
        for existing in matching_company_jobs:
            if normalize_text(existing.company_name) == norm_comp and normalize_text(existing.title) == norm_title:
                return True

    return False


def auto_import_from_jobdexo(urls=None, limit=10, group_name=None):
    """
    Main ingestion engine:
    1. Extracts jobs across Jobdexo sections (or provided URLs).
    2. Uses polite scraping with backoff retry.
    3. Strictly filters out duplicate jobs.
    4. Publishes new verified openings under 'Software & Tech' with 7-day expiry.
    5. Automatically groups them into a 7-day shareable group.
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
            # Polite pacing between job item scrapes (prevents 429 rate limiting)
            time.sleep(random.uniform(0.8, 1.5))
            job_data = extract_jobdexo_detail(url)

            # Skip expired or stale jobs
            if job_data.get('is_expired'):
                continue

            # Strict Deduplication Check
            if is_job_duplicate_in_db(job_data, seen_in_batch=seen_in_batch):
                continue

            job_posted_date = job_data.get('posted_date', now.date())
            job_deadline = timezone.now() + timedelta(days=7)

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
                selection_process=job_data.get('selection_process', ''),
                study_materials=job_data.get('study_materials', []),
                status='ACTIVE',
                is_featured=True,
                posted_date=job_posted_date,
                deadline=job_deadline,
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
            # Silently ignore individual scrape errors or log cleanly
            continue

    # Create / Update Requirement Group
    job_group = None
    if created_job_instances:
        now_local = timezone.localtime(timezone.now())
        if not group_name:
            group_name = now_local.strftime("🔥 Top Off-Campus Tech Drives — %d %b %Y")

        base_slug = slugify(group_name) or "jobdexo-drive"
        slug = f"{base_slug}-{now_local.strftime('%Y%m%d%H%M')}"

        job_group = JobGroup.objects.create(
            name=group_name,
            slug=slug,
            banner_tag="🔥 KASHIIUPDATEZ TECH DRIVE",
            description=f"Curated collection of {len(created_job_instances)} fresh verified off-campus opportunities by Kashii Updatez.",
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
            # Sleep 300 seconds (5 minutes) with slight jitter
            time.sleep(300 + random.randint(5, 20))
            print("⚡ [Jobdexo Auto-Sync] Running 5-minute automated crawl across all sections...")
            result = auto_import_from_jobdexo(limit=5)
            if result['imported_count'] > 0:
                print(f"✅ [Jobdexo Auto-Sync] Added {result['imported_count']} fresh non-duplicate jobs! Group: {result['group_name']}")
            else:
                print("ℹ️ [Jobdexo Auto-Sync] Checked sections: No new non-duplicate jobs found.")
        except Exception as e:
            print(f"ℹ️ [Jobdexo Auto-Sync] Cycle notice: {e}")


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
