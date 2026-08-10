from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from instaautomation.models import (
    InstagramAccount,
    CommentAutomation,
    InstagramConversation,
    InstagramMessage,
    AutomationExecution
)

class InstagramAccountModelTest(TestCase):
    def setUp(self):
        self.account = InstagramAccount.objects.create(
            instagram_user_id='17841400000000000',
            username='pythonkashi',
            display_name='Python Kashi',
            access_token='test_access_token_123',
            token_expires_at=timezone.now() + timedelta(days=60),
            connection_status=InstagramAccount.ConnectionStatus.CONNECTED
        )

    def test_account_creation(self):
        self.assertEqual(self.account.username, 'pythonkashi')
        self.assertTrue(self.account.is_token_valid)
        self.assertEqual(str(self.account), '@pythonkashi (Connected)')

    def test_token_expiration(self):
        self.account.token_expires_at = timezone.now() - timedelta(days=1)
        self.account.save()
        self.assertFalse(self.account.is_token_valid)


class CommentAutomationModelTest(TestCase):
    def setUp(self):
        self.account = InstagramAccount.objects.create(
            instagram_user_id='17841400000000001',
            username='mybusiness',
            access_token='tok_123'
        )
        self.automation = CommentAutomation.objects.create(
            instagram_account=self.account,
            name='Python Guide',
            keywords='python, python guide, learn python',
            comment_reply='Check your DM!',
            dm_message='Hey {{username}} reply DONE',
            confirmation_keyword='DONE',
            final_message='Here is your link: {{resource_url}}',
            resource_url='https://kashiiupdatez.online'
        )

    def test_automation_keywords_parsing(self):
        kw_list = self.automation.get_keywords_list()
        self.assertEqual(kw_list, ['python', 'python guide', 'learn python'])
