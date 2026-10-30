"""
The live editor must not hand a stranger somebody else's identity.

Role templates (summary, skills, education structure) are fine to preload — they
are suggestions. A name, email, phone or profile URL is a fact about a specific
person, and the export buttons will happily turn it into a PDF a recruiter reads.
"""

import json
import re
from types import SimpleNamespace
from unittest.mock import patch

from django.test import Client, TestCase

from requirements.models import Category, JobPosting

PERSONAL = [
    'kashinath@example.com',
    '+91 98765 43210',
    'kashinath-chavan',
    'github.com/kashichavan',
    'Kashinath Chavan',
]

# base.html carries the site owner's schema.org profile (sameAs), which is
# legitimate page chrome on every page. The resume editor's own payload is what
# this module guards, so the JSON-LD block is removed before asserting.
LD_JSON = re.compile(r'<script[^>]+type="application/ld\+json"[^>]*>.*?</script>', re.S)


def page_without_site_schema(response):
    return LD_JSON.sub('', response.content.decode())


class EditorShipsNoIdentityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Engineering", slug="eng-editor")
        self.job = JobPosting.objects.create(
            title="Backend Engineer",
            company_name="Acme Corp",
            category=self.category,
            skills_required="Python, Django",
            description="Backend work.",
            status='ACTIVE',
        )

    def test_editor_page_has_no_seeded_person(self):
        res = self.client.get('/resume/')
        self.assertEqual(res.status_code, 200)
        html = page_without_site_schema(res)
        for value in PERSONAL:
            self.assertNotIn(value, html, f"editor exposes {value!r}")

    def test_editor_page_with_job_has_no_seeded_person(self):
        res = self.client.get(f'/resume/?job_id={self.job.uuid}')
        self.assertEqual(res.status_code, 200)
        html = page_without_site_schema(res)
        for value in PERSONAL:
            self.assertNotIn(value, html, f"editor exposes {value!r}")

    def test_editor_with_a_job_tailors_automatically_and_offers_one_action(self):
        res = self.client.get(f'/resume/?job_id={self.job.uuid}')
        html = page_without_site_schema(res)
        self.assertIn('id="targetJobBanner"', html)
        self.assertIn(f'data-job-id="{self.job.uuid}"', html)
        self.assertIn('autoAlterResumeForTargetJob({ silent: true })', html)
        # The generic "rewrite for role" button would be a second, vaguer action.
        self.assertNotIn('id="btnOneClickAiBoost"', html)

    def test_editor_without_a_job_keeps_the_role_rewrite_button(self):
        res = self.client.get('/resume/')
        html = page_without_site_schema(res)
        self.assertIn('id="btnOneClickAiBoost"', html)
        self.assertNotIn('id="targetJobBanner"', html)

    def test_export_without_a_name_does_not_invent_one(self):
        resume = {
            'name': '',
            'contact': {'email': '', 'phone': '', 'location': '', 'linkedin': '', 'github': ''},
            'summary': 'Backend engineer working with Python and Django.',
            'skills': {'Languages': 'Python'},
            'projects': [{
                'title': 'Order service',
                'role': 'Backend',
                'tech_stack': 'Python',
                'bullets': ['Built an order service that reserves inventory before payment.'],
            }],
            'education': {'degree': 'B.Tech in Computer Science', 'institution': '',
                          'year': '', 'gpa': '', 'coursework': ''},
            'certifications': [],
            'experience': [],
        }
        for path, ext in (('/api/resume/download-pdf/', 'pdf'),
                          ('/api/resume/download-docx/', 'docx')):
            res = self.client.post(
                path,
                data=json.dumps({'resume': resume}),
                content_type='application/json',
            )
            self.assertEqual(res.status_code, 200, path)
            disposition = res['Content-Disposition']
            self.assertIn(f'ATS_Resume.{ext}', disposition)
            self.assertNotIn('Candidate', disposition)

    def test_template_api_ships_blank_contact(self):
        for level in ('fresher', 'experienced'):
            res = self.client.get(f'/api/resume/template/python-backend/?level={level}')
            self.assertEqual(res.status_code, 200)
            resume = res.json()['resume']
            self.assertEqual(resume['name'], '')
            self.assertEqual(resume['contact']['email'], '')
            self.assertEqual(resume['contact']['phone'], '')
            # The role content is still a usable starting point.
            self.assertTrue(resume['summary'])
            self.assertTrue(resume['skills'])


class GitHubImportHonestyTests(TestCase):
    """The paste-a-repo importer defaults to 'I studied it', not 'I built it'."""

    def setUp(self):
        self.client = Client()

    def _import(self, payload):
        fake = {
            'title': 'Ansible Automation Platform',
            'role': 'Creator',
            'tech_stack': 'Python, Django',
            'bullets': [
                'Architected an engine cutting latency by 40%.',
                'Studied how job templates are scheduled and executed.',
            ],
        }
        with patch('requirements.ai_engine.generate_github_project_bullets', return_value=fake) as gen:
            res = self.client.post(
                '/api/ai/github-project/',
                data=json.dumps(payload),
                content_type='application/json',
            )
        return res, gen

    def test_defaults_to_studied_and_drops_invented_metrics(self):
        res, gen = self._import({'repo': 'ansible/awx'})
        self.assertEqual(res.status_code, 200)
        project = res.json()['project']
        self.assertEqual(gen.call_args.kwargs['relationship'], 'RECOMMENDED')
        self.assertEqual(project['relationship'], 'RECOMMENDED')
        self.assertEqual(project['bullets'], ['Studied how job templates are scheduled and executed.'])
        self.assertNotIn('Enterprise', project['title'])

    def test_explicit_relationship_is_passed_through(self):
        res, gen = self._import({'repo': 'me/my-project', 'relationship': 'built'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(gen.call_args.kwargs['relationship'], 'BUILT')

    def test_unknown_relationship_falls_back_to_studied(self):
        res, gen = self._import({'repo': 'me/my-project', 'relationship': 'IINVENTEDTHISTOKEN'})
        self.assertEqual(gen.call_args.kwargs['relationship'], 'RECOMMENDED')


class AutoUpgradeAndAnalysisViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_resume_analysis_page_loads(self):
        res = self.client.get('/ai-resume-analysis/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode()
        self.assertIn('AI Resume Checker', content)
        self.assertIn('gaugeScoreNumber', content)

    def test_auto_upgrade_api(self):
        raw_resume = {
            'name': 'Priya Sharma',
            'summary': 'Software developer looking for opportunities.',
            'skills': {
                'Languages': 'Python, JavaScript',
                'Frameworks': 'Django'
            },
            'experience': [],
            'projects': [
                {
                    'title': 'E-Commerce Platform',
                    'role': 'Full-Stack Developer',
                    'tech_stack': 'Python, Django, PostgreSQL, Redis',
                    'bullets': [
                        'Built an ecommerce app with Django',
                        'Added redis caching and postgres'
                    ]
                }
            ],
            'education': [
                {
                    'institution': 'VTU Belagavi',
                    'degree': 'B.E. Computer Science',
                    'year': '2024',
                    'gpa': '8.6 CGPA'
                }
            ],
            'contact': {
                'email': 'priya@example.com',
                'phone': '+91 9123456789',
                'location': 'Bengaluru, India',
                'linkedin': 'linkedin.com/in/priya',
                'github': 'github.com/priya'
            }
        }
        res = self.client.post(
            '/api/ai/auto-upgrade-resume/',
            data=json.dumps({
                'resume_data': raw_resume,
                'role_key': 'python_backend',
                'target_skills': ['Python', 'Django', 'Redis', 'PostgreSQL', 'Docker', 'REST API']
            }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get('status'), 'success')
        self.assertGreaterEqual(data.get('new_score', 0), 80)
        upgraded = data.get('upgraded_resume', {})
        self.assertTrue(len(upgraded.get('projects', [])[0].get('bullets', [])) >= 2)

