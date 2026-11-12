import hashlib
import hmac
import json
import os
import subprocess
from datetime import datetime, time
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from requirements.models import Category, IGAccount, IGHandledEvent, IGPost, JobPosting, ReelDraft
from requirements.services import ig_autopilot, ig_link_dm


def at(hour, minute=0):
    return timezone.make_aware(datetime.combine(timezone.localdate(), time(hour, minute)))


class Base(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Own", slug="own-cat")
        self.job = JobPosting.objects.create(title="Backend Dev", company_name="Delta", category=cat, location="Pune",
                                             deadline=timezone.now() + timezone.timedelta(days=5))
        self.acc = IGAccount.objects.create(ig_user_id="1784", username="kashii_jobs", access_token="IGtok",
                                            is_primary=True)
        self.post = IGPost.objects.create(account=self.acc, media_id="reel1", kind="reel", job=self.job,
                                          link_url="https://kashiiupdatez.online/job/x/")


@override_settings(INSTAGRAM_APP_SECRET="appsecret", META_VERIFY_TOKEN="verify-me")
class WebhookTests(Base):
    def _post(self, payload, secret="appsecret"):
        body = json.dumps(payload).encode()
        sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return self.client.post("/instagram/webhook/", body, content_type="application/json",
                                HTTP_X_HUB_SIGNATURE_256=sig)

    def test_verification_handshake(self):
        ok = self.client.get("/instagram/webhook/", {"hub.mode": "subscribe", "hub.verify_token": "verify-me",
                                                     "hub.challenge": "42"})
        self.assertEqual(ok.content, b"42")
        bad = self.client.get("/instagram/webhook/", {"hub.mode": "subscribe", "hub.verify_token": "nope",
                                                      "hub.challenge": "42"})
        self.assertEqual(bad.status_code, 403)

    def test_rejects_bad_signature(self):
        self.assertEqual(self._post({"entry": []}, secret="wrong").status_code, 403)

    @patch("threading.Thread")
    def test_accepts_signed_event(self, thread):
        self.assertEqual(self._post({"entry": []}).status_code, 200)
        thread.return_value.start.assert_called_once()


class LinkDmFlowTests(Base):
    def comment(self, text="LINK please", cid="c1", media="reel1", sender="u1"):
        return {"entry": [{"id": "1784", "changes": [{"field": "comments", "value": {
            "id": cid, "text": text, "media": {"id": media}, "from": {"id": sender, "username": "stu"}}}]}]}

    @patch("requirements.services.ig_graph.send_message")
    @patch("requirements.services.ig_graph.reply_to_comment")
    def test_comment_link_prompts_once(self, reply, send):
        self.assertEqual(ig_link_dm.handle_webhook(self.comment()), ["prompted"])
        self.assertEqual(ig_link_dm.handle_webhook(self.comment()), ["ignored"])  # Meta retry
        reply.assert_called_once()
        recipient, = send.call_args.args[1:2]
        self.assertEqual(recipient, {"comment_id": "c1"})
        self.assertEqual(send.call_args.kwargs["buttons"][0]["payload"], "LINK:reel1")

    @patch("requirements.services.ig_graph.send_message")
    @patch("requirements.services.ig_graph.reply_to_comment")
    def test_ignores_other_comments_and_unknown_posts(self, reply, send):
        self.assertEqual(ig_link_dm.handle_webhook(self.comment(text="nice", cid="c2")), ["ignored"])
        self.assertEqual(ig_link_dm.handle_webhook(self.comment(media="other", cid="c3")), ["ignored"])
        self.assertEqual(ig_link_dm.handle_webhook(self.comment(text="linkedin?", cid="c4")), ["ignored"])
        send.assert_not_called()

    def postback(self, mid="p1"):
        return {"entry": [{"id": "1784", "messaging": [{"sender": {"id": "u1"}, "recipient": {"id": "1784"},
                                                        "timestamp": 1, "postback": {"mid": mid, "payload": "LINK:reel1",
                                                                                     "title": "Send me the link"}}]}]}

    @patch("requirements.services.ig_graph.send_message")
    @patch("requirements.services.ig_graph.follows_us", return_value=True)
    def test_follower_gets_link(self, _f, send):
        self.assertEqual(ig_link_dm.handle_webhook(self.postback()), ["delivered"])
        self.assertIn("https://kashiiupdatez.online/job/x/", send.call_args.args[2])
        self.assertEqual(send.call_args.kwargs["buttons"][0]["url"], "https://kashiiupdatez.online/job/x/")

    @patch("requirements.services.ig_graph.send_message")
    @patch("requirements.services.ig_graph.follows_us", return_value=False)
    def test_non_follower_is_gated(self, _f, send):
        self.assertEqual(ig_link_dm.handle_webhook(self.postback("p2")), ["gated"])
        titles = [b["title"] for b in send.call_args.kwargs["buttons"]]
        self.assertEqual(titles, ["Visit profile", "I'm following ✅"])

    @patch("requirements.services.ig_graph.send_message")
    @patch("requirements.services.ig_graph.follows_us", return_value=True)
    def test_story_reply_gets_link(self, _f, send):
        IGPost.objects.create(account=self.acc, media_id="story1", kind="story", job=self.job,
                              link_url="https://kashiiupdatez.online/job/s/")
        payload = {"entry": [{"id": "1784", "messaging": [{"sender": {"id": "u5"}, "message": {
            "mid": "m1", "text": "APPLY", "reply_to": {"story": {"id": "story1"}}}}]}]}
        self.assertEqual(ig_link_dm.handle_webhook(payload), ["delivered"])


class AutopilotTests(Base):
    @override_settings(REELS_CRON_SECRET="cron")
    @patch("requirements.services.ig_autopilot.run_due_async")
    def test_cron_endpoint_requires_secret(self, run):
        self.assertEqual(self.client.post("/internal/reels/run/", HTTP_X_CRON_SECRET="bad").status_code, 403)
        self.assertEqual(self.client.post("/internal/reels/run/", HTTP_X_CRON_SECRET="cron").status_code, 202)
        run.assert_called_once()

    @patch("requirements.services.ig_graph.refresh_if_needed", side_effect=lambda a: a)
    @patch("requirements.services.ig_graph.publish_media", return_value="newreel")
    def test_run_due_posts_reel_and_deletes_video(self, publish, _r):
        rendered = []
        real = ig_autopilot.render_video

        def spy(*a, **kw):
            p = real(*a, **kw)
            rendered.append(p)
            return p
        with patch("requirements.services.ig_autopilot.render_video", side_effect=spy):
            res = ig_autopilot.run_due(now=at(9, 5))
        self.assertEqual(res, {"posted": 1, "attempted": 1})
        d = ReelDraft.objects.get()
        self.assertEqual((d.status, d.media_id), ("posted", "newreel"))
        self.assertEqual(publish.call_args.kwargs["media_type"], "REELS")
        self.assertIn("Comment LINK", publish.call_args.kwargs["caption"])
        self.assertTrue(IGPost.objects.filter(media_id="newreel", kind="reel", job=self.job).exists())
        self.assertTrue(rendered and not os.path.exists(rendered[0]))  # nothing kept after upload

    @patch("requirements.services.ig_graph.refresh_if_needed", side_effect=lambda a: a)
    @patch("requirements.services.ig_graph.publish_media", side_effect=__import__(
        "requirements.services.ig_graph", fromlist=["IGError"]).IGError("boom"))
    def test_failure_retries_then_fails(self, _p, _r):
        for _ in range(3):
            ig_autopilot.run_due(now=at(9, 5))
        d = ReelDraft.objects.get()
        self.assertEqual((d.status, d.attempts), ("failed", 3))
        self.assertIn("boom", d.error)

    def test_music_is_mixed_in(self):
        from requirements.services import story_render
        tone = os.path.join(story_render.tempfile.gettempdir(), "test_tone.wav")
        subprocess.run([story_render._ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "lavfi",
                        "-i", "sine=frequency=440:duration=3", tone], check=True)
        path = story_render.render_video(self.job, "https://kashiiupdatez.online", reply_cta="comment",
                                         seconds=4.0, music=tone)
        probe = subprocess.run([story_render._ffmpeg_exe(), "-i", path], capture_output=True, text=True).stderr
        self.assertIn("Audio: aac", probe)
        self.assertIn("Duration: 00:00:04", probe)
        os.remove(path)


class OAuthTests(Base):
    def test_callback_rejects_bad_state_and_stores_account(self):
        c = Client()
        c.force_login(User.objects.create_user("own_owner", password="x", is_staff=True))
        self.assertIn("state_error", c.get("/instagram/oauth/callback/?code=abc&state=x")["Location"])
        s = c.session
        s["ig_oauth_state"] = "good"
        s.save()
        data = {"access_token": "IGnew", "expires_at": timezone.now(), "ig_user_id": "999", "username": "second"}
        with patch("requirements.services.ig_graph.exchange_code", return_value=data), \
             patch("requirements.services.ig_graph.subscribe_webhooks", return_value=(True, "subscribed")):
            r = c.get("/instagram/oauth/callback/?code=abc&state=good")
        self.assertIn("ig=connected", r["Location"])
        acc = IGAccount.objects.get(ig_user_id="999")
        self.assertTrue(acc.webhooks_ok)
        self.assertFalse(acc.is_primary)  # existing primary kept
        resp = c.get("/api/owner/instagram/accounts/").json()
        self.assertNotIn("IGnew", json.dumps(resp))  # tokens never leave the server


class InstaAutomationPosterTests(TestCase):
    def test_get_poster_prefers_insta_automation(self):
        from requirements.services import ig_autopilot
        with self.settings(REELFLOW_STORY_TOKEN="tok", REEL_ACCOUNT_HANDLE="@jobs_account"):
            p = ig_autopilot.get_poster()
        self.assertIsInstance(p, ig_autopilot.InstaAutomationPoster)
        self.assertEqual(p.username, "jobs_account")

    def test_get_poster_none_without_config(self):
        from requirements.services import ig_autopilot
        with self.settings(REELFLOW_STORY_TOKEN="", REEL_ACCOUNT_HANDLE="", INSTAGRAM_ACCOUNT_HANDLE=""):
            self.assertIsNone(ig_autopilot.get_poster())

    def test_publish_failure_raises(self):
        from unittest.mock import Mock, patch
        from requirements.services import ig_autopilot, ig_graph
        bad = Mock(status_code=400)
        bad.json.return_value = {"message": "No connected account", "needs_reconnect": True}
        with self.settings(REELFLOW_STORY_TOKEN="tok"), patch("requests.post", return_value=bad):
            with self.assertRaises(ig_graph.IGError) as ctx:
                ig_autopilot.InstaAutomationPoster("x").publish("reel", video_url="https://v")
        self.assertTrue(ctx.exception.needs_reconnect)

    def test_enable_automation_calls_insta_automation(self):
        from unittest.mock import Mock, patch
        from django.contrib.auth.models import User
        from django.test import Client
        c = Client()
        c.force_login(User.objects.create_user("auto_owner", password="x", is_staff=True))
        ok = Mock(status_code=200)
        ok.json.return_value = {"success": True}
        with self.settings(REELFLOW_STORY_TOKEN="tok", REEL_ACCOUNT_HANDLE="jobs_account"), \
             patch("requests.post", return_value=ok) as post:
            r = c.post("/api/owner/reels/enable-automation/", data="{}", content_type="application/json",
                       HTTP_ORIGIN="http://testserver")
        self.assertTrue(r.json()["success"])
        self.assertTrue(post.call_args.args[0].endswith("/internal/reels/link-automation/"))
        self.assertEqual(post.call_args.kwargs["json"]["username"], "jobs_account")
