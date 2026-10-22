"""
Tests for production fixes:
1. Dynamic PDF/DOCX Resume Upload and ATS Evaluation
2. Fresher GitHub Discovery without company name interference
3. India-wide Multi-source Job Aggregation (Naukri, LinkedIn, Jobdexo)
"""

import io
import json
import uuid
from django.test import TestCase, Client
from django.utils import timezone
from .models import JobPosting, Category
from .github_discovery import extract_keywords_from_job, build_search_queries, search_github_repositories


class ProductionFixesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Software Engineering", slug="software-tech")
        self.job = JobPosting.objects.create(
            title="Senior Backend Engineer at Infosys Limited",
            company_name="Infosys Limited",
            category=self.category,
            location="Bengaluru, India",
            normalized_city="Bengaluru",
            skills_required="Python, Django, PostgreSQL, Redis, Docker",
            description="We are hiring a backend engineer for scalable microservices.",
            status="ACTIVE",
            deadline=timezone.now() + timezone.timedelta(days=7),
            source_name="Naukri",
            source_job_id="test_naukri_001"
        )

    def test_resume_upload_endpoint(self):
        """Test uploading a resume file parses successfully and computes job-tailored ATS score."""
        content = (
            b"Kashinath Chavan\n"
            b"kashinath@example.com | +91 9876543210 | Bengaluru, India\n"
            b"linkedin.com/in/kashinath-chavan | github.com/kashichavan\n"
            b"SUMMARY\n"
            b"Backend engineer specialized in Python, Django, REST APIs, and PostgreSQL.\n"
            b"SKILLS\n"
            b"Python, Django, PostgreSQL, Redis, Docker, Git\n"
            b"PROJECTS\n"
            b"E-Commerce Microservices Engine\n"
            b"- Architected distributed checkout microservice handling 1,500 req/sec with Redis queue.\n"
            b"- Reduced database latency by 35% with indexed PostgreSQL queries.\n"
        )
        fake_file = io.BytesIO(content)
        fake_file.name = "resume.pdf"

        res = self.client.post('/api/resume/upload/', {
            'resume_file': fake_file,
            'job_id': str(self.job.uuid),
            'job_skills': self.job.skills_required
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['parsed_resume']['name'], "Kashinath Chavan")
        self.assertIn('ats_eval', data)
        self.assertGreaterEqual(data['ats_eval']['score'], 75)
        self.assertIn('pillars', data['ats_eval'])
        self.assertIn('checks', data['ats_eval'])

    def test_fresher_github_discovery_excludes_company_name(self):
        """Verify GitHub search queries strictly extract technical skills and NEVER search company name."""
        keywords = extract_keywords_from_job(
            job_title=self.job.title,
            job_skills=self.job.skills_required,
            job_description=self.job.description
        )
        self.assertIn("python", keywords)
        self.assertIn("django", keywords)
        # Verify company name was excluded
        self.assertNotIn("infosys", keywords)
        self.assertNotIn("limited", keywords)

        queries = build_search_queries(self.job.title, keywords)
        self.assertTrue(len(queries) > 0)
        for q in queries:
            self.assertNotIn("infosys", q.lower())
            self.assertNotIn("limited", q.lower())

    def test_fresher_github_discovery_direct_api(self):
        """Test the direct GitHub discovery AJAX endpoint."""
        res = self.client.get('/api/resume/github-discovery/', {
            'job_skills': 'Python, Django, PostgreSQL',
            'job_title': 'Python Backend Engineer',
            'limit': 4
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['projects']), 1)
        # Check first repo matches tech
        first = data['projects'][0]
        self.assertIn('repo_name', first)
        self.assertIn('relevance_score', first)

    def test_ats_score_eval_with_target_job(self):
        """Test api_ats_score_eval recalculation endpoint with job_id."""
        resume_payload = {
            'name': 'Kashinath Chavan',
            'contact': {'email': 'kashi@example.com', 'phone': '+91 9876543210'},
            'skills': {'Core': 'Python, Django, PostgreSQL, Docker'},
            'projects': [{
                'title': 'Test Project',
                'role': 'Developer',
                'tech_stack': 'Python, Django',
                'bullets': ['Architected API reducing latency by 40% with 10k users.']
            }]
        }
        res = self.client.post(
            '/api/resume/evaluate/',
            data=json.dumps({
                'resume': resume_payload,
                'job_id': str(self.job.uuid),
                'job_skills': self.job.skills_required
            }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('score', data)
        self.assertIn('checks', data)
        self.assertGreaterEqual(data['score'], 70)

    def test_naukri_and_linkedin_presence_in_aggregator(self):
        """Verify Naukri and LinkedIn adapters are registered and discover Indian jobs."""
        from .job_aggregator.orchestrator import orchestrator
        registered = [s['name'] for s in orchestrator.get_registered_sources()]
        self.assertIn('Naukri', registered)
        self.assertIn('LinkedIn', registered)
        self.assertIn('Jobdexo', registered)
