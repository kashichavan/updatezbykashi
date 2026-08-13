import requests
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = 'v19.0'
BASE_GRAPH_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

class InstagramClient:
    def __init__(self, access_token=None):
        self.access_token = access_token or getattr(settings, 'META_PAGE_ACCESS_TOKEN', '')

    def get_media(self, media_id):
        """Fetch details for a specific Instagram Reel or Post."""
        url = f"{BASE_GRAPH_URL}/{media_id}"
        params = {
            'fields': 'id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,username',
            'access_token': self.access_token
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                return {'success': True, 'data': res.json()}
            return {'success': False, 'error': res.json()}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_comments(self, media_id):
        """Fetch comments for an Instagram Reel or Post."""
        url = f"{BASE_GRAPH_URL}/{media_id}/comments"
        params = {
            'fields': 'id,text,timestamp,username,from',
            'access_token': self.access_token
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                return {'success': True, 'data': res.json().get('data', [])}
            return {'success': False, 'error': res.json()}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def reply_to_comment(self, comment_id, message):
        """Post a public reply to a comment on a Reel."""
        url = f"{BASE_GRAPH_URL}/{comment_id}/replies"
        payload = {
            'message': message,
            'access_token': self.access_token
        }
        try:
            res = requests.post(url, data=payload, timeout=10)
            res_json = res.json()
            if res.status_code == 200:
                return {'success': True, 'data': res_json}
            return {'success': False, 'error': res_json}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_message(self, recipient_id, message):
        """Send a Direct Message (DM) to an Instagram user."""
        url = f"{BASE_GRAPH_URL}/me/messages"
        headers = {'Content-Type': 'application/json'}
        payload = {
            'recipient': {'id': recipient_id},
            'message': {'text': message},
            'access_token': self.access_token
        }
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            res_json = res.json()
            if res.status_code == 200:
                return {'success': True, 'data': res_json}
            return {'success': False, 'error': res_json}
        except Exception as e:
            return {'success': False, 'error': str(e)}
