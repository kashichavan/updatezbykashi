import json
import uuid
from unittest.mock import patch
from django.test import TestCase, Client
from requirements.models import Category, JobPosting, ResumeGenerationJob, DiscoveredProject
from requirements.resume_generation_service import finalize_resume_synthesis

class ResumeGenerationPipelineTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Engineering", slug="engineering")
        self.job = JobPosting.objects.create(
            title="Junior Python Engineer",
            company_name="Acme Corp",
            category=self.category,
            skills_required="Python, Django, PostgreSQL, Docker",
            description="We are seeking a junior python developer proficient with Django and relational databases."
        )

    def test_resume_generation_job_model(self):
        job = ResumeGenerationJob.objects.create(
            job=self.job,
            mode='FRESHER_GITHUB',
            candidate_data={"name": "Alice Tester", "skills": "Python, Django"},
            status='PENDING'
        )
        self.assertIsNotNone(job.uuid)
        self.assertEqual(job.status, 'PENDING')
        self.assertEqual(job.progress_pct, 0)

        dp = DiscoveredProject.objects.create(
            generation_job=job,
            repo_name="acme/api-starter",
            repo_url="https://github.com/acme/api-starter",
            description="Sample starter project",
            stars=42,
            language="Python",
            tech_stack=["Python", "Django"],
            relevance_score=88.5,
            candidate_relationship="RECOMMENDED",
            is_selected=True
        )
        self.assertEqual(job.discovered_projects.count(), 1)
        self.assertEqual(dp.candidate_relationship, "RECOMMENDED")

    def test_finalize_resume_synthesis(self):
        gen_job = ResumeGenerationJob.objects.create(
            job=self.job,
            mode='FRESHER_GITHUB',
            candidate_data={
                "name": "Jane Developer",
                "email": "jane@example.com",
                "phone": "+91 91234 56789",
                "location": "Bengaluru",
                "degree": "B.Tech in Computer Science",
                "institution": "VTU Engineering",
                "gpa": "8.7 / 10.0",
                "skills": ["Python", "Django", "PostgreSQL", "Docker"]
            },
            status='AWAITING_SELECTION'
        )

        DiscoveredProject.objects.create(
            generation_job=gen_job,
            repo_name="jane/django-task-manager",
            repo_url="https://github.com/jane/django-task-manager",
            description="Scalable task management platform",
            stars=15,
            language="Python",
            tech_stack=["Python", "Django", "PostgreSQL"],
            relevance_score=91.0,
            candidate_relationship="BUILT",
            is_selected=True
        )

        result = finalize_resume_synthesis(str(gen_job.uuid))
        gen_job.refresh_from_db()

        self.assertEqual(gen_job.status, 'COMPLETED')
        self.assertEqual(gen_job.progress_pct, 100)
        self.assertIn("resume", result)
        self.assertIn("ats_eval", result)
        
        resume = result["resume"]
        self.assertEqual(resume["name"], "Jane Developer")
        self.assertTrue(len(resume["projects"]) >= 1)
        self.assertIn("Personally Developed", resume["projects"][0]["title"])
        self.assertIn("ats_score", resume["projects"][0])

    @patch('requirements.resume_generation_service.start_generation_pipeline_async')
    def test_api_resume_generation_create(self, mock_async):
        payload = {
            "mode": "FRESHER_GITHUB",
            "job_id": str(self.job.uuid),
            "candidate_data": {
                "name": "Bob Fresher",
                "degree": "B.Tech CSE"
            }
        }
        res = self.client.post(
            "/api/resume/generations/",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("job_id", data)
        mock_async.assert_called_once()

        # Test status polling
        job_id = data["job_id"]
        status_res = self.client.get(f"/api/resume/generations/{job_id}/")
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.json()
        self.assertTrue(status_data["success"])
        self.assertIn("status", status_data)

    def test_api_resume_github_discovery_direct(self):
        res = self.client.get(
            f"/api/resume/github-discovery/?job_skills=Python,Django&job_title=Python+Engineer"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertTrue(len(data["projects"]) >= 1)
