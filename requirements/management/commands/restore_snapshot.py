import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connection
from django.conf import settings
from requirements.models import Category as JobCategory, JobPosting, JobGroup
from blog.models import Category as BlogCategory, Tag as BlogTag, BlogPost


class Command(BaseCommand):
    help = "Safely restores and upserts a full backup snapshot JSON fixture into the connected database."

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

        data_by_model = {}
        for item in data:
            m = item.get('model')
            if m:
                data_by_model.setdefault(m, []).append(item)

        # 1. Categories
        cat_id_map = {}
        for item in data_by_model.get('requirements.category', []):
            old_pk = item.get('pk')
            f = item.get('fields', {})
            slug = f.get('slug')
            name = f.get('name')
            obj = JobCategory.objects.filter(slug=slug).first() or JobCategory.objects.filter(name=name).first()
            if not obj:
                obj = JobCategory.objects.create(name=name, slug=slug, icon=f.get('icon', 'code'), description=f.get('description', ''))
            cat_id_map[old_pk] = obj
            cat_id_map[slug] = obj

        default_cat = JobCategory.objects.filter(slug='software-engineering').first() or JobCategory.objects.first()

        # 2. Blog Categories
        blog_cat_map = {}
        for item in data_by_model.get('blog.category', []):
            old_pk = item.get('pk')
            f = item.get('fields', {})
            slug = f.get('slug')
            name = f.get('name')
            obj = BlogCategory.objects.filter(slug=slug).first() or BlogCategory.objects.filter(name=name).first()
            if not obj:
                obj = BlogCategory.objects.create(
                    name=name, slug=slug, icon=f.get('icon', 'code'),
                    description=f.get('description', ''), color=f.get('color', 'blue'),
                    order=f.get('order', 0)
                )
            blog_cat_map[old_pk] = obj

        # 3. Blog Tags
        tag_map = {}
        for item in data_by_model.get('blog.tag', []):
            old_pk = item.get('pk')
            f = item.get('fields', {})
            name = f.get('name')
            slug = f.get('slug')
            obj = BlogTag.objects.filter(name=name).first() or BlogTag.objects.filter(slug=slug).first()
            if not obj:
                obj = BlogTag.objects.create(name=name, slug=slug)
            tag_map[old_pk] = obj

        # 4. Job Postings
        jobs_loaded = 0
        job_id_map = {}
        for item in data_by_model.get('requirements.jobposting', []):
            old_pk = item.get('pk')
            f = item.get('fields', {})
            cat_val = f.get('category')
            resolved_cat = cat_id_map.get(cat_val) or default_cat

            apply_url = f.get('apply_url', '')
            title = f.get('title', '')
            company = f.get('company_name', '')

            obj = None
            if old_pk:
                obj = JobPosting.objects.filter(pk=old_pk).first()
            if not obj and apply_url:
                obj = JobPosting.objects.filter(apply_url=apply_url).first()

            job_kwargs = {
                'title': title,
                'company_name': company,
                'company_logo_icon': f.get('company_logo_icon', 'building'),
                'category': resolved_cat,
                'job_type': f.get('job_type', 'Full-time'),
                'stipend_salary': f.get('stipend_salary', 'Competitive Salary'),
                'location': f.get('location', 'Pan India'),
                'is_remote': f.get('is_remote', False),
                'skills_required': f.get('skills_required', ''),
                'apply_url': apply_url,
                'allow_direct_apply': f.get('allow_direct_apply', True),
                'description': f.get('description', ''),
                'eligibility': f.get('eligibility', ''),
                'selection_process': f.get('selection_process', ''),
                'status': f.get('status', 'ACTIVE'),
                'is_featured': f.get('is_featured', False),
                'views_count': f.get('views_count', 0),
                'applications_count': f.get('applications_count', 0),
                'posted_date': f.get('posted_date'),
                'deadline': f.get('deadline'),
            }

            if obj:
                for k, v in job_kwargs.items():
                    setattr(obj, k, v)
                obj.save()
            else:
                try:
                    obj = JobPosting.objects.create(pk=old_pk, **job_kwargs)
                except Exception:
                    obj = JobPosting.objects.create(**job_kwargs)

            job_id_map[old_pk] = obj
            jobs_loaded += 1

        # 5. Job Groups
        groups_loaded = 0
        for item in data_by_model.get('requirements.jobgroup', []):
            old_pk = item.get('pk')
            f = item.get('fields', {})
            slug = f.get('slug')
            name = f.get('name')
            jobs_pks = f.get('jobs', [])

            obj = JobGroup.objects.filter(slug=slug).first()
            if not obj and old_pk:
                obj = JobGroup.objects.filter(pk=old_pk).first()

            grp_kwargs = {
                'name': name,
                'slug': slug,
                'banner_tag': f.get('banner_tag', '🔥 HIRING DRIVE'),
                'description': f.get('description', ''),
                'posted_date': f.get('posted_date'),
                'deadline': f.get('deadline'),
                'is_active': f.get('is_active', True),
                'custom_css': f.get('custom_css', ''),
            }

            if obj:
                for k, v in grp_kwargs.items():
                    setattr(obj, k, v)
                obj.save()
            else:
                try:
                    obj = JobGroup.objects.create(pk=old_pk, **grp_kwargs)
                except Exception:
                    obj = JobGroup.objects.create(**grp_kwargs)

            # Link jobs
            mapped_jobs = [job_id_map[jpk] for jpk in jobs_pks if jpk in job_id_map]
            if mapped_jobs:
                obj.jobs.set(mapped_jobs)
            groups_loaded += 1

        # 6. Blog Posts
        blogs_loaded = 0
        for item in data_by_model.get('blog.blogpost', []):
            old_pk = item.get('pk')
            f = item.get('fields', {})
            slug = f.get('slug')
            title = f.get('title')
            cat_val = f.get('category')
            resolved_cat = blog_cat_map.get(cat_val)
            tag_pks = f.get('tags', [])

            obj = BlogPost.objects.filter(slug=slug).first()
            if not obj and old_pk:
                obj = BlogPost.objects.filter(pk=old_pk).first()

            blog_kwargs = {
                'title': title,
                'slug': slug,
                'category': resolved_cat,
                'excerpt': f.get('excerpt', ''),
                'content': f.get('content', ''),
                'cover_image_url': f.get('cover_image_url', ''),
                'author_name': f.get('author_name', 'Kashinath Chavan'),
                'author_title': f.get('author_title', 'Software Architect'),
                'author_avatar_url': f.get('author_avatar_url', ''),
                'is_published': f.get('is_published', True),
                'is_featured': f.get('is_featured', False),
                'views_count': f.get('views_count', 0),
                'likes_count': f.get('likes_count', 0),
            }

            if obj:
                for k, v in blog_kwargs.items():
                    setattr(obj, k, v)
                obj.save()
            else:
                try:
                    obj = BlogPost.objects.create(pk=old_pk, **blog_kwargs)
                except Exception:
                    obj = BlogPost.objects.create(**blog_kwargs)

            mapped_tags = [tag_map[tpk] for tpk in tag_pks if tpk in tag_map]
            if mapped_tags:
                obj.tags.set(mapped_tags)
            blogs_loaded += 1

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

        self.stdout.write(self.style.SUCCESS(
            f"🎉 FULL RESTORE COMPLETED! Restored: {jobs_loaded} Jobs, {groups_loaded} Groups, {blogs_loaded} Blog Posts, {len(cat_id_map)} Categories, {len(tag_map)} Tags into new Neon database!"
        ))
