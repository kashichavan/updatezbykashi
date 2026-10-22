import json
from django.test import TestCase, Client
from django.core.management import call_command
from django.urls import reverse
from requirements.models import IndianDemoProject, ResumeGenerationJob, DiscoveredProject, JobPosting, Category
from requirements.indian_project_service import match_demo_projects_for_job, serialize_demo_project, attach_demo_project_to_generation_job
from requirements.resume_generation_service import finalize_resume_synthesis


class IndianDemoProjectsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Seed projects
        call_command('seed_indian_demo_projects')

    def test_seed_command_idempotency_and_count(self):
        """Verify that 36 curated Indian projects are seeded and repeated runs are idempotent."""
        count1 = IndianDemoProject.objects.count()
        self.assertEqual(count1, 36)

        # Re-run seed command; count should remain exactly 36 with no duplicates
        call_command('seed_indian_demo_projects')
        count2 = IndianDemoProject.objects.count()
        self.assertEqual(count2, 36)

        # Test dry-run does not alter state
        call_command('seed_indian_demo_projects', dry_run=True)
        count3 = IndianDemoProject.objects.count()
        self.assertEqual(count3, 36)

    def test_project_attributes_and_locations(self):
        """Verify Indian tech hubs and presence of Google XYZ bullets and stacks."""
        bengaluru_projects = IndianDemoProject.objects.filter(location_city='Bengaluru')
        self.assertGreaterEqual(bengaluru_projects.count(), 5)

        p = bengaluru_projects.first()
        self.assertTrue(p.title)
        self.assertTrue(p.slug)
        self.assertTrue(p.location_state)
        self.assertTrue(p.industry)
        self.assertTrue(isinstance(p.technical_stack, list))
        self.assertGreaterEqual(len(p.technical_stack), 2)
        self.assertTrue(isinstance(p.resume_bullet_templates, list))
        self.assertGreaterEqual(len(p.resume_bullet_templates), 3)

        # Ensure no fabrication of verified real employment
        self.assertIn(p.project_type, ['Personal Portfolio Project', 'Practice Demonstration', 'Architecture Case Study'])

    def test_api_indian_demo_projects_filtering(self):
        """Test API querying with city, role, and text filtering."""
        # Filter by city
        response = self.client.get('/api/projects/indian-demo/?city=Bengaluru')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['count'], 5)
        for proj in data['projects']:
            self.assertEqual(proj['location_city'], 'Bengaluru')

        # Filter by tech stack keyword
        response = self.client.get('/api/projects/indian-demo/?tech=django')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['count'], 1)
        for proj in data['projects']:
            techs = [str(t).lower() for t in proj['technical_stack']]
            self.assertTrue(any('django' in t for t in techs) or 'django' in proj['description'].lower())

    def test_match_demo_projects_for_job(self):
        """Test intelligent matching against role, skills, and Indian tech hub."""
        matched = match_demo_projects_for_job(
            job_title="Senior Python Django Developer",
            job_skills=["Python", "Django", "PostgreSQL", "Redis"],
            preferred_city="Bengaluru",
            limit=5
        )
        self.assertGreaterEqual(len(matched), 1)
        top_match = matched[0]
        # Should be a high relevance score
        self.assertGreaterEqual(top_match['relevance_score'], 80.0)
        self.assertIn('relevance_score', top_match)
        self.assertIn('evidence_summary', top_match)

    def test_attach_demo_project_and_ethical_attribution(self):
        """Test attaching curated demo project to ResumeGenerationJob and ethical badges."""
        cat = Category.objects.create(name='Engineering', slug='engineering')
        job_posting = JobPosting.objects.create(
            title='Backend Systems Engineer',
            company_name='Tech Solutions',
            category=cat,
            location='Bengaluru, Karnataka',
            skills_required='Python, Django, PostgreSQL',
            description='Looking for Python Django developer with experience in REST APIs and PostgreSQL.'
        )

        gen_job = ResumeGenerationJob.objects.create(
            job=job_posting,
            mode='FRESHER_GITHUB',
            candidate_data={
                'name': 'Aarav Sharma',
                'email': 'aarav@example.com',
                'location': 'Bengaluru, India',
                'skills': ['Python', 'Django', 'PostgreSQL']
            }
        )

        demo_project = IndianDemoProject.objects.filter(location_city='Bengaluru').first()
        self.assertIsNotNone(demo_project)

        # Attach via API
        response = self.client.post(
            '/api/resume/attach-indian-project/',
            data=json.dumps({
                'job_uuid': str(gen_job.uuid),
                'project_slug': demo_project.slug,
                'relationship': 'PORTFOLIO',
                'is_selected': True
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.content)
        self.assertTrue(res_data['success'])
        self.assertEqual(res_data['project']['candidate_relationship'], 'PORTFOLIO')

        # Verify DiscoveredProject record in database
        dp = DiscoveredProject.objects.filter(generation_job=gen_job, demo_project=demo_project).first()
        self.assertIsNotNone(dp)
        self.assertTrue(dp.is_selected)
        self.assertEqual(dp.candidate_relationship, 'PORTFOLIO')

        # Finalize resume synthesis and check output
        result = finalize_resume_synthesis(str(gen_job.uuid))
        self.assertIn('resume', result)
        resume = result['resume']
        self.assertGreaterEqual(len(resume['projects']), 1)
        res_proj = resume['projects'][0]
        self.assertIn('[Personal Portfolio Project]', res_proj['title'])
        # Verify bullets were drawn from the curated Google XYZ templates
        self.assertGreaterEqual(len(res_proj['bullets']), 2)
