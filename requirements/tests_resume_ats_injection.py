import json
from unittest.mock import patch
from django.test import SimpleTestCase, TestCase, Client
from requirements.resume_engine import inject_missing_ats_skills, categorize_skill
from requirements.ai_engine import build_resume_for_job


class AtsSkillInjectionTests(SimpleTestCase):
    def test_categorize_skill(self):
        self.assertEqual(categorize_skill('Python'), 'Languages')
        self.assertEqual(categorize_skill('Django'), 'Frameworks & Libraries')
        self.assertEqual(categorize_skill('Docker'), 'Cloud & DevOps')
        self.assertEqual(categorize_skill('PostgreSQL'), 'Databases & Caching')
        self.assertEqual(categorize_skill('REST API'), 'Architecture & Tools')

    def test_inject_missing_skills_into_dict(self):
        skills = {
            'Languages': 'Python, SQL',
            'Frameworks': 'Django'
        }
        missing = ['Docker', 'AWS', 'PostgreSQL', 'Redis']
        injected = inject_missing_ats_skills(skills, missing)

        self.assertIn('Docker', injected.get('Cloud & DevOps', ''))
        self.assertIn('AWS', injected.get('Cloud & DevOps', ''))
        self.assertIn('PostgreSQL', injected.get('Databases & Caching', ''))
        self.assertIn('Redis', injected.get('Databases & Caching', ''))
        self.assertIn('Python', injected.get('Languages', ''))

    def test_inject_preserves_existing_skills(self):
        skills = {'Technical Skills': 'Python, Django'}
        missing = ['Docker', 'Kubernetes']
        injected = inject_missing_ats_skills(skills, missing)
        self.assertIn('Python', injected['Technical Skills'])
        self.assertIn('Docker', injected['Technical Skills'])
        self.assertIn('Kubernetes', injected['Technical Skills'])


class BuildResumeAtsWordsTests(TestCase):
    def test_build_resume_adds_confirmed_ats_words(self):
        jd = "We need a Backend Developer with Python, Django, Docker, AWS, and PostgreSQL experience."
        candidate = {
            'name': 'Kashi',
            'contact': {'email': 'kashi@dev.com', 'phone': '9876543210', 'linkedin': 'linkedin.com/in/kashi', 'github': 'github.com/kashi'},
            'skills': {'Languages': 'Python'},
            'projects': [{'title': 'Order API', 'tech_stack': 'Python, Django', 'bullets': ['Architected REST API with Python and Django, reducing latency by 45%.']}],
            'education': {'degree': 'B.Tech', 'institution': 'MIT', 'year': '2024'}
        }
        confirmed = ['Docker', 'AWS', 'PostgreSQL', 'Django']
        result = build_resume_for_job(
            job_description=jd,
            candidate_info=candidate,
            confirmed_skills=confirmed
        )
        skills_text = json.dumps(result['resume']['skills'])
        self.assertIn('Docker', skills_text)
        self.assertIn('AWS', skills_text)
        self.assertIn('PostgreSQL', skills_text)
        self.assertIn('Django', skills_text)
        self.assertGreaterEqual(result['ats_score'], 80)


class TailorResumeEndpointAtsTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_tailor_endpoint_returns_injected_skills(self):
        fake_tailor = {
            'match_score': 65,
            'match_grade': 'Moderate',
            'matched_keywords': ['Python'],
            'missing_critical_keywords': ['Docker', 'AWS', 'PostgreSQL', 'Kafka'],
            'tailored_summary': 'Backend developer with Python experience.',
            'suggested_project_improvements': [],
            'quick_recommendations': ['Add Docker and AWS']
        }
        with patch('requirements.ai_engine.tailor_resume_to_job', return_value=fake_tailor):
            res = self.client.post(
                '/api/ai/tailor-resume/',
                data=json.dumps({
                    'job_description': 'Senior Backend with Python, Docker, AWS, PostgreSQL, Kafka',
                    'resume_summary': 'Backend developer.',
                    'resume_skills': ['Python'],
                    'resume_skills_dict': {'Languages': 'Python'},
                    'resume_projects': []
                }),
                content_type='application/json'
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()['data']
            self.assertIn('tailored_skills', data)
            self.assertIn('injected_ats_keywords', data)
            skills_dump = json.dumps(data['tailored_skills'])
            self.assertIn('Docker', skills_dump)
            self.assertIn('AWS', skills_dump)
            self.assertIn('PostgreSQL', skills_dump)
            self.assertIn('Kafka', skills_dump)
