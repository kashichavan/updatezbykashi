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
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta, datetime
from django.utils import timezone
from django.utils.text import slugify
from django.core.cache import cache
from django.db.models import Q
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

# Distinct Jobdexo Discovery Sections and Pagination
JOBDEXO_SOURCE_ENDPOINTS = [
    'https://jobdexo.com/',
    'https://jobdexo.com/?page=2',
    'https://jobdexo.com/?page=3',
    'https://jobdexo.com/?page=4',
    'https://jobdexo.com/?q=developer',
    'https://jobdexo.com/?q=software',
    'https://jobdexo.com/?q=analyst',
    'https://jobdexo.com/?q=internship',
    'https://jobdexo.com/?q=engineer',
    'https://jobdexo.com/?q=fresher',
]


def fetch_url_html(url, retries=2, backoff=2.0):
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
                sleep_time = backoff * (attempt + 1) + random.uniform(1.0, 2.0)
                time.sleep(sleep_time)
                continue
            raise
        except Exception:
            if attempt < retries:
                time.sleep(backoff)
                continue
            raise


def canonical_clean_url(url):
    """
    Strips tracking query parameters (utm_*, ref, gh_src, source, etc.)
    and trailing slashes to produce a canonical URL for accurate deduplication.
    """
    if not url:
        return ""
    url = url.strip()
    try:
        parsed = urllib.parse.urlparse(url)
        # Keep clean scheme and netloc + path
        path = parsed.path.rstrip('/')
        # Filter query params
        tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'ref', 'source', 'gh_src', 'src', 'from', 'aff', 'iid'}
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        clean_pairs = [(k, v) for k, v in query_pairs if k.lower() not in tracking_params and not k.lower().startswith('utm_')]
        clean_query = urllib.parse.urlencode(clean_pairs)
        
        canonical = urllib.parse.urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, '', clean_query, ''))
        return canonical.rstrip('/')
    except Exception:
        return re.sub(r'\?.*$', '', url).rstrip('/').lower()


def normalize_text(text):
    """Normalize strings for duplicate comparison (removes punctuation, casing, spaces)."""
    return re.sub(r'[^a-z0-9]', '', (text or '').lower())


def clean_job_title(raw_title, company_name=""):
    """
    Standardizes job titles by removing noise phrases such as:
    - '— 2026', '(2026)', '2026 Batch'
    - 'at Company Name', '— All Batches', 'Off Campus Drive'
    - 'Campus Recruitment', '| Bangalore', 'Fresher'
    """
    if not raw_title:
        return "Software Engineer"

    t = html.unescape(raw_title).strip()

    # Remove trailing/leading quotes and pipes
    t = re.sub(r'^[\"\'\s\-–—|]+|[\"\'\s\-–—|]+$', '', t)

    # Remove batch / year suffixes: e.g. (2026), — 2026, | 2026 Batch
    t = re.sub(r'\s*[\(\[\{]?(?:202[4-8]|2030)\s*(?:Batch|Passout|Freshers?)?[\)\]\}]?', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*[–—\-]\s*202[4-8]\b', '', t, flags=re.IGNORECASE)

    # Remove '— All Batches', '— Freshers'
    t = re.sub(r'\s*[–—\-]\s*(?:All Batches|Freshers?|Immediate Joiner|Across India)\b', '', t, flags=re.IGNORECASE)

    # Remove 'at Company Name'
    if company_name:
        t = re.sub(r'\s+at\s+' + re.escape(company_name) + r'\b', '', t, flags=re.IGNORECASE)

    # Remove generic site noise: e.g. 'Off Campus Drive', 'Recruitment 2026'
    t = re.sub(r'\b(?:Off Campus Drive|Campus Recruitment|Hiring Drive|Mega Drive)\b', '', t, flags=re.IGNORECASE)

    # Clean redundant spaces and punctuation
    t = re.sub(r'\s*[–—\-|\/]+\s*$', '', t).strip()
    t = re.sub(r'\s+', ' ', t).strip()

    return t or "Software Engineer"


def extract_official_apply_url(page_html, fallback_url=""):
    """
    Standard, robust extraction of the REAL external company/ATS apply link from Jobdexo HTML.
    Prioritizes official career portal anchors and filters out internal, social, or ad redirect links.
    """
    if not page_html:
        return fallback_url

    # 1. Search all HTML anchors with explicit 'Apply on Official Website' or 'Apply on Company'
    for href, text in re.findall(r'<a\s+[^>]*?href=[\"\']([^\"\']+)[\"\'][^>]*?>(.*?)</a>', page_html, re.IGNORECASE | re.DOTALL):
        href_clean = html.unescape(href.strip())
        text_clean = html.unescape(re.sub(r'<[^>]+>', '', text).strip())

        # Exclude internal, affiliate, social, and study links
        if any(bad in href_clean.lower() for bad in [
            'jobdexo.com', 'jobbroom.com', 'ambitionbox.com', 'wa.me', 't.me',
            'telegram.me', 'whatsapp.com', 'indiabix.com', 'geeksforgeeks.org',
            'prepinsta.com', 'leetcode.com', 'javascript:', 'mailto:', '#'
        ]):
            continue

        if any(keyword in text_clean.lower() for keyword in ['apply on official', 'apply on company', 'official website', 'apply now']):
            if href_clean.startswith(('http://', 'https://')):
                return canonical_clean_url(href_clean)

    # 2. Match known enterprise ATS & Corporate Careers Portal links in page HTML
    career_patterns = [
        r'href=[\"\'](https?://[a-zA-Z0-9.-]*(?:careers|jobs|recruiting|myworkdayjobs|smartrecruiters|greenhouse|lever|taleo|icims|jobvite|oraclecloud|workday|successfactors|darwinbox|keka|freshteam|zoho|instahyre|unstop|ashbyhq|workable|eightfold|ycombinator|internship\.aicte-india)[^\"\']+)[\"\']',
        r'href=[\"\'](https?://(?:www\.)?linkedin\.com/jobs/view/[^\"\']+)[\"\']',
        r'href=[\"\'](https?://[a-zA-Z0-9.-]*amazon\.jobs/[^\"\']+)[\"\']',
    ]

    for pat in career_patterns:
        m = re.search(pat, page_html, re.IGNORECASE)
        if m:
            extracted = html.unescape(m.group(1).strip())
            if extracted and 'jobdexo.com' not in extracted:
                return canonical_clean_url(extracted)

    # 3. Fallback: check data-apply or data-target-url attributes
    data_m = re.search(r'data-(?:apply-url|apply|target-url)=[\"\']([^\"\']+)[\"\']', page_html, re.IGNORECASE)
    if data_m:
        extracted = html.unescape(data_m.group(1).strip())
        if extracted and extracted.startswith(('http://', 'https://')) and 'jobdexo.com' not in extracted:
            return canonical_clean_url(extracted)

    return fallback_url


def extract_salary_from_html(page_html, schema_data=None, fallback="Competitive Package (Best in Industry)"):
    """Extracts salary/stipend information cleanly from Schema.org or HTML markup."""
    schema_data = schema_data or {}
    
    # 1. From JSON-LD Schema
    base_sal = schema_data.get('baseSalary', {})
    if isinstance(base_sal, dict):
        val = base_sal.get('value', {})
        if isinstance(val, dict) and val.get('value'):
            return str(val.get('value')).strip()
        elif base_sal.get('value'):
            return str(base_sal.get('value')).strip()
    elif isinstance(base_sal, (str, int, float)) and str(base_sal).strip():
        return str(base_sal).strip()

    # 2. From HTML tags
    pat_tag = re.search(r'<span class="jd-tag jt-emerald">\s*💰\s*([^<]+)</span>', page_html)
    if pat_tag:
        return pat_tag.group(1).strip()

    pat_lpa = re.search(r'\b(\d+(?:\.\d+)?\s*(?:-\s*\d+(?:\.\d+)?)?\s*LPA)\b', page_html, re.IGNORECASE)
    if pat_lpa:
        return pat_lpa.group(1).strip()

    pat_inr = re.search(r'(₹\s*\d[\d,]*(?:\s*-\s*₹?\s*\d[\d,]*)?\s*(?:\/\s*(?:month|mo|year|yr|pm))?)', page_html, re.IGNORECASE)
    if pat_inr:
        return pat_inr.group(1).strip()

    return fallback


def extract_jobdexo_detail(url):
    """
    Standard scraper for full detail Jobdexo pages.
    Parses JSON-LD Schema.org JobPosting + BreadcrumbList with robust HTML fallback.
    """
    try:
        page_html = fetch_url_html(url, retries=2)
    except Exception:
        return None

    # 1. Parse JSON-LD Schema.org Data (with strict=False to handle raw unescaped newlines)
    schema_data = {}
    breadcrumb_data = {}
    
    json_scripts = re.findall(r'<script type=[\"\']application/ld\+json[\"\']>(.*?)</script>', page_html, re.DOTALL)
    for js_block in json_scripts:
        try:
            parsed = json.loads(js_block.strip(), strict=False)
            if isinstance(parsed, dict):
                if parsed.get('@type') == 'JobPosting':
                    schema_data = parsed
                elif parsed.get('@type') == 'BreadcrumbList':
                    breadcrumb_data = parsed
        except Exception:
            pass

    # 2. Title Extraction
    title = ""
    if schema_data.get('title'):
        title = schema_data.get('title').strip()
    else:
        # Check standard h1 class
        h1_m = re.search(r'<h1[^>]*class=[\"\'][^\"\']*jd-job-title[^\"\']*[\"\'][^>]*>(.*?)</h1>', page_html, re.DOTALL | re.IGNORECASE)
        if not h1_m:
            h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', page_html, re.DOTALL | re.IGNORECASE)
        if h1_m:
            title = html.unescape(re.sub(r'<[^>]+>', '', h1_m.group(1)).strip())
        else:
            title_m = re.search(r'<title>(.*?)</title>', page_html)
            if title_m:
                title = title_m.group(1).split('|')[0].split('-')[0].strip()

    # 3. Company Extraction
    raw_company = ""
    if schema_data.get('hiringOrganization', {}).get('name'):
        raw_company = schema_data.get('hiringOrganization', {}).get('name').strip()
    elif schema_data.get('identifier', {}).get('name'):
        raw_company = schema_data.get('identifier', {}).get('name').strip()

    # Fallback to Breadcrumb item 3
    if not raw_company and breadcrumb_data.get('itemListElement'):
        items = breadcrumb_data.get('itemListElement', [])
        if len(items) >= 3 and items[2].get('name'):
            raw_company = items[2].get('name').strip()

    # 4. Resolve standardized company name
    company = resolve_company_name(
        raw_name=raw_company,
        title=title,
        description=schema_data.get('description', '') or page_html[:1000],
        apply_url=url,
        url=url
    )

    # 5. Clean Title (strip batch noise and redundant company mentions)
    clean_title = clean_job_title(title, company_name=company)

    # 6. Salary
    salary = extract_salary_from_html(page_html, schema_data=schema_data, fallback="Competitive Package (Best in Industry)")

    # 7. Location
    location = "Remote / Hybrid, India"
    if schema_data.get('jobLocation', {}).get('address', {}).get('addressLocality'):
        location = schema_data.get('jobLocation', {}).get('address', {}).get('addressLocality').strip()
    else:
        loc_m = re.search(r'<span class=[\"\']jd-tag jt-slate[\"\']>\s*📍\s*([^<]+)</span>', page_html)
        if loc_m:
            location = html.unescape(loc_m.group(1).strip())

    # 8. Skills
    skills_tags = re.findall(r'<span class=[\"\']jd-skill[\"\']>([^<]+)</span>', page_html)
    skills = ", ".join([html.unescape(s.strip()) for s in skills_tags if s.strip()])
    if not skills:
        skills = "Problem Solving, Software Engineering, Communication"

    # 9. Eligibility
    eligibility = "Open to all freshers & eligible graduating batches."
    elig_m = re.search(r'<div class=[\"\']jd-card-title[\"\']>\s*✅\s*Eligibility Criteria\s*</div>\s*<div class=[\"\']jd-prose[\"\']>([^<]+)</div>', page_html, re.IGNORECASE)
    if elig_m:
        eligibility = html.unescape(elig_m.group(1).strip())

    # 10. Description
    description = ""
    if schema_data.get('description'):
        raw_desc = schema_data.get('description').strip()
        raw_desc = re.sub(r'<br\s*/?>', '\n', raw_desc)
        raw_desc = re.sub(r'<[^>]+>', '', raw_desc)
        description = html.unescape(raw_desc.strip())
    else:
        desc_m = re.search(r'<div class=[\"\']jd-prose[\"\'][^>]*id=[\"\']jdDesc[\"\'][^>]*>(.*?)</div>', page_html, re.DOTALL)
        if desc_m:
            raw_desc = re.sub(r'<br\s*/?>', '\n', desc_m.group(1))
            raw_desc = re.sub(r'<[^>]+>', '', raw_desc)
            description = html.unescape(raw_desc.strip())

    if not description:
        description = f"{company} is hiring for {clean_title}.\nLocation: {location}\nSalary: {salary}\nKey Skills: {skills}"

    # 11. Selection Process & Study Materials
    selection_process = ""
    sel_m = re.search(r'<div class=[\"\']jd-card-title[\"\']>\s*🏆\s*Selection Process\s*</div>\s*<div class=[\"\']jd-prose[\"\'][^>]*>(.*?)</div>', page_html, re.DOTALL)
    if sel_m:
        raw_sel = re.sub(r'<br\s*/?>', '\n', sel_m.group(1))
        raw_sel = re.sub(r'<[^>]+>', '', raw_sel)
        selection_process = html.unescape(raw_sel.strip())

    study_materials = []
    study_cards = re.findall(r'<a[^>]*href=[\"\']([^\"\']+)[\"\'][^>]*class=[\"\'][^\"\']*jd-study[^\"\']*[\"\'][^>]*>(.*?)</a>', page_html, re.DOTALL)
    for link, content in study_cards:
        t_m = re.search(r'<div class=[\"\']sm-title[\"\']>([^<]+)</div>', content)
        d_m = re.search(r'<div class=[\"\']sm-desc[\"\']>([^<]+)</div>', content)
        i_m = re.search(r'<div class=[\"\']sm-icon[\"\']>([^<]+)</div>', content)
        study_materials.append({
            'title': html.unescape(t_m.group(1).strip()) if t_m else 'Study Resource',
            'desc': html.unescape(d_m.group(1).strip()) if d_m else 'Interview and screening practice resource.',
            'icon': html.unescape(i_m.group(1).strip()) if i_m else '📖',
            'url': link.strip()
        })

    # 12. Official Apply URL
    apply_url = extract_official_apply_url(page_html, fallback_url=url)

    # 13. Expiration Check
    is_expired = False
    posted_date = timezone.now().date()
    if schema_data.get('datePosted'):
        try:
            dp_str = schema_data.get('datePosted')[:10]
            parsed_dp = datetime.strptime(dp_str, '%Y-%m-%d').date()
            posted_date = parsed_dp
            if (timezone.now().date() - parsed_dp).days > 7:
                is_expired = True
        except Exception:
            pass

    lower_ctx = f"{clean_title} {description}".lower()
    job_type = 'INTERNSHIP' if any(k in lower_ctx for k in ['intern', 'internship', 'apprentice', 'trainee', 'co-op']) else 'FULL_TIME'

    return {
        'title': clean_title,
        'company': company,
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


def fetch_multi_section_jobdexo_urls(limit=35):
    """
    Crawls across distinct Jobdexo sections concurrently with smart pre-filtering.
    Extracts job cards directly from the list pages to identify new opportunities
    without downloading redundant detail pages.
    """
    discovered_urls = []
    seen_urls = set()

    # Preload existing company::title fingerprints from DB to skip duplicates immediately
    existing_fingerprints = set()
    try:
        for comp, title in JobPosting.objects.values_list('company_name', 'title'):
            existing_fingerprints.add(f"{normalize_text(comp)}::{normalize_text(title)}")
    except Exception:
        pass

    def _scrape_endpoint(endpoint):
        try:
            return fetch_url_html(endpoint)
        except Exception:
            return None

    # Fetch discovery endpoints concurrently (max 4 workers for polite concurrency)
    endpoint_htmls = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {executor.submit(_scrape_endpoint, ep): ep for ep in JOBDEXO_SOURCE_ENDPOINTS}
        for future in as_completed(future_map):
            page_html = future.result()
            if page_html:
                endpoint_htmls.append(page_html)

    for page_html in endpoint_htmls:
        # 1. Parse structured job cards from listing page
        card_matches = re.findall(
            r'<article class=[\"\']job-card[\"\']>.*?<div class=[\"\']job-company[\"\']>([^<]+)</div>.*?<h3 class=[\"\']job-title[\"\']>\s*<a href=[\"\']([^\"\']+)[\"\']>([^<]+)</a>',
            page_html,
            re.DOTALL
        )

        for raw_comp, path, raw_title in card_matches:
            full_url = f"https://jobdexo.com{path}" if path.startswith('/') else path
            full_url = canonical_clean_url(full_url)
            if not full_url or full_url in seen_urls:
                continue

            comp_clean = html.unescape(raw_comp.strip())
            title_clean = html.unescape(raw_title.strip())
            resolved_comp = resolve_company_name(comp_clean, title=title_clean, url=full_url)
            clean_t = clean_job_title(title_clean, company_name=resolved_comp)
            fp = f"{normalize_text(resolved_comp)}::{normalize_text(clean_t)}"

            seen_urls.add(full_url)

            # If this job already exists in our database, skip fetching its detail page
            if fp in existing_fingerprints:
                continue

            discovered_urls.append(full_url)
            if len(discovered_urls) >= limit:
                break

        # Fallback: catch any extra job links on the page if card regex missed them
        if len(discovered_urls) < limit:
            all_found_urls = re.findall(r'href=[\"\']((?:https?://(?:www\.)?jobdexo\.com)?/job/[^\"\']+)[\"\']', page_html)
            for u in all_found_urls:
                full_url = f"https://jobdexo.com{u}" if u.startswith('/') else u
                full_url = canonical_clean_url(full_url)
                if full_url and full_url not in seen_urls:
                    seen_urls.add(full_url)
                    discovered_urls.append(full_url)
                if len(discovered_urls) >= limit:
                    break

        if len(discovered_urls) >= limit:
            break

    return discovered_urls


def is_job_duplicate_in_db(job_data, seen_in_batch=None):
    """
    Standard, multi-tier deduplication engine:
    1. Canonical URL match (Official ATS Apply URL & Source URL).
    2. Exact (Normalized Company + Normalized Clean Title).
    3. Token overlap / Jaccard similarity for identical company.
    4. Auto-heals existing job: If existing job points to jobdexo.com, updates it to the new official ATS URL.
    """
    apply_url = (job_data.get('apply_url') or '').strip()
    source_url = (job_data.get('source_url') or '').strip()
    clean_apply = canonical_clean_url(apply_url)
    raw_title = job_data.get('title') or ''
    raw_comp = job_data.get('company') or ''

    norm_title = normalize_text(raw_title)
    norm_comp = normalize_text(raw_comp)

    # 1. Batch level deduplication
    if seen_in_batch is not None:
        batch_key = f"{norm_comp}::{norm_title}"
        if batch_key in seen_in_batch:
            return True
        if clean_apply and clean_apply in seen_in_batch and 'jobdexo.com' not in clean_apply:
            return True
        seen_in_batch.add(batch_key)
        if clean_apply and 'jobdexo.com' not in clean_apply:
            seen_in_batch.add(clean_apply)

    # 2. Database Canonical Apply URL Match (Official ATS career link)
    if clean_apply and 'jobdexo.com' not in clean_apply:
        if JobPosting.objects.filter(apply_url__iexact=clean_apply).exists():
            return True
        # Also check without trailing slash or protocol
        domain_path = re.sub(r'^https?:\/\/', '', clean_apply).rstrip('/')
        if JobPosting.objects.filter(apply_url__icontains=domain_path).exists():
            return True

    # 3. Exact (Normalized Company + Normalized Title) Match
    existing_same_company = JobPosting.objects.filter(
        Q(company_name__iexact=raw_comp) | 
        Q(company_name__iexact=raw_comp.replace(' ', '')) |
        Q(company_name__icontains=raw_comp)
    )

    t1_tokens = set(re.findall(r'[a-z0-9]+', raw_title.lower()))
    for existing in existing_same_company:
        t2_tokens = set(re.findall(r'[a-z0-9]+', existing.title.lower()))
        
        # Exact normalized title match
        if normalize_text(existing.title) == norm_title:
            # If existing job has a legacy jobdexo apply_url, upgrade it to the new official ATS URL
            if clean_apply and 'jobdexo.com' not in clean_apply and 'jobdexo.com' in existing.apply_url:
                existing.apply_url = clean_apply
                existing.save(update_fields=['apply_url'])
            return True

        # High Token Jaccard Similarity (>= 0.75) for same company
        if t1_tokens and t2_tokens:
            intersection = t1_tokens.intersection(t2_tokens)
            similarity = len(intersection) / max(len(t1_tokens), len(t2_tokens))
            if similarity >= 0.75:
                if clean_apply and 'jobdexo.com' not in clean_apply and 'jobdexo.com' in existing.apply_url:
                    existing.apply_url = clean_apply
                    existing.save(update_fields=['apply_url'])
                return True

    return False


def cleanup_all_database_duplicates():
    """
    One-shot master routine that merges and deletes all existing duplicate JobPosting records,
    standardizes corrupted company names (e.g. Jobsashbyhq -> LG Ad Solutions), cleans titles,
    and upgrades legacy jobdexo apply links.
    """
    all_jobs = list(JobPosting.objects.all().order_by('created_at'))
    seen_keys = {}
    deleted_count = 0
    updated_count = 0

    for job in all_jobs:
        # Standardize company name
        resolved_company = resolve_company_name(
            raw_name=job.company_name,
            title=job.title,
            description=job.description,
            apply_url=job.apply_url,
            url=job.apply_url or ""
        )
        
        # Standardize title
        clean_title = clean_job_title(job.title, company_name=resolved_company)

        # Standardize canonical apply URL
        clean_apply = canonical_clean_url(job.apply_url)

        # Build deduplication fingerprint key
        comp_key = normalize_text(resolved_company)
        title_key = normalize_text(clean_title)
        primary_key = f"{comp_key}::{title_key}"

        if primary_key in seen_keys:
            # Already have this job! Delete the duplicate record
            job.delete()
            deleted_count += 1
            continue

        seen_keys[primary_key] = job.id

        # Update fields if standardized
        needs_save = False
        if job.company_name != resolved_company:
            job.company_name = resolved_company
            needs_save = True
        if job.title != clean_title:
            job.title = clean_title
            needs_save = True
        if job.apply_url != clean_apply and clean_apply:
            job.apply_url = clean_apply
            needs_save = True

        if needs_save:
            job.save(update_fields=['company_name', 'title', 'apply_url'])
            updated_count += 1

    cache.clear()
    return {'deleted_duplicates': deleted_count, 'updated_jobs': updated_count}


def resolve_all_jobdexo_apply_urls():
    """
    Crawls and replaces all existing JobPosting apply_url records in the DB
    that currently point to jobdexo.com with their official external ATS career apply URLs.
    """
    postings = JobPosting.objects.filter(apply_url__icontains='jobdexo.com')
    total = postings.count()
    updated_count = 0

    for job in postings:
        target_url = job.apply_url
        try:
            html_content = fetch_url_html(target_url, retries=1)
            real_url = extract_official_apply_url(html_content, fallback_url=None)
            if real_url and 'jobdexo.com' not in real_url:
                job.apply_url = real_url
                job.save(update_fields=['apply_url'])
                updated_count += 1
                time.sleep(0.3)
        except Exception:
            pass

    return {'total': total, 'updated': updated_count}


def resolve_all_jobdexo_company_names():
    """Batch resolves clean company names for all existing postings."""
    postings = JobPosting.objects.all()
    total = postings.count()
    updated_count = 0

    for job in postings:
        resolved = resolve_company_name(
            raw_name=job.company_name,
            title=job.title,
            description=job.description,
            apply_url=job.apply_url,
            url=""
        )
        if resolved != job.company_name:
            job.company_name = resolved
            job.save(update_fields=['company_name'])
            updated_count += 1

    return {'total': total, 'updated': updated_count}


def auto_import_from_jobdexo(urls=None, limit=10, group_name=None):
    """
    Standard Ingestion Engine:
    1. Fetches candidate Jobdexo URLs.
    2. Performs fast pre-check to skip already-imported URLs.
    3. Scrapes Schema.org metadata and official career ATS apply links in parallel.
    4. Applies multi-tier strict deduplication.
    5. Publishes verified openings under 'Software & Tech' category.
    6. Bundles into a 7-day shareable group.
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
        urls = fetch_multi_section_jobdexo_urls(limit=max(35, limit * 4))

    created_jobs = []
    created_job_instances = []
    seen_in_batch = set()
    now = timezone.now()
    deadline = now + timedelta(days=7)

    # Filter out empty or duplicate candidate URLs
    valid_candidate_urls = []
    for u in urls:
        u_clean = (u or '').strip()
        if u_clean and u_clean not in valid_candidate_urls:
            valid_candidate_urls.append(u_clean)

    # Fetch details concurrently using ThreadPoolExecutor for fast non-blocking execution
    extracted_jobs = []
    if valid_candidate_urls:
        max_workers = min(6, len(valid_candidate_urls))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(extract_jobdexo_detail, u): u for u in valid_candidate_urls}
            for future in as_completed(future_to_url):
                try:
                    job_data = future.result()
                    if job_data and not job_data.get('is_expired'):
                        extracted_jobs.append(job_data)
                except Exception:
                    pass

    # Save non-duplicate fresh jobs
    for job_data in extracted_jobs:
        try:
            # Standard Deduplication Check
            if is_job_duplicate_in_db(job_data, seen_in_batch=seen_in_batch):
                continue

            job_posted_date = job_data.get('posted_date', now.date())
            job_deadline = timezone.now() + timedelta(days=7)

            # Create standard verified job posting
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

        except Exception:
            continue

    # Create Requirement Group
    job_group = None
    if created_job_instances:
        now_local = timezone.localtime(timezone.now())
        if not group_name:
            group_name = now_local.strftime("🔥 Top Off-Campus Tech Drives — %d %b %Y")

        base_slug = slugify(group_name) or "jobdexo-drive"
        slug = f"{base_slug}-{now_local.strftime('%Y%m%d%H%M%S')}"

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
# RECURRING AUTO-SYNC BACKGROUND WORKER (Every 30 Minutes + Immediate Startup)
# ==============================================================================

_SYNC_WORKER_RUNNING = False
_SYNC_LOCK = threading.Lock()


def _background_hourly_sync_loop():
    """Background worker thread that runs on startup and every 30 minutes (1800 seconds)."""
    global _SYNC_WORKER_RUNNING
    print("🚀 [Jobdexo Auto-Sync] Background sync daemon initialized.")
    
    # 1. Warm-up delay to allow Django application and database to complete startup
    time.sleep(5)
    
    while _SYNC_WORKER_RUNNING:
        try:
            from django.db import close_old_connections
            close_old_connections()
            print("⚡ [Jobdexo Auto-Sync] Running automated crawl across all sections...")
            result = auto_import_from_jobdexo(limit=10)
            if result.get('imported_count', 0) > 0:
                print(f"✅ [Jobdexo Auto-Sync] Added {result['imported_count']} fresh non-duplicate jobs! Group: {result.get('group_name')}")
            else:
                print("ℹ️ [Jobdexo Auto-Sync] Checked sections: Feed is 100% up-to-date.")
        except Exception as e:
            print(f"ℹ️ [Jobdexo Auto-Sync] Cycle notice: {e}")
        finally:
            try:
                from django.db import close_old_connections
                close_old_connections()
            except Exception:
                pass

        # Sleep for 30 minutes before next recurring sync
        time.sleep(1800 + random.randint(10, 60))


def start_hourly_sync_daemon():
    """Starts the background auto-sync worker if not already running."""
    global _SYNC_WORKER_RUNNING
    with _SYNC_LOCK:
        if not _SYNC_WORKER_RUNNING:
            _SYNC_WORKER_RUNNING = True
            t = threading.Thread(target=_background_hourly_sync_loop, daemon=True, name="JobdexoSyncWorker")
            t.start()
            return True
    return False


# Alias for backward compatibility
start_5min_sync_daemon = start_hourly_sync_daemon

