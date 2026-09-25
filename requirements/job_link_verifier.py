import re
import urllib.parse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from django.utils import timezone
from requirements.models import JobPosting

logger = logging.getLogger(__name__)

EXPIRED_PHRASES = [
    "job has expired",
    "job is no longer available",
    "position has been filled",
    "application has closed",
    "applications are now closed",
    "applications are closed",
    "posting has expired",
    "no longer accepting applications",
    "no longer accepting responses",
    "this opening is closed",
    "this requisition has been closed",
    "this job post is closed",
    "job not found",
    "page not found",
    "404 not found",
    "this listing is expired",
    "position is closed",
    "this form is no longer accepting responses",
    "the requested job could not be found",
    "job posting has been removed",
]

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
}


def check_single_job_url(url: str, timeout: int = 8) -> dict:
    """
    Checks if a job application URL is active, expired, closed, or redirected to a generic root homepage.
    Returns: {'is_active': bool, 'status_code': int, 'final_url': str, 'reason': str}
    """
    if not url or not url.startswith(('http://', 'https://')):
        return {'is_active': False, 'status_code': 0, 'final_url': url, 'reason': 'Invalid URL scheme'}

    try:
        parsed_orig = urllib.parse.urlparse(url)
        orig_path = parsed_orig.path.strip('/')

        session = requests.Session()
        resp = session.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
        final_url = resp.url
        parsed_final = urllib.parse.urlparse(final_url)
        final_path = parsed_final.path.strip('/')

        # 1. Check HTTP Status
        if resp.status_code in [404, 410]:
            return {'is_active': False, 'status_code': resp.status_code, 'final_url': final_url, 'reason': f'HTTP {resp.status_code} Not Found'}
        elif resp.status_code >= 500:
            return {'is_active': False, 'status_code': resp.status_code, 'final_url': final_url, 'reason': f'HTTP {resp.status_code} Server Error'}

        # 2. Check Homepage / Generic Portal Fallback Redirect
        # e.g. original was a specific job detail link (/jobs/12345), but got bounced back to root domain (/)
        if orig_path and len(orig_path.split('/')) >= 1:
            if not final_path or final_path in ['', 'home', 'index', 'index.html', 'careers', 'jobs', 'jobs/']:
                # If final is just root homepage and original had deep job slug
                if orig_path not in ['', 'home', 'index', 'index.html']:
                    return {
                        'is_active': False,
                        'status_code': resp.status_code,
                        'final_url': final_url,
                        'reason': 'Redirected to root homepage (Job opening deactivated)'
                    }

        # 3. Check HTML content for explicit expired/closed phrases
        html_sample = (resp.text[:50000] if resp.text else '').lower()

        # Check Google Forms specific response closed message
        if "docs.google.com/forms" in url and ("no longer accepting responses" in html_sample or "form closed" in html_sample):
            return {
                'is_active': False,
                'status_code': resp.status_code,
                'final_url': final_url,
                'reason': 'Google Form closed (No longer accepting responses)'
            }

        for phrase in EXPIRED_PHRASES:
            if phrase in html_sample:
                # Discard false positives if page also contains active application form buttons
                if "apply now" in html_sample or "submit application" in html_sample or "fill out the form" in html_sample:
                    if phrase not in ["job is no longer available", "position has been filled", "this requisition has been closed"]:
                        continue
                return {
                    'is_active': False,
                    'status_code': resp.status_code,
                    'final_url': final_url,
                    'reason': f'Page contains expired indicator: "{phrase}"'
                }

        return {'is_active': True, 'status_code': resp.status_code, 'final_url': final_url, 'reason': 'Active Link'}

    except requests.exceptions.Timeout:
        # Network timeout: do not immediately expire on single transient timeout
        return {'is_active': True, 'status_code': 408, 'final_url': url, 'reason': 'Connection timeout (Kept active)'}
    except requests.exceptions.SSLError:
        return {'is_active': False, 'status_code': 495, 'final_url': url, 'reason': 'SSL Certificate Error'}
    except requests.exceptions.ConnectionError:
        return {'is_active': False, 'status_code': 503, 'final_url': url, 'reason': 'Domain unresolvable / Connection refused'}
    except Exception as e:
        return {'is_active': True, 'status_code': 500, 'final_url': url, 'reason': f'Transient error: {str(e)}'}


def verify_active_job_links(limit: int = 50, auto_expire: bool = True) -> dict:
    """
    Checks active job postings and soft-expires any link that returns 404/expired/home redirect.
    """
    jobs_to_check = list(
        JobPosting.objects.filter(status='ACTIVE')
        .exclude(apply_url__isnull=True)
        .exclude(apply_url='')
        .order_by('updated_at')[:limit]
    )

    if not jobs_to_check:
        return {'checked': 0, 'expired': 0, 'active': 0, 'details': []}

    results = []
    expired_count = 0
    active_count = 0

    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_job = {
            executor.submit(check_single_job_url, job.apply_url): job
            for job in jobs_to_check
        }

        for future in as_completed(future_to_job):
            job = future_to_job[future]
            try:
                res = future.result()
                is_active = res.get('is_active', True)
                reason = res.get('reason', '')

                if not is_active:
                    expired_count += 1
                    if auto_expire:
                        job.status = 'EXPIRED'
                        job.save(update_fields=['status', 'updated_at'])
                        logger.info(f"🚫 [Link Health Guard] Marked Job #{job.id} '{job.title}' as EXPIRED: {reason}")
                else:
                    active_count += 1

                results.append({
                    'job_id': job.id,
                    'title': job.title,
                    'company': job.company_name,
                    'url': job.apply_url,
                    'is_active': is_active,
                    'reason': reason
                })
            except Exception as e:
                logger.error(f"Error checking job #{job.id}: {e}")

    return {
        'checked': len(jobs_to_check),
        'expired': expired_count,
        'active': active_count,
        'details': results
    }
