from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from instaautomation.services.oauth import InstagramOAuthService

from django.contrib.auth.models import User

class InstagramOAuthTest(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='adminstaff', password='password123', is_staff=True)
        self.client.login(username='adminstaff', password='password123')

    def test_state_generation_and_validation(self):
        state = InstagramOAuthService.generate_state()
        self.assertTrue(InstagramOAuthService.validate_state(state))
        # Re-validation should fail (single use state)
        self.assertFalse(InstagramOAuthService.validate_state(state))

    def test_invalid_state_rejection(self):
        self.assertFalse(InstagramOAuthService.validate_state("fake_invalid_state_999"))

    def test_authorization_url_contains_params(self):
        oauth = InstagramOAuthService()
        url, state = oauth.get_authorization_url()
        self.assertIn("client_id=", url)
        self.assertIn("redirect_uri=", url)
        self.assertIn("state=", url)
        self.assertIn("response_type=code", url)

    def test_oauth_callback_with_error(self):
        url = reverse('instaautomation:oauth_callback') + '?error=access_denied&error_reason=user_denied&error_description=User+denied'
        response = self.client.get(url, secure=True)
        self.assertRedirects(response, reverse('instaautomation:dashboard'), target_status_code=301)
