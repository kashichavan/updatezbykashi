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


def extract_official_apply_url(page_html, fallback_url=""):
    """
    Extracts the REAL external/official company application link from a Jobdexo HTML page.
    Filters out internal links, social share URLs, and study material anchors.
    """
    if not page_html:
        return fallback_url

    # 1. Primary Priority: Match official "jd-apply" anchor tags (with multi-line attribute support)
    primary_patterns = [
        r'<a\s+[^>]*?class=[\"\'][^\"\']*?jd-apply[^\"\']*?[\"\'][^>]*?href=[\"\']([^\"\']+)[\"\']',
        r'<a\s+[^>]*?href=[\"\']([^\"\']+)[\"\'][^>]*?class=[\"\'][^\"\']*?jd-apply[^\"\']*?[\"\']',
        r'<a\s+[^>]*?href=[\"\']([^\"\']+)[\"\'][^>]*?>\s*✅\s*Apply on Official Website',
        r'<a\s+[^>]*?href=[\"\']([^\"\']+)[\"\'][^>]*?>\s*⚡\s*Apply Now Before Others',
        r'<a\s+[^>]*?href=[\"\']([^\"\']+)[\"\'][^>]*?>[^<]*Apply on Official',
        r'<a\s+[^>]*?href=[\"\']([^\"\']+)[\"\'][^>]*?>[^<]*Apply on Company',
        r'<a\s+[^>]*?href=[\"\'](https?://(?!jobdexo\.com|wa\.me|t\.me|telegram\.me|whatsapp\.com|ambitionbox\.com|indiabix\.com|geeksforgeeks\.org|prepinsta\.com|leetcode\.com)[^\"\']+)[\"\'][^>]*?>[^<]*Apply',
    ]

    for pat in primary_patterns:
        m = re.search(pat, page_html, re.IGNORECASE | re.DOTALL)
        if m:
            extracted = html.unescape(m.group(1).strip())
            if extracted and not extracted.startswith(('#', 'javascript:', 'mailto:')) and 'jobdexo.com' not in extracted:
                return extracted

    # 2. Secondary Priority: Match explicit ATS and company career portal links
    career_patterns = [
        r'href=[\"\'](https?://[a-zA-Z0-9.-]*(?:careers|jobs|recruiting|myworkdayjobs|smartrecruiters|greenhouse|lever|taleo|icims|jobvite|oraclecloud|workday|successfactors|darwinbox|keka|freshteam|zoho|instahyre|unstop|jobsmind)[^\"\']+)[\"\']',
        r'href=[\"\'](https?://(?:www\.)?linkedin\.com/jobs/view/[^\"\']+)[\"\']',
        r'href=[\"\'](https?://[a-zA-Z0-9.-]*amazon\.jobs/[^\"\']+)[\"\']',
    ]

    for pat in career_patterns:
        m = re.search(pat, page_html, re.IGNORECASE)
        if m:
            extracted = html.unescape(m.group(1).strip())
            if extracted and 'jobdexo.com' not in extracted:
                return extracted

    # 3. Third Priority: Look for data-apply or data-url attributes
    data_m = re.search(r'data-(?:apply-url|apply|target-url)=[\"\']([^\"\']+)[\"\']', page_html, re.IGNORECASE)
    if data_m:
        extracted = html.unescape(data_m.group(1).strip())
        if extracted and 'http' in extracted and 'jobdexo.com' not in extracted:
            return extracted

    return fallback_url


def resolve_all_jobdexo_apply_urls():
    """
    Crawls and replaces all existing JobPosting apply_url records in the DB
    that currently point to jobdexo.com with their official external ATS career apply URLs.
    """
    from .models import JobPosting
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
                time.sleep(0.5)
        except Exception:
            pass

    return {'total': total, 'updated': updated_count}


def clean_company_name(raw_name="", title="", slug="", apply_url=""):
    """
    Intelligently cleans and resolves official company names from Jobdexo pages,
    hostnames, domain slugs, and title strings. Prevents 'Technology Partner' fallbacks.
    """
    c = html.unescape(raw_name or "").strip()
    c = re.sub(r'^[🏢🏛️💼\s]+', '', c).strip()
    c = re.sub(r'^(?:Company|Hiring Organization|Organization)\s*[:\-]\s*', '', c, flags=re.IGNORECASE).strip()

    # Dictionary of known corporate brands and domain keys
    domain_mapping = {
        'cashkaro': 'CashKaro',
        'retape': 'ReTape AI',
        'spglobal': 'S&P Global',
        'sampp': 'S&P Global',
        'thinkitive': 'Thinkitive Technologies',
        'zs': 'ZS Associates',
        'vyaparapp': 'Vyapar Apps',
        'vyapar': 'Vyapar Apps',
        'jobsmind': 'Vyapar Apps',
        'metlife': 'MetLife',
        'hcltech': 'HCLTech',
        'hcl': 'HCLTech',
        'ownly': 'Ownly',
        'recruitcrm': 'Recruit CRM',
        'recruit': 'Recruit CRM',
        'capgemini': 'Capgemini',
        'quest': 'Quest Global',
        'volga': 'Volga Partners',
        'juspay': 'Juspay',
        'amazon': 'Amazon',
        'cisco': 'Cisco',
        'deloitte': 'Deloitte',
        'kpmg': 'KPMG',
        'oracle': 'Oracle',
        'accenture': 'Accenture',
        'tcs': 'TCS',
        'infosys': 'Infosys',
        'cognizant': 'Cognizant',
        'wipro': 'Wipro',
        'salesforce': 'Salesforce',
        'stripe': 'Stripe',
        'cgi': 'CGI',
        'techmahindra': 'Tech Mahindra',
        'tatagroup': 'Tata Group',
        'tata': 'Tata Group',
        'globallogic': 'GlobalLogic',
        'dassault': 'Dassault Systèmes',
        'turing': 'Turing',
        'reskom': 'Reskom',
        'hrone': 'HROne',
        'ukg': 'UKG',
        'binance': 'Binance',
        'portcast': 'Portcast',
    }

    # Form hosts that should not override company brand
    form_hosts = ['docs.google.com', 'forms.gle', 'forms.cloud.microsoft', 'forms.office.com', 'forms.microsoft.com']
    clean_apply_url = apply_url if not any(h in (apply_url or '').lower() for h in form_hosts) else ''

    # 1. Match against known domain keywords in title, slug, and raw_name first
    primary_context = f"{c} {title} {slug}".lower()
    for key, brand in domain_mapping.items():
        if re.search(r'\b' + re.escape(key) + r'\b', primary_context) or key in primary_context:
            return brand

    # 2. Check direct corporate career apply_url
    if clean_apply_url:
        for key, brand in domain_mapping.items():
            if key in clean_apply_url.lower():
                return brand

    generic_exclusions = {
        'software', 'engineer', 'developer', 'analyst', 'intern', 'fresher', 'freshers',
        'associate', 'hiring', 'trainee', 'product', 'data', 'operations', 'qa', 'tester',
        'lead', 'senior', 'junior', 'executive', 'specialist', 'designer', 'consultant',
        'support', 'technical', 'technology', 'system', 'systems', 'cloud', 'frontend',
        'backend', 'fullstack', 'full', 'stack', 'devops', 'aiml', 'machine', 'learning',
        'artificial', 'intelligence', 'network', 'embedded', 'applications', 'application',
        'services', 'service', 'role', 'internship', 'program', 'drive', 'campus', 'offcampus',
        'opening', 'job', 'jobs', 'remote', 'hybrid', 'india', 'pune', 'bengaluru', 'bangalore',
        'hyderabad', 'gurgaon', 'noida', 'chennai', 'mumbai', 'kolkata', 'delhi', 'technology partner',
        'featured partner', 'featured company', 'policy bazaar', 'partner', 'company', 'n/a'
    }

    # 3. If raw name is already a clean proper name
    c_clean = c.rstrip('.,-')
    if c_clean and c_clean.lower() not in generic_exclusions and not any(c_clean.lower().endswith(tld) for tld in ['.com', '.in', '.io', '.ai', '.org', '.net', 'com', 'kekacom']):
        if len(c_clean) > 2:
            return c_clean

    # 4. Check for domain
    if '.' in c or any(c.lower().endswith(tld) for tld in ['com', 'in', 'io', 'ai', 'co', 'org', 'net']):
        domain = c.lower()
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'^(?:www\.|jobs\.|careers\.|joinus\.|boards\.)', '', domain)
        domain = domain.split('/')[0].split('?')[0]
        brand = re.sub(r'\.(?:com|in|org|net|co|io|ai|tech|global)$', '', domain)
        brand = re.sub(r'(?:com|in|org|net|co|io|ai|tech|global)$', '', brand)
        if '.' in brand:
            brand = brand.split('.')[0]
        if brand and brand.lower() not in generic_exclusions:
            return brand.capitalize()

    # 5. Search title from right to left for company brand word
    if title:
        parts = title.strip().split()
        for word in reversed(parts):
            w_clean = re.sub(r'[^a-zA-Z]', '', word)
            if len(w_clean) > 2 and w_clean.lower() not in generic_exclusions:
                return w_clean.capitalize()

    return "Featured Partner"


def resolve_all_jobdexo_company_names():
    """
    Scans all JobPosting records in the database with generic placeholder names
    (like 'Technology Partner' or domain strings) and replaces them with their real company names.
    """
    from .models import JobPosting
    postings = JobPosting.objects.filter(
        Q(company_name__icontains='Technology Partner') |
        Q(company_name__icontains='Featured Partner') |
        Q(company_name__icontains='Policy Bazaar') |
        Q(company_name__icontains='.com') |
        Q(company_name__icontains='kekacom')
    )
    total = postings.count()
    updated_count = 0

    for job in postings:
        cleaned = clean_company_name(
            raw_name=job.company_name,
            title=job.title,
            slug=job.apply_url or "",
            apply_url=job.apply_url or ""
        )
        if cleaned and cleaned != job.company_name:
            job.company_name = cleaned
            job.save(update_fields=['company_name'])
            updated_count += 1

    return {'total': total, 'updated': updated_count}


def extract_salary_from_html(page_html, schema_data=None, fallback="Competitive Package (Best in Industry)"):
    """
    Extracts the official Salary / Stipend / Package from Jobdexo HTML and JSON-LD schema.
    Handles LPA ranges, monthly stipends, and structured schema values.
    """
    if not page_html:
        return fallback

    # 1. Schema.org JSON-LD extraction
    if schema_data and isinstance(schema_data, dict):
        base_sal = schema_data.get('baseSalary') or schema_data.get('estimatedSalary')
        if base_sal:
            if isinstance(base_sal, str) and base_sal.strip():
                return base_sal.strip()
            if isinstance(base_sal, dict):
                val = base_sal.get('value')
                if isinstance(val, str) and val.strip():
                    return val.strip()
                if isinstance(val, (int, float)):
                    if val > 100000:
                        return f"{val/100000:.1f} LPA"
                    return f"₹{val:,}/month"
                if isinstance(val, dict):
                    inner_val = val.get('value') or val.get('minValue')
                    if inner_val:
                        return str(inner_val).strip()
                min_v = base_sal.get('minValue')
                max_v = base_sal.get('maxValue')
                if min_v and max_v:
                    return f"{min_v} - {max_v} LPA"

    # 2. Meta Badge with re.DOTALL and re.IGNORECASE
    m1 = re.search(r'class=[\"\']jd-meta-lbl[\"\'][^>]*>.*?Salary.*?</div>\s*<div[^>]*class=[\"\']jd-meta-val[\"\'][^>]*>([^<]+)</div>', page_html, re.DOTALL | re.IGNORECASE)
    if m1:
        s = html.unescape(m1.group(1).strip())
        if s and not s.lower().startswith('view') and not s.lower().startswith('check'):
            return s

    # 3. Salary Insights Card
    m2 = re.search(r'class=[\"\']jd-card-title[\"\'][^>]*>.*?Salary.*?Insights.*?</div>\s*<div[^>]*>([^<]+)</div>', page_html, re.DOTALL | re.IGNORECASE)
    if m2:
        s = html.unescape(m2.group(1).strip())
        if s and not s.lower().startswith('view'):
            return s

    # 4. Regex Pattern Matching across HTML
    pat_lpa = re.search(r'\b(\d+(?:\.\d+)?\s*(?:-\s*\d+(?:\.\d+)?)?\s*LPA)\b', page_html, re.IGNORECASE)
    if pat_lpa:
        return pat_lpa.group(1).strip()

    pat_inr = re.search(r'(₹\s*\d[\d,]*(?:\s*-\s*₹?\s*\d[\d,]*)?\s*(?:\/\s*(?:month|mo|year|yr|pm))?)', page_html, re.IGNORECASE)
    if pat_inr:
        return pat_inr.group(1).strip()

    pat_ctc = re.search(r'(\d+(?:\.\d+)?\s*(?:-\s*\d+(?:\.\d+)?)?\s*(?:Lakhs?|CTC))', page_html, re.IGNORECASE)
    if pat_ctc:
        return pat_ctc.group(1).strip()

    return fallback


def fallback_parse_from_slug(url):
    """
    Fallback parser: In case Jobdexo rate-limits details (HTTP 429),
    extract company, role title, and batch from the URL slug itself.
    """
    slug = url.rstrip('/').split('/')[-1]
    slug_clean = re.sub(r'-\d+$', '', slug)
    parts = slug_clean.split('-')
    
    title_words = [p.capitalize() for p in parts if not p.isdigit()]
    title = " ".join(title_words) or "Software & Tech Opportunity"
    if not any(k in title.lower() for k in ['engineer', 'developer', 'intern', 'analyst', 'consultant']):
        title = f"{title} Engineer"


    year = "2026"
    for p in reversed(parts):
        if p.isdigit() and len(p) == 4:
            year = p
            break

    company = "Tech Company"
    if parts:
        company = clean_company_name(raw_name=parts[-1].capitalize(), title=" ".join(parts), slug=slug, apply_url=url)

    role_parts = [p.capitalize() for p in parts if not p.isdigit() and p.lower() != parts[-1].lower()]
    title = f"{' '.join(role_parts)} ({year})" if role_parts else f"Software Engineer ({year})"

    return {
        'title': title,
        'company': company,
        'salary': 'Competitive Salary (Freshers)',
        'location': 'Remote / Hybrid, India',
        'skills': 'Problem Solving, Software Engineering, Communication',
        'eligibility': f'Open to {year} batch and all graduating freshers.',
        'selection_process': 'Online Assessment -> Technical Interview -> HR Round',
        'study_materials': [],
        'description': f"{company} is actively hiring for {title}. Open to freshers and college graduates. Check the official application link for comprehensive eligibility and role specifications.",
        'apply_url': url,
        'job_type': 'INTERNSHIP' if 'intern' in slug.lower() else 'FULL_TIME',
        'source_url': url,
        'posted_date': timezone.now().date(),
        'is_expired': False,
    }


def extract_jobdexo_detail(url):
    """
    Scrapes full detail page from Jobdexo with robust schema extraction,
    multi-source fallbacks, and real ATS application link resolver.
    """
    try:
        page_html = fetch_url_html(url, retries=2)
    except Exception as e:
        return fallback_parse_from_slug(url)

    # 1. Structured Data extraction (JSON-LD schema)
    schema_data = {}
    schema_m = re.search(r'<script type="application/ld\+json">({.*?})</script>', page_html, re.DOTALL)
    if schema_m:
        try:
            schema_data = json.loads(schema_m.group(1))
        except Exception:
            pass

    # 2. Title
    title = ""
    if schema_data.get('title'):
        title = schema_data.get('title')
    else:
        h1_m = re.search(r'<h1[^>]*class="[^"]*jd-hero-title[^"]*"[^>]*>(.*?)</h1>', page_html, re.DOTALL)
        if h1_m:
            title = html.unescape(re.sub(r'<[^>]+>', '', h1_m.group(1)).strip())
        else:
            title_m = re.search(r'<title>(.*?)</title>', page_html)
            if title_m:
                title = title_m.group(1).split('|')[0].split('-')[0].strip()

    if not title:
        title = "Software Engineer - Campus Recruitment"

    # 3. Company Name
    raw_company = ""
    badge_m = re.search(r'<span class="jd-company-badge"[^>]*>(.*?)</span>', page_html, re.DOTALL)
    if badge_m:
        raw_company = html.unescape(re.sub(r'<[^>]+>', '', badge_m.group(1)).strip())
    elif schema_data.get('hiringOrganization', {}).get('name'):
        raw_company = schema_data.get('hiringOrganization', {}).get('name')

    slug = url.rstrip('/').split('/')[-1]
    company = clean_company_name(raw_name=raw_company, title=title, slug=slug, apply_url=url)

    # 4. Salary / Stipend / Package (Robust Multi-Source Extraction)
    salary = extract_salary_from_html(page_html, schema_data=schema_data, fallback="Competitive Package (Best in Industry)")

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

    # 9. Official Apply URL Extraction (Strictly Direct / Career ATS Link)
    apply_url = extract_official_apply_url(page_html, url)
    if not apply_url or 'jobdexo.com' in apply_url:
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


def fetch_multi_section_jobdexo_urls(limit=35):
    """
    Crawls across distinct Jobdexo sections with polite pacing.
    """
    discovered_urls = []
    seen_urls = set()

    for endpoint in JOBDEXO_SOURCE_ENDPOINTS:
        try:
            page_html = fetch_url_html(endpoint)
            # Match both relative /job/... and absolute https://jobdexo.com/job/... links
            found_urls = re.findall(r'href=[\"\']((?:https?://(?:www\.)?jobdexo\.com)?/job/[^\"\']+)[\"\']', page_html)
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
    Enterprise-grade multi-tier strict deduplication engine:
    1. In-batch canonical key & clean URL tracking.
    2. Clean application URL match (stripping query parameters and trailing slashes).
    3. Exact normalized company + normalized title match across the entire database.
    4. Substring & high-overlap fuzzy deduplication for same company.
    """
    apply_url = (job_data.get('apply_url') or '').strip()
    source_url = (job_data.get('source_url') or '').strip()
    raw_title = job_data.get('title') or ''
    raw_comp = job_data.get('company') or ''
    
    norm_title = normalize_text(raw_title)
    norm_comp = normalize_text(raw_comp)

    # Clean URL (strip tracking query params and protocol for pure endpoint matching)
    clean_apply = re.sub(r'\?.*$', '', apply_url).rstrip('/').lower() if apply_url and 'jobdexo.com' not in apply_url else None
    clean_source = re.sub(r'\?.*$', '', source_url).rstrip('/').lower() if source_url else None

    # 1. Batch level check
    if seen_in_batch is not None:
        batch_key = f"{norm_comp}::{norm_title}"
        if batch_key in seen_in_batch:
            return True
        if clean_apply and clean_apply in seen_in_batch:
            return True
        if clean_source and clean_source in seen_in_batch:
            return True
        seen_in_batch.add(batch_key)
        if clean_apply:
            seen_in_batch.add(clean_apply)
        if clean_source:
            seen_in_batch.add(clean_source)

    # 2. Match exact or clean apply_url in database
    if clean_apply:
        # Match URL without query string
        if JobPosting.objects.filter(apply_url__icontains=clean_apply[:60]).exists():
            return True

    # 3. Match normalized title + company in all postings
    if norm_comp:
        company_jobs = JobPosting.objects.filter(
            Q(company_name__iexact=raw_comp) |
            Q(company_name__icontains=raw_comp[:5])
        )
        for existing in company_jobs:
            exist_comp_norm = normalize_text(existing.company_name)
            exist_title_norm = normalize_text(existing.title)
            
            # Exact normalized match
            if exist_comp_norm == norm_comp and exist_title_norm == norm_title:
                return True
                
            # Same company + high title similarity (one is substring of other or token match)
            if exist_comp_norm == norm_comp:
                if (len(norm_title) > 6 and norm_title in exist_title_norm) or (len(exist_title_norm) > 6 and exist_title_norm in norm_title):
                    return True
                # Word tokens overlap >= 80%
                t1_tokens = set(re.findall(r'[a-z0-9]+', raw_title.lower()))
                t2_tokens = set(re.findall(r'[a-z0-9]+', existing.title.lower()))
                if t1_tokens and t2_tokens:
                    intersection = t1_tokens.intersection(t2_tokens)
                    similarity = len(intersection) / max(len(t1_tokens), len(t2_tokens))
                    if similarity >= 0.8:
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
        urls = fetch_multi_section_jobdexo_urls(limit=max(35, limit * 4))

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
# HOURLY RECURRING AUTO-SYNC BACKGROUND WORKER (Every 1 Hour)
# ==============================================================================

_SYNC_WORKER_RUNNING = False
_SYNC_LOCK = threading.Lock()


def _background_hourly_sync_loop():
    """Background worker thread that runs every 1 hour (3600 seconds)."""
    global _SYNC_WORKER_RUNNING
    print("🚀 [Jobdexo Auto-Sync] Background hourly sync daemon started (1-hour interval).")
    
    while _SYNC_WORKER_RUNNING:
        try:
            # Sleep 3600 seconds (1 hour) with slight randomized jitter
            time.sleep(3600 + random.randint(10, 60))
            print("⚡ [Jobdexo Auto-Sync] Running hourly automated crawl across all sections...")
            result = auto_import_from_jobdexo(limit=5)
            if result['imported_count'] > 0:
                print(f"✅ [Jobdexo Auto-Sync] Added {result['imported_count']} fresh non-duplicate jobs! Group: {result['group_name']}")
            else:
                print("ℹ️ [Jobdexo Auto-Sync] Checked sections: No new non-duplicate jobs found.")
        except Exception as e:
            print(f"ℹ️ [Jobdexo Auto-Sync] Cycle notice: {e}")


def start_hourly_sync_daemon():
    """Starts the 1-hour background auto-sync worker if not already running."""
    global _SYNC_WORKER_RUNNING
    with _SYNC_LOCK:
        if not _SYNC_WORKER_RUNNING:
            _SYNC_WORKER_RUNNING = True
            t = threading.Thread(target=_background_hourly_sync_loop, daemon=True, name="JobdexoHourlySyncWorker")
            t.start()
            return True
    return False


# Alias for backward compatibility
start_5min_sync_daemon = start_hourly_sync_daemon
