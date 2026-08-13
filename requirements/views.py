import os
import json
import re
import urllib.request
import ssl
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.utils.text import slugify
from django.db.models import Q, Count
from django.core.cache import cache
from .models import Category, JobPosting

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

def index_view(request):
    sync_expired_jobs()
    videos = get_cached_youtube_videos()
    return render(request, 'content/home.html', {'youtube_videos': videos})

def about_view(request):
    return render(request, 'content/about.html')

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

    context = {
        'job': job,
        'skills_list': job.get_skills_list(),
        'posted_date_display': job.get_posted_date_display(),
        'related_jobs': related_jobs,
        'youtube_videos': videos,
        'share_url': full_share_url,
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

            cache.clear()
            return JsonResponse({
                'success': True,
                'count': len(created_jobs),
                'created_jobs': created_jobs,
                'message': f'Successfully published {len(created_jobs)} opportunities under Software & Tech! Active for 7 days.'
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

        cache_key = f"jobs_feed_{query}_{category_slug}_{job_type}_{filter_today}_{filter_yesterday}_{filter_previous}_{sort}_{page}_{page_size}"
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

def custom_404_view(request, exception=None):
    """Custom 404 handler for expired jobs, deleted requirements, or non-existent URLs."""
    response = render(request, '404.html', status=404)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


