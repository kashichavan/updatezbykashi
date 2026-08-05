import json
import re
import urllib.request
import ssl
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.utils.text import slugify
from django.db.models import Q, Count
from .models import Category, JobPosting

def sync_expired_jobs():
    """Automatically deletes postings older than 3 days (72 hours) so feed stays 100% fresh daily."""
    now = timezone.now()
    JobPosting.objects.filter(deadline__lte=now).delete()

def index_view(request):
    sync_expired_jobs()
    return render(request, 'content/home.html')

def about_view(request):
    return render(request, 'content/about.html')

def youtube_view(request):
    return render(request, 'content/youtube.html')

def category_detail_view(request, slug):
    sync_expired_jobs()
    category = get_object_or_404(Category, slug=slug)
    return render(request, 'content/category_detail.html', {'category': category})

def owner_view(request):
    sync_expired_jobs()
    return render(request, 'owner.html')

def api_youtube_videos(request):
    """Fetches real YouTube video thumbnails and titles directly from @pythonkashi channel."""
    default_videos = [
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

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        url = 'https://www.youtube.com/@pythonkashi/videos'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            html = resp.read().decode('utf-8')
            video_ids = list(dict.fromkeys(re.findall(r'\"videoId\":\"([^\"]+)\"', html)))[:10]
            
            videos = []
            for vid in video_ids:
                oembed_url = f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json'
                try:
                    oreq = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(oreq, context=ctx, timeout=2) as oresp:
                        data = json.loads(oresp.read().decode('utf-8'))
                        videos.append({
                            'video_id': vid,
                            'title': data.get('title', 'Python Kashi Tutorial'),
                            'thumbnail_url': f'https://img.youtube.com/vi/{vid}/hqdefault.jpg',
                            'watch_url': f'https://www.youtube.com/watch?v={vid}'
                        })
                except Exception:
                    pass

            if videos:
                return JsonResponse({'videos': videos})

    except Exception:
        pass

    return JsonResponse({'videos': default_videos})

@csrf_exempt
def api_owner_bulk_parse_and_post(request):
    """Bulk Auto-Parser for posting multiple job announcements at once (STRICTLY Software & Tech category)."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            raw_text = data.get('raw_text', '').strip()

            if not raw_text:
                return JsonResponse({'error': 'Raw text snippet cannot be empty.'}, status=400)

            blocks = [b.strip() for b in re.split(r'\n+(?=[1-9]\d*[\.\)\*])', raw_text) if b.strip()]
            
            if not blocks:
                blocks = [raw_text]

            created_jobs = []

            # STRICT CATEGORY: Software & Tech
            software_category = Category.objects.filter(slug='software-tech').first()
            if not software_category:
                software_category = Category.objects.create(
                    name='Software & Tech',
                    slug='software-tech',
                    description='Software engineering, web development, internships, and IT roles.'
                )

            for block in blocks:
                # 1. Extract Apply Link
                url_m = re.search(r'https?://[^\s]+', block)
                apply_url = url_m.group(0).rstrip('.,;)*') if url_m else ""

                if not apply_url:
                    continue

                # 2. Extract Company
                company = ""
                mh_m = re.search(r'Mass Hiring Alert\s*-\s*([A-Za-z0-9\s]+)(?:\((.*?)\))?', block, re.IGNORECASE)
                if mh_m:
                    company = mh_m.group(1).strip()

                if not company:
                    hiring_m = re.search(r'([A-Za-z0-9\s]+?)\s+is Hiring', block, re.IGNORECASE)
                    if hiring_m:
                        company = hiring_m.group(1).strip()

                if not company:
                    comp_m = re.search(r'(?:Company(?:\s+Name)?):\s*(.+)', block, re.IGNORECASE)
                    if comp_m:
                        company = comp_m.group(1).strip()

                if not company:
                    company = "Featured Hiring Partner"

                # 3. Extract Role / Title
                title = ""
                if mh_m and mh_m.group(2):
                    title = mh_m.group(2).strip()

                if not title:
                    title_m = re.search(r'(?:Role|Position|Title):\s*(.+)', block, re.IGNORECASE)
                    if title_m:
                        title = title_m.group(1).strip()

                if not title:
                    title = "Software & Technology Opportunity"

                # 4. Qualification, Eligibility, Batch & Exp
                qual_m = re.search(r'(?:Qualification|Eligibility|Degree):\s*(.+)', block, re.IGNORECASE)
                batch_m = re.search(r'(?:Batch|Graduation Year):\s*(.+)', block, re.IGNORECASE)
                exp_m = re.search(r'(?:Experience):\s*(.+)', block, re.IGNORECASE)

                elig_parts = []
                if qual_m: elig_parts.append(qual_m.group(1).strip())
                if batch_m: elig_parts.append(f"Batch: {batch_m.group(1).strip()}")
                if exp_m: elig_parts.append(f"Exp: {exp_m.group(1).strip()}")
                eligibility = " • ".join(elig_parts) if elig_parts else "Open to all freshers & graduating batches."

                # 5. Skills
                skills_m = re.search(r'(?:Skills|Tech Stack):\s*(.+)', block, re.IGNORECASE)
                skills_required = skills_m.group(1).strip() if skills_m else "Software Engineering, Problem Solving, Communication"

                # 6. Location
                loc_m = re.search(r'(?:Location\(s\)?|Location):\s*(.+)', block, re.IGNORECASE)
                location = loc_m.group(1).strip() if loc_m else "Remote / Hybrid"

                # 7. Salary
                sal_m = re.search(r'(?:Salary|Stipend|Pay):\s*(.+)', block, re.IGNORECASE)
                stipend_salary = sal_m.group(1).strip() if sal_m else "Competitive Salary (Freshers)"

                lower_title = title.lower() + " " + skills_required.lower()
                deadline = timezone.now() + timedelta(days=3)
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
                    posted_by=request.user.username,
                    poster_email=request.user.email or "admin@kashiiupdatez.com",
                    deadline=deadline,
                )

                created_jobs.append({'id': job.id, 'title': job.title, 'company': job.company_name})

            return JsonResponse({
                'success': True,
                'count': len(created_jobs),
                'created_jobs': created_jobs,
                'message': f'Successfully published {len(created_jobs)} opportunities under Software & Tech! Active for 3 days.'
            }, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def api_owner_parse_and_post(request):
    """Single Job Auto-Parser for posting a raw text snippet (STRICTLY Software & Tech category)."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            raw_text = data.get('raw_text', '').strip()

            if not raw_text:
                return JsonResponse({'error': 'Raw text snippet cannot be empty.'}, status=400)

            # 1. Extract Apply Link
            url_match = re.search(r'https?://[^\s]+', raw_text)
            apply_url = url_match.group(0).rstrip('.,;') if url_match else ""

            # 2. Extract Company
            company_match = re.search(r'(?:Company|Organization):\s*(.+)', raw_text, re.IGNORECASE)
            company_name = company_match.group(1).strip() if company_match else "Featured Hiring Partner"

            # 3. Extract Role / Title
            title_match = re.search(r'(?:Role|Title|Position|Job):\s*(.+)', raw_text, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else "Software & Technology Opportunity"

            # 4. Extract Qualification & Experience for Eligibility
            qual_match = re.search(r'(?:Qualification|Eligibility|Degree):\s*(.+)', raw_text, re.IGNORECASE)
            exp_match = re.search(r'(?:Experience):\s*(.+)', raw_text, re.IGNORECASE)
            
            eligibility_parts = []
            if qual_match:
                eligibility_parts.append(f"Qualification: {qual_match.group(1).strip()}")
            if exp_match:
                eligibility_parts.append(f"Experience: {exp_match.group(1).strip()}")
            eligibility = " • ".join(eligibility_parts) if eligibility_parts else "Open to final year students and fresh graduates."

            # 5. Extract Skills
            skills_match = re.search(r'(?:Skills|Tech Stack):\s*(.+)', raw_text, re.IGNORECASE)
            skills_required = skills_match.group(1).strip() if skills_match else "Software Engineering, Problem Solving, Communication"

            # 6. Extract Location
            loc_match = re.search(r'(?:Location):\s*(.+)', raw_text, re.IGNORECASE)
            location = loc_match.group(1).strip() if loc_match else "Remote"

            # 7. Extract Stipend / Salary
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
            deadline = timezone.now() + timedelta(days=3)

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
                posted_by=request.user.username,
                poster_email=request.user.email or "admin@kashiiupdatez.com",
                deadline=deadline,
            )

            return JsonResponse({
                'success': True,
                'id': job.id,
                'title': job.title,
                'company_name': job.company_name,
                'message': 'Software & Tech opportunity auto-parsed and published! Active for 3 days.'
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
    categories = Category.objects.annotate(
        active_count=Count('job_postings', filter=Q(job_postings__status='ACTIVE'))
    ).values('id', 'name', 'slug', 'icon', 'description', 'active_count')
    return JsonResponse({'categories': list(categories)})

@csrf_exempt
def api_owner_categories(request):
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data['name'].strip()
            slug = slugify(name)
            description = data.get('description', '').strip()

            cat = Category.objects.create(name=name, slug=slug, description=description)
            return JsonResponse({'success': True, 'id': cat.id, 'name': cat.name}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def api_owner_job_delete(request, pk):
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)

    if request.method == 'DELETE':
        job = get_object_or_404(JobPosting, pk=pk)
        job.delete()
        return JsonResponse({'success': True, 'message': 'Job posting deleted.'})

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

            # Case-insensitive username lookup
            user_obj = User.objects.filter(username__iexact=raw_username).first()
            actual_username = user_obj.username if user_obj else raw_username

            user = authenticate(request, username=actual_username, password=password)
            if user is not None and user.is_staff:
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'username': user.username,
                    'is_admin': True,
                    'message': 'Owner login successful!'
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
    return JsonResponse({
        'is_admin': is_admin,
        'username': request.user.username if is_admin else None
    })

@csrf_exempt
def api_jobs(request):
    sync_expired_jobs()

    if request.method == 'GET':
        qs = JobPosting.objects.all().select_related('category')

        query = request.GET.get('q', '').strip()
        if query:
            qs = qs.filter(
                Q(title__icontains=query) | 
                Q(company_name__icontains=query) | 
                Q(skills_required__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query)
            )

        category_slug = request.GET.get('category', '').strip()
        if category_slug and category_slug != 'all':
            qs = qs.filter(category__slug=category_slug)

        job_type = request.GET.get('job_type', '').strip()
        if job_type and job_type != 'all':
            qs = qs.filter(job_type=job_type)

        sort = request.GET.get('sort', 'newest')
        if sort == 'deadline':
            qs = qs.order_by('deadline')
        else:
            qs = qs.order_by('-created_at')

        results = []
        now = timezone.now()
        for j in qs:
            time_left_seconds = max(0, int((j.deadline - now).total_seconds()))
            results.append({
                'id': j.id,
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
            })

        # Pagination Logic (default 3 for homepage, 6 for catalog)
        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1

        try:
            page_size = int(request.GET.get('page_size', 6))
        except ValueError:
            page_size = 6

        total_count = len(results)
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        page = min(max(1, page), total_pages)

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = results[start_idx:end_idx]

        return JsonResponse({
            'jobs': paginated_results,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page,
            'page_size': page_size,
            'has_next': page < total_pages,
            'has_previous': page > 1,
        })

    elif request.method == 'POST':
        if not (request.user.is_authenticated and request.user.is_staff):
            return JsonResponse({'error': 'Unauthorized. Only Kashii Updatez Owner can post opportunities.'}, status=401)

        try:
            data = json.loads(request.body)
            category = get_object_or_404(Category, id=data.get('category_id'))

            deadline = timezone.now() + timedelta(days=3)

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
                posted_by=request.user.username,
                poster_email=request.user.email or "admin@kashiiupdatez.com",
                deadline=deadline,
            )

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
            }
        })
