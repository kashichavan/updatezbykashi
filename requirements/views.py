import os
import json
import re
import urllib.request
import ssl
import hashlib
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.utils.text import slugify
from django.core.cache import cache
from django.db.models import Count, Q
from .models import Category, JobPosting, GuideArticle, ContactInquiry, JobGroup
from .jobdexo_service import auto_import_from_jobdexo

DEFAULT_YOUTUBE_VIDEOS = [
    {
        "video_id": "eJ1Jg6zLE5U",
        "title": "Python OOP Project: Build a Swiggy Clone with SQLite",
        "thumbnail_url": "https://img.youtube.com/vi/eJ1Jg6zLE5U/hqdefault.jpg",
        "watch_url": "https://www.youtube.com/watch?v=eJ1Jg6zLE5U"
    },
    {
        "video_id": "Sf-3x6uDYOg",
        "title": "Django Day 5 | MVT Architecture | Create Endpoints",
        "thumbnail_url": "https://img.youtube.com/vi/Sf-3x6uDYOg/hqdefault.jpg",
        "watch_url": "https://www.youtube.com/watch?v=Sf-3x6uDYOg"
    },
    {
        "video_id": "Ue5iDaQADfA",
        "title": "Python Sets Explained | Python Tutorial 2026 | pythonkashi",
        "thumbnail_url": "https://img.youtube.com/vi/Ue5iDaQADfA/hqdefault.jpg",
        "watch_url": "https://www.youtube.com/watch?v=Ue5iDaQADfA"
    },
    {
        "video_id": "AK87UIPioOQ",
        "title": "Master Python Tuples in One Video | pythonkashi",
        "thumbnail_url": "https://img.youtube.com/vi/AK87UIPioOQ/hqdefault.jpg",
        "watch_url": "https://www.youtube.com/watch?v=AK87UIPioOQ"
    },
    {
        "video_id": "TnWFxW5sJTo",
        "title": "Python Lists Explained | Create, Modify & Slicing",
        "thumbnail_url": "https://img.youtube.com/vi/TnWFxW5sJTo/hqdefault.jpg",
        "watch_url": "https://www.youtube.com/watch?v=TnWFxW5sJTo"
    },
    {
        "video_id": "-P4gExqsIuY",
        "title": "Python Data Types Explained | pythonkashi",
        "thumbnail_url": "https://img.youtube.com/vi/-P4gExqsIuY/hqdefault.jpg",
        "watch_url": "https://www.youtube.com/watch?v=-P4gExqsIuY"
    }
]

def is_authenticated_owner(request):
    if hasattr(request, 'user') and request.user and request.user.is_authenticated and request.user.is_staff:
        return True, request.user

    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            access = AccessToken(token)
            user_id = access.get('user_id')
            user = User.objects.filter(id=user_id, is_staff=True).first()
            if user:
                return True, user
        except Exception:
            pass

    return False, None

def get_cached_youtube_videos():
    cached = cache.get('youtube_videos_feed')
    if cached:
        return cached
    cache.set('youtube_videos_feed', DEFAULT_YOUTUBE_VIDEOS, 3600)
    return DEFAULT_YOUTUBE_VIDEOS

def sync_expired_jobs():
    """Automatically deletes postings older than 3 days (72 hours) so feed stays 100% fresh daily."""
    now = timezone.now()
    deleted_count, _ = JobPosting.objects.filter(deadline__lte=now).delete()
    if deleted_count > 0:
        cache.clear()

def api_ping(request):
    """Ultra-fast Keep-Alive Heartbeat endpoint for UptimeRobot auto pings."""
    return JsonResponse({
        'status': 'ok',
        'app': 'Kashii Updatez',
        'timestamp': timezone.now().isoformat()
    })

def ads_txt_verification_view(request):
    """Direct plain-text verification view for ad networks."""
    return HttpResponse("8f373caaa0ca1b604bcf", content_type="text/plain")

def ads_txt_view(request):
    """Standard Google AdSense Authorized Digital Sellers (ads.txt) file."""
    content = "google.com, pub-2115508498538506, DIRECT, f08c47fec0942fa0\n"
    return HttpResponse(content, content_type="text/plain")


def index_view(request):
    sync_expired_jobs()
    videos = get_cached_youtube_videos()
    initial_jobs = JobPosting.objects.filter(status='ACTIVE', deadline__gt=timezone.now()).select_related('category').order_by('-created_at')[:6]
    from blog.models import BlogPost
    recent_posts = BlogPost.objects.filter(is_published=True).select_related('category').order_by('-published_at')[:3]
    return render(request, 'content/home.html', {
        'youtube_videos': videos,
        'initial_jobs': initial_jobs,
        'recent_posts': recent_posts,
    })

def about_view(request):
    return render(request, 'content/about.html')

def privacy_policy_view(request):
    return render(request, 'content/privacy_policy.html')

def terms_view(request):
    return render(request, 'content/terms.html')

def disclaimer_view(request):
    return render(request, 'content/disclaimer.html')

def contact_view(request):
    success_message = None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', 'General Inquiry').strip()
        message = request.POST.get('message', '').strip()
        if name and email and message:
            ContactInquiry.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            success_message = "Thank you for reaching out! Your message has been received. We will respond within 24 hours."

    return render(request, 'content/contact.html', {'success_message': success_message})

def ensure_guides_seeded():
    """Guarantees production has all 13 high-value technical articles populated with PDF attachments."""
    if GuideArticle.objects.filter(status='PUBLISHED').count() >= 13:
        return
    try:
        from .seed_prod import guides_seeds
        for g in guides_seeds:
            GuideArticle.objects.update_or_create(slug=g['slug'], defaults=g)
    except Exception:
        pass

def guides_list_view(request):
    """Seamlessly redirects legacy /guides/ traffic to the new Tech Blog."""
    topic = request.GET.get('topic')
    if topic:
        return redirect(f'/blog/?search={topic}', permanent=False)
    return redirect('/blog/', permanent=False)

def guide_detail_view(request, slug):
    """Seamlessly redirects legacy /guides/<slug>/ traffic to the new Tech Blog."""
    return redirect(f'/blog/{slug}/', permanent=False)


def sitemap_xml_view(request):
    """Dynamic XML Sitemap for Search Engines & Google AdSense Crawlers."""
    host = request.build_absolute_uri('/')[:-1]
    now_str = timezone.now().strftime('%Y-%m-%d')
    
    # Static pages
    static_urls = [
        ('', 'daily', '1.0'),
        ('/guides/', 'daily', '0.9'),
        ('/about/', 'weekly', '0.8'),
        ('/youtube/', 'weekly', '0.8'),
        ('/debugger/', 'weekly', '0.8'),
        ('/privacy-policy/', 'monthly', '0.5'),
        ('/terms/', 'monthly', '0.5'),
        ('/disclaimer/', 'monthly', '0.5'),
        ('/contact/', 'monthly', '0.6'),
    ]

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for path, changefreq, priority in static_urls:
        xml_lines.append(f'  <url>')
        xml_lines.append(f'    <loc>{host}{path}</loc>')
        xml_lines.append(f'    <lastmod>{now_str}</lastmod>')
        xml_lines.append(f'    <changefreq>{changefreq}</changefreq>')
        xml_lines.append(f'    <priority>{priority}</priority>')
        xml_lines.append(f'  </url>')

    # Guide articles
    for guide in GuideArticle.objects.filter(status='PUBLISHED'):
        g_mod = guide.updated_at.strftime('%Y-%m-%d')
        xml_lines.append(f'  <url>')
        xml_lines.append(f'    <loc>{host}/guides/{guide.slug}/</loc>')
        xml_lines.append(f'    <lastmod>{g_mod}</lastmod>')
        xml_lines.append(f'    <changefreq>weekly</changefreq>')
        xml_lines.append(f'    <priority>0.8</priority>')
        xml_lines.append(f'  </url>')

    # Interactive Learning Academy Topics
    try:
        from debugger.learn_curriculum import CURRICULUM
        for lang_key, l_data in CURRICULUM.items():
            xml_lines.append(f'  <url>')
            xml_lines.append(f'    <loc>{host}/learn/{lang_key}/</loc>')
            xml_lines.append(f'    <lastmod>{now_str}</lastmod>')
            xml_lines.append(f'    <changefreq>weekly</changefreq>')
            xml_lines.append(f'    <priority>0.85</priority>')
            xml_lines.append(f'  </url>')
            for top in l_data.get('topics', []):
                xml_lines.append(f'  <url>')
                xml_lines.append(f'    <loc>{host}/learn/{lang_key}/{top["slug"]}/</loc>')
                xml_lines.append(f'    <lastmod>{now_str}</lastmod>')
                xml_lines.append(f'    <changefreq>weekly</changefreq>')
                xml_lines.append(f'    <priority>0.8</priority>')
                xml_lines.append(f'  </url>')
    except Exception:
        pass


    # Active Categories
    for cat in Category.objects.all():
        xml_lines.append(f'  <url>')
        xml_lines.append(f'    <loc>{host}/category/{cat.slug}/</loc>')
        xml_lines.append(f'    <lastmod>{now_str}</lastmod>')
        xml_lines.append(f'    <changefreq>daily</changefreq>')
        xml_lines.append(f'    <priority>0.8</priority>')
        xml_lines.append(f'  </url>')

    # Active Jobs
    for job in JobPosting.objects.filter(status='ACTIVE', deadline__gt=timezone.now()):
        j_mod = job.updated_at.strftime('%Y-%m-%d')
        xml_lines.append(f'  <url>')
        xml_lines.append(f'    <loc>{host}/category/{job.category.slug}/job/{job.uuid}/</loc>')
        xml_lines.append(f'    <lastmod>{j_mod}</lastmod>')
        xml_lines.append(f'    <changefreq>daily</changefreq>')
        xml_lines.append(f'    <priority>0.75</priority>')
        xml_lines.append(f'  </url>')

    xml_lines.append('</urlset>')
    return HttpResponse('\n'.join(xml_lines), content_type='application/xml')

def robots_txt_view(request):
    """Robots.txt directing crawlers to sitemap.xml."""
    host = request.build_absolute_uri('/')[:-1]
    content = f"User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /api/admin/\nDisallow: /owner/\n\nSitemap: {host}/sitemap.xml\n"
    return HttpResponse(content, content_type='text/plain')


def youtube_view(request):
    videos = get_cached_youtube_videos()
    return render(request, 'content/youtube.html', {'youtube_videos': videos})

def category_detail_view(request, slug):
    sync_expired_jobs()
    category = get_object_or_404(Category, slug=slug)
    videos = get_cached_youtube_videos()
    return render(request, 'content/category_detail.html', {'category': category, 'youtube_videos': videos})

def job_detail_view(request, category_slug=None, uuid=None, pk=None):
    sync_expired_jobs()
    job = None
    if uuid:
        job = JobPosting.objects.filter(uuid=uuid).first()
        if not job:
            clean_str = str(uuid).replace('-', '')
            job = JobPosting.objects.filter(uuid__icontains=clean_str).first()
    if not job and pk:
        job = JobPosting.objects.filter(pk=pk).first()

    if not job:
        from django.http import Http404
        raise Http404("No job posting matches the requested link.")

    # Increment view counter
    JobPosting.objects.filter(pk=job.pk).update(views_count=job.views_count + 1)
    job.views_count += 1

    related_jobs = JobPosting.objects.filter(
        status='ACTIVE',
        deadline__gt=timezone.now()
    ).exclude(pk=job.pk).select_related('category').order_by('-created_at')[:4]

    videos = get_cached_youtube_videos()

    full_share_url = request.build_absolute_uri(f"/category/{job.category.slug}/job/{job.uuid}/")
    from .interview_prep import generate_interview_prep
    interview_prep = generate_interview_prep(
        title=job.title,
        company=job.company_name,
        skills=job.skills_required,
        eligibility=job.eligibility
    )

    context = {
        'job': job,
        'skills_list': job.get_skills_list(),
        'posted_date_display': job.get_posted_date_display(),
        'related_jobs': related_jobs,
        'youtube_videos': videos,
        'share_url': full_share_url,
        'interview_prep': interview_prep,
    }
    return render(request, 'content/job_detail.html', context)

def owner_view(request):
    sync_expired_jobs()
    is_admin = request.user.is_authenticated and request.user.is_staff
    return render(request, 'owner.html', {
        'is_owner_authenticated': is_admin,
        'owner_username': request.user.username if is_admin else ''
    })

def api_youtube_videos(request):
    videos = get_cached_youtube_videos()
    return JsonResponse({'videos': videos})

@csrf_exempt
def api_owner_bulk_parse_and_post(request):
    """Bulk Auto-Parser for posting multiple job announcements at once (STRICTLY Software & Tech category)."""
    is_auth, owner_user = is_authenticated_owner(request)
    if not is_auth:
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            raw_text = data.get('raw_text', '').strip()

            if not raw_text:
                return JsonResponse({'error': 'Raw text snippet cannot be empty.'}, status=400)

            blocks = [b.strip() for b in re.split(r'\n{2,}|\n+(?=Apply Link:)|\n+(?=[1-9]\d*[\.\)\*])', raw_text) if b.strip()]
            
            if not blocks:
                blocks = [raw_text]

            created_jobs = []
            created_job_instances = []

            software_category = Category.objects.filter(slug='software-tech').first()
            if not software_category:
                software_category = Category.objects.create(
                    name='Software & Tech',
                    slug='software-tech',
                    description='Software engineering, web development, internships, and IT roles.'
                )

            for block in blocks:
                url_m = re.search(r'https?://[^\s]+', block)
                apply_url = url_m.group(0).rstrip('.,;)*') if url_m else ""

                if not apply_url:
                    continue

                company = ""
                mh_m = re.search(r'Mass Hiring Alert\s*-\s*([A-Za-z0-9\s]+)(?:\((.*?)\))?', block, re.IGNORECASE)
                if mh_m:
                    company = mh_m.group(1).strip()

                if not company:
                    hiring_m = re.search(r'([A-Za-z0-9\s]+?)\s+is Hiring', block, re.IGNORECASE)
                    if hiring_m:
                        company = hiring_m.group(1).strip()

                if not company:
                    comp_m = re.search(r'(?:Company(?:\s+Name)?):\s*([^\r\n]+)', block, re.IGNORECASE)
                    if comp_m:
                        company = comp_m.group(1).strip()

                if not company:
                    company = "Featured Hiring Partner"

                title = ""
                if mh_m and mh_m.group(2):
                    title = mh_m.group(2).strip()

                if not title:
                    title_m = re.search(r'(?:Role|Position|Title):\s*([^\r\n]+)', block, re.IGNORECASE)
                    if title_m:
                        title = title_m.group(1).strip()

                if not title:
                    title = "Software & Technology Opportunity"

                qual_m = re.search(r'(?:Qualification|Eligibility|Degree):\s*([^\r\n]+)', block, re.IGNORECASE)
                batch_m = re.search(r'(?:Batch|Graduation Year):\s*([^\r\n]+)', block, re.IGNORECASE)
                exp_m = re.search(r'(?:Experience):\s*([^\r\n]+)', block, re.IGNORECASE)

                elig_parts = []
                if qual_m: elig_parts.append(qual_m.group(1).strip())
                if batch_m: elig_parts.append(f"Batch: {batch_m.group(1).strip()}")
                if exp_m: elig_parts.append(f"Exp: {exp_m.group(1).strip()}")
                eligibility = " • ".join(elig_parts) if elig_parts else "Open to all freshers & graduating batches."

                skills_m = re.search(r'(?:Skills|Tech Stack):\s*([^\r\n]+)', block, re.IGNORECASE)
                skills_required = skills_m.group(1).strip() if skills_m else "Software Engineering, Problem Solving, Communication"

                loc_m = re.search(r'(?:Location\(s\)?|Location):\s*([^\r\n]+)', block, re.IGNORECASE)
                location = loc_m.group(1).strip() if loc_m else "Remote / Hybrid"

                sal_m = re.search(r'(?:Salary|Stipend|Pay):\s*([^\r\n]+)', block, re.IGNORECASE)
                stipend_salary = sal_m.group(1).strip() if sal_m else "Competitive Salary (Freshers)"

                lower_title = title.lower() + " " + skills_required.lower()
                deadline = timezone.now() + timedelta(days=7)
                description = f"{company} is hiring for {title}.\nKey Skills: {skills_required}.\nLocation: {location}."

                job = JobPosting.objects.create(
                    title=title,
                    company_name=company,
                    company_logo_icon='building',
                    category=software_category,
                    job_type='INTERNSHIP' if any(k in lower_title for k in ['intern', 'apprentice', 'co-op', 'trainee']) else 'FULL_TIME',
                    stipend_salary=stipend_salary,
                    location=location,
                    is_remote='remote' in location.lower(),
                    skills_required=skills_required,
                    apply_url=apply_url,
                    allow_direct_apply=False,
                    description=description,
                    eligibility=eligibility,
                    posted_by=owner_user.username if owner_user else "Owner",
                    poster_email=(owner_user.email if owner_user and owner_user.email else "admin@kashiiupdatez.com"),
                    deadline=deadline,
                )

                created_jobs.append({'id': job.id, 'title': job.title, 'company': job.company_name})
                created_job_instances.append(job)

            # --- AUTOMATIC REQUIREMENT GROUP CREATION ---
            job_group = None
            if created_job_instances:
                group_name = data.get('group_name', '').strip()
                now_local = timezone.localtime(timezone.now())
                if not group_name:
                    group_name = now_local.strftime("Hiring Drive — %d %b %Y, %I:%M %p")

                base_slug = slugify(group_name)
                if not base_slug:
                    base_slug = "hiring-drive"
                slug = f"{base_slug}-{now_local.strftime('%Y%m%d%H%M')}"

                job_group = JobGroup.objects.create(
                    name=group_name,
                    slug=slug,
                    banner_tag="🔥 SPECIAL HIRING DRIVE BUNDLE",
                    description=f"Curated bundle of {len(created_job_instances)} verified student requirements.",
                )
                job_group.jobs.set(created_job_instances)

            cache.clear()
            host_url = request.build_absolute_uri('/')[:-1]
            group_url = f"/group/{job_group.slug}/" if job_group else ""
            full_group_url = f"{host_url}/group/{job_group.slug}/" if job_group else ""
            whatsapp_broadcast = job_group.get_whatsapp_broadcast_text(host_url) if job_group else ""
            telegram_broadcast = job_group.get_telegram_broadcast_text(host_url) if job_group else ""

            return JsonResponse({
                'success': True,
                'count': len(created_jobs),
                'created_jobs': created_jobs,
                'group_id': job_group.id if job_group else None,
                'group_name': job_group.name if job_group else "",
                'group_slug': job_group.slug if job_group else "",
                'group_url': group_url,
                'full_group_url': full_group_url,
                'whatsapp_broadcast': whatsapp_broadcast,
                'telegram_broadcast': telegram_broadcast,
                'message': f'Successfully published {len(created_jobs)} opportunities and created shareable Group "{job_group.name if job_group else ""}"!'
            }, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def api_owner_jobdexo_import(request):
    """Import jobs from pasted Jobdexo URLs."""
    is_auth, owner_user = is_authenticated_owner(request)
    if not is_auth:
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            raw_urls = data.get('urls', '')
            if isinstance(raw_urls, str):
                urls = [u.strip() for u in raw_urls.split('\n') if u.strip() and 'jobdexo.com' in u]
            elif isinstance(raw_urls, list):
                urls = [u.strip() for u in raw_urls if u.strip()]
            else:
                urls = []

            if not urls:
                return JsonResponse({'error': 'Please provide at least one valid Jobdexo URL.'}, status=400)

            group_name = data.get('group_name', '').strip()

            result = auto_import_from_jobdexo(
                urls=urls,
                group_name=group_name if group_name else None
            )

            job_group = result.get('job_group')
            host_url = request.build_absolute_uri('/')[:-1]
            full_group_url = f"{host_url}/group/{job_group.slug}/" if job_group else ""
            whatsapp_broadcast = job_group.get_whatsapp_broadcast_text(host_url) if job_group else ""
            telegram_broadcast = job_group.get_telegram_broadcast_text(host_url) if job_group else ""

            return JsonResponse({
                'success': True,
                'imported_count': result['imported_count'],
                'total_in_group': result['total_in_group'],
                'created_jobs': result['created_jobs'],
                'group_id': result['group_id'],
                'group_name': result['group_name'],
                'group_slug': result['group_slug'],
                'group_url': result['group_url'],
                'full_group_url': full_group_url,
                'whatsapp_broadcast': whatsapp_broadcast,
                'telegram_broadcast': telegram_broadcast,
                'message': f"Successfully imported {result['imported_count']} new jobs from Jobdexo into Group '{result['group_name']}'!"
            }, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def api_owner_jobdexo_fetch_latest(request):
    """Crawl Jobdexo homepage and auto-import the newest 5 or 10 off-campus openings."""
    is_auth, owner_user = is_authenticated_owner(request)
    if not is_auth:
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else {}
            limit = int(data.get('limit', 5))
            group_name = data.get('group_name', '').strip()

            result = auto_import_from_jobdexo(
                urls=None,
                limit=limit,
                group_name=group_name if group_name else None
            )

            job_group = result.get('job_group')
            host_url = request.build_absolute_uri('/')[:-1]
            full_group_url = f"{host_url}/group/{job_group.slug}/" if job_group else ""
            whatsapp_broadcast = job_group.get_whatsapp_broadcast_text(host_url) if job_group else ""
            telegram_broadcast = job_group.get_telegram_broadcast_text(host_url) if job_group else ""

            return JsonResponse({
                'success': True,
                'imported_count': result['imported_count'],
                'total_in_group': result['total_in_group'],
                'created_jobs': result['created_jobs'],
                'group_id': result['group_id'],
                'group_name': result['group_name'],
                'group_slug': result['group_slug'],
                'group_url': result['group_url'],
                'full_group_url': full_group_url,
                'whatsapp_broadcast': whatsapp_broadcast,
                'telegram_broadcast': telegram_broadcast,
                'message': f"Successfully fetched and published {result['imported_count']} fresh jobs from Jobdexo into Group '{result['group_name']}'!"
            }, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def api_owner_parse_and_post(request):
    """Single Job Auto-Parser for posting a raw text snippet (STRICTLY Software & Tech category)."""
    is_auth, owner_user = is_authenticated_owner(request)
    if not is_auth:
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            raw_text = data.get('raw_text', '').strip()

            if not raw_text:
                return JsonResponse({'error': 'Raw text snippet cannot be empty.'}, status=400)

            url_match = re.search(r'https?://[^\s]+', raw_text)
            apply_url = url_match.group(0).rstrip('.,;') if url_match else ""

            company_match = re.search(r'(?:Company|Organization):\s*(.+)', raw_text, re.IGNORECASE)
            company_name = company_match.group(1).strip() if company_match else "Featured Hiring Partner"

            title_match = re.search(r'(?:Role|Title|Position|Job):\s*(.+)', raw_text, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else "Software & Technology Opportunity"

            qual_match = re.search(r'(?:Qualification|Eligibility|Degree):\s*(.+)', raw_text, re.IGNORECASE)
            exp_match = re.search(r'(?:Experience):\s*(.+)', raw_text, re.IGNORECASE)
            
            eligibility_parts = []
            if qual_match:
                eligibility_parts.append(f"Qualification: {qual_match.group(1).strip()}")
            if exp_match:
                eligibility_parts.append(f"Experience: {exp_match.group(1).strip()}")
            eligibility = " • ".join(eligibility_parts) if eligibility_parts else "Open to final year students and fresh graduates."

            skills_match = re.search(r'(?:Skills|Tech Stack):\s*(.+)', raw_text, re.IGNORECASE)
            skills_required = skills_match.group(1).strip() if skills_match else "Software Engineering, Problem Solving, Communication"

            loc_match = re.search(r'(?:Location):\s*(.+)', raw_text, re.IGNORECASE)
            location = loc_match.group(1).strip() if loc_match else "Remote"

            salary_match = re.search(r'(?:Salary|Stipend|Pay):\s*(.+)', raw_text, re.IGNORECASE)
            stipend_salary = salary_match.group(1).strip() if salary_match else "Competitive Salary (Freshers)"

            category = Category.objects.filter(slug='software-tech').first()
            if not category:
                category = Category.objects.create(
                    name='Software & Tech',
                    slug='software-tech',
                    description='Software engineering, web development, internships, and IT roles.'
                )

            description = f"{company_name} is hiring for {title}.\nKey Requirements & Skills: {skills_required}.\nLocation: {location}."
            deadline = timezone.now() + timedelta(days=7)

            job = JobPosting.objects.create(
                title=title,
                company_name=company_name,
                company_logo_icon='building',
                category=category,
                job_type='INTERNSHIP' if 'intern' in title.lower() or 'apprentice' in title.lower() else 'FULL_TIME',
                stipend_salary=stipend_salary,
                location=location,
                is_remote='remote' in location.lower(),
                skills_required=skills_required,
                apply_url=apply_url,
                allow_direct_apply=False,
                description=description,
                eligibility=eligibility,
                posted_by=owner_user.username if owner_user else "Owner",
                poster_email=(owner_user.email if owner_user and owner_user.email else "admin@kashiiupdatez.com"),
                deadline=deadline,
            )

            cache.clear()
            return JsonResponse({
                'success': True,
                'id': job.id,
                'title': job.title,
                'company_name': job.company_name,
                'message': 'Software & Tech opportunity auto-parsed and published! Active for 7 days.'
            }, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

def api_stats(request):
    sync_expired_jobs()
    now = timezone.now()
    active_jobs = JobPosting.objects.filter(status='ACTIVE', deadline__gt=now).count()
    companies_count = JobPosting.objects.values('company_name').distinct().count()

    return JsonResponse({
        'active_jobs': active_jobs,
        'companies_count': companies_count,
    })

def api_categories(request):
    sync_expired_jobs()
    categories = list(Category.objects.annotate(
        active_count=Count('job_postings', filter=Q(job_postings__status='ACTIVE'))
    ).values('id', 'name', 'slug', 'icon', 'description', 'active_count'))
    
    return JsonResponse({'categories': categories})

@csrf_exempt
def api_owner_categories(request):
    is_auth, owner_user = is_authenticated_owner(request)
    if not is_auth:
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    if request.method == 'GET':
        categories = list(Category.objects.annotate(job_count=Count('job_postings')).values('id', 'name', 'slug', 'icon', 'description', 'job_count'))
        return JsonResponse({'categories': categories})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data['name'].strip()
            slug = slugify(name)
            description = data.get('description', '').strip()

            cat = Category.objects.create(name=name, slug=slug, description=description)
            cache.clear()
            return JsonResponse({'success': True, 'id': cat.id, 'name': cat.name}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def api_owner_job_delete(request, pk):
    is_auth, owner_user = is_authenticated_owner(request)
    if not is_auth:
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    if request.method in ['POST', 'DELETE']:
        job = get_object_or_404(JobPosting, pk=pk)
        job.delete()
        cache.clear()
        return JsonResponse({'success': True, 'message': 'Job posting deleted successfully.'})

@csrf_exempt
def api_owner_job_toggle_status(request, pk):
    is_auth, owner_user = is_authenticated_owner(request)
    if not is_auth:
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    if request.method in ['POST', 'PUT']:
        job = get_object_or_404(JobPosting, pk=pk)
        if job.status == 'ACTIVE':
            job.status = 'EXPIRED'
        else:
            job.status = 'ACTIVE'
            job.deadline = timezone.now() + timedelta(days=7)
        job.save(update_fields=['status', 'deadline'])
        cache.clear()
        return JsonResponse({
            'success': True,
            'status': job.status,
            'status_display': job.get_status_display(),
            'message': f"Job status updated to {job.get_status_display()}."
        })

@csrf_exempt
def api_owner_job_update(request, pk):
    is_auth, owner_user = is_authenticated_owner(request)
    if not is_auth:
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    if request.method in ['POST', 'PUT']:
        try:
            job = get_object_or_404(JobPosting, pk=pk)
            data = json.loads(request.body)

            if 'title' in data:
                job.title = data['title'].strip()
            if 'company_name' in data:
                job.company_name = data['company_name'].strip()
            if 'category_id' in data:
                cat = get_object_or_404(Category, id=data['category_id'])
                job.category = cat
            if 'job_type' in data:
                job.job_type = data['job_type']
            if 'apply_url' in data:
                job.apply_url = data['apply_url'].strip()
            if 'stipend_salary' in data:
                job.stipend_salary = data['stipend_salary'].strip()
            if 'location' in data:
                job.location = data['location'].strip()
                job.is_remote = 'remote' in job.location.lower()
            if 'skills_required' in data:
                job.skills_required = data['skills_required'].strip()
            if 'description' in data:
                job.description = data['description'].strip()
            if 'eligibility' in data:
                job.eligibility = data['eligibility'].strip()

            job.save()
            cache.clear()
            return JsonResponse({'success': True, 'message': 'Posting updated successfully!', 'id': job.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def api_admin_login(request):
    if request.method == 'POST':
        try:
            raw_username = ""
            password = ""
            
            if request.body:
                try:
                    data = json.loads(request.body)
                    raw_username = data.get('username', '').strip()
                    password = data.get('password', '').strip()
                except Exception:
                    pass

            if not raw_username:
                raw_username = request.POST.get('username', '').strip()
                password = request.POST.get('password', '').strip()

            if '@' in raw_username:
                user_obj = User.objects.filter(email__iexact=raw_username).first()
            else:
                user_obj = User.objects.filter(username__iexact=raw_username).first()

            actual_username = user_obj.username if user_obj else raw_username

            user = authenticate(request, username=actual_username, password=password)
            if user is not None and user.is_staff:
                login(request, user)
                request.session.set_expiry(2592000)  # 30 Days persistent session cookie
                request.session.modified = True

                # Generate SimpleJWT Tokens for Owner
                from rest_framework_simplejwt.tokens import RefreshToken
                refresh = RefreshToken.for_user(user)

                # Cache owner credentials & JWT session details in high-performance Redis/LocMem cache (24 hours)
                cache_key = f"owner_session_{user.id}"
                user_session_data = {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff,
                    'access_token': str(refresh.access_token),
                    'authenticated_at': timezone.now().isoformat()
                }
                cache.set(cache_key, user_session_data, 86400)

                return JsonResponse({
                    'success': True,
                    'username': user.username,
                    'is_admin': True,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'cached_session': True,
                    'message': 'Owner JWT authentication successful & credentials cached!'
                })
            else:
                return JsonResponse({'error': 'Invalid owner credentials or insufficient privileges.'}, status=401)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def api_admin_logout(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'success': True, 'message': 'Logged out successfully.'})

def api_admin_status(request):
    is_admin = request.user.is_authenticated and request.user.is_staff
    username = request.user.username if is_admin else None

    if not is_admin:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                from django.contrib.auth.models import User
                access = AccessToken(token)
                user_id = access.get('user_id')
                user = User.objects.filter(id=user_id, is_staff=True).first()
                if user:
                    is_admin = True
                    username = user.username
            except Exception:
                pass

    return JsonResponse({
        'is_admin': is_admin,
        'username': username
    })

@csrf_exempt
def api_jobs(request):
    sync_expired_jobs()

    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        category_slug = request.GET.get('category', '').strip()
        job_type = request.GET.get('job_type', '').strip()
        filter_today = request.GET.get('today', '').strip()
        filter_yesterday = request.GET.get('yesterday', '').strip()
        filter_previous = request.GET.get('previous', '').strip()
        sort = request.GET.get('sort', 'newest')
        page = request.GET.get('page', '1')
        page_size = request.GET.get('page_size', '6')

        raw_key = f"jobs_feed_{query}_{category_slug}_{job_type}_{filter_today}_{filter_yesterday}_{filter_previous}_{sort}_{page}_{page_size}"
        cache_key = f"jobs_feed_{hashlib.md5(raw_key.encode('utf-8')).hexdigest()}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return JsonResponse(cached_response)

        # STRICT NEWEST-FIRST SORTING (-created_at)
        qs = JobPosting.objects.all().select_related('category').order_by('-created_at')

        if filter_yesterday == 'true' or filter_yesterday == '1':
            today_date = timezone.now().date()
            yesterday_date = today_date - timedelta(days=1)
            yesterday_qs = qs.filter(posted_date=yesterday_date)
            if yesterday_qs.exists():
                qs = yesterday_qs
            else:
                # Fallback to last 4 days if exact yesterday has no postings
                four_days_ago = today_date - timedelta(days=4)
                qs = qs.filter(posted_date__gte=four_days_ago)
        elif filter_today == 'true' or filter_today == '1':
            today_date = timezone.now().date()
            today_qs = qs.filter(posted_date=today_date)
            if today_qs.exists():
                qs = today_qs
            else:
                # Fallback to recent postings from the last 4 days if today has no postings
                four_days_ago = today_date - timedelta(days=4)
                qs = qs.filter(posted_date__gte=four_days_ago)
        elif filter_previous == 'true' or filter_previous == '1':
            today_date = timezone.now().date()
            four_days_ago = today_date - timedelta(days=4)
            qs = qs.filter(posted_date__gte=four_days_ago)

        if query:
            qs = qs.filter(
                Q(title__icontains=query) | 
                Q(company_name__icontains=query) | 
                Q(skills_required__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query)
            )

        if category_slug and category_slug != 'all':
            qs = qs.filter(category__slug=category_slug)

        if job_type and job_type != 'all':
            qs = qs.filter(job_type=job_type)

        if sort == 'deadline':
            qs = qs.order_by('deadline')

        results = []
        now = timezone.now()
        for j in qs:
            time_left_seconds = max(0, int((j.deadline - now).total_seconds()))
            
            # Use the explicit posted_date field (editable in admin)
            posted_date_display = j.get_posted_date_display()

            results.append({
                'id': j.id,
                'uuid': str(j.uuid),
                'share_url': f"/category/{j.category.slug}/job/{j.uuid}/",
                'title': j.title,
                'company_name': j.company_name,
                'company_logo_icon': j.company_logo_icon,
                'category_name': j.category.name,
                'category_slug': j.category.slug,
                'job_type': j.job_type,
                'job_type_display': j.get_job_type_display(),
                'stipend_salary': j.stipend_salary,
                'location': j.location,
                'is_remote': j.is_remote,
                'skills_required': j.skills_required,
                'skills_list': j.get_skills_list(),
                'apply_url': j.apply_url,
                'allow_direct_apply': j.allow_direct_apply,
                'description': j.description,
                'eligibility': j.eligibility,
                'posted_by': j.posted_by,
                'status': j.status,
                'status_display': j.get_status_display(),
                'views_count': j.views_count,
                'is_featured': j.is_featured,
                'deadline': j.deadline.isoformat(),
                'time_left_seconds': time_left_seconds,
                'created_at': j.created_at.isoformat(),
                'posted_date': j.posted_date.isoformat(),
                'posted_date_display': posted_date_display,
            })

        try:
            page_int = int(page)
        except ValueError:
            page_int = 1

        try:
            page_size_int = int(page_size)
        except ValueError:
            page_size_int = 6

        total_count = len(results)
        total_pages = max(1, (total_count + page_size_int - 1) // page_size_int)
        page_int = min(max(1, page_int), total_pages)

        start_idx = (page_int - 1) * page_size_int
        end_idx = start_idx + page_size_int
        paginated_results = results[start_idx:end_idx]

        response_data = {
            'jobs': paginated_results,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page_int,
            'page_size': page_size_int,
            'has_next': page_int < total_pages,
            'has_previous': page_int > 1,
        }

        cache.set(cache_key, response_data, 120)
        return JsonResponse(response_data)

    elif request.method == 'POST':
        is_auth, owner_user = is_authenticated_owner(request)
        if not is_auth:
            return JsonResponse({'error': 'Unauthorized. Only Kashii Updatez Owner can post opportunities.'}, status=401)

        try:
            data = json.loads(request.body)
            category = get_object_or_404(Category, id=data.get('category_id'))

            deadline = timezone.now() + timedelta(days=7)

            job = JobPosting.objects.create(
                title=data['title'].strip(),
                company_name=data['company_name'].strip(),
                company_logo_icon=data.get('company_logo_icon', 'building'),
                category=category,
                job_type=data.get('job_type', 'INTERNSHIP'),
                stipend_salary=data.get('stipend_salary', 'Competitive Stipend').strip(),
                location=data.get('location', 'Remote').strip(),
                is_remote=data.get('is_remote', True),
                skills_required=data.get('skills_required', '').strip(),
                apply_url=data.get('apply_url', '').strip(),
                allow_direct_apply=False,
                description=data['description'].strip(),
                eligibility=data.get('eligibility', 'Open to all students').strip(),
                posted_by=owner_user.username if owner_user else "Owner",
                poster_email=(owner_user.email if owner_user and owner_user.email else "admin@kashiiupdatez.com"),
                deadline=deadline,
            )

            cache.clear()
            return JsonResponse({'success': True, 'id': job.id, 'message': 'Opportunity published! Automatically active for 3 days.'}, status=201)
        except KeyError as e:
            return JsonResponse({'error': f'Missing field: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def api_job_detail(request, pk):
    sync_expired_jobs()
    job = get_object_or_404(JobPosting, pk=pk)

    if request.method == 'GET':
        job.views_count += 1
        job.save(update_fields=['views_count'])

        now = timezone.now()
        time_left_seconds = max(0, int((job.deadline - now).total_seconds()))

        # Use the explicit posted_date field
        posted_date_display = job.get_posted_date_display()

        return JsonResponse({
            'job': {
                'id': job.id,
                'title': job.title,
                'company_name': job.company_name,
                'company_logo_icon': job.company_logo_icon,
                'category_name': job.category.name,
                'category_slug': job.category.slug,
                'job_type': job.job_type,
                'job_type_display': job.get_job_type_display(),
                'stipend_salary': job.stipend_salary,
                'location': job.location,
                'is_remote': job.is_remote,
                'skills_required': job.skills_required,
                'skills_list': job.get_skills_list(),
                'apply_url': job.apply_url,
                'allow_direct_apply': job.allow_direct_apply,
                'description': job.description,
                'eligibility': job.eligibility,
                'posted_by': job.posted_by,
                'status': job.status,
                'status_display': job.get_status_display(),
                'views_count': job.views_count,
                'is_featured': job.is_featured,
                'deadline': job.deadline.isoformat(),
                'time_left_seconds': time_left_seconds,
                'created_at': job.created_at.isoformat(),
                'posted_date': job.posted_date.isoformat(),
                'posted_date_display': posted_date_display,
            }
        })

def api_job_ig_story_image(request, pk):
    from io import BytesIO
    from django.http import HttpResponse
    from PIL import Image, ImageDraw, ImageFont

    job = get_object_or_404(JobPosting, pk=pk)

    # 1080x1920 9:16 Canvas
    img = Image.new('RGB', (1080, 1920), color='#090d16')
    draw = ImageDraw.Draw(img)

    # Premium Radial & Linear Ambient Glows
    for y in range(1920):
        r = int(9 + (15 - 9) * (y / 1920))
        g = int(13 + (23 - 13) * (y / 1920))
        b = int(22 + (42 - 22) * (y / 1920))
        draw.line([(0, y), (1080, y)], fill=(r, g, b))

    # Decorative Ambient Lighting Orbs
    draw.ellipse([700, 100, 1200, 600], fill=(131, 58, 180, 50))
    draw.ellipse([-100, 1300, 450, 1850], fill=(37, 99, 235, 45))

    # Main Classy Card Outline & Solid Dark Background
    draw.rounded_rectangle([90, 240, 990, 1680], radius=52, fill=(15, 23, 42), outline=(56, 189, 248), width=3)
    draw.rounded_rectangle([94, 244, 986, 1676], radius=48, fill=(17, 24, 39))

    # Load High-Quality System TTF Fonts
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "Arial.ttf"
    ]

    def get_font(size, bold=False):
        for path in font_paths:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    font_badge = get_font(30, bold=True)
    font_handle = get_font(32)
    font_company = get_font(44, bold=True)
    font_title = get_font(58, bold=True)
    font_label = get_font(30, bold=True)
    font_val = get_font(38, bold=True)
    font_btn = get_font(38, bold=True)
    font_domain = get_font(28, bold=True)

    # 1. Top Category & Handle Header
    draw.rounded_rectangle([150, 300, 560, 375], radius=38, fill=(236, 72, 153))
    draw.text((180, 322), "🔥 NEW REQUIREMENT", fill=(255, 255, 255), font=font_badge)
    draw.text((710, 322), "@ikashii_07", fill=(148, 163, 184), font=font_handle)

    # Divider Line
    draw.line([(150, 410), (930, 410)], fill=(51, 65, 85), width=2)

    # 2. Company Name & Title Header
    draw.text((150, 450), job.company_name.upper(), fill=(56, 189, 248), font=font_company)

    # Multiline Job Title
    words = job.title.split()
    line = ""
    y_pos = 530
    for word in words:
        test = line + word + " "
        if len(test) > 20 and line:
            draw.text((150, y_pos), line, fill=(255, 255, 255), font=font_title)
            line = word + " "
            y_pos += 76
        else:
            line = test
    if line:
        draw.text((150, y_pos), line, fill=(255, 255, 255), font=font_title)

    # 3. Classy Details Section (Card Inset matching HTML Preview)
    box_top = max(y_pos + 70, 780)
    draw.rounded_rectangle([150, box_top, 930, box_top + 400], radius=36, fill=(30, 41, 59), outline=(71, 85, 105), width=2)

    # Load PNG Icon Assets
    static_img_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
    
    def load_png_icon(filename, size=(38, 38)):
        try:
            path = os.path.join(static_img_dir, filename)
            icon = Image.open(path).convert("RGBA")
            icon = icon.resize(size, Image.Resampling.LANCZOS)
            return icon
        except Exception:
            return None

    icon_salary = load_png_icon('icon-salary.png')
    icon_location = load_png_icon('icon-location.png')
    icon_eligibility = load_png_icon('icon-type.png')
    icon_link = load_png_icon('icon-apply.png', size=(42, 42))

    # Detail Item 1: Salary / Stipend
    draw.text((190, box_top + 45), "STIPEND / SALARY", fill=(148, 163, 184), font=font_label)
    if icon_salary:
        img.paste(icon_salary, (190, box_top + 92), icon_salary)
        draw.text((240, box_top + 90), f"{job.stipend_salary}", fill=(52, 211, 153), font=font_val)
    else:
        draw.text((190, box_top + 90), f"{job.stipend_salary}", fill=(52, 211, 153), font=font_val)

    # Detail Item 2: Location
    draw.text((190, box_top + 165), "LOCATION", fill=(148, 163, 184), font=font_label)
    if icon_location:
        img.paste(icon_location, (190, box_top + 212), icon_location)
        draw.text((240, box_top + 210), f"{job.location}", fill=(244, 244, 245), font=font_val)
    else:
        draw.text((190, box_top + 210), f"{job.location}", fill=(244, 244, 245), font=font_val)

    # Detail Item 3: Eligibility
    draw.text((190, box_top + 285), "ELIGIBILITY", fill=(148, 163, 184), font=font_label)
    if icon_eligibility:
        img.paste(icon_eligibility, (190, box_top + 332), icon_eligibility)
        draw.text((240, box_top + 330), "All Eligible Batches / Students", fill=(244, 244, 245), font=font_val)
    else:
        draw.text((190, box_top + 330), "All Eligible Batches / Students", fill=(244, 244, 245), font=font_val)

    # 4. Link Sticker Call-To-Action Button (Instagram Gradient)
    btn_y = box_top + 470
    draw.rounded_rectangle([150, btn_y, 930, btn_y + 120], radius=60, fill=(225, 48, 108))
    
    if icon_link:
        img.paste(icon_link, (200, btn_y + 39), icon_link)
        draw.text((560, btn_y + 40), "Tap Link Sticker Below to Apply", fill=(255, 255, 255), font=font_btn, anchor="mm")
    else:
        draw.text((540, btn_y + 40), "Tap Link Sticker Below to Apply ->", fill=(255, 255, 255), font=font_btn, anchor="mm")

    # Domain Attribution Footer
    draw.text((540, btn_y + 170), "kashiiupdatez.online", fill=(148, 163, 184), font=font_domain, anchor="mm")

    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')

# ==============================================================================
# REQUIREMENT GROUPS & MULTI-JOB BUNDLES
# ==============================================================================

def group_detail_view(request, slug):
    """Public web page displaying a curated collection/drive of multiple job requirements."""
    sync_expired_jobs()
    group = get_object_or_404(JobGroup, slug=slug, is_active=True)
    group.views_count += 1
    group.save(update_fields=['views_count'])
    jobs = list(group.get_active_jobs())
    host_url = request.build_absolute_uri('/')[:-1]
    return render(request, 'content/group_detail.html', {
        'group': group,
        'jobs': jobs,
        'is_expired': group.is_expired(),
        'time_left_seconds': group.get_time_left_seconds(),
        'time_left_display': group.get_time_left_display(),
        'share_whatsapp_text': group.get_whatsapp_broadcast_text(host_url),
        'share_telegram_text': group.get_telegram_broadcast_text(host_url),
    })

def api_groups(request):
    """Public JSON API returning active requirement groups (active for 7 days)."""
    sync_expired_jobs()
    now = timezone.now()
    groups = JobGroup.objects.filter(is_active=True, deadline__gt=now).prefetch_related('jobs')
    host_url = request.build_absolute_uri('/')[:-1]
    res = []
    for g in groups:
        res.append({
            'id': g.id,
            'name': g.name,
            'slug': g.slug,
            'banner_tag': g.banner_tag,
            'description': g.description,
            'jobs_count': g.get_active_jobs().count(),
            'time_left_seconds': g.get_time_left_seconds(),
            'time_left_display': g.get_time_left_display(),
            'url': f"/group/{g.slug}/",
            'full_url': f"{host_url}/group/{g.slug}/",
            'created_at': g.created_at.isoformat(),
        })
    return JsonResponse({'groups': res})

@csrf_exempt
def api_owner_groups(request):
    """Owner endpoint to list all requirement groups or create a new group."""
    is_auth, owner_user = is_authenticated_owner(request)
    if not is_auth:
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    if request.method == 'GET':
        groups = JobGroup.objects.all().prefetch_related('jobs')
        res = []
        host_url = request.build_absolute_uri('/')[:-1]
        for g in groups:
            res.append({
                'id': g.id,
                'name': g.name,
                'slug': g.slug,
                'banner_tag': g.banner_tag,
                'description': g.description,
                'total_jobs_count': g.jobs.count(),
                'active_jobs_count': g.get_active_jobs().count(),
                'views_count': g.views_count,
                'is_expired': g.is_expired(),
                'time_left_display': g.get_time_left_display(),
                'time_left_seconds': g.get_time_left_seconds(),
                'deadline': g.deadline.strftime('%d %b %Y, %I:%M %p') if g.deadline else "",
                'created_at': g.created_at.strftime('%d %b %Y, %I:%M %p'),
                'url': f"/group/{g.slug}/",
                'full_url': f"{host_url}/group/{g.slug}/",
            })
        return JsonResponse({'groups': res})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            job_ids = data.get('job_ids', [])
            now_local = timezone.localtime(timezone.now())
            if not name:
                name = now_local.strftime("Hiring Drive — %d %b %Y, %I:%M %p")

            base_slug = slugify(name) or "hiring-drive"
            slug = f"{base_slug}-{now_local.strftime('%Y%m%d%H%M')}"

            group = JobGroup.objects.create(
                name=name,
                slug=slug,
                banner_tag=data.get('banner_tag', '🔥 SPECIAL HIRING DRIVE BUNDLE').strip(),
                description=data.get('description', '').strip(),
            )
            if job_ids:
                group.jobs.set(JobPosting.objects.filter(id__in=job_ids))

            host_url = request.build_absolute_uri('/')[:-1]
            return JsonResponse({
                'success': True,
                'id': group.id,
                'name': group.name,
                'slug': group.slug,
                'url': f"/group/{group.slug}/",
                'full_url': f"{host_url}/group/{group.slug}/",
                'whatsapp_broadcast': group.get_whatsapp_broadcast_text(host_url),
                'telegram_broadcast': group.get_telegram_broadcast_text(host_url),
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def api_owner_group_broadcast(request, pk):
    """Generates formatted WhatsApp and Telegram multi-job broadcast texts for 1-click copying."""
    is_auth, owner_user = is_authenticated_owner(request)
    if not is_auth:
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    group = get_object_or_404(JobGroup, pk=pk)
    host_url = request.build_absolute_uri('/')[:-1]
    return JsonResponse({
        'group_id': group.id,
        'group_name': group.name,
        'group_slug': group.slug,
        'group_url': f"/group/{group.slug}/",
        'full_group_url': f"{host_url}/group/{group.slug}/",
        'whatsapp_broadcast': group.get_whatsapp_broadcast_text(host_url),
        'telegram_broadcast': group.get_telegram_broadcast_text(host_url),
    })

@csrf_exempt
def api_owner_group_delete(request, pk):
    """Deletes a requirement group."""
    is_auth, owner_user = is_authenticated_owner(request)
    if not is_auth:
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    group = get_object_or_404(JobGroup, pk=pk)
    group.delete()
    return JsonResponse({'success': True, 'message': 'Requirement group deleted successfully.'})

def custom_404_view(request, exception=None):
    """Custom 404 handler for expired jobs, deleted requirements, or non-existent URLs."""
    response = render(request, '404.html', status=404)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


