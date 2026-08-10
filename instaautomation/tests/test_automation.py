from django.test import TestCase
from unittest.mock import patch
from instaautomation.models import (
    InstagramAccount,
    CommentAutomation,
    InstagramConversation,
    InstagramMessage,
    AutomationExecution
)
from instaautomation.services.automation import AutomationEngine

class AutomationEngineTest(TestCase):
    def setUp(self):
        self.account = InstagramAccount.objects.create(
            instagram_user_id='17841400000000088',
            username='autotestacc',
            access_token='tok_888'
        )
        self.automation = CommentAutomation.objects.create(
            instagram_account=self.account,
            name='Python Guide Rule',
            keywords='python, guide',
            comment_reply='Check your DM!',
            dm_message='Hey {{username}} reply DONE',
            confirmation_keyword='DONE',
            final_message='Here is link: {{resource_url}}',
            resource_url='https://kashiiupdatez.online/python/'
        )
        self.engine = AutomationEngine()

    @patch('instaautomation.services.automation.InstagramAPI')
    def test_comment_matching_and_execution(self, mock_api):
        event_data = {
            'id': 'comment_111222333',
            'text': 'I need the python guide please!',
            'from': {'id': 'user_444555', 'username': 'studentdev'}
        }

        res = self.engine.process_comment_event(self.account, event_data)
        self.assertEqual(res['status'], 'SUCCESS')
        
        # Check execution created
        self.assertTrue(AutomationExecution.objects.filter(external_event_id='comment_comment_111222333').exists())

        # Check conversation state created
        conv = InstagramConversation.objects.get(instagram_account=self.account, participant_id='user_444555')
        self.assertTrue(conv.awaiting_confirmation)

    @patch('instaautomation.services.automation.InstagramAPI')
    def test_done_confirmation_workflow(self, mock_api):
        # Pre-create awaiting confirmation conversation
        conv = InstagramConversation.objects.create(
            instagram_account=self.account,
            participant_id='user_444555',
            participant_username='studentdev',
            active_automation=self.automation,
            awaiting_confirmation=True
        )

        msg_event = {
            'mid': 'm_999888777',
            'sender': {'id': 'user_444555'},
            'message': {'text': 'DONE'}
        }

        res = self.engine.process_message_event(self.account, msg_event)
        self.assertEqual(res['status'], 'SUCCESS')

        conv.refresh_from_db()
        self.assertFalse(conv.awaiting_confirmation)
        self.assertIsNone(conv.active_automation)
