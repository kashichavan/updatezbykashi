import os
import requests
from django.conf import settings

META_GRAPH_URL = "https://graph.facebook.com/v19.0"

class InstagramAPI:
    """
    Official Meta / Instagram Graph API Service wrapper.
    Handles replying to comments, sending DMs, fetching conversation messages.
    """

    def __init__(self, account):
        self.account = account
        self.access_token = account.access_token

    def _get(self, endpoint, params=None):
        if not params:
            params = {}
        params['access_token'] = self.access_token
        try:
            res = requests.get(f"{META_GRAPH_URL}/{endpoint}", params=params, timeout=10)
            return res.json()
        except requests.RequestException as e:
            return {'error': {'message': str(e)}}

    def _post(self, endpoint, data=None):
        if not data:
            data = {}
        data['access_token'] = self.access_token
        try:
            res = requests.post(f"{META_GRAPH_URL}/{endpoint}", json=data, timeout=10)
            return res.json()
        except requests.RequestException as e:
            return {'error': {'message': str(e)}}

    def get_account_profile(self):
        """Fetch current IG profile details."""
        return self._get(self.account.instagram_user_id, {'fields': 'id,username,name,profile_picture_url'})

    def check_is_following(self, user_id):
        """
        Checks if a user is following the connected Instagram business account.
        Queries Graph API or verifies conversation relationship.
        """
        if not user_id:
            return False
        try:
            res = self._get(f"{self.account.instagram_user_id}/followers", {'user_id': user_id})
            if res and 'data' in res:
                return any(follower.get('id') == str(user_id) for follower in res['data'])
            return True
        except Exception:
            return True

    def reply_to_comment(self, comment_id, message):
        """
        Public comment reply to a specific media comment.
        POST /{comment-id}/replies
        """
        if not comment_id or not message:
            return None
        return self._post(f"{comment_id}/replies", {'message': message})

    def send_private_reply(self, comment_id, message):
        """
        Private DM reply triggered directly from a comment (Official Private Reply API).
        POST /{ig-user-id}/messages with recipient={'comment_id': comment_id}
        """
        if not comment_id or not message:
            return None
        payload = {
            'recipient': {'comment_id': comment_id},
            'message': {'text': message}
        }
        return self._post(f"{self.account.instagram_user_id}/messages", payload)

    def send_direct_message(self, recipient_id, message_text):
        """
        Standard Instagram Direct Message.
        POST /{ig-user-id}/messages with recipient={'id': recipient_id}
        """
        if not recipient_id or not message_text:
            return None
        payload = {
            'recipient': {'id': recipient_id},
            'message': {'text': message_text}
        }
        return self._post(f"{self.account.instagram_user_id}/messages", payload)
