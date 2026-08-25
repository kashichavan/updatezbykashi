import hashlib
import re
from django.utils import timezone


class VisitorAnalyticsMiddleware:
    """
    Zero-dependency, high-performance visitor analytics middleware.
    Tracks real-time website visits, unique daily visitors, referrers,
    device distribution, and top pages directly into the database.
    """

    EXCLUDED_PREFIXES = (
        '/static/',
        '/media/',
        '/favicon.ico',
        '/robots.txt',
        '/ads.txt',
        '/sitemap.xml',
        '/api/ping',
        '/api/stats',
        '/api/owner/analytics',
        '/admin/',
    )

    BOT_KEYWORDS = (
        'bot', 'crawl', 'spider', 'slurp', 'mediapartners', 'uptime',
        'pingdom', 'headless', 'python-requests', 'curl', 'wget', 'bytespider'
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only track GET HTML / public page responses
        path = request.path
        if request.method == 'GET' and response.status_code == 200:
            if not any(path.startswith(prefix) for prefix in self.EXCLUDED_PREFIXES):
                # Don't track logged-in staff/admin traffic to keep student data clean
                if not (request.user.is_authenticated and request.user.is_staff and path.startswith('/owner')):
                    try:
                        self.log_visit(request, path)
                    except Exception as err:
                        pass

        return response

    def log_visit(self, request, path):
        from .models import SiteVisit

        user_agent = request.META.get('HTTP_USER_AGENT', '')[:490]
        ua_lower = user_agent.lower()

        # Check if bot
        is_bot = any(bot in ua_lower for bot in self.BOT_KEYWORDS)

        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')

        # Anonymized unique visitor hash (SHA-256)
        raw_hash = f"{ip}:{user_agent}:{timezone.now().strftime('%Y-%m-%d')}"
        visitor_hash = hashlib.sha256(raw_hash.encode('utf-8')).hexdigest()

        # Mask IP (e.g. 192.168.1.xxx)
        ip_parts = ip.split('.')
        masked_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.xxx" if len(ip_parts) == 4 else ip[:16]

        # Referrer Classification
        referer_raw = request.META.get('HTTP_REFERER', '')[:490]
        ref_lower = referer_raw.lower()
        referrer = "Direct"

        if 'instagram.com' in ref_lower or 'instagram' in ua_lower:
            referrer = "Instagram"
        elif 'whatsapp' in ref_lower or 'wa.me' in ref_lower:
            referrer = "WhatsApp"
        elif 't.me' in ref_lower or 'telegram' in ref_lower:
            referrer = "Telegram"
        elif 'google.com' in ref_lower or 'google' in ref_lower:
            referrer = "Google Search"
        elif 'linkedin.com' in ref_lower:
            referrer = "LinkedIn"
        elif 'youtube.com' in ref_lower:
            referrer = "YouTube"
        elif 'twitter.com' in ref_lower or 'x.com' in ref_lower:
            referrer = "Twitter / X"
        elif referer_raw and not any(h in ref_lower for h in ['kashiiupdatez', 'updatezbykashi', 'localhost', '127.0.0.1']):
            referrer = "Other Websites"

        # Device Classification
        device_type = "Desktop"
        if any(m in ua_lower for m in ['mobile', 'android', 'iphone', 'ipod', 'webos', 'blackberry', 'iemobile', 'opera mini']):
            device_type = "Mobile"
        elif 'ipad' in ua_lower or 'tablet' in ua_lower:
            device_type = "Tablet"

        # Browser Classification
        browser = "Other"
        if 'instagram' in ua_lower:
            browser = "Instagram Webview"
        elif 'chrome' in ua_lower and 'edg' not in ua_lower and 'opr' not in ua_lower:
            browser = "Chrome"
        elif 'safari' in ua_lower and 'chrome' not in ua_lower:
            browser = "Safari"
        elif 'firefox' in ua_lower:
            browser = "Firefox"
        elif 'edg' in ua_lower:
            browser = "Edge"
        elif 'opera' in ua_lower or 'opr' in ua_lower:
            browser = "Opera"

        # OS Classification
        os_type = "Other"
        if 'android' in ua_lower:
            os_type = "Android"
        elif 'iphone' in ua_lower or 'ipad' in ua_lower or 'ios' in ua_lower:
            os_type = "iOS"
        elif 'windows' in ua_lower:
            os_type = "Windows"
        elif 'mac' in ua_lower or 'macintosh' in ua_lower:
            os_type = "macOS"
        elif 'linux' in ua_lower:
            os_type = "Linux"

        # Page Type / Title extraction
        page_title = "Website Page"
        if path == '/':
            page_title = "Homepage (Fresh Job Feeds)"
        elif path.startswith('/job/') or '/job/' in path:
            page_title = "Job Requirement Detail"
        elif path.startswith('/group/') or path.startswith('/groups/'):
            page_title = "Multi-Job Hiring Drive Group"
        elif path.startswith('/category/'):
            page_title = "Category Explorer"
        elif path.startswith('/debugger'):
            page_title = "Live Code Execution Debugger"
        elif path.startswith('/learn'):
            page_title = "Learning Academy"
        elif path.startswith('/guides') or path.startswith('/tutorials'):
            page_title = "Study Guides & Prep"
        elif path.startswith('/blog'):
            page_title = "Technical Blog"

        SiteVisit.objects.create(
            visitor_hash=visitor_hash,
            path=path[:500],
            page_title=page_title,
            referrer=referrer,
            referrer_raw=referer_raw,
            device_type=device_type,
            browser=browser,
            os=os_type,
            user_agent=user_agent,
            ip_address_masked=masked_ip,
            is_bot=is_bot,
        )
