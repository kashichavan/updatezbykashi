import json
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from instaautomation.models import InstagramAccount

class InstagramWebhookTest(TestCase):
    def setUp(self):
        self.account = InstagramAccount.objects.create(
            instagram_user_id='17841400000000099',
            username='webhooktestacc',
            access_token='tok_999'
        )

    def test_webhook_get_verification_success(self):
        token = getattr(settings, 'META_VERIFY_TOKEN', '') or 'kashii_insta_verify_token_2026'
        url = reverse('instaautomation:webhook') + f'?hub.mode=subscribe&hub.verify_token={token}&hub.challenge=123456789'
        res = self.client.get(url, secure=True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content.decode('utf-8'), '123456789')

    def test_webhook_get_verification_failure(self):
        url = reverse('instaautomation:webhook') + '?hub.mode=subscribe&hub.verify_token=wrong_token&hub.challenge=123456789'
        res = self.client.get(url, secure=True)
        self.assertEqual(res.status_code, 403)

    def test_webhook_post_event(self):
        url = reverse('instaautomation:webhook')
        payload = {
            'object': 'instagram',
            'entry': [{
                'id': '17841400000000099',
                'time': 1700000000,
                'changes': []
            }]
        }
        res = self.client.post(url, data=json.dumps(payload), content_type='application/json', secure=True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get('status'), 'EVENT_RECEIVED')
