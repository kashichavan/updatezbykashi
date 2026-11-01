"""
End-to-end check: python manage.py publish_test_story [--job ID] [--dry-run]

Publishes one real story, so it first confirms the image is publicly fetchable.
"""
import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from requirements.models import JobPosting
from requirements.services.instagram_story import InstagramStoryPublisher


class Command(BaseCommand):
    help = 'Publishes one story for the latest (or given) job and confirms it on Instagram.'

    def add_arguments(self, parser):
        parser.add_argument('--job', type=int, help='Job ID. Defaults to the latest job.')
        parser.add_argument('--base-url', default='https://kashiiupdatez.online')
        parser.add_argument('--dry-run', action='store_true', help='Run the checks without publishing.')

    def handle(self, *args, **options):
        jobs = JobPosting.objects.order_by('-id')
        job = jobs.filter(id=options['job']).first() if options['job'] else jobs.first()
        if not job:
            raise CommandError('Job not found.')
        self.stdout.write(f'Job #{job.id}: {job.title} at {job.company_name}')

        if not settings.INSTAGRAM_ACCESS_TOKEN:
            raise CommandError('INSTAGRAM_ACCESS_TOKEN is empty. Run setup_instagram_token first.')

        # IDs can drift between local and production, so confirm it is the same job.
        detail = requests.get(f"{options['base_url']}/api/jobs/{job.id}/", timeout=60)
        if detail.status_code != 200 or job.title not in detail.text or job.company_name not in detail.text:
            raise CommandError(f'Job #{job.id} on production does not match the local job. Nothing was published.')

        url = f"{options['base_url']}/api/jobs/{job.id}/ig-story-image/?v={int(time.time())}"
        resp = requests.get(url, timeout=60)
        content_type = resp.headers.get('Content-Type', '')
        if resp.status_code != 200 or content_type != 'image/jpeg':
            raise CommandError(
                f'{url} returned {resp.status_code} {content_type}. Instagram needs a public JPEG, '
                'so deploy the current code first.')
        self.stdout.write(self.style.SUCCESS(f'Public image OK ({len(resp.content)} bytes).'))

        if options['dry_run']:
            self.stdout.write('Dry run: nothing was published.')
            return

        publisher = InstagramStoryPublisher()
        result = publisher.publish_job_story(job, base_url=options['base_url'])
        if not result.get('success'):
            raise CommandError(f"{result.get('error')}: {result.get('message')}")

        resp = requests.get(f"{publisher.base_graph_url}/{result['media_id']}", timeout=30, params={
            'fields': 'media_product_type,permalink,timestamp', 'access_token': publisher.access_token})
        media = resp.json()
        if resp.status_code != 200 or media.get('media_product_type') != 'STORY':
            raise CommandError(f"Published {result['media_id']}, but could not confirm it as a story.")
        self.stdout.write(self.style.SUCCESS(f"Story live: {result['media_id']} {media.get('permalink', '')}"))
