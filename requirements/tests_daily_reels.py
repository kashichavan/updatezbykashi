from datetime import datetime, time
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from requirements.models import Category, JobPosting, ReelDraft
from requirements.services import daily_reels


def at(hour, minute=0):
    today = timezone.localdate()
    return timezone.make_aware(datetime.combine(today, time(hour, minute)))


@override_settings(REELS_ENABLED=True)
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


class ReelsPausedTests(TestCase):
    """REELS_ENABLED is off by default: nothing drafts, renders or posts reels."""

    def setUp(self):
        from django.contrib.auth.models import User
        self.owner = User.objects.create_user("owner_paused", password="x", is_staff=True)
        self.client = Client()
        self.client.force_login(self.owner)

    @override_settings(REELS_ENABLED=False, REELS_CRON_SECRET="s3cret")
    def test_paused_reels_do_no_work(self):
        from unittest.mock import patch
        from requirements.models import ReelDraft
        with patch("requirements.services.story_render.render_video") as render:
            data = self.client.get("/api/owner/reels/today/").json()
            cron = self.client.post("/internal/reels/run/", HTTP_X_CRON_SECRET="s3cret")
            video = self.client.get("/api/jobs/1/ig-reel-video/")
        self.assertTrue(data["disabled"])
        self.assertEqual(data["reels"], [])
        self.assertEqual(cron.status_code, 200)
        self.assertTrue(cron.json()["disabled"])
        self.assertEqual(video.status_code, 404)
        self.assertEqual(ReelDraft.objects.count(), 0)
        render.assert_not_called()
