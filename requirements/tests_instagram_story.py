from io import BytesIO
from unittest.mock import Mock, patch
from django.contrib.auth.models import User
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from PIL import Image
from requirements.models import JobPosting, Category
from requirements.services.instagram_story import generate_job_story_image, InstagramStoryPublisher


@override_settings(INSTAGRAM_ACCESS_TOKEN="")
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
        self.assertEqual(img.format, "JPEG")

    def test_api_story_image_view(self):
        """Verifies the GET /api/jobs/<pk>/ig-story-image/ returns 200 and image/jpeg."""
        resp = self.client.get(f"/api/jobs/{self.fresher_job.id}/ig-story-image/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "image/jpeg")
        self.assertGreater(len(resp.content), 50000)

    def test_api_publish_story_endpoint(self):
        """Verifies POST /api/jobs/<pk>/publish-ig-story/ returns graceful response."""
        # GET should be rejected with 405 Method Not Allowed
        resp_get = self.client.get(f"/api/jobs/{self.fresher_job.id}/publish-ig-story/")
        self.assertEqual(resp_get.status_code, 405)

        # Owner POST without live access token returns 200 with MISSING_ACCESS_TOKEN and fallback details
        self.client.force_login(User.objects.create_user("owner", password="x", is_staff=True))
        resp_post = self.client.post(
            f"/api/jobs/{self.fresher_job.id}/publish-ig-story/",
            HTTP_ORIGIN="http://testserver",
        )
        self.assertEqual(resp_post.status_code, 200)
        data = resp_post.json()
        self.assertEqual(data["error"], "MISSING_ACCESS_TOKEN")
        self.assertIn("story_image_url", data)
        self.assertIn("story_text", data)


class InstagramPublisherHardeningTests(TestCase):
    def setUp(self):
        self.client = Client()
        category = Category.objects.create(name="Backend", slug="backend-hardening")
        self.job = JobPosting.objects.create(
            title="Engineer", company_name="Acme", category=category,
            location="Pune", deadline=timezone.now() + timezone.timedelta(days=7),
        )

    def test_publish_endpoint_rejects_anonymous_post(self):
        resp = self.client.post(f"/api/jobs/{self.job.id}/publish-ig-story/")
        self.assertEqual(resp.status_code, 401)

    def test_host_follows_token_type(self):
        ig = InstagramStoryPublisher(access_token="IGAAtest", account_id="1", api_version="v26.0")
        fb = InstagramStoryPublisher(access_token="EAAtest", account_id="1", api_version="v26.0")
        self.assertEqual(ig.base_graph_url, "https://graph.instagram.com/v26.0")
        self.assertEqual(fb.base_graph_url, "https://graph.facebook.com/v26.0")

    @patch("requirements.services.instagram_story.time.sleep")
    @patch("requirements.services.instagram_story.requests")
    def test_waits_for_container_before_publishing(self, mock_requests, _sleep):
        def response(payload):
            return Mock(status_code=200, json=Mock(return_value=payload), text="")

        mock_requests.post.side_effect = [response({"id": "c1"}), response({"id": "m1"})]
        mock_requests.get.side_effect = [response({"status_code": "IN_PROGRESS"}),
                                         response({"status_code": "FINISHED"})]
        result = InstagramStoryPublisher(access_token="IGAAtest", account_id="1").publish_job_story(self.job)
        self.assertTrue(result["success"])
        self.assertEqual(mock_requests.get.call_count, 2)
        self.job.refresh_from_db()
        self.assertEqual(self.job.insta_story_media_id, "m1")

    @patch("requirements.services.instagram_story.time.sleep")
    @patch("requirements.services.instagram_story.requests")
    def test_failed_container_is_not_published(self, mock_requests, _sleep):
        mock_requests.post.return_value = Mock(status_code=200, json=Mock(return_value={"id": "c1"}), text="")
        mock_requests.get.return_value = Mock(json=Mock(return_value={"status_code": "ERROR", "status": "bad image"}))
        result = InstagramStoryPublisher(access_token="IGAAtest", account_id="1").publish_job_story(self.job)
        self.assertEqual(result["error"], "CONTAINER_NOT_READY")
        self.assertEqual(mock_requests.post.call_count, 1)
