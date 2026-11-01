import json
from datetime import timedelta
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from .ai_engine import _basic_bullet_cleanup, polish_resume_bullet
from .indian_project_service import serialize_demo_project
from .models import IndianDemoProject
from .management.commands.restore_snapshot import listing_deadline


class ListingFreshnessTests(SimpleTestCase):
    def test_old_listing_is_already_closed(self):
        now = timezone.now()
        posted = (now - timedelta(days=30)).date()
        self.assertLess(listing_deadline(str(posted), now), now)

    def test_recent_listing_stays_open(self):
        now = timezone.now()
        posted = (now - timedelta(days=2)).date()
        self.assertGreater(listing_deadline(str(posted), now), now)

    def test_unreadable_date_uses_fallback(self):
        now = timezone.now()
        self.assertEqual(listing_deadline('not-a-date', now), now)


class BulletPolishTests(SimpleTestCase):
    def _polish(self, *responses):
        with patch('requirements.ai_engine.call_groq_chat', side_effect=[json.dumps(r) for r in responses]):
            return polish_resume_bullet('built a login page', tech_stack='Django')

    def test_retries_when_first_answer_is_rejected(self):
        data = self._polish(
            {'polished': 'Built a robust login page with Django.'},
            {'polished': 'Built a login page with Django.'},
        )
        self.assertTrue(data['ai'])
        self.assertEqual(data['polished'], 'Built a login page with Django.')

    def test_rejects_tools_the_candidate_never_listed(self):
        answer = {'polished': 'Built a login page with Django and Redis.'}
        data = self._polish(answer, answer)
        self.assertFalse(data['ai'])
        self.assertNotIn('Redis', data['polished'])

    def test_rejects_invented_numbers(self):
        answer = {'polished': 'Built a login page used by 500 students.'}
        data = self._polish(answer, answer)
        self.assertFalse(data['ai'])
        self.assertNotIn('500', data['polished'])

    def test_offline_cleanup_reads_like_a_sentence(self):
        self.assertEqual(_basic_bullet_cleanup('worked on dashboard'), 'Developed dashboard.')
        self.assertEqual(_basic_bullet_cleanup('- built a login page.'), 'Built a login page.')


class DemoProjectLinkTests(TestCase):
    def test_demo_project_never_exposes_a_repository(self):
        project = IndianDemoProject.objects.create(
            slug='demo', title='Demo', location_city='Pune', location_state='Maharashtra',
            industry='Tech', description='Demo', github_url='https://github.com/fullstack-mastery/demo',
        )
        data = serialize_demo_project(project)
        self.assertEqual(data['github_url'], '')
        self.assertEqual(data['github_repo'], '')


class RetiredPagesTests(TestCase):
    def test_blog_and_guides_redirect_home(self):
        for path in ('/blog/', '/blog/some-post/', '/guides/', '/guides/some-guide/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 301, path)
            self.assertEqual(response['Location'], '/', path)

    def test_sitemap_has_no_retired_links(self):
        body = self.client.get('/sitemap.xml').content.decode()
        self.assertNotIn('/blog/', body)
        self.assertNotIn('/guides/', body)

    def test_home_has_no_fake_alert_form(self):
        body = self.client.get('/').content.decode()
        self.assertNotIn('formJobAlerts', body)
        self.assertNotIn('100% Verified', body)


JOB_POST = 'Python Developer\nWe need Python, Django, PostgreSQL and Docker experience for our backend team.'


class ResumeFromJobPostTests(TestCase):
    def _post(self, **payload):
        with patch('requirements.ai_engine.call_groq_chat', side_effect=ValueError('offline')):
            return self.client.post(
                '/api/resume/from-job-description/',
                data=json.dumps({'job_description': JOB_POST, **payload}),
                content_type='application/json',
            ).json()

    def test_preview_splits_known_and_missing_skills(self):
        data = self._post(preview=True, candidate={'skills': {'Languages': 'Python, Django'}})
        self.assertEqual(data['job_title'], 'Python Developer')
        self.assertEqual(sorted(data['matched_skills']), ['Django', 'Python'])
        self.assertEqual(sorted(data['missing_skills']), ['Docker', 'PostgreSQL'])

    def test_blank_candidate_gets_nothing_invented(self):
        resume = self._post(candidate={})['resume']
        self.assertEqual(resume['name'], '')
        self.assertEqual(resume['projects'], [])
        self.assertFalse(resume['education'])
        self.assertEqual(resume['certifications'], [])
        self.assertEqual(resume['skills'], {})

    def test_only_confirmed_skills_are_added(self):
        data = self._post(
            candidate={'skills': {'Languages': 'Python'}},
            confirmed_skills=['Docker'],
        )
        text = json.dumps(data['resume']['skills'])
        self.assertIn('Docker', text)
        self.assertNotIn('PostgreSQL', text)
        self.assertEqual(data['missing_skills'], ['Django', 'PostgreSQL'])

    def test_score_is_not_forced_up(self):
        self.assertLess(self._post(candidate={})['ats_score'], 90)

    def test_practice_project_is_labelled_and_number_free(self):
        from .comprehensive_projects_catalog import ALL_PROJECTS
        title = ALL_PROJECTS[0]['title']
        project = self._post(candidate={}, practice_projects=[title])['resume']['projects'][0]
        self.assertIn('(Practice Project)', project['title'])
        self.assertEqual(project['github_url'], '')
        self.assertNotRegex(project['bullets'][0], r'\d+%')

    def test_old_generator_address_redirects_to_builder(self):
        response = self.client.get('/tools/job-description-generator/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], '/resume-builder/?paste_jd=1')


class CompanyPeopleTests(SimpleTestCase):
    def test_reads_person_from_a_real_profile_result(self):
        from .services.recruiter_finder import _person_from_linkedin_result
        person = _person_from_linkedin_result({
            'url': 'https://in.linkedin.com/in/asha-rao?trk=x',
            'title': 'Asha Rao - Technical Recruiter - Freecharge | LinkedIn',
            'snippet': '',
        }, 'Freecharge')
        self.assertEqual(person['name'], 'Asha Rao')
        self.assertEqual(person['url'], 'https://in.linkedin.com/in/asha-rao')

    def test_ignores_results_that_are_not_recruiters_at_the_company(self):
        from .services.recruiter_finder import _person_from_linkedin_result
        for item in (
            {'url': 'https://www.healthline.com/health/mupirocin', 'title': 'Mupirocin', 'snippet': 'Freecharge recruiter'},
            {'url': 'https://www.linkedin.com/in/x', 'title': 'Ravi Kumar - Engineer - Freecharge', 'snippet': ''},
            {'url': 'https://www.linkedin.com/in/y', 'title': 'Asha Rao - Recruiter - Acme', 'snippet': ''},
            {'url': 'https://www.linkedin.com/in/z', 'title': 'Supriya S - APAC Recruiter', 'snippet': 'Formerly at Freecharge'},
        ):
            self.assertIsNone(_person_from_linkedin_result(item, 'Freecharge'))
