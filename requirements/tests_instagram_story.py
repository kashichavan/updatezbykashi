from io import BytesIO
from django.test import TestCase, Client
from django.utils import timezone
from PIL import Image
from requirements.models import JobPosting, Category
from requirements.services.instagram_story import generate_job_story_image, InstagramStoryPublisher


class InstagramStoryAutomationTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Software Engineering", slug="software-engineering")
        self.fresher_job = JobPosting.objects.create(
            category=self.category,
            title="Junior Software Engineer",
            company_name="Google India",
            location="Bengaluru, Karnataka",
            stipend_salary="₹18-24 LPA",
            skills_required="Python, Django, React, Algorithms",
            eligibility="2024 / 2025 B.Tech graduates",
            apply_url="https://careers.google.com/jobs/123",
            experience_tier="FRESHER",
            deadline=timezone.now() + timezone.timedelta(days=7),
            status="ACTIVE"
        )
        self.experienced_job = JobPosting.objects.create(
            category=self.category,
            title="Senior Backend Architect",
            company_name="Amazon AWS",
            location="Hyderabad, Telangana",
            stipend_salary="₹35-50 LPA",
            skills_required="Golang, Distributed Systems, Redis, AWS",
            eligibility="5+ years backend development",
            apply_url="https://amazon.jobs/456",
            experience_tier="SENIOR_LEVEL",
            deadline=timezone.now() + timezone.timedelta(days=7),
            status="ACTIVE"
        )
        self.client = Client()

    def test_fresher_job_story_text(self):
        """Verifies that fresher jobs highlight freshers eligibility and include apply link."""
        text = self.fresher_job.get_insta_story_text()
        self.assertIn(self.fresher_job.to_unicode_bold("GOOGLE INDIA"), text)
        self.assertIn("Junior Software Engineer", text)
        self.assertIn("FRESHERS ELIGIBLE", text)
        self.assertIn("Apply Here:", text)
        self.assertIn(str(self.fresher_job.uuid), text)
        self.assertIn("#fresherjobs", text)

    def test_experienced_job_story_text(self):
        """Verifies that experienced jobs highlight experienced professionals requirement."""
        text = self.experienced_job.get_insta_story_text()
        self.assertIn(self.experienced_job.to_unicode_bold("AMAZON AWS"), text)
        self.assertIn("Senior Backend Architect", text)
        self.assertIn("EXPERIENCED PROS", text)
        self.assertIn("Apply Here:", text)
        self.assertIn(str(self.experienced_job.uuid), text)
        self.assertIn("#experiencedjobs", text)

    def test_story_image_generation_dimensions_and_format(self):
        """Verifies that the generated image is a 1080x1920 9:16 PNG."""
        buf = generate_job_story_image(self.fresher_job)
        self.assertIsInstance(buf, BytesIO)
        img = Image.open(buf)
        self.assertEqual(img.size, (1080, 1920))
        self.assertEqual(img.format, "PNG")

    def test_api_story_image_view(self):
        """Verifies the GET /api/jobs/<pk>/ig-story-image/ returns 200 and image/png."""
        resp = self.client.get(f"/api/jobs/{self.fresher_job.id}/ig-story-image/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "image/png")
        self.assertGreater(len(resp.content), 50000)

    def test_api_publish_story_endpoint(self):
        """Verifies POST /api/jobs/<pk>/publish-ig-story/ returns graceful response."""
        # GET should be rejected with 405 Method Not Allowed
        resp_get = self.client.get(f"/api/jobs/{self.fresher_job.id}/publish-ig-story/")
        self.assertEqual(resp_get.status_code, 405)

        # POST without live access token returns 200 with MISSING_ACCESS_TOKEN and fallback details
        resp_post = self.client.post(f"/api/jobs/{self.fresher_job.id}/publish-ig-story/")
        self.assertEqual(resp_post.status_code, 200)
        data = resp_post.json()
        self.assertEqual(data["error"], "MISSING_ACCESS_TOKEN")
        self.assertIn("story_image_url", data)
        self.assertIn("story_text", data)
