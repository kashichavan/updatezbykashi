from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from requirements.models import Category, JobPosting, StudentApplication

class Command(BaseCommand):
    help = 'Seeds student job postings, internship requirements, and student applications.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Seeding database with Student Jobs & Requirements...'))

        # Create Admin Superuser if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Created admin user: username=admin, password=admin123'))

        # Clear existing data
        StudentApplication.objects.all().delete()
        JobPosting.objects.all().delete()
        Category.objects.all().delete()

        # Categories
        categories_data = [
            {'name': 'Software & Tech', 'slug': 'software-tech', 'icon': 'code', 'description': 'Full-stack, Backend, Frontend, and Mobile Engineering roles.'},
            {'name': 'Data & AI', 'slug': 'data-ai', 'icon': 'database', 'description': 'Machine Learning, Data Science, Data Engineering, and Analytics.'},
            {'name': 'Design & Media', 'slug': 'design-media', 'icon': 'palette', 'description': 'UI/UX Design, Product Design, Graphic & Video Content.'},
            {'name': 'Internships & Co-ops', 'slug': 'internships', 'icon': 'academic-cap', 'description': 'Summer 2026 internships, winter co-ops, and student trainees.'},
            {'name': 'Business & Product', 'slug': 'business-product', 'icon': 'chart-bar', 'description': 'Product Management, Business Analyst, and Growth Marketing.'},
            {'name': 'Remote Gigs', 'slug': 'remote-gigs', 'icon': 'globe', 'description': 'Flexible hourly contracts, student freelance gigs, and project work.'},
        ]

        categories_objs = {}
        for cdata in categories_data:
            cat = Category.objects.create(**cdata)
            categories_objs[cat.slug] = cat

        now = timezone.now()

        # Job Postings Seed Data
        jobs_seed = [
            {
                'title': 'Junior Software Engineer (2025/2026 Batch)',
                'company_name': 'Stripe',
                'company_logo_icon': 'credit-card',
                'category': categories_objs['software-tech'],
                'job_type': 'FULL_TIME',
                'stipend_salary': '$115,000 / year',
                'location': 'Remote / San Francisco',
                'is_remote': True,
                'skills_required': 'Python, Django, React, PostgreSQL, REST APIs',
                'apply_url': 'https://stripe.com/jobs/university-software-engineer-2026',
                'allow_direct_apply': True,
                'description': 'Join the Stripe Infrastructure & Developer Experience team. You will work on API reliability, merchant dashboard features, and high-throughput transaction pipelines.',
                'eligibility': 'Graduating in 2025 or 2026 with B.S./M.S. in Computer Science or related fields.',
                'posted_by': 'Stripe University Recruiting',
                'poster_email': 'university-recruiting@stripe.com',
                'status': 'ACTIVE',
                'views_count': 342,
                'applications_count': 18,
                'is_featured': True,
                'deadline': now + timedelta(days=14),
            },
            {
                'title': 'Backend Developer Intern - Summer 2026',
                'company_name': 'Vercel',
                'company_logo_icon': 'server',
                'category': categories_objs['internships'],
                'job_type': 'INTERNSHIP',
                'stipend_salary': '$45 / hour ($7,200/mo)',
                'location': 'Remote',
                'is_remote': True,
                'skills_required': 'Node.js, TypeScript, Next.js, Go, Serverless Architecture',
                'apply_url': 'https://vercel.com/careers/backend-intern-2026',
                'allow_direct_apply': True,
                'description': 'We are looking for a passionate Backend Developer Intern to help build edge networking infrastructure, analytics collection, and continuous deployment workflows.',
                'eligibility': 'Enrolled in an accredited University degree program with expected graduation 2026-2027.',
                'posted_by': 'Vercel Talent Team',
                'poster_email': 'careers@vercel.com',
                'status': 'ACTIVE',
                'views_count': 512,
                'applications_count': 34,
                'is_featured': True,
                'deadline': now + timedelta(days=7),
            },
            {
                'title': 'AI & Data Science Student Trainee',
                'company_name': 'Databricks',
                'company_logo_icon': 'cpu',
                'category': categories_objs['data-ai'],
                'job_type': 'INTERNSHIP',
                'stipend_salary': '$50 / hour',
                'location': 'Hybrid - Seattle, WA',
                'is_remote': False,
                'skills_required': 'Python, PyTorch, SQL, Apache Spark, Scikit-learn',
                'apply_url': 'https://databricks.com/company/careers/ai-internship',
                'allow_direct_apply': True,
                'description': 'Work alongside world-class Machine Learning researchers. Help benchmark Large Language Models, build data cleaning pipelines, and deploy LLM serving endpoints.',
                'eligibility': 'Strong foundations in Data Structures, Linear Algebra, and Machine Learning algorithms.',
                'posted_by': 'Databricks Campus Outreach',
                'poster_email': 'campus@databricks.com',
                'status': 'ACTIVE',
                'views_count': 280,
                'applications_count': 12,
                'is_featured': False,
                'deadline': now + timedelta(days=10),
            },
            {
                'title': 'UI/UX Product Design Apprentice',
                'company_name': 'Figma',
                'company_logo_icon': 'palette',
                'category': categories_objs['design-media'],
                'job_type': 'INTERNSHIP',
                'stipend_salary': '$40 / hour',
                'location': 'San Francisco, CA / Remote',
                'is_remote': True,
                'skills_required': 'Figma, Design Systems, User Research, Prototyping',
                'apply_url': 'https://figma.com/careers/design-apprentice-2026',
                'allow_direct_apply': True,
                'description': 'Craft intuitive UI micro-interactions, conduct user feedback interviews, and contribute to Figma design system components.',
                'eligibility': 'Portfolio required demonstrating user-centered product design projects.',
                'posted_by': 'Figma Design Team',
                'poster_email': 'design-careers@figma.com',
                'status': 'ACTIVE',
                'views_count': 195,
                'applications_count': 9,
                'is_featured': False,
                'deadline': now + timedelta(days=5),
            },
            {
                'title': 'Campus Ambassador & Growth Associate',
                'company_name': 'Notion',
                'company_logo_icon': 'book-open',
                'category': categories_objs['business-product'],
                'job_type': 'PART_TIME',
                'stipend_salary': '$25 / hour + Tech Perks',
                'location': 'On Campus (University-wide)',
                'is_remote': False,
                'skills_required': 'Event Planning, Social Media, Student Engagement, Communication',
                'apply_url': 'https://notion.so/careers/campus-ambassador',
                'allow_direct_apply': True,
                'description': 'Represent Notion on your university campus. Host productivity workshops, distribute swags, and onboard student organizations.',
                'eligibility': 'Current active undergraduate student with strong campus involvement.',
                'posted_by': 'Notion Student Program',
                'poster_email': 'students@m.notion.so',
                'status': 'ACTIVE',
                'views_count': 140,
                'applications_count': 22,
                'is_featured': False,
                'deadline': now + timedelta(days=12),
            },
        ]

        created_jobs = []
        for jdata in jobs_seed:
            job = JobPosting.objects.create(**jdata)
            created_jobs.append(job)

        # Student Applications Seed
        apps_seed = [
            {
                'job': created_jobs[0], # Stripe
                'student_name': 'Rohan Sharma',
                'student_email': 'rohan.sharma@stanford.edu',
                'student_phone': '+1 650-555-0192',
                'degree_major': 'B.S. Computer Science',
                'graduation_year': '2026',
                'resume_url': 'https://drive.google.com/file/d/demo-rohan-resume/view',
                'github_linkedin': 'https://github.com/rohansharma-dev',
                'cover_note': 'Built full-stack Django SaaS apps with Stripe payment integration and row-level multi-tenancy. Extremely excited about Stripe platform architecture!',
                'status': 'SHORTLISTED',
            },
            {
                'job': created_jobs[1], # Vercel
                'student_name': 'Ananya Patel',
                'student_email': 'ananya.p@mit.edu',
                'student_phone': '+1 617-555-0144',
                'degree_major': 'M.S. Artificial Intelligence',
                'graduation_year': '2026',
                'resume_url': 'https://drive.google.com/file/d/demo-ananya-resume/view',
                'github_linkedin': 'https://linkedin.com/in/ananyapatel-mit',
                'cover_note': 'Top contributor to open-source Next.js libraries. Strong background in TypeScript and Go edge workers.',
                'status': 'REVIEWED',
            },
        ]

        for adata in apps_seed:
            StudentApplication.objects.create(**adata)

        self.stdout.write(self.style.SUCCESS('Successfully seeded Student Jobs, Requirements, and Applications!'))
