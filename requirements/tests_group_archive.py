import json
import tempfile
from datetime import timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .group_archive import export_groups, merge_archive
from .models import Category, JobGroup, JobPosting


class GroupArchiveTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Software Engineering', slug='software-engineering')
        self.job = JobPosting.objects.create(
            title='Backend Intern', company_name='Acme', category=self.category,
            description='Build APIs', stipend_salary='Paid', skills_required='Python',
            deadline=timezone.now() + timedelta(days=5),
            poster_email='private@example.com', posted_by='Private Person',
        )
        self.group = JobGroup.objects.create(name='Drive', slug='drive-1', is_active=True)
        self.group.jobs.add(self.job)
        self.since = timezone.now() - timedelta(days=1)

    def _wipe(self):
        JobGroup.objects.all().delete()
        JobPosting.objects.all().delete()

    def test_round_trip_restores_group_link_and_jobs(self):
        data = json.loads(json.dumps(export_groups(self.since)))
        created_at, job_uuid = self.group.created_at, self.job.uuid
        self._wipe()

        self.assertEqual(merge_archive(data), {'groups': 1, 'jobs': 1})

        group = JobGroup.objects.get(slug='drive-1')
        self.assertEqual(group.created_at, created_at)
        self.assertEqual(list(group.jobs.values_list('uuid', flat=True)), [job_uuid])
        self.assertEqual(self.client.get('/group/drive-1/').status_code, 200)

    def test_merge_never_changes_an_existing_group(self):
        data = json.loads(json.dumps(export_groups(self.since)))
        data['groups'][0].update(name='Overwritten', job_uuids=[], is_active=False)

        self.assertEqual(merge_archive(data), {'groups': 0, 'jobs': 0})

        self.group.refresh_from_db()
        self.assertEqual(self.group.name, 'Drive')
        self.assertTrue(self.group.is_active)
        self.assertEqual(self.group.jobs.count(), 1)

    def test_merge_twice_adds_nothing_the_second_time(self):
        data = json.loads(json.dumps(export_groups(self.since)))
        self._wipe()
        merge_archive(data)
        self.assertEqual(merge_archive(data), {'groups': 0, 'jobs': 0})

    def test_restoring_a_job_does_not_trigger_save_side_effects(self):
        data = json.loads(json.dumps(export_groups(self.since)))
        self._wipe()
        with patch('requirements.models.JobPosting.save') as save:
            merge_archive(data)
        save.assert_not_called()

    def test_export_holds_no_personal_details(self):
        text = json.dumps(export_groups(self.since))
        self.assertNotIn('private@example.com', text)
        self.assertNotIn('Private Person', text)

    def test_api_requires_a_valid_since(self):
        self.assertEqual(self.client.get('/api/groups/archive/').status_code, 400)
        self.assertEqual(self.client.get('/api/groups/archive/', {'since': 'nope'}).status_code, 400)
        response = self.client.get('/api/groups/archive/', {'since': self.since.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['groups'][0]['slug'], 'drive-1')

    def test_live_failure_does_not_stop_the_deploy(self):
        with patch('requirements.management.commands.preserve_groups.fetch_live_groups', side_effect=OSError('down')), \
                patch('requirements.management.commands.preserve_groups.load_archive_file', return_value={}):
            call_command('preserve_groups')
        self.assertTrue(JobGroup.objects.filter(slug='drive-1').exists())


class RestoreSnapshotKeepsLinksTests(TestCase):
    def test_id_clash_does_not_rename_a_live_group(self):
        Category.objects.create(name='Software Engineering', slug='software-engineering')
        live = JobGroup.objects.create(name='Live', slug='live-link')
        snapshot = [{'model': 'requirements.jobgroup', 'pk': live.pk, 'fields': {
            'name': 'From snapshot', 'slug': 'old-link', 'posted_date': '2026-10-01', 'jobs': [],
        }}]
        with tempfile.NamedTemporaryFile('w', suffix='.json') as handle:
            json.dump(snapshot, handle)
            handle.flush()
            call_command('restore_snapshot', file=handle.name, verbosity=0)

        live.refresh_from_db()
        self.assertEqual(live.slug, 'live-link')
        self.assertEqual(live.name, 'Live')
        self.assertTrue(JobGroup.objects.filter(slug='old-link').exists())
