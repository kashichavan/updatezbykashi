from django.test import TestCase, Client
from django.utils import timezone
from .models import InstagramAccount, Automation, AutomationTrigger, AutomationAction, CommentEvent, AutomationExecution
from .services.automation_service import AutomationService
from .services.comment_service import CommentService
from .services.messaging_service import MessagingService

class InstagramAutomationTests(TestCase):
    def setUp(self):
        self.account = InstagramAccount.objects.create(
            instagram_user_id="test_ig_user_100",
            username="testcreator",
            access_token="test_access_token_xyz"
        )
        self.automation = Automation.objects.create(
            instagram_account=self.account,
            name="Guide DM Campaign",
            trigger_type="KEYWORD",
            status="ACTIVE"
        )
        self.trigger = AutomationTrigger.objects.create(
            automation=self.automation,
            keyword="guide",
            match_type="CONTAINS"
        )
        self.reply_action = AutomationAction.objects.create(
            automation=self.automation,
            action_type="REPLY_COMMENT",
            configuration={"reply_text": "Sent you a DM 📩"},
            order=1
        )
        self.dm_action = AutomationAction.objects.create(
            automation=self.automation,
            action_type="SEND_DM",
            configuration={"dm_text": "Hey {{username}}, here is your link: {{link}}", "resource_url": "https://kashiiupdatez.online/"},
            order=2
        )

    def test_automation_creation(self):
        """Test model creation and UUID generation."""
        self.assertIsNotNone(self.automation.uuid)
        self.assertEqual(self.automation.status, "ACTIVE")
        self.assertEqual(self.automation.triggers.count(), 1)
        self.assertEqual(self.automation.actions.count(), 2)

    def test_comment_service_variations(self):
        """Test reply variations selection and formatting."""
        variations = ["Check inbox! 🚀", "Sent DM 📩", "Check messages!"]
        res = CommentService.select_reply_variation(variations, username="student_user")
        self.assertIn(res, variations)

    def test_messaging_service_template(self):
        """Test DM message variable substitution."""
        formatted = MessagingService.format_dm_message(
            "Hey {{username}}! Resource link: {{link}}",
            username="kashi",
            link="https://kashiiupdatez.online/"
        )
        self.assertEqual(formatted, "Hey kashi! Resource link: https://kashiiupdatez.online/")

    def test_automation_service_idempotency(self):
        """Test comment processing and idempotency guard against duplicates."""
        comment_id = "comment_meta_9999"
        
        # 1st Execution
        res1 = AutomationService.process_comment_event(
            comment_id=comment_id,
            username="student_dev",
            comment_text="Send guide please"
        )
        self.assertEqual(res1['status'], 'EXECUTED')
        self.assertEqual(CommentEvent.objects.count(), 1)
        self.assertEqual(AutomationExecution.objects.count(), 2)

        # 2nd Execution (Duplicate Event)
        res2 = AutomationService.process_comment_event(
            comment_id=comment_id,
            username="student_dev",
            comment_text="Send guide please"
        )
        self.assertEqual(res2['status'], 'DUPLICATE_SKIPPED')
        self.assertEqual(CommentEvent.objects.count(), 1)

    def test_webhook_verification_endpoint(self):
        """Test Meta Webhook verification handshake."""
        c = Client()
        res = c.get('/instagram/webhooks/instagram/', {'hub.mode': 'subscribe', 'hub.verify_token': '8722183087', 'hub.challenge': 'test_challenge_123'}, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content.decode('utf-8'), 'test_challenge_123')
