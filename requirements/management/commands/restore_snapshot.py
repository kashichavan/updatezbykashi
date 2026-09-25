import json
from pathlib import Path
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings
from django.utils import timezone
from requirements.models import Category as JobCategory, JobPosting, JobGroup
from blog.models import Category as BlogCategory, Tag as BlogTag, BlogPost


class Command(BaseCommand):
    help = "Fast bulk-restore of full snapshot into database with active status and refreshed deadlines."

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='backups/kashii_full_snapshot_latest.json',
            help='Path to the backup JSON file'
        )

    def handle(self, *args, **options):
        file_path = Path(options['file'])
        if not file_path.is_absolute():
            file_path = Path(settings.BASE_DIR) / file_path

        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"Backup file not found: {file_path}"))
            return

        self.stdout.write(self.style.NOTICE(f"Loading snapshot from {file_path}..."))
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        now = timezone.now()
        default_deadline = now + timedelta(days=7)
        default_posted_date = timezone.localtime(now).date()

        data_by_model = {}
        for item in data:
            m = item.get('model')
            if m:
                data_by_model.setdefault(m, []).append(item)

        with transaction.atomic():
            # 1. Job Categories
            cat_id_map = {}
            for item in data_by_model.get('requirements.category', []):
                old_pk = item.get('pk')
                f = item.get('fields', {})
                slug = f.get('slug') or f"cat-{old_pk}"
                name = f.get('name') or "Software & Tech"
                obj = JobCategory.objects.filter(slug=slug).first() or JobCategory.objects.filter(name=name).first()
                if not obj:
                    obj = JobCategory.objects.create(
                        name=name,
                        slug=slug,
                        icon=f.get('icon', 'code'),
                        description=f.get('description', '')
                    )
                cat_id_map[old_pk] = obj
                cat_id_map[slug] = obj

            default_cat = JobCategory.objects.filter(slug='software-tech').first() or JobCategory.objects.first()
            if not default_cat:
                default_cat = JobCategory.objects.create(
                    name="Software & Tech",
                    slug="software-tech",
                    icon="code",
                    description="All software engineering and technology opportunities."
                )

            # 2. Blog Categories
            blog_cat_map = {}
            for item in data_by_model.get('blog.category', []):
                old_pk = item.get('pk')
                f = item.get('fields', {})
                slug = f.get('slug') or f"blog-cat-{old_pk}"
                name = f.get('name') or "Engineering"
                obj = BlogCategory.objects.filter(slug=slug).first() or BlogCategory.objects.filter(name=name).first()
                if not obj:
                    obj = BlogCategory.objects.create(
                        name=name,
                        slug=slug,
                        icon=f.get('icon', 'code'),
                        description=f.get('description', ''),
                        color=f.get('color', 'blue'),
                        order=f.get('order', 0)
                    )
                blog_cat_map[old_pk] = obj

            # 3. Blog Tags
            tag_map = {}
            for item in data_by_model.get('blog.tag', []):
                old_pk = item.get('pk')
                f = item.get('fields', {})
                name = f.get('name') or f"tag-{old_pk}"
                slug = f.get('slug') or f"tag-{old_pk}"
                obj = BlogTag.objects.filter(name=name).first() or BlogTag.objects.filter(slug=slug).first()
                if not obj:
                    obj = BlogTag.objects.create(name=name, slug=slug)
                tag_map[old_pk] = obj

            # 4. Job Postings Bulk Upsert
            existing_jobs = {j.id: j for j in JobPosting.objects.all()}
            existing_urls = {j.apply_url: j for j in existing_jobs.values() if j.apply_url}

            jobs_to_create = []
            jobs_to_update = []
            job_id_map = {}

            for item in data_by_model.get('requirements.jobposting', []):
                old_pk = item.get('pk')
                f = item.get('fields', {})
                cat_val = f.get('category')
                resolved_cat = cat_id_map.get(cat_val) or default_cat

                apply_url = f.get('apply_url') or ''
                title = f.get('title') or 'Job Opening'
                company = f.get('company_name') or 'Company'

                # Ensure requirement is ACTIVE and unexpired (at least 7 days from now)
                deadline = f.get('deadline')
                if not deadline:
                    deadline = default_deadline
                posted_date = f.get('posted_date') or default_posted_date

                target_obj = existing_jobs.get(old_pk) or (existing_urls.get(apply_url) if apply_url else None)

                if target_obj:
                    target_obj.title = title
                    target_obj.company_name = company
                    target_obj.company_logo_icon = f.get('company_logo_icon', 'building')
                    target_obj.category = resolved_cat
                    target_obj.job_type = f.get('job_type', 'INTERNSHIP')
                    target_obj.stipend_salary = f.get('stipend_salary', 'Competitive')
                    target_obj.location = f.get('location', 'Pan India')
                    target_obj.is_remote = f.get('is_remote', False)
                    target_obj.skills_required = f.get('skills_required', '')
                    target_obj.apply_url = apply_url
                    target_obj.allow_direct_apply = f.get('allow_direct_apply', True)
                    target_obj.description = f.get('description', '')
                    target_obj.eligibility = f.get('eligibility', '')
                    target_obj.selection_process = f.get('selection_process', '')
                    target_obj.status = 'ACTIVE'  # Reactivate
                    target_obj.deadline = default_deadline  # Refresh deadline
                    target_obj.posted_date = posted_date
                    target_obj.is_featured = f.get('is_featured', False)
                    jobs_to_update.append(target_obj)
                    job_id_map[old_pk] = target_obj
                else:
                    new_job = JobPosting(
                        id=old_pk,
                        title=title,
                        company_name=company,
                        company_logo_icon=f.get('company_logo_icon', 'building'),
                        category=resolved_cat,
                        job_type=f.get('job_type', 'INTERNSHIP'),
                        stipend_salary=f.get('stipend_salary', 'Competitive'),
                        location=f.get('location', 'Pan India'),
                        is_remote=f.get('is_remote', False),
                        skills_required=f.get('skills_required', ''),
                        apply_url=apply_url,
                        allow_direct_apply=f.get('allow_direct_apply', True),
                        description=f.get('description', ''),
                        eligibility=f.get('eligibility', ''),
                        selection_process=f.get('selection_process', ''),
                        status='ACTIVE',  # All seeded requirements ACTIVE
                        deadline=default_deadline,  # Active 7-day window
                        posted_date=posted_date,
                        is_featured=f.get('is_featured', False),
                        views_count=f.get('views_count', 0),
                        applications_count=f.get('applications_count', 0),
                    )
                    jobs_to_create.append(new_job)

            if jobs_to_update:
                JobPosting.objects.bulk_update(
                    jobs_to_update,
                    fields=[
                        'title', 'company_name', 'company_logo_icon', 'category', 'job_type',
                        'stipend_salary', 'location', 'is_remote', 'skills_required', 'apply_url',
                        'allow_direct_apply', 'description', 'eligibility', 'selection_process',
                        'status', 'deadline', 'posted_date', 'is_featured'
                    ],
                    batch_size=200
                )

            if jobs_to_create:
                created_jobs = JobPosting.objects.bulk_create(jobs_to_create, batch_size=200)
                for j in created_jobs:
                    job_id_map[j.id] = j

            # Re-map all jobs
            all_db_jobs = {j.id: j for j in JobPosting.objects.all()}
            for old_pk in [item.get('pk') for item in data_by_model.get('requirements.jobposting', [])]:
                if old_pk in all_db_jobs:
                    job_id_map[old_pk] = all_db_jobs[old_pk]

            # 5. Job Groups Bulk Upsert
            existing_groups = {g.slug: g for g in JobGroup.objects.all()}
            existing_groups_by_id = {g.id: g for g in existing_groups.values()}

            groups_to_create = []
            groups_to_update = []
            group_jobs_map = {}

            for item in data_by_model.get('requirements.jobgroup', []):
                old_pk = item.get('pk')
                f = item.get('fields', {})
                slug = f.get('slug') or f"group-{old_pk}"
                name = f.get('name') or "Hiring Drive"
                jobs_pks = f.get('jobs', [])

                target_grp = existing_groups.get(slug) or existing_groups_by_id.get(old_pk)
                if target_grp:
                    target_grp.name = name
                    target_grp.slug = slug
                    target_grp.banner_tag = f.get('banner_tag', '🔥 HIRING DRIVE')
                    target_grp.description = f.get('description', '')
                    target_grp.posted_date = f.get('posted_date') or default_posted_date
                    target_grp.deadline = default_deadline  # Refresh group deadline
                    target_grp.is_active = True  # Reactivate group
                    groups_to_update.append(target_grp)
                    group_jobs_map[target_grp.id] = jobs_pks
                else:
                    new_grp = JobGroup(
                        id=old_pk,
                        name=name,
                        slug=slug,
                        banner_tag=f.get('banner_tag', '🔥 HIRING DRIVE'),
                        description=f.get('description', ''),
                        posted_date=f.get('posted_date') or default_posted_date,
                        deadline=default_deadline,  # Active deadline
                        is_active=True,
                    )
                    groups_to_create.append(new_grp)
                    group_jobs_map[old_pk] = jobs_pks

            if groups_to_update:
                JobGroup.objects.bulk_update(
                    groups_to_update,
                    fields=['name', 'slug', 'banner_tag', 'description', 'posted_date', 'deadline', 'is_active'],
                    batch_size=100
                )

            if groups_to_create:
                JobGroup.objects.bulk_create(groups_to_create, batch_size=100)

            # Re-map all group M2M associations in bulk
            ThroughModel = JobGroup.jobs.through
            ThroughModel.objects.all().delete()

            m2m_relations = []
            all_db_groups = {g.id: g for g in JobGroup.objects.all()}
            for grp_id, j_pks in group_jobs_map.items():
                if grp_id in all_db_groups:
                    for j_pk in j_pks:
                        if j_pk in job_id_map:
                            m2m_relations.append(ThroughModel(jobgroup_id=grp_id, jobposting_id=job_id_map[j_pk].id))

            if m2m_relations:
                ThroughModel.objects.bulk_create(m2m_relations, batch_size=500, ignore_conflicts=True)

            # 6. Blog Posts Bulk Upsert
            existing_blogs = {b.slug: b for b in BlogPost.objects.all()}
            blogs_to_create = []
            blogs_to_update = []
            blog_tags_map = {}

            for item in data_by_model.get('blog.blogpost', []):
                old_pk = item.get('pk')
                f = item.get('fields', {})
                slug = f.get('slug')
                title = f.get('title')
                cat_val = f.get('category')
                resolved_cat = blog_cat_map.get(cat_val)
                tag_pks = f.get('tags', [])

                target_blog = existing_blogs.get(slug)
                if target_blog:
                    target_blog.title = title
                    target_blog.category = resolved_cat
                    target_blog.excerpt = f.get('excerpt', '')
                    target_blog.content = f.get('content', '')
                    target_blog.cover_image_url = f.get('cover_image_url', '')
                    target_blog.author_name = f.get('author_name', 'Kashinath Chavan')
                    target_blog.author_title = f.get('author_title', 'Software Architect')
                    target_blog.is_published = True
                    target_blog.is_featured = f.get('is_featured', False)
                    blogs_to_update.append(target_blog)
                    blog_tags_map[target_blog.id] = tag_pks
                else:
                    new_blog = BlogPost(
                        id=old_pk,
                        title=title,
                        slug=slug,
                        category=resolved_cat,
                        excerpt=f.get('excerpt', ''),
                        content=f.get('content', ''),
                        cover_image_url=f.get('cover_image_url', ''),
                        author_name=f.get('author_name', 'Kashinath Chavan'),
                        author_title=f.get('author_title', 'Software Architect'),
                        is_published=True,
                        is_featured=f.get('is_featured', False),
                        views_count=f.get('views_count', 0),
                        likes_count=f.get('likes_count', 0),
                    )
                    blogs_to_create.append(new_blog)
                    blog_tags_map[old_pk] = tag_pks

            if blogs_to_update:
                BlogPost.objects.bulk_update(
                    blogs_to_update,
                    fields=['title', 'category', 'excerpt', 'content', 'cover_image_url', 'author_name', 'author_title', 'is_published', 'is_featured'],
                    batch_size=100
                )

            if blogs_to_create:
                BlogPost.objects.bulk_create(blogs_to_create, batch_size=100)

            # Blog Tag M2M links
            BlogTagThrough = BlogPost.tags.through
            BlogTagThrough.objects.all().delete()
            tag_relations = []
            all_db_blogs = {b.id: b for b in BlogPost.objects.all()}
            for b_id, t_pks in blog_tags_map.items():
                if b_id in all_db_blogs:
                    for t_pk in t_pks:
                        if t_pk in tag_map:
                            tag_relations.append(BlogTagThrough(blogpost_id=b_id, tag_id=tag_map[t_pk].id))

            if tag_relations:
                BlogTagThrough.objects.bulk_create(tag_relations, batch_size=500, ignore_conflicts=True)

        # Align Postgres Sequences
        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                for ModelClass in [JobPosting, JobGroup, JobCategory, BlogPost, BlogCategory, BlogTag]:
                    table = ModelClass._meta.db_table
                    pk_name = ModelClass._meta.pk.name
                    if ModelClass._meta.pk.get_internal_type() in ['AutoField', 'BigAutoField', 'SmallAutoField']:
                        try:
                            cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', '{pk_name}'), coalesce(max({pk_name}), 1)) FROM {table};")
                        except Exception:
                            pass

        total_jobs = JobPosting.objects.filter(status='ACTIVE', deadline__gt=timezone.now()).count()
        total_groups = JobGroup.objects.filter(is_active=True, deadline__gt=timezone.now()).count()
        self.stdout.write(self.style.SUCCESS(
            f"🎉 FAST RESTORE & REACTIVATION COMPLETED!\n"
            f"  - Active Jobs: {total_jobs} (All Unexpired & Accepting Applications)\n"
            f"  - Active Groups: {total_groups} (All Unexpired)\n"
            f"  - Blog Posts: {BlogPost.objects.count()}\n"
            f"  - Tags: {BlogTag.objects.count()}\n"
            f"  - Group-Job Links: {JobGroup.jobs.through.objects.count()}"
        ))
