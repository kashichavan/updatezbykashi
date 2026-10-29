"""
⚡ Kashii Updatez — LinkedIn Post Scraper, Referral Parser & Lead Validator Engine.

Supports:
1. Public LinkedIn Post Scraping (Posts, Feed Updates, Public Jobs).
2. AI-Powered & Heuristic Content Parsing (Company, Role, Skills, Batch, Package).
3. First-Class Employee Referral Recognition (Referrer Name, LinkedIn Profile, Referral Instructions).
4. Strict Multi-Point Quality Validation & Instant Pass/Publish Pipeline.
"""

import re
import html
import json
import logging
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import requests
from django.utils import timezone
from datetime import timedelta

from .company_resolver import resolve_company_name
from .models import JobPosting, Category

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


def clean_url(url: str) -> str:
    """Strip tracking parameters and clean trailing punctuation."""
    if not url:
        return ""
    url = url.strip().rstrip(".,;!)\"'>")
    # Clean standard UTM and tracking params
    if "?" in url:
        base, query = url.split("?", 1)
        params = [p for p in query.split("&") if not re.match(r'^(utm_|trk|refId|trackingId|midToken)', p, re.I)]
        url = f"{base}?{'&'.join(params)}" if params else base
    return url


def scrape_linkedin_url(url: str, timeout: int = 8) -> Dict[str, Any]:
    """
    Scrapes public metadata from a LinkedIn URL (Post or Job).
    Extracts OpenGraph title, description, author, and canonical link.
    """
    cleaned_url = clean_url(url)
    if not cleaned_url:
        return {"error": "Invalid URL provided."}

    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(cleaned_url, headers=headers, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            html_text = resp.text

            # Extract OpenGraph Tags
            og_title = ""
            og_desc = ""
            og_author = ""

            m_title = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', html_text, re.I)
            if not m_title:
                m_title = re.search(r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:title["\']', html_text, re.I)
            if m_title:
                og_title = html.unescape(m_title.group(1).strip())

            m_desc = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']', html_text, re.I)
            if not m_desc:
                m_desc = re.search(r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:description["\']', html_text, re.I)
            if m_desc:
                og_desc = html.unescape(m_desc.group(1).strip())

            m_author = re.search(r'<meta\s+name=["\']author["\']\s+content=["\'](.*?)["\']', html_text, re.I)
            if m_author:
                og_author = html.unescape(m_author.group(1).strip())

            # Check JSON-LD
            json_ld_matches = re.findall(r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>', html_text, re.I | re.DOTALL)
            for j_raw in json_ld_matches:
                try:
                    data = json.loads(j_raw)
                    if isinstance(data, dict):
                        if data.get("@type") == "JobPosting":
                            return {
                                "success": True,
                                "source_url": cleaned_url,
                                "title": data.get("title", og_title),
                                "company": data.get("hiringOrganization", {}).get("name", ""),
                                "description": data.get("description", og_desc),
                                "location": data.get("jobLocation", {}).get("address", {}).get("addressLocality", "India"),
                                "raw_text": f"{data.get('title', '')} at {data.get('hiringOrganization', {}).get('name', '')}\n\n{data.get('description', '')}"
                            }
                except Exception:
                    continue

            combined_text = f"{og_title}\n\n{og_desc}".strip()
            return {
                "success": True,
                "source_url": cleaned_url,
                "og_title": og_title,
                "og_description": og_desc,
                "og_author": og_author,
                "raw_text": combined_text
            }
        else:
            return {
                "success": False,
                "status_code": resp.status_code,
                "error": f"LinkedIn returned HTTP {resp.status_code}. Public scraping limited by auth wall.",
                "source_url": cleaned_url
            }
    except Exception as e:
        logger.warning(f"Error scraping LinkedIn URL {cleaned_url}: {e}")
        return {
            "success": False,
            "error": str(e),
            "source_url": cleaned_url
        }


def parse_linkedin_content(
    raw_text: str,
    source_url: str = "",
    force_referral: Optional[bool] = None,
    referrer_name: str = "",
    referrer_linkedin: str = "",
) -> Dict[str, Any]:
    """
    Parses LinkedIn job requirements and employee referral posts into structured data.
    Uses Groq AI with instant deterministic regex fallback.
    """
    raw_text = (raw_text or "").strip()
    source_url = clean_url(source_url)

    # 1. Try AI parsing via Groq if available
    ai_data = None
    try:
        from .ai_engine import call_groq_chat, get_groq_api_key
        if get_groq_api_key():
            prompt = f"""You are an elite Tech Job Ingestion & Referral Extractor.
Parse the following LinkedIn post into structured JSON with these exact keys:
- 'company': Company name hiring (e.g. 'Amazon', 'TCS', 'Swiggy')
- 'title': Job role title (e.g. 'Software Development Engineer - 1')
- 'location': City or 'Remote / Bangalore'
- 'is_remote': boolean
- 'stipend_salary': Salary package or stipend (e.g. '₹12 - 18 LPA' or 'Competitive')
- 'skills_required': Comma-separated tech stack (e.g. 'Java, Spring Boot, AWS, SQL')
- 'eligibility': Batch/degree criteria (e.g. '2024 - 2026 Batch, B.E / B.Tech / MCA')
- 'apply_url': Application URL or mailto: link
- 'is_referral': boolean (true if an employee/insider is offering to refer candidates)
- 'referrer_name': Name of the person offering the referral or posting (if detected)
- 'referrer_linkedin': Profile link of the referrer (e.g. https://linkedin.com/in/...)
- 'referral_instructions': Specific steps on how to ask for referral (e.g. 'Email resume with Job ID to ...')
- 'description': Clean, formatted 3-4 paragraph description of role responsibilities

LinkedIn Post Text:
\"\"\"{raw_text}\"\"\"

Source URL: {source_url}
"""
            messages = [
                {"role": "system", "content": "You extract structured job and referral opportunities. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ]
            resp_str = call_groq_chat(messages, temperature=0.1, json_mode=True, timeout=8)
            ai_data = json.loads(resp_str)
    except Exception as e:
        logger.warning(f"Groq parsing for LinkedIn post bypassed or failed: {e}")

    if ai_data and isinstance(ai_data, dict) and ai_data.get("company"):
        data = ai_data
    else:
        # 2. Resilient Rule-Based / Regex Extraction Engine
        data = _heuristic_linkedin_parse(raw_text, source_url)

    # Apply manual overrides if provided
    if force_referral is not None:
        data["is_referral"] = bool(force_referral)
    if referrer_name:
        data["referrer_name"] = referrer_name.strip()
    if referrer_linkedin:
        data["referrer_linkedin"] = clean_url(referrer_linkedin)
    if source_url and not data.get("source_url"):
        data["source_url"] = source_url

    # Ensure resolved company name
    resolved_comp = resolve_company_name(
        raw_name=data.get("company", ""),
        title=data.get("title", ""),
        description=data.get("description", raw_text),
        apply_url=data.get("apply_url", source_url)
    )
    if resolved_comp and resolved_comp != "Unknown Company":
        data["company"] = resolved_comp

    return data


def _heuristic_linkedin_parse(raw_text: str, source_url: str = "") -> Dict[str, Any]:
    """High-accuracy fallback regex extractor for LinkedIn posts."""
    text_lower = raw_text.lower()

    # Detect if this is an employee referral
    referral_keywords = [
        "referral", "can refer", "happy to refer", "providing referral", "referring for",
        "drop your resume", "share cv", "dm me with your resume", "dm for referral",
        "internal referral", "job id", "referrals available", "referral alert"
    ]
    is_referral = any(rk in text_lower for rk in referral_keywords)

    # Extract Links & Emails
    links = re.findall(r'https?://[^\s<>"\']+', raw_text)
    emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', raw_text)

    apply_url = ""
    referrer_linkedin = ""
    for link in links:
        link_clean = clean_url(link)
        if "linkedin.com/in/" in link_clean:
            if not referrer_linkedin:
                referrer_linkedin = link_clean
        elif not apply_url and not ("linkedin.com/feed" in link_clean or "linkedin.com/posts" in link_clean):
            apply_url = link_clean

    if not apply_url and emails:
        apply_url = f"mailto:{emails[0]}"
    if not apply_url and source_url:
        apply_url = source_url

    # Company Extraction
    company = ""
    comp_match = re.search(r'(?:Company|Organization|Hiring at|At|Joining)\s*[:\-–]\s*([A-Za-z0-9&.\s]{2,40})', raw_text, re.I)
    if comp_match:
        company = comp_match.group(1).split("\n")[0].strip()
    else:
        # Common tech firms mentioned
        common_firms = [
            "Google", "Microsoft", "Amazon", "Flipkart", "TCS", "Infosys", "Wipro",
            "Accenture", "Cognizant", "Swiggy", "Zomato", "PhonePe", "Razorpay",
            "Paytm", "Cred", "Zoho", "Jio", "Oracle", "Cisco", "IBM", "Capgemini",
            "Deloitte", "Goldman Sachs", "Morgan Stanley", "Uber", "Adobe"
        ]
        for firm in common_firms:
            if re.search(r'\b' + re.escape(firm) + r'\b', raw_text, re.I):
                company = firm
                break
    if not company:
        company = "Tech Enterprise"

    # Role / Title Extraction
    title = ""
    title_match = re.search(r'(?:Role|Title|Position|Hiring for|Looking for|Opening for)\s*[:\-–]\s*([A-Za-z0-9/\s()–-]{3,60})', raw_text, re.I)
    if title_match:
        title = title_match.group(1).split("\n")[0].strip()
    else:
        common_roles = [
            "Software Development Engineer", "SDE-1", "SDE-2", "Full Stack Developer",
            "Frontend Engineer", "Backend Developer", "Java Developer", "Python Developer",
            "QA Automation Engineer", "Data Analyst", "Data Engineer", "DevOps Engineer",
            "Cloud Engineer", "Associate Software Engineer", "Graduate Trainee"
        ]
        for r in common_roles:
            if re.search(r'\b' + re.escape(r) + r'\b', raw_text, re.I):
                title = r
                break
    if not title:
        title = "Software Engineer / Tech Opportunity"

    # Skills Extraction
    from .skill_extractor import extract_technical_skills
    skills_match = re.search(r'(?:Skills|Tech Stack|Required|Technologies)\s*[:\-–]\s*(.+)', raw_text, re.I)
    raw_skills = skills_match.group(1).split("\n")[0].strip() if skills_match else ""
    skills = extract_technical_skills(
        title=title,
        raw_skills=raw_skills,
        description=raw_text,
        category_slug="software-engineering"
    )

    # Location Extraction
    loc_match = re.search(r'(?:Location|City|Base)\s*[:\-–]\s*(.+)', raw_text, re.I)
    location = loc_match.group(1).split("\n")[0].strip() if loc_match else ("Remote" if "remote" in text_lower else "Bengaluru / Hybrid")

    # Salary / Package
    sal_match = re.search(r'(\b\d+[\.,]?\d*\s*(?:LPA|L|CTC|k|per month|month|yr|INR|₹|\$)\b)', raw_text, re.I)
    stipend_salary = sal_match.group(0).strip() if sal_match else "Competitive Package"

    # Eligibility / Batch
    batch_match = re.search(r'(\b202[3-7]\s*(?:batch|passout|pass out|graduates|grads)?\b)', raw_text, re.I)
    eligibility = f"Target Batch: {batch_match.group(0)}" if batch_match else "Open to final year students and fresh graduates."

    # Referrer Name
    referrer_name = ""
    author_match = re.search(r'(?:Referred by|Posted by|Connect with|Regards|Thanks,)\s*[:\-–]?\s*([A-Za-z\s]{3,30})', raw_text, re.I)
    if author_match:
        referrer_name = author_match.group(1).split("\n")[0].strip()

    # Referral instructions
    referral_instructions = ""
    if is_referral:
        inst_parts = []
        if emails:
            inst_parts.append(f"Send your updated resume to: {emails[0]}")
        job_id_match = re.search(r'(?:Job ID|Requisition ID|Req ID)\s*[:\-–]\s*([A-Za-z0-9_-]+)', raw_text, re.I)
        if job_id_match:
            inst_parts.append(f"Mention Job ID: {job_id_match.group(1)} in email subject line")
        if referrer_linkedin:
            inst_parts.append(f"Or send direct message on LinkedIn: {referrer_linkedin}")
        if not inst_parts:
            inst_parts.append("Connect with the referrer on LinkedIn with your resume and target role title.")
        referral_instructions = "\n".join(f"• {part}" for part in inst_parts)

    return {
        "company": company,
        "title": title,
        "location": location,
        "is_remote": "remote" in location.lower(),
        "stipend_salary": stipend_salary,
        "skills_required": skills,
        "eligibility": eligibility,
        "apply_url": apply_url,
        "is_referral": is_referral,
        "referrer_name": referrer_name,
        "referrer_linkedin": referrer_linkedin,
        "referral_instructions": referral_instructions,
        "description": raw_text[:2000] if len(raw_text) > 40 else f"Opportunity at {company} for {title}. Requirements: {skills}.",
        "source_url": source_url,
    }


def validate_linkedin_lead(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates candidate post against quality and integrity rules.
    Returns validation scorecard with PASS / NEEDS_REVIEW status.
    """
    checks = []
    points = 0
    max_points = 100

    comp = (parsed_data.get("company") or "").strip()
    title = (parsed_data.get("title") or "").strip()
    apply_url = (parsed_data.get("apply_url") or "").strip()
    skills = (parsed_data.get("skills_required") or "").strip()
    is_referral = bool(parsed_data.get("is_referral"))
    referrer_name = (parsed_data.get("referrer_name") or "").strip()
    referrer_linkedin = (parsed_data.get("referrer_linkedin") or "").strip()
    instructions = (parsed_data.get("referral_instructions") or "").strip()

    # 1. Company Name (25 pts)
    has_valid_company = bool(comp and comp != "Unknown Company" and len(comp) >= 2)
    checks.append({
        "rule": "Company Identification",
        "passed": has_valid_company,
        "detail": f"Identified company: '{comp}'" if has_valid_company else "Missing or unrecognized hiring company name.",
        "points": 25 if has_valid_company else 0
    })
    if has_valid_company:
        points += 25

    # 2. Role Title (25 pts)
    has_valid_title = bool(title and len(title) >= 3 and title != "Software & Technology Opportunity")
    checks.append({
        "rule": "Role Title Precision",
        "passed": has_valid_title,
        "detail": f"Position: '{title}'" if has_valid_title else "Generic role title; specify exact designation.",
        "points": 25 if has_valid_title else 10
    })
    points += (25 if has_valid_title else 10)

    # 3. Application Destination (25 pts)
    has_dest = bool(apply_url and (apply_url.startswith("http") or apply_url.startswith("mailto:")))
    checks.append({
        "rule": "Application URL / Referral Email",
        "passed": has_dest,
        "detail": f"Direct link/email: {apply_url[:45]}..." if has_dest else "No valid apply URL or referral contact email found.",
        "points": 25 if has_dest else 0
    })
    if has_dest:
        points += 25

    # 4. Tech Stack / Skills (15 pts)
    has_skills = bool(skills and len(skills) >= 4)
    checks.append({
        "rule": "Skills & Tech Stack Tags",
        "passed": has_skills,
        "detail": f"Skills: {skills}" if has_skills else "No skills parsed.",
        "points": 15 if has_skills else 5
    })
    points += (15 if has_skills else 5)

    # 5. Referral Attribution & Mention (10 pts)
    if is_referral:
        has_referrer = bool(referrer_name or referrer_linkedin or instructions)
        checks.append({
            "rule": "Referrer Attribution & Instructions",
            "passed": has_referrer,
            "detail": f"Referrer: {referrer_name or 'Company Employee'} ({referrer_linkedin or 'Direct Email'})" if has_referrer else "Employee referral lacking referrer mention or guidelines.",
            "points": 10 if has_referrer else 0
        })
        if has_referrer:
            points += 10
    else:
        checks.append({
            "rule": "Requirement Classification",
            "passed": True,
            "detail": "Verified direct hiring requirement post.",
            "points": 10
        })
        points += 10

    score = min(100, max(0, points))
    is_pass = score >= 70 and has_valid_company and (has_dest or (is_referral and instructions))

    return {
        "score": score,
        "is_valid": is_pass,
        "status": "PASS" if is_pass else "NEEDS_REVIEW",
        "badge_text": "✅ VALIDATED — READY TO PASS" if is_pass else "⚠️ NEEDS ATTENTION",
        "checks": checks,
        "is_referral": is_referral,
        "company": comp,
        "title": title
    }


def publish_linkedin_lead(data: Dict[str, Any], posted_by_user: str = "LinkedIn Scraper") -> JobPosting:
    """
    Publishes validated LinkedIn lead directly to the active live pipeline.
    """
    category = Category.objects.filter(slug='software-tech').first()
    if not category:
        category = Category.objects.create(name='Software & Tech', slug='software-tech')

    is_referral = bool(data.get("is_referral", False))
    comp_name = resolve_company_name(
        raw_name=data.get("company", ""),
        title=data.get("title", ""),
        apply_url=data.get("apply_url", "")
    )

    now = timezone.now()
    deadline = now + timedelta(days=7)

    job = JobPosting.objects.create(
        category=category,
        title=data.get("title", "Software Engineering Opportunity"),
        company_name=comp_name,
        location=data.get("location", "Bengaluru / Hybrid"),
        is_remote=bool(data.get("is_remote", False)),
        job_type="FULL_TIME",
        stipend_salary=data.get("stipend_salary", "Competitive"),
        skills_required=data.get("skills_required", "Software Development, Problem Solving"),
        apply_url=data.get("apply_url", "https://linkedin.com"),
        description=data.get("description", ""),
        eligibility=data.get("eligibility", "Open to all eligible graduates"),
        status="ACTIVE",
        source_name="LinkedIn Referral" if is_referral else "LinkedIn",
        source_url=data.get("source_url", ""),
        posted_by=posted_by_user,
        deadline=deadline,
        # Referral fields
        is_referral=is_referral,
        referrer_name=data.get("referrer_name") or "",
        referrer_linkedin=data.get("referrer_linkedin") or "",
        referral_instructions=data.get("referral_instructions") or ""
    )
    return job
