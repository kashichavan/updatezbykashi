import hashlib
import time
import re
from django.utils import timezone
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse


class RateLimitMiddleware:
    """
    Enterprise-grade sliding-window rate limiting middleware.
    Protects authentication against brute-force attacks, limits API abuse,
    and defends public feeds against scrapers and DDoS.
    """

    EXEMPT_PREFIXES = (
        '/static/',
        '/media/',
        '/favicon.ico',
        '/robots.txt',
        '/ads.txt',
        '/sitemap.xml',
        '/instagram/webhook',
        '/meta/webhook',
    )

    # (Pattern matcher, max_requests, window_seconds, rule_id)
    RATE_RULES = [
        # 1. Login & Auth endpoints: 10 requests per 60s
        ({'prefix': '/api/admin/login', 'methods': ['POST']}, 10, 60, 'auth_login'),
        ({'prefix': '/owner', 'methods': ['POST']}, 10, 60, 'owner_login'),

        # 2. Critical Action APIs: 40 requests per 60s
        ({'prefix': '/api/owner/', 'methods': ['POST', 'PUT', 'DELETE']}, 40, 60, 'owner_actions'),

        # 3. Public API queries (Student feed & search): 120 requests per 60s
        ({'prefix': '/api/', 'methods': None}, 120, 60, 'public_api'),

        # 4. General HTML Web Browsing: 300 requests per 60s
        ({'prefix': '/', 'methods': None}, 300, 60, 'general_web'),
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    def get_rule_for_request(self, request):
        path = request.path
        method = request.method

        for matcher, max_reqs, window_sec, rule_id in self.RATE_RULES:
            if path.startswith(matcher['prefix']):
                if matcher['methods'] is None or method in matcher['methods']:
                    return max_reqs, window_sec, rule_id
        return None, None, None

    def __call__(self, request):
        path = request.path

        # 1. Skip static & webhook endpoints
        if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            return self.get_response(request)

        # 2. Check rule
        limit, window, rule_id = self.get_rule_for_request(request)

        if limit:
            client_ip = self.get_client_ip(request)
            cache_key = f"rl:{client_ip}:{rule_id}"
            current_time = int(time.time())

            # Get timestamp list from cache
            request_log = cache.get(cache_key, [])
            window_start = current_time - window

            # Filter out timestamps outside the sliding window
            request_log = [t for t in request_log if t > window_start]

            if len(request_log) >= limit:
                retry_after = window - (current_time - request_log[0]) if request_log else window
                retry_after = max(1, retry_after)

                is_json = path.startswith('/api/') or 'application/json' in request.headers.get('Accept', '').lower()
                if is_json:
                    resp = JsonResponse({
                        'error': 'Too Many Requests',
                        'message': f'Rate limit exceeded for {rule_id}. Please retry after {retry_after} seconds.',
                        'retry_after_seconds': retry_after,
                        'status': 429
                    }, status=429)
                else:
                    resp = HttpResponse(
                        f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>429 — Rate Limit Exceeded | Kashii Updatez</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #0f172a; display: grid; place-items: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
    .card {{ max-width: 440px; width: 100%; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 20px; padding: 32px; box-shadow: 0 10px 30px rgba(15,23,42,0.08); text-align: center; }}
    .badge {{ display: inline-block; padding: 4px 10px; background: #fef2f2; color: #dc2626; border-radius: 20px; font-size: 11px; font-weight: 800; margin-bottom: 14px; border: 1px solid #fecaca; }}
    h1 {{ font-size: 22px; font-weight: 800; margin: 0 0 8px; color: #0f172a; }}
    p {{ font-size: 13.5px; color: #64748b; line-height: 1.5; margin: 0 0 20px; }}
    .timer {{ font-family: monospace; font-size: 20px; font-weight: 800; color: #2563eb; background: #eff6ff; border: 1px solid #bfdbfe; padding: 10px; border-radius: 12px; margin-bottom: 20px; }}
  </style>
</head>
<body>
  <div class="card">
    <span class="badge">429 RATE LIMIT REACHED</span>
    <h1>Too Many Requests</h1>
    <p>You have reached the maximum allowed request rate. Please wait a few moments before trying again.</p>
    <div class="timer">Retry in {retry_after}s</div>
    <a href="/" style="display: inline-block; background: #2563eb; color: #fff; text-decoration: none; padding: 10px 20px; border-radius: 10px; font-size: 13px; font-weight: 700;">Return to Home</a>
  </div>
</body>
</html>""",
                        status=429,
                        content_type='text/html'
                    )

                resp['Retry-After'] = str(retry_after)
                resp['X-RateLimit-Limit'] = str(limit)
                resp['X-RateLimit-Remaining'] = '0'
                resp['X-RateLimit-Reset'] = str(retry_after)
                return resp

            # Record this request
            request_log.append(current_time)
            cache.set(cache_key, request_log, timeout=window + 10)

            response = self.get_response(request)
            response['X-RateLimit-Limit'] = str(limit)
            response['X-RateLimit-Remaining'] = str(max(0, limit - len(request_log)))
            return response

        return self.get_response(request)


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
