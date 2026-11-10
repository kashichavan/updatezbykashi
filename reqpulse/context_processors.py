"""Site-wide SEO / analytics IDs exposed to templates.

Every value comes from an environment variable and is validated against a
strict pattern, so a mistyped or malicious env value can never inject markup
into <head>. Unset or invalid = the tag is simply not rendered.
"""
import os
import re

_PATTERNS = {
    # GA4 measurement ID, e.g. G-AB12CD34EF
    "GA_MEASUREMENT_ID": re.compile(r"^G-[A-Z0-9]{4,16}$"),
    # Microsoft Clarity project ID, e.g. k3x9abcd12
    "CLARITY_PROJECT_ID": re.compile(r"^[a-z0-9]{6,16}$"),
    # Google Search Console HTML-tag verification token
    "GOOGLE_SITE_VERIFICATION": re.compile(r"^[A-Za-z0-9_\-]{20,100}$"),
    # Bing Webmaster Tools msvalidate.01 token
    "BING_SITE_VERIFICATION": re.compile(r"^[A-F0-9]{32}$"),
}


def _clean(name):
    value = os.environ.get(name, "").strip()
    if name == "BING_SITE_VERIFICATION":
        value = value.upper()
    return value if _PATTERNS[name].match(value) else ""


def seo_settings(request):
    return {name.lower(): _clean(name) for name in _PATTERNS}
