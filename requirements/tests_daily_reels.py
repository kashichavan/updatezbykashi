from datetime import datetime, time
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from requirements.models import Category, JobPosting, ReelDraft
from requirements.services import daily_reels


def at(hour, minute=0):
    today = timezone.localdate()
    return timezone.make_aware(datetime.combine(today, time(hour, minute)))


class DailyReelsTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Reels", slug="reels-cat")
        self.jobs = [JobPosting.objects.create(title=f"Role {i}", company_name=f"Co {i}", category=cat, location="Pune",
                                               deadline=timezone.now() + timezone.timedelta(days=5)) for i in range(5)]

    def test_only_started_slots_get_drafts_newest_jobs_first(self):
        drafts = daily_reels.ensure_due_drafts("https://kashiiupdatez.online", now=at(14), prerender=False)
        self.assertEqual(len(drafts), 2)  # 9 AM and 1 PM, not 7 PM yet
        self.assertEqual({d.job_id for d in drafts}, {self.jobs[4].id, self.jobs[3].id})
        # Idempotent, and the evening slot takes the next unused job.
        drafts = daily_reels.ensure_due_drafts("https://kashiiupdatez.online", now=at(19, 5), prerender=False)
        self.assertEqual(len(drafts), 3)
        self.assertEqual(drafts[-1].job_id, self.jobs[2].id)
        self.assertEqual(ReelDraft.objects.count(), 3)

    def test_caption_has_link_and_comment_cta(self):
        d = daily_reels.ensure_due_drafts("https://kashiiupdatez.online", now=at(9, 1), prerender=False)[0]
        self.assertIn("Comment LINK", d.caption)
        self.assertIn("https://kashiiupdatez.online/category/reels-cat/job/", d.caption)

    def test_owner_api(self):
        self.assertEqual(Client().get("/api/owner/reels/today/").status_code, 401)
        c = Client()
        c.force_login(User.objects.create_user("reel_owner", password="x", is_staff=True))
        with patch("requirements.services.daily_reels.prerender_async"), \
             patch("requirements.services.daily_reels.timezone.now", return_value=at(13, 30)):
            data = c.get("/api/owner/reels/today/").json()
        self.assertEqual(len(data["reels"]), 2)
        rid = data["reels"][0]["id"]
        r = c.post(f"/api/owner/reels/{rid}/status/", data='{"status": "posted"}', content_type="application/json",
                   HTTP_ORIGIN="http://testserver")
        self.assertEqual(r.json()["reel"]["status"], "posted")
        self.assertEqual(c.post(f"/api/owner/reels/{rid}/status/", data='{"status": "bogus"}',
                                content_type="application/json", HTTP_ORIGIN="http://testserver").status_code, 400)

    def test_reel_video_endpoint(self):
        resp = Client().get(f"/api/jobs/{self.jobs[0].id}/ig-reel-video/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "video/mp4")

    def test_enable_automation_calls_insta_automation(self):
        c = Client()
        c.force_login(User.objects.create_user("reel_owner2", password="x", is_staff=True))
        ok = Mock()
        ok.json.return_value = {"success": True, "username": "kashii_jobs", "keyword": "LINK"}
        with self.settings(REELFLOW_STORY_TOKEN="tok", REEL_ACCOUNT_HANDLE="kashii_jobs"), \
             patch("requests.post", return_value=ok) as post:
            data = c.post("/api/owner/reels/enable-automation/", HTTP_ORIGIN="http://testserver").json()
        self.assertTrue(data["success"])
        self.assertEqual(post.call_args.kwargs["json"], {"username": "kashii_jobs", "keyword": "LINK"})
