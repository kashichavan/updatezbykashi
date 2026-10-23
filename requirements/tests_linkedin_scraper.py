from django.test import TestCase, Client
from django.contrib.auth.models import User
from requirements.models import JobPosting, Category
from requirements.linkedin_service import (
    parse_linkedin_content,
    validate_linkedin_lead,
    publish_linkedin_lead
)


class LinkedInScraperTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Software & Tech', slug='software-tech')
        self.owner = User.objects.create_superuser(username='owner_test', password='password123', email='owner@test.com')
        self.client = Client()

    def test_parse_linkedin_referral_post(self):
        raw_text = """
        Hiring Alert! We are looking for SDE-1 at Microsoft Hyderabad.
        Tech Stack: C#, .NET Core, Azure, SQL.
        Eligibility: 2024 / 2025 batch freshers.
        I can provide employee referrals! Send your resume with Job ID MS-9082 to referral.ms@microsoft.com
        Connect on LinkedIn: https://linkedin.com/in/rohit-microsoft
        Regards, Rohit Verma
        """
        parsed = parse_linkedin_content(raw_text)

        self.assertEqual(parsed['company'], 'Microsoft')
        self.assertEqual(parsed['title'], 'SDE-1')
        self.assertTrue(parsed['is_referral'])
        self.assertIn('C#', parsed['skills_required'])
        self.assertEqual(parsed['referrer_name'], 'Rohit Verma')
        self.assertEqual(parsed['referrer_linkedin'], 'https://linkedin.com/in/rohit-microsoft')
        self.assertIn('mailto:referral.ms@microsoft.com', parsed['apply_url'])

    def test_validate_linkedin_lead_pass_and_score(self):
        lead_data = {
            'company': 'Google',
            'title': 'Software Engineer - Backend',
            'location': 'Bengaluru',
            'skills_required': 'Python, Go, Distributed Systems, SQL',
            'apply_url': 'https://careers.google.com/jobs/results/12345',
            'is_referral': False,
        }
        val = validate_linkedin_lead(lead_data)
        self.assertTrue(val['is_valid'])
        self.assertGreaterEqual(val['score'], 80)
        self.assertEqual(val['status'], 'PASS')

    def test_validate_linkedin_lead_needs_review_when_empty(self):
        val = validate_linkedin_lead({})
        self.assertFalse(val['is_valid'])
        self.assertEqual(val['status'], 'NEEDS_REVIEW')

    def test_publish_linkedin_lead(self):
        lead_data = {
            'company': 'Swiggy',
            'title': 'Backend Developer',
            'location': 'Bengaluru',
            'stipend_salary': '₹14 LPA',
            'skills_required': 'Java, Go, Kafka, AWS',
            'apply_url': 'mailto:swiggy.ref@swiggy.com',
            'is_referral': True,
            'referrer_name': 'Ananya Sharma',
            'referrer_linkedin': 'https://linkedin.com/in/ananya-swiggy',
            'referral_instructions': 'Email resume with Subject: Referral Backend',
            'description': 'Exciting role at Swiggy engineering team.'
        }
        job = publish_linkedin_lead(lead_data, posted_by_user="Test Ingestor")

        self.assertIsInstance(job, JobPosting)
        self.assertEqual(job.company_name, 'Swiggy')
        self.assertEqual(job.title, 'Backend Developer')
        self.assertTrue(job.is_referral)
        self.assertEqual(job.referrer_name, 'Ananya Sharma')
        self.assertEqual(job.referrer_linkedin, 'https://linkedin.com/in/ananya-swiggy')
        self.assertIn('Referral Backend', job.referral_instructions)
        self.assertEqual(job.status, 'ACTIVE')
        self.assertTrue(job.get_absolute_url().startswith('/category/'))

    def test_api_owner_linkedin_parse_and_publish(self):
        self.client.force_login(self.owner)

        # 1. Parse endpoint
        parse_resp = self.client.post(
            '/api/owner/linkedin/parse/',
            data={
                'raw_text': 'Hiring Java Developers at TCS Pune. Package: 4 LPA. Apply: https://tcs.com/careers'
            },
            content_type='application/json'
        )
        self.assertEqual(parse_resp.status_code, 200)
        p_json = parse_resp.json()
        self.assertTrue(p_json['success'])
        self.assertIn('TCS', p_json['parsed']['company'])
        self.assertTrue(p_json['validation']['is_valid'])

        # 2. Publish endpoint
        publish_resp = self.client.post(
            '/api/owner/linkedin/publish/',
            data=p_json['parsed'],
            content_type='application/json'
        )
        self.assertEqual(publish_resp.status_code, 200)
        pub_json = publish_resp.json()
        self.assertTrue(pub_json['success'])
        self.assertIn('job_id', pub_json)
        self.assertTrue(JobPosting.objects.filter(id=pub_json['job_id']).exists())
