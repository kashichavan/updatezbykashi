# requirements/services/recruiter_finder.py
"""
Recruiter & Hiring-Manager Contact Discovery Engine.

Design rules (important):
  1. NEVER invent, guess, or pattern-generate an email address.
  2. Every email shown to a candidate must be traceable to a public source URL.
  3. If no public email exists, say so and give the candidate better next steps.

Discovery sources:
  - The job posting itself (highest confidence).
  - Public GitHub profiles and public commit metadata (author email).
  - Public web search results (Bing / optional SearXNG / optional Serper / optional Brave API)
    plus a small number of fetched public pages.
  - The employer's own careers/contact pages (role inboxes only).

LinkedIn itself is auth-walled and is not scraped. We generate X-Ray search links so the
candidate can review public profiles in their own browser, and we can resolve an email only
when that person's address is independently published elsewhere.
"""

from __future__ import annotations

import base64
import hashlib
import ipaddress
import logging
import os
import re
import socket
import urllib.parse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from xml.etree import ElementTree

import requests
from django.core.cache import cache

try:  # Optional but strongly recommended for HTML parsing.
    from lxml import html as lxml_html
except Exception:  # pragma: no cover - exercised only on minimal installs
    lxml_html = None

try:
    import dns.resolver
    DNSPYTHON_AVAILABLE = True
except Exception:  # pragma: no cover
    DNSPYTHON_AVAILABLE = False


logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 8
PAGE_TIMEOUT = 7
MAX_PAGE_BYTES = 600_000
MAX_FETCHED_PAGES = 3
SEARCH_CACHE_TTL = 60 * 60 * 6       # 6 hours
DISCOVERY_CACHE_TTL = 60 * 60 * 6    # 6 hours
MX_CACHE_TTL = 60 * 60 * 24          # 24 hours

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HTTP_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}

EMAIL_RE = re.compile(
    r"(?<![\w.+-])([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24})(?![\w.\-])"
)
ROLE_LOCAL_PARTS = {
    "careers", "career", "jobs", "job", "hiring", "hr", "humanresources",
    "recruit", "recruiting", "recruitment", "recruiter", "talent", "ta",
    "people", "team", "hello", "contact", "info", "support", "admin",
    "office", "enquiry", "enquiries", "inquiry", "inquiries", "apply",
    "applications", "resume", "resumes", "cv", "referral", "referrals",
}
NON_DELIVERABLE_LOCAL_PARTS = {
    "noreply", "no-reply", "donotreply", "do-not-reply", "postmaster",
    "abuse", "webmaster", "hostmaster", "root", "mailer-daemon",
}
BLOCKED_EMAIL_DOMAINS = {
    "example.com", "example.org", "example.net", "domain.com", "email.com",
    "yourdomain.com", "yourcompany.com", "company.com", "test.com",
    "sentry.io", "sentry-next.wixpress.com", "wixpress.com", "sentry.wixpress.com",
    "linkedin.com", "facebook.com", "twitter.com", "instagram.com",
    "googlemail.com", "users.noreply.github.com",
}
BLOCKED_TLDS = {
    "png", "jpg", "jpeg", "gif", "webp", "svg", "ico", "css", "js", "json",
    "woff", "woff2", "ttf", "eot", "map", "pdf",
}
SOCIAL_HOSTS = {
    "linkedin.com", "www.linkedin.com", "facebook.com", "www.facebook.com",
    "twitter.com", "x.com", "instagram.com", "www.instagram.com",
    "youtube.com", "www.youtube.com", "tiktok.com", "pinterest.com",
    "glassdoor.com", "www.glassdoor.com", "indeed.com", "www.indeed.com",
    "naukri.com", "www.naukri.com", "quora.com", "www.quora.com",
    "reddit.com", "www.reddit.com",
}
SEARCH_HOSTS = {
    "bing.com", "www.bing.com", "google.com", "www.google.com",
    "duckduckgo.com", "html.duckduckgo.com", "search.brave.com",
    "mojeek.com", "www.mojeek.com",
}
# Contact-data brokers gate addresses behind paywalls and frequently show stale or
# invented "teaser" emails. They are never treated as evidence.
DATA_BROKER_HOSTS = {
    "contactout.com", "rocketreach.co", "wiza.co", "wiza.com", "aeroleads.com",
    "hunter.io", "snov.io", "lusha.com", "apollo.io", "zoominfo.com",
    "leadiq.com", "seamless.ai", "uplead.com", "clearbit.com", "signalhire.com",
    "datanyze.com", "kompass.com", "leadiq", "emailist.io", "findthatemail.com",
    "salezshark.com", "slintel.com", "insideview.com", "lead411.com",
    "peopledatalabs.com", "spokeo.com", "beenverified.com", "whitepages.com",
    "truepeoplesearch.com", "fastpeoplesearch.com", "radaris.com",
}
ROLE_TITLE_HINTS = re.compile(
    r"(?i)\b(recruit|talent|hiring|human resources|\bhr\b|sourcer|people partner|campus)\b"
)


# High-frequency employer domains. Used only to build search/careers links and to
# rank candidates; never to construct an email local-part.
KNOWN_COMPANY_DOMAINS = {
    "accenture": "accenture.com",
    "tcs": "tcs.com",
    "tata consultancy services": "tcs.com",
    "infosys": "infosys.com",
    "wipro": "wipro.com",
    "cognizant": "cognizant.com",
    "hcl": "hcltech.com",
    "hcltech": "hcltech.com",
    "tech mahindra": "techmahindra.com",
    "capgemini": "capgemini.com",
    "ltimindtree": "ltimindtree.com",
    "l&t": "ltts.com",
    "ltts": "ltts.com",
    "deloitte": "deloitte.com",
    "pwc": "pwc.com",
    "ey": "ey.com",
    "ernst & young": "ey.com",
    "kpmg": "kpmg.com",
    "ibm": "ibm.com",
    "oracle": "oracle.com",
    "sap": "sap.com",
    "cisco": "cisco.com",
    "salesforce": "salesforce.com",
    "epam": "epam.com",
    "epam systems": "epam.com",
    "virtusa": "virtusa.com",
    "hexaware": "hexaware.com",
    "hexaware technologies": "hexaware.com",
    "aspire systems": "aspiresys.com",
    "mphasis": "mphasis.com",
    "cgi": "cgi.com",
    "trigent": "trigent.com",
    "trigent software": "trigent.com",
    "opentext": "opentext.com",
    "zettamine": "zettamine.com",
    "zettamine labs": "zettamine.com",
    "sparity": "sparity.com",
    "honeybee tech solutions": "honeybeetechsolutions.com",
    "yotta infrastructure": "yotta.com",
    "swiggy": "swiggy.in",
    "zomato": "zomato.com",
    "razorpay": "razorpay.com",
    "phonepe": "phonepe.com",
    "paytm": "paytm.com",
    "zepto": "zeptonow.com",
    "blinkit": "blinkit.com",
    "flipkart": "flipkart.com",
    "meesho": "meesho.com",
    "cred": "cred.club",
    "zerodha": "zerodha.com",
    "groww": "groww.in",
    "ola": "olacabs.com",
    "ola electric": "olaelectric.com",
    "uber": "uber.com",
    "freshworks": "freshworks.com",
    "zoho": "zoho.com",
    "unacademy": "unacademy.com",
    "byjus": "byjus.com",
    "jio": "jio.com",
    "reliance jio": "jio.com",
    "airtel": "airtel.in",
    "amazon": "amazon.com",
    "google": "google.com",
    "microsoft": "microsoft.com",
    "meta": "meta.com",
    "apple": "apple.com",
    "adobe": "adobe.com",
    "netflix": "netflix.com",
    "intuit": "intuit.com",
    "atlassian": "atlassian.com",
    "walmart": "walmart.com",
    "qualcomm": "qualcomm.com",
    "jpmorgan": "jpmorgan.com",
    "jpmorganchase": "jpmorgan.com",
    "goldman sachs": "gs.com",
    "morgan stanley": "morganstanley.com",
    "barclays": "barclays.com",
    "siemens": "siemens.com",
    "intel": "intel.com",
    "nvidia": "nvidia.com",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class EmailCandidate:
    email: str
    label: str
    confidence: str                 # high | medium | team
    source: str                     # job_post | github_profile | github_commit | web | company_site | user
    source_url: str = ""
    evidence: str = ""
    is_personal: bool = True
    company_linked: bool = False    # tied to the employer by domain, page text, or repo owner
    mx_valid: Optional[bool] = None
    score: int = 0
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cache_get(key: str) -> Any:
    try:
        return cache.get(key)
    except Exception:
        return None


def _cache_set(key: str, value: Any, ttl: int) -> None:
    try:
        cache.set(key, value, ttl)
    except Exception:
        pass


def _hash(*parts: str) -> str:
    raw = "|".join(p or "" for p in parts).lower().strip()
    return hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:32]


def _norm_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _name_tokens(value: str) -> List[str]:
    return [t for t in _norm_name(value).split() if len(t) > 1]


def _contains_person(text: str, name: str) -> bool:
    """True when all meaningful tokens of a name appear in the text."""
    tokens = _name_tokens(name)
    if not tokens:
        return False
    haystack = _norm_name(text)
    return all(t in haystack for t in tokens)


def _person_match_strength(text: str, name: str) -> int:
    """0 = no match, 1 = last name only, 2 = full name present."""
    tokens = _name_tokens(name)
    if not tokens:
        return 0
    haystack = _norm_name(text)
    if all(t in haystack for t in tokens):
        return 2
    if len(tokens) > 1 and tokens[-1] in haystack:
        return 1
    return 0


def clean_company_name_for_search(company_name: str) -> str:
    """Normalize raw company strings for search queries."""
    if not company_name:
        return ""
    clean = re.sub(
        r"(?i)\b(pvt\.?|private|ltd\.?|limited|llc|inc\.?|corp\.?|corporation|"
        r"solutions|technologies|technology services|services india|india|"
        r"technologies pvt ltd)\b",
        "",
        company_name,
    )
    clean = re.sub(r"(?i)\b(mega|walk-in|walkin|drive|off-campus|hiring|fresher)\b", "", clean)
    clean = re.sub(r"[^a-zA-Z0-9\s&]", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip(" ,.-")
    return clean or company_name.strip()


def resolve_company_domain(company_name: str) -> str:
    """Best-effort company domain used for search links and ranking (never for guessing emails)."""
    raw = (company_name or "").strip().lower()
    if re.fullmatch(r"(?:www\.)?[a-z0-9][a-z0-9\-]*\.[a-z]{2,12}", raw):
        return raw[4:] if raw.startswith("www.") else raw
    clean = clean_company_name_for_search(company_name).lower().strip()
    if len(clean) < 2:
        return ""
    for name_key, domain in KNOWN_COMPANY_DOMAINS.items():
        if not name_key:
            continue
        if clean == name_key:
            return domain
        if len(clean) >= 4 and len(name_key) >= 4 and (clean in name_key or name_key in clean):
            return domain
    slug = re.sub(r"[^a-zA-Z0-9]+", "", clean)
    return f"{slug}.com" if slug else ""


def parse_linkedin_profile_url(linkedin_url: str) -> Optional[Dict[str, str]]:
    """
    Parse a LinkedIn profile URL (CrossLinked-style slug parsing).

    Example: 'https://www.linkedin.com/in/sneha-nair-recruiter/' -> 'Sneha Nair'
    """
    if not linkedin_url:
        return None
    match = re.search(r"linkedin\.com/in/([a-zA-Z0-9_\-\.]+)", linkedin_url.strip())
    if not match:
        return None
    slug = match.group(1).strip("/")
    clean_slug = re.sub(r"-[0-9a-f]{5,}$", "", slug)
    clean_slug = re.sub(r"-\d+$", "", clean_slug)
    clean_slug = re.sub(
        r"(?i)-(recruiter|talent|hr|ta|lead|tech|sourcing|hiring|partner|specialist|manager|campus)$",
        "",
        clean_slug,
    )
    parts = [
        p.capitalize()
        for p in clean_slug.split("-")
        if p and not p.isdigit() and len(p) > 1 and p.lower() not in ROLE_LOCAL_PARTS
    ]
    first_name = parts[0] if parts else ""
    last_name = parts[-1] if len(parts) > 1 else ""
    full_name = f"{first_name} {last_name}".strip()
    return {
        "slug": slug,
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name or clean_slug.replace("-", " ").title(),
    }


def build_google_xray_url(company_name: str, name: str = "") -> str:
    """High-precision Google X-Ray URL for public LinkedIn profiles (no scraping)."""
    clean_company = clean_company_name_for_search(company_name) or company_name
    name_part = f'"{name}" ' if name else ""
    query = (
        f'{name_part}site:linkedin.com/in "{clean_company}" '
        f'(recruiter OR "talent acquisition" OR "technical recruiter" OR "hiring manager")'
    )
    return f"https://www.google.com/search?q={urllib.parse.quote(query)}"


def build_sourcing_links(name: str, company_name: str, linkedin_url: str = "") -> Dict[str, str]:
    """Deep links the candidate can open themselves (no scraping, no login bypass)."""
    clean_company = clean_company_name_for_search(company_name) or company_name
    domain = resolve_company_domain(company_name)
    person = (name or "").strip()
    encoded_name = urllib.parse.quote_plus(person)
    encoded_company = urllib.parse.quote_plus(clean_company)
    encoded_domain = urllib.parse.quote_plus(domain)

    linkedin_people = (
        "https://www.linkedin.com/search/results/people/?"
        f"keywords={urllib.parse.quote_plus(f'{person} {clean_company} recruiter'.strip())}"
    )
    gmail_query = f'"{person}" OR "{domain}"' if person else f'"{domain}"'
    github_query = f'"{person}" "{clean_company}"' if person else f'"{clean_company}"'

    return {
        "linkedin_search_url": linkedin_url or linkedin_people,
        "linkedin_people_url": linkedin_people,
        "google_xray_url": build_google_xray_url(company_name, person),
        "google_email_url": (
            "https://www.google.com/search?q="
            + urllib.parse.quote_plus(f'"{person}" "{clean_company}" email'.strip())
        ),
        "google_phone_url": (
            "https://www.google.com/search?q="
            + urllib.parse.quote_plus(f'"{person}" "{clean_company}" phone'.strip())
        ),
        "bing_search_url": (
            "https://www.bing.com/search?q="
            + urllib.parse.quote_plus(f'"{person}" "{clean_company}" (email OR contact)'.strip())
        ),
        "gmail_search_url": "https://mail.google.com/mail/u/0/#search/" + urllib.parse.quote(gmail_query),
        "github_search_url": "https://github.com/search?type=users&q=" + urllib.parse.quote_plus(github_query),
        "company_careers_url": f"https://{domain}/careers" if domain else "",
        "company_contact_url": f"https://{domain}/contact" if domain else "",
        "google_company_recruiter_url": (
            "https://www.google.com/search?q="
            + urllib.parse.quote_plus(f'site:linkedin.com/in "{clean_company}" recruiter')
        ),
        "encoded_name": encoded_name,
        "encoded_company": encoded_company,
        "encoded_domain": encoded_domain,
    }


# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------

def is_valid_email_syntax(email: str) -> bool:
    if not email or len(email) > 254:
        return False
    if email.count("@") != 1:
        return False
    local, domain = email.rsplit("@", 1)
    if not local or not domain or "." not in domain:
        return False
    if len(local) > 64 or local.startswith(".") or local.endswith(".") or ".." in local:
        return False
    if domain.startswith(".") or domain.endswith(".") or ".." in domain:
        return False
    tld = domain.rsplit(".", 1)[-1].lower()
    if not tld.isalpha() or len(tld) < 2 or tld in BLOCKED_TLDS:
        return False
    return True


def normalize_email(email: str) -> str:
    return (email or "").strip().strip(".,;:()[]<>\"'").lower()


def is_role_inbox(email: str) -> bool:
    local = email.split("@", 1)[0].lower()
    base = re.split(r"[._+\-]", local)[0]
    return base in ROLE_LOCAL_PARTS or local in ROLE_LOCAL_PARTS


def email_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower() if "@" in email else ""


def _domain_matches(email: str, company_domain: str) -> bool:
    domain = email_domain(email)
    company_domain = (company_domain or "").lower().strip()
    if not domain or not company_domain:
        return False
    if domain == company_domain or domain.endswith("." + company_domain):
        return True
    # linux-foundation.org vs linuxfoundation.com -> same org core
    core = _domain_core(domain)
    return bool(core) and core == _domain_core(company_domain)


def _domain_core(domain: str) -> str:
    """Reduce a domain to its organisation label: www.linux-foundation.org -> linuxfoundation."""
    value = (domain or "").lower().strip().strip(".")
    if value.startswith("www."):
        value = value[4:]
    parts = [p for p in value.split(".") if p]
    if len(parts) >= 3 and parts[-2] in {"co", "com", "org", "net", "ac", "gov", "edu"}:
        value = parts[-3]
    elif len(parts) >= 2:
        value = parts[-2]
    elif parts:
        value = parts[0]
    else:
        value = ""
    return re.sub(r"[^a-z0-9]", "", value)


GENERIC_COMPANY_WORDS = {
    "india", "pvt", "ltd", "limited", "inc", "llc", "corp", "corporation",
    "solutions", "technologies", "technology", "services", "labs", "private",
    "group", "global", "the", "and",
}


def _company_mentioned(text: str, company_name: str = "", company_domain: str = "") -> bool:
    """True when the page/repo text plausibly refers to this employer."""
    if not text:
        return False
    haystack = _norm_name(text)
    core = _domain_core(company_domain)
    if core and len(core) >= 4 and core in re.sub(r"[^a-z0-9]", "", haystack):
        return True
    tokens = [
        t for t in _name_tokens(clean_company_name_for_search(company_name))
        if t not in GENERIC_COMPANY_WORDS and len(t) > 2
    ]
    if not tokens:
        return False
    return all(token in haystack for token in tokens)


def _refine_company_domain(company_name: str, domain: str) -> str:
    """
    If the guessed domain has no DNS at all, try a small set of realistic variants.

    This only fixes *dead* guesses (e.g. linuxfoundation.com -> linux-foundation.org).
    It never turns a guess into an email address.
    """
    if not domain:
        return domain
    try:
        primary = check_domain_mx(domain)
        if primary.get("accepts_mail") is not False:
            return domain
    except Exception:
        return domain

    clean = clean_company_name_for_search(company_name).lower()
    words = [w for w in re.split(r"[^a-z0-9]+", clean) if w]
    if not words:
        return domain
    slug = "".join(words)
    hyphen = "-".join(words)
    candidates = []
    for base in (hyphen, slug):
        for tld in ("com", "org", "io", "co", "in", "net", "ai"):
            candidate = f"{base}.{tld}"
            if candidate != domain and candidate not in candidates:
                candidates.append(candidate)

    for candidate in candidates[:8]:
        try:
            if check_domain_mx(candidate).get("accepts_mail"):
                return candidate
        except Exception:
            continue
    return domain


def check_domain_mx(domain: str) -> Dict[str, Any]:
    """
    Check whether a domain accepts mail. Uses MX first, A record as implicit-MX fallback.
    Returns {'checked': bool, 'mx': bool, 'accepts_mail': Optional[bool]}.
    """
    domain = (domain or "").lower().strip()
    if not domain:
        return {"checked": False, "mx": False, "accepts_mail": None}

    cache_key = f"recruiter:mx:{domain}"
    cached = _cache_get(cache_key)
    if isinstance(cached, dict):
        return cached

    result: Dict[str, Any] = {"checked": True, "mx": False, "accepts_mail": None}
    if not DNSPYTHON_AVAILABLE:
        return result

    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=4)
        result["mx"] = bool(answers)
        result["accepts_mail"] = True
    except Exception:
        try:
            answers = dns.resolver.resolve(domain, "A", lifetime=4)
            result["mx"] = False
            result["accepts_mail"] = bool(answers)
        except Exception:
            result["accepts_mail"] = False

    _cache_set(cache_key, result, MX_CACHE_TTL)
    return result


# ---------------------------------------------------------------------------
# HTTP + search providers
# ---------------------------------------------------------------------------

def _is_public_http_url(url: str) -> bool:
    """SSRF guard: only allow public http(s) hosts on standard ports."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        if parsed.port and parsed.port not in (80, 443):
            return False
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        if not infos:
            return False
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                return False
        return True
    except Exception:
        return False


def _request(method: str, url: str, **kwargs) -> Optional[requests.Response]:
    kwargs.setdefault("headers", HTTP_HEADERS)
    kwargs.setdefault("timeout", HTTP_TIMEOUT)
    try:
        response = requests.request(method, url, **kwargs)
        if response.status_code >= 400:
            logger.debug("HTTP %s for %s", response.status_code, url)
            return None
        return response
    except requests.RequestException as exc:
        logger.debug("Request failed for %s: %s", url, exc)
        return None


def _fetch_page_text(url: str) -> str:
    """Fetch a public page and return visible text. Never follows into private hosts."""
    if not _is_public_http_url(url):
        return ""
    if any(host in url.lower() for host in DATA_BROKER_HOSTS):
        return ""
    response = _request("GET", url, stream=True, timeout=PAGE_TIMEOUT, allow_redirects=True)
    if response is None:
        return ""
    if response.url and not _is_public_http_url(response.url):
        return ""
    content_type = (response.headers.get("Content-Type") or "").lower()
    if content_type and not any(t in content_type for t in ("text/html", "text/plain", "application/xhtml")):
        return ""

    chunks: List[bytes] = []
    total = 0
    try:
        for chunk in response.iter_content(chunk_size=32_768):
            if not chunk:
                continue
            chunks.append(chunk)
            total += len(chunk)
            if total >= MAX_PAGE_BYTES:
                break
    except requests.RequestException:
        return ""
    finally:
        response.close()

    raw = b"".join(chunks)
    encoding = response.encoding or "utf-8"
    try:
        body = raw.decode(encoding, errors="ignore")
    except (LookupError, TypeError):
        body = raw.decode("utf-8", errors="ignore")

    if lxml_html is not None:
        try:
            tree = lxml_html.fromstring(body)
            for bad in tree.xpath("//script|//style|//noscript|//svg"):
                bad.getparent().remove(bad)
            return " ".join(tree.text_content().split())
        except Exception:
            pass
    body = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", body)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    return " ".join(re.sub(r"\s+", " ", body).split())


def _decode_bing_url(href: str) -> str:
    if not href:
        return ""
    if "bing.com/ck/a" in href:
        try:
            query = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
            encoded = (query.get("u") or [""])[0]
            if encoded.startswith("a1"):
                encoded = encoded[2:]
            padded = encoded + "=" * (-len(encoded) % 4)
            decoded = base64.urlsafe_b64decode(padded).decode("utf-8", "ignore")
            if decoded.startswith(("http://", "https://")):
                return decoded
        except Exception:
            pass
    return href


def _parse_bing(html_text: str, limit: int = 10) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    if lxml_html is not None:
        try:
            tree = lxml_html.fromstring(html_text)
            nodes = tree.xpath(
                '//li[contains(concat(" ", normalize-space(@class), " "), " b_algo ")]'
            )
            for node in nodes:
                anchors = node.xpath(".//h2//a")
                if not anchors:
                    continue
                href = _decode_bing_url(anchors[0].get("href") or "")
                title = " ".join(anchors[0].text_content().split())
                snippet = " ".join(node.text_content().split())
                if href:
                    results.append({"title": title, "url": href, "snippet": snippet[:1000]})
                if len(results) >= limit:
                    break
            return results
        except Exception:
            pass

    # Regex fallback
    for block in re.findall(r'(?is)<li class="b_algo".*?</li>', html_text):
        href_match = re.search(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"', block)
        title_match = re.search(r'<h2[^>]*>(.*?)</h2>', block, re.S)
        if not href_match:
            continue
        href = _decode_bing_url(href_match.group(1))
        title = re.sub(r"<[^>]+>", " ", title_match.group(1)) if title_match else ""
        snippet = re.sub(r"<[^>]+>", " ", block)
        if href:
            results.append(
                {
                    "title": " ".join(title.split()),
                    "url": href,
                    "snippet": " ".join(snippet.split())[:1000],
                }
            )
        if len(results) >= limit:
            break
    return results


def _search_bing(query: str, limit: int = 10) -> List[Dict[str, str]]:
    response = _request(
        "GET",
        "https://www.bing.com/search",
        params={"q": query, "count": str(limit), "first": "1", "FORM": "PERE", "setlang": "en"},
    )
    if response is None:
        return []
    return _parse_bing(response.text, limit=limit)


def _search_bing_rss(query: str, limit: int = 10) -> List[Dict[str, str]]:
    """Bing's RSS endpoint is far lighter than the HTML page and rarely challenged."""
    response = _request(
        "GET",
        "https://www.bing.com/search",
        params={"q": query, "format": "rss", "count": str(limit), "setlang": "en"},
        headers={**HTTP_HEADERS, "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8"},
    )
    if response is None:
        return []

    results: List[Dict[str, str]] = []
    try:
        root = ElementTree.fromstring(response.content)
    except ElementTree.ParseError:
        return results

    for item in root.iter("item"):
        title = " ".join((item.findtext("title") or "").split())
        url = (item.findtext("link") or "").strip()
        snippet = " ".join((item.findtext("description") or "").split())
        if not url or not url.startswith(("http://", "https://")):
            continue
        results.append({"title": title, "url": url, "snippet": snippet[:1000]})
        if len(results) >= limit:
            break
    return results


def _parse_jina_markdown(markdown: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Parse the markdown that Jina Reader produces for a Bing result page.

    Shape:
        ## [Result title](https://www.bing.com/ck/a?...)
        Snippet sentence...
    """
    results: List[Dict[str, str]] = []
    pattern = re.compile(r"^\s*(?:\d+\.\s*)?#{2,3}\s*\[(.+?)\]\((https?://[^\s)]+)\)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(markdown))
    for index, match in enumerate(matches):
        title = re.sub(r"\*\*|__", "", match.group(1)).strip()
        url = _decode_bing_url(match.group(2).strip())
        if not title or not url:
            continue
        if any(host in url.lower() for host in SEARCH_HOSTS) or "r.jina.ai" in url.lower():
            continue
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        snippet = markdown[match.end():block_end]
        snippet = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", snippet)
        snippet = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", snippet)
        snippet = " ".join(snippet.replace("*", "").split())[:1000]
        results.append({"title": title, "url": url, "snippet": snippet})
        if len(results) >= limit:
            break
    return results


def _search_jina_bing(query: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Fetch Bing results through the public Jina Reader proxy.

    Direct Bing HTML is unreliable from data-centre and proxy IP ranges, but the
    Reader proxy returns clean markdown. It is best-effort: if the proxy is rate
    limited or blocked we simply return no results.
    """
    if (os.getenv("RECRUITER_ENABLE_JINA_READER") or "1").strip().lower() in {"0", "false", "off", "no"}:
        return []

    proxy = (os.getenv("RECRUITER_SEARCH_PROXY") or "https://r.jina.ai/").rstrip("/") + "/"
    target = "https://www.bing.com/search?" + urllib.parse.urlencode(
        {
            "q": query,
            "count": str(max(limit, 10)),
            "first": "1",
            "FORM": "PERE",
            "setlang": "en",
        }
    )
    response = _request(
        "GET",
        proxy + target,
        headers={**HTTP_HEADERS, "Accept": "text/plain", "X-Return-Format": "markdown"},
        timeout=max(HTTP_TIMEOUT, 15),
    )
    if response is None:
        return []
    body = response.text or ""
    if not body or '"code":403' in body[:400] or body.lstrip().startswith('{"data":null'):
        return []
    return _parse_jina_markdown(body, limit=limit)


def _parse_searxng(html_text: str, limit: int = 10) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    if lxml_html is not None:
        try:
            tree = lxml_html.fromstring(html_text)
            for article in tree.xpath('//article[contains(@class,"result")]')[:limit]:
                anchors = article.xpath(".//h3//a") or article.xpath(".//a")
                if not anchors:
                    continue
                href = anchors[0].get("href") or ""
                title = " ".join(anchors[0].text_content().split())
                snippet = " ".join(article.text_content().split())
                if href:
                    results.append({"title": title, "url": href, "snippet": snippet[:1000]})
        except Exception:
            pass
    return results


def _search_searxng(query: str, limit: int = 10) -> List[Dict[str, str]]:
    base = (os.getenv("SEARXNG_URL") or "").rstrip("/")
    if not base:
        return []
    response = _request(
        "GET",
        f"{base}/search",
        params={"q": query, "format": "json", "language": "en"},
        headers={**HTTP_HEADERS, "Accept": "application/json,text/html;q=0.9"},
    )
    if response is None:
        return []
    try:
        payload = response.json()
        results = []
        for item in payload.get("results", [])[:limit]:
            if item.get("url"):
                results.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("content", "")[:1000],
                    }
                )
        if results:
            return results
    except ValueError:
        pass
    return _parse_searxng(response.text, limit=limit)


def _search_serper(query: str, limit: int = 10) -> List[Dict[str, str]]:
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return []
    response = _request(
        "POST",
        "https://google.serper.dev/search",
        headers={**HTTP_HEADERS, "X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": limit},
    )
    if response is None:
        return []
    try:
        payload = response.json()
    except ValueError:
        return []
    results = []
    for item in payload.get("organic", [])[:limit]:
        if item.get("link"):
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")[:1000],
                }
            )
    return results


def _search_brave(query: str, limit: int = 10) -> List[Dict[str, str]]:
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    if not api_key:
        return []
    response = _request(
        "GET",
        "https://api.search.brave.com/res/v1/web/search",
        headers={**HTTP_HEADERS, "X-Subscription-Token": api_key, "Accept": "application/json"},
        params={"q": query, "count": min(limit, 20)},
    )
    if response is None:
        return []
    try:
        payload = response.json()
    except ValueError:
        return []
    results = []
    for item in (payload.get("web", {}) or {}).get("results", [])[:limit]:
        if item.get("url"):
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("description", "")[:1000],
                }
            )
    return results


def search_web(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search the public web through the best available provider.

    Order:
      1. Serper        (SERPER_API_KEY)
      2. Brave API     (BRAVE_SEARCH_API_KEY)
      3. SearXNG       (SEARXNG_URL)
      4. Bing via Jina Reader proxy (no key required, best-effort)
      5. Bing RSS      (no key required)
      6. Bing HTML     (no key required, last resort)

    Results are cached so a page render never repeats the same upstream calls.
    """
    cache_key = f"recruiter:search:{_hash(query)}:{limit}"
    cached = _cache_get(cache_key)
    if isinstance(cached, dict):
        return cached

    errors: List[str] = []
    results: List[Dict[str, str]] = []
    provider = ""

    for name, fn in (
        ("serper", _search_serper),
        ("brave", _search_brave),
        ("searxng", _search_searxng),
        ("jina_bing", _search_jina_bing),
        ("bing_rss", _search_bing_rss),
        ("bing_html", _search_bing),
    ):
        try:
            results = fn(query, limit=limit)
        except Exception as exc:  # defensive: one provider must not break discovery
            errors.append(f"{name}: {exc}")
            results = []
        if results:
            provider = name
            break

    payload = {
        "provider": provider,
        "results": results,
        "errors": errors,
        "configured": bool(
            os.getenv("SERPER_API_KEY") or os.getenv("BRAVE_SEARCH_API_KEY") or os.getenv("SEARXNG_URL")
        ),
    }
    _cache_set(cache_key, payload, SEARCH_CACHE_TTL)
    return payload


# ---------------------------------------------------------------------------
# Email extraction
# ---------------------------------------------------------------------------

def _clean_evidence(text: str, start: int, end: int, window: int = 90) -> str:
    return " ".join(text[max(0, start - window): min(len(text), end + window)].split())


def extract_email_candidates(
    text: str,
    *,
    name: str = "",
    company_domain: str = "",
    company_name: str = "",
    source: str = "web",
    source_url: str = "",
    page_title: str = "",
    require_person: bool = False,
) -> List[EmailCandidate]:
    """
    Extract real email addresses from a piece of public text.

    If require_person is True, an address outside the company domain is only accepted
    when the person's full name (or last name) appears near it or in the page title.
    """
    if not text:
        return []

    found: List[EmailCandidate] = []
    seen = set()
    person_strength = _person_match_strength(f"{page_title} {text[:4000]}", name)

    for match in EMAIL_RE.finditer(text):
        email = normalize_email(match.group(1))
        if email in seen:
            continue
        seen.add(email)
        if not is_valid_email_syntax(email):
            continue

        local, domain = email.rsplit("@", 1)
        if domain in BLOCKED_EMAIL_DOMAINS or any(
            domain.endswith("." + blocked) for blocked in BLOCKED_EMAIL_DOMAINS
        ):
            continue
        if local in NON_DELIVERABLE_LOCAL_PARTS or local.startswith(("noreply", "no-reply", "donotreply")):
            continue
        if len(local) > 40 or re.fullmatch(r"[0-9a-f]{16,}", local):
            continue
        if local.startswith("u003") or local.startswith("&#"):
            continue
        # Drop asset filenames that look like emails (e.g. logo@2x.png)
        if domain.rsplit(".", 1)[-1] in BLOCKED_TLDS:
            continue

        evidence = _clean_evidence(text, match.start(), match.end())
        on_company_domain = _domain_matches(email, company_domain)
        nearby_strength = _person_match_strength(evidence, name) if name else 0
        page_strength = max(person_strength, nearby_strength)
        mentions_company = _company_mentioned(
            f"{page_title} {text[:6000]}", company_name, company_domain
        )

        if require_person and not on_company_domain and page_strength == 0:
            continue
        if not on_company_domain and not is_role_inbox(email) and page_strength == 0 and name:
            # Avoid collecting random third-party addresses from listicles.
            continue

        role = is_role_inbox(email)
        if role:
            label = "Company recruiting inbox"
            confidence = "team"
        elif on_company_domain and page_strength >= 1:
            label = "Public work email"
            confidence = "high"
        elif on_company_domain:
            label = "Public company email"
            confidence = "medium"
        elif page_strength >= 2:
            label = "Public personal email"
            confidence = "high"
        else:
            label = "Public email"
            confidence = "medium"

        found.append(
            EmailCandidate(
                email=email,
                label=label,
                confidence=confidence,
                source=source,
                source_url=source_url,
                evidence=evidence[:320],
                is_personal=not role,
                company_linked=bool(on_company_domain or mentions_company),
            )
        )

    return found


def _collect_from_results(
    results: Sequence[Dict[str, str]],
    *,
    name: str,
    company_domain: str,
    company_name: str = "",
    source: str = "web",
) -> List[EmailCandidate]:
    candidates: List[EmailCandidate] = []
    for item in results:
        url = (item.get("url") or "").lower()
        if any(host in url for host in DATA_BROKER_HOSTS):
            continue
        candidates.extend(
            extract_email_candidates(
                f"{item.get('title', '')} {item.get('snippet', '')}",
                name=name,
                company_domain=company_domain,
                company_name=company_name,
                source=source,
                source_url=item.get("url", ""),
                page_title=item.get("title", ""),
                require_person=False,
            )
        )
    return candidates


def _rank_page_result(item: Dict[str, str], name: str, company_domain: str) -> int:
    url = (item.get("url") or "").lower()
    text = f"{item.get('title', '')} {item.get('snippet', '')}"
    score = 0
    if company_domain and company_domain.lower() in url:
        score += 6
    strength = _person_match_strength(text, name)
    score += strength * 3
    if any(term in url for term in ("contact", "about", "team", "career", "resume", "cv", "profile")):
        score += 2
    if any(term in url for term in ("github.com", "gitlab.com", "medium.com", "dev.to")):
        score += 1
    if any(host in url for host in SOCIAL_HOSTS) or any(host in url for host in SEARCH_HOSTS):
        score -= 8
    if any(host in url for host in DATA_BROKER_HOSTS):
        score -= 15
    return score


# ---------------------------------------------------------------------------
# GitHub provider
# ---------------------------------------------------------------------------

def _github_headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "KashiiUpdatez-RecruiterFinder/2.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token.strip()}"
    return headers


def _github_get(path: str, params: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    response = _request(
        "GET",
        f"https://api.github.com{path}",
        headers=_github_headers(),
        params=params or {},
        timeout=8,
    )
    if response is None:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def _github_commit_lookup(name: str, company_domain: str) -> Tuple[List[EmailCandidate], List[str]]:
    candidates: List[EmailCandidate] = []
    errors: List[str] = []
    if not name:
        return candidates, errors

    payload = _github_get(
        "/search/commits",
        {"q": f'author-name:"{name}"', "per_page": "20", "sort": "author-date"},
    )
    if not payload:
        errors.append("github_commits: no response")
        return candidates, errors
    if payload.get("message"):
        errors.append(f"github_commits: {payload.get('message')}")
        return candidates, errors

    for item in payload.get("items", []):
        author = ((item.get("commit") or {}).get("author") or {})
        author_name = author.get("name") or ""
        email = normalize_email(author.get("email") or "")
        if not email or not is_valid_email_syntax(email):
            continue
        if email.endswith("users.noreply.github.com") or email.endswith("noreply.github.com"):
            continue
        if _norm_name(author_name) != _norm_name(name):
            continue
        on_company = _domain_matches(email, company_domain)
        repo_path = urllib.parse.urlparse(item.get("html_url", "")).path.strip("/")
        repo_owner = repo_path.split("/")[0] if repo_path else ""
        owner_core = re.sub(r"[^a-z0-9]", "", repo_owner.lower())
        org_core = _domain_core(company_domain)
        repo_linked = bool(
            owner_core
            and org_core
            and len(owner_core) >= 4
            and len(org_core) >= 4
            and (owner_core in org_core or org_core.startswith(owner_core))
        )
        candidates.append(
            EmailCandidate(
                email=email,
                label="Public commit email" if not on_company else "Public work email",
                confidence="high" if on_company else "medium",
                source="github_commit",
                source_url=item.get("html_url", ""),
                evidence=f"GitHub commit authored by {author_name}",
                is_personal=True,
                company_linked=bool(on_company or repo_linked),
                score=20 + (15 if on_company else 0),
            )
        )

    return candidates, errors


def _github_profile_lookup(name: str, company: str, company_domain: str) -> Tuple[List[EmailCandidate], List[str]]:
    candidates: List[EmailCandidate] = []
    errors: List[str] = []
    tokens = _name_tokens(name)
    if not tokens:
        return candidates, errors

    payload = _github_get(
        "/search/users",
        {"q": f"{name} in:fullname", "per_page": "5"},
    )
    if not payload:
        errors.append("github_users: no response")
        return candidates, errors
    if payload.get("message"):
        errors.append(f"github_users: {payload.get('message')}")
        return candidates, errors

    for user in payload.get("items", [])[:4]:
        login = user.get("login")
        if not login:
            continue
        profile = _github_get(f"/users/{login}")
        if not profile:
            continue
        profile_name = profile.get("name") or ""
        if _norm_name(profile_name) != _norm_name(name):
            continue
        email = normalize_email(profile.get("email") or "")
        if not email or not is_valid_email_syntax(email):
            continue
        if email.endswith("users.noreply.github.com") or email.endswith("noreply.github.com"):
            continue
        on_company = _domain_matches(email, company_domain)
        company_field = (profile.get("company") or "").lower()
        company_match = bool(company and _norm_name(company) and _norm_name(company) in _norm_name(company_field))
        bio_text = " ".join(
            str(profile.get(field) or "")
            for field in ("company", "bio", "blog", "name", "location")
        )
        profile_linked = company_match or _company_mentioned(bio_text, company, company_domain)
        candidates.append(
            EmailCandidate(
                email=email,
                label="GitHub profile email",
                confidence="high" if (on_company or profile_linked) else "medium",
                source="github_profile",
                source_url=profile.get("html_url", user.get("html_url", "")),
                evidence=f"Public GitHub profile for {profile_name}",
                is_personal=True,
                company_linked=bool(on_company or profile_linked),
                score=18 + (15 if (on_company or profile_linked) else 0),
            )
        )

    return candidates, errors


# ---------------------------------------------------------------------------
# Company site provider
# ---------------------------------------------------------------------------

def _company_site_lookup(company_domain: str, name: str = "") -> Tuple[List[EmailCandidate], List[str]]:
    candidates: List[EmailCandidate] = []
    errors: List[str] = []
    if not company_domain:
        return candidates, errors

    paths = ["/careers", "/contact", "/about", "/careers/contact", ""]
    seen_urls = set()
    for path in paths:
        url = f"https://{company_domain}{path}"
        if url in seen_urls:
            continue
        seen_urls.add(url)
        text = _fetch_page_text(url)
        if not text:
            continue
        candidates.extend(
            extract_email_candidates(
                text,
                name=name,
                company_domain=company_domain,
                source="company_site",
                source_url=url,
                page_title=f"{company_domain} careers/contact",
                require_person=False,
            )
        )
        if len(candidates) >= 8:
            break
    return candidates, errors


# ---------------------------------------------------------------------------
# Scoring / validation
# ---------------------------------------------------------------------------

def _finalise_candidates(candidates: Iterable[EmailCandidate], company_domain: str) -> List[EmailCandidate]:
    by_email: Dict[str, EmailCandidate] = {}

    for candidate in candidates:
        email = normalize_email(candidate.email)
        if not email or not is_valid_email_syntax(email):
            continue
        candidate.email = email
        existing = by_email.get(email)
        if existing is None:
            by_email[email] = candidate
            continue
        # Keep the stronger evidence/source, merge score.
        existing.score += max(4, candidate.score // 3)
        existing.company_linked = bool(existing.company_linked or candidate.company_linked)
        if candidate.score > existing.score:
            candidate.score = existing.score
            candidate.company_linked = bool(candidate.company_linked or existing.company_linked)
            by_email[email] = candidate

    finalised: List[EmailCandidate] = []
    for candidate in by_email.values():
        domain = email_domain(candidate.email)
        mx = check_domain_mx(domain)
        candidate.mx_valid = mx.get("accepts_mail")
        if candidate.mx_valid is False:
            # The domain rejects mail (no MX and no A record). Do not present it.
            continue

        if candidate.source == "job_post":
            candidate.score += 60
        if _domain_matches(candidate.email, company_domain):
            candidate.score += 40
        if candidate.is_personal:
            candidate.score += 12
        else:
            candidate.score -= 10
        if candidate.source in ("github_commit", "github_profile"):
            candidate.score += 10
        if candidate.mx_valid:
            candidate.score += 8
        if candidate.confidence == "high":
            candidate.score += 10

        finalised.append(candidate)

    finalised.sort(key=lambda c: (c.is_personal, c.score, c.confidence == "high"), reverse=True)
    return finalised


# ---------------------------------------------------------------------------
# Job posting extraction
# ---------------------------------------------------------------------------

def extract_job_contact_emails(job) -> List[EmailCandidate]:
    if job is None:
        return []
    corpus = " ".join(
        part for part in (
            getattr(job, "description", "") or "",
            getattr(job, "eligibility", "") or "",
            getattr(job, "referral_instructions", "") or "",
            getattr(job, "selection_process", "") or "",
        )
        if part
    )
    company_domain = resolve_company_domain(getattr(job, "company_name", "") or "")
    candidates = extract_email_candidates(
        corpus,
        name=getattr(job, "referrer_name", "") or "",
        company_domain=company_domain,
        company_name=getattr(job, "company_name", "") or "",
        source="job_post",
        source_url=getattr(job, "apply_url", "") or "",
        page_title=getattr(job, "title", "") or "",
        require_person=False,
    )
    # Anything the employer themselves published in the post is linked by definition.
    for candidate in candidates:
        candidate.company_linked = True
    return candidates


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def discover_recruiter_contact(
    name: str = "",
    company: str = "",
    linkedin_url: str = "",
    job=None,
    deep_search: bool = True,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    Discover publicly-published contact details for one recruiter.

    This function never fabricates an address. If nothing is found, it returns
    status="not_found" with a clear explanation and sourcing links.
    """
    parsed = parse_linkedin_profile_url(linkedin_url) if linkedin_url else None
    person_name = (name or (parsed or {}).get("full_name") or "").strip()
    person_name = re.sub(r"\s+", " ", person_name)
    company_name = (company or getattr(job, "company_name", "") or "").strip()
    clean_company = clean_company_name_for_search(company_name) or company_name
    company_domain = resolve_company_domain(company_name)
    if deep_search:
        company_domain = _refine_company_domain(company_name, company_domain)

    links = build_sourcing_links(person_name, company_name, linkedin_url)
    base_result: Dict[str, Any] = {
        "query": {
            "name": person_name,
            "company": clean_company,
            "domain": company_domain,
            "linkedin_url": linkedin_url,
        },
        "recruiter": {
            "name": person_name,
            "title": "Recruiter / hiring contact" if person_name else "",
            "linkedin_url": linkedin_url,
            "company": clean_company,
        },
        "company": {
            "name": company_name,
            "clean_name": clean_company,
            "domain": company_domain,
        },
        "emails": [],
        "best_email": None,
        "has_personal_email": False,
        "status": "invalid_input",
        "message": "Add a recruiter name or paste their public LinkedIn profile URL.",
        "sourcing_links": links,
        "checked_sources": [],
        "errors": [],
        "searched_at": _now_iso(),
        "from_cache": False,
        "notice": (
            "Only publicly published contact details are shown. "
            "Kashii Updatez never guesses or pattern-generates email addresses."
        ),
    }

    if not person_name and not company_domain:
        return base_result

    cache_key = f"recruiter:discover:{_hash(person_name, clean_company, linkedin_url, str(deep_search))}"
    if not deep_search or force_refresh:
        cached = None
    else:
        cached = _cache_get(cache_key)
    if isinstance(cached, dict):
        cached = dict(cached)
        cached["from_cache"] = True
        return cached

    candidates: List[EmailCandidate] = []
    errors: List[str] = []
    checked: List[str] = []

    # 1. Job posting metadata (fast, local, highest confidence).
    if job is not None:
        checked.append("job_post")
        try:
            candidates.extend(extract_job_contact_emails(job))
        except Exception as exc:
            errors.append(f"job_post: {exc}")

    # 2. GitHub public profile + commit metadata.
    if person_name:
        checked.append("github")
        try:
            gh_commits, gh_errors = _github_commit_lookup(person_name, company_domain)
            candidates.extend(gh_commits)
            errors.extend(gh_errors)
            gh_profile, gh_errors = _github_profile_lookup(person_name, clean_company, company_domain)
            candidates.extend(gh_profile)
            errors.extend(gh_errors)
        except Exception as exc:
            errors.append(f"github: {exc}")

    # 3. Public web search + a few fetched pages.
    if person_name:
        checked.append("web_search")
        try:
            queries = [
                f'"{person_name}" "{clean_company}" (email OR contact) -site:linkedin.com',
                f'"{person_name}" "{company_domain}"',
            ]
            if person_name:
                queries.append(f'"{person_name}" recruiter "{clean_company}"')
            web_results: List[Dict[str, str]] = []
            for query in queries[:2]:
                payload = search_web(query, limit=10)
                web_results.extend(payload.get("results", []))
                errors.extend(payload.get("errors", []))

            # Deduplicate results by URL.
            unique_results: List[Dict[str, str]] = []
            seen_urls = set()
            for item in web_results:
                url = item.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                unique_results.append(item)

            candidates.extend(
                _collect_from_results(
                    unique_results,
                    name=person_name,
                    company_domain=company_domain,
                    company_name=company_name,
                    source="web",
                )
            )

            # Fetch the most promising public pages (never social/search hosts).
            ranked = sorted(
                unique_results,
                key=lambda item: _rank_page_result(item, person_name, company_domain),
                reverse=True,
            )
            fetched = 0
            for item in ranked:
                if fetched >= MAX_FETCHED_PAGES:
                    break
                url = item.get("url", "")
                lower = url.lower()
                if any(host in lower for host in SOCIAL_HOSTS) or any(host in lower for host in SEARCH_HOSTS):
                    continue
                if any(host in lower for host in DATA_BROKER_HOSTS):
                    continue
                # Only spend a page fetch when the result is clearly about this
                # person (full name) or sits on the employer's own domain.
                if _rank_page_result(item, person_name, company_domain) < 6:
                    continue
                text = _fetch_page_text(url)
                if not text:
                    continue
                fetched += 1
                candidates.extend(
                    extract_email_candidates(
                        text,
                        name=person_name,
                        company_domain=company_domain,
                        company_name=company_name,
                        source="web",
                        source_url=url,
                        page_title=item.get("title", ""),
                        require_person=True,
                    )
                )
        except Exception as exc:
            errors.append(f"web_search: {exc}")

    # 4. Employer site fallback (role inboxes only in practice).
    if deep_search and company_domain and not any(c.is_personal for c in candidates):
        checked.append("company_site")
        try:
            site_candidates, site_errors = _company_site_lookup(company_domain, person_name)
            candidates.extend(site_candidates)
            errors.extend(site_errors)
        except Exception as exc:
            errors.append(f"company_site: {exc}")

    finalised = _finalise_candidates(candidates, company_domain)
    linkage_required = bool(company_domain or company_name)
    if linkage_required:
        ignored_namesakes = sum(1 for c in finalised if not c.company_linked)
        finalised = [c for c in finalised if c.company_linked]
    else:
        ignored_namesakes = 0

    personal = [c for c in finalised if c.is_personal]
    team = [c for c in finalised if not c.is_personal]

    # Prefer personal contacts; keep the best 2 team inboxes as fallback.
    chosen = personal[:6] + team[:2]

    status = "not_found"
    message = (
        f"No publicly published email was found for {person_name or clean_company}. "
        "We will not invent one. Use the LinkedIn X-Ray search or Gmail search links below."
    )
    if personal:
        status = "found"
        message = (
            f"Found {len(personal)} public email "
            f"{'address' if len(personal) == 1 else 'addresses'} connected to "
            f"{person_name}. Review the source before sending."
        )
    elif team:
        status = "team_only"
        message = (
            f"No individual email is public for {person_name or clean_company}. "
            "The employer's recruiting inbox is shown instead; it is a real address, not a guess."
        )

    if ignored_namesakes:
        message += (
            f" {ignored_namesakes} other "
            f"{'address was' if ignored_namesakes == 1 else 'addresses were'} "
            f"hidden because {'it' if ignored_namesakes == 1 else 'they'} could not be "
            f"linked to {clean_company or 'this employer'}."
        )

    result = {
        **base_result,
        "recruiter": {
            "name": person_name,
            "title": "Recruiter / hiring contact" if person_name else "",
            "linkedin_url": linkedin_url,
            "company": clean_company,
        },
        "emails": [c.to_dict() for c in chosen],
        "best_email": chosen[0].to_dict() if chosen else None,
        "has_personal_email": bool(personal),
        "status": status,
        "message": message,
        "checked_sources": checked,
        "errors": errors[:8],
        "ignored_namesakes": ignored_namesakes,
        "searched_at": _now_iso(),
    }

    if deep_search:
        _cache_set(cache_key, result, DISCOVERY_CACHE_TTL)
    return result


def scrape_original_recruiter_email_from_linkedin(
    linkedin_url: str,
    company_name: str,
    name: str = "",
) -> Dict[str, Any]:
    """
    Backwards-compatible wrapper. Resolves a public profile URL to a *found* email only.
    The old version generated first.last@company.com patterns; that behaviour is removed.
    """
    result = discover_recruiter_contact(
        name=name,
        company=company_name,
        linkedin_url=linkedin_url,
        deep_search=True,
    )
    best = result.get("best_email") or {}
    return {
        "name": (result.get("recruiter") or {}).get("name", ""),
        "title": (result.get("recruiter") or {}).get("title", "Recruiter / hiring contact"),
        "email": best.get("email", ""),
        "company": (result.get("company") or {}).get("clean_name", company_name),
        "domain": (result.get("company") or {}).get("domain", ""),
        "status": (
            "Verified public email" if best.get("confidence") == "high" else
            "Public email found" if best.get("email") else
            "No public email found"
        ),
        "verified": bool(best.get("email")) and best.get("confidence") == "high",
        "linkedin_url": linkedin_url,
        "source_url": best.get("source_url", ""),
        "candidates": result.get("emails", []),
        "message": result.get("message", ""),
        "searched_at": result.get("searched_at", _now_iso()),
    }


def get_recruiter_intelligence_for_job(job) -> Dict[str, Any]:
    """
    Cheap, local intelligence bundle for job detail pages. No network calls.

    Returns contact details only when they literally appear in the job post or the
    referrer metadata. Discovery is user-triggered on the recruiter page.
    """
    company_name = getattr(job, "company_name", "") or ""
    clean_company = clean_company_name_for_search(company_name)
    domain = resolve_company_domain(company_name)
    referrer_name = (getattr(job, "referrer_name", "") or "").strip()
    referrer_linkedin = (getattr(job, "referrer_linkedin", "") or "").strip()

    job_emails = extract_job_contact_emails(job)
    best = job_emails[0] if job_emails else None

    links = build_sourcing_links(referrer_name, company_name, referrer_linkedin)

    active_recruiter = {
        "name": referrer_name,
        "title": "Referrer / hiring contact" if referrer_name else "",
        "email": best.email if best else "",
        "company": clean_company,
        "verified": bool(best),
        "linkedin_url": referrer_linkedin,
        "source": best.source if best else "",
        "source_url": best.source_url if best else "",
        "label": best.label if best else "",
    }

    return {
        "company_name": company_name,
        "clean_company_name": clean_company,
        "domain": domain,
        "google_xray_url": links["google_xray_url"],
        "sourcing_links": links,
        "active_recruiter": active_recruiter,
        "job_contact_emails": [c.to_dict() for c in job_emails[:4]],
        "has_public_email": bool(best),
        "message": (
            "Email found in the job post."
            if best
            else "No email is published in this job post. Run a source-linked search on the recruiter page."
        ),
    }
