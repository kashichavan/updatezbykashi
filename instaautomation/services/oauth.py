import os
import secrets
import urllib.parse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import requests

META_OAUTH_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"
META_GRAPH_URL = "https://graph.facebook.com/v19.0"
INSTAGRAM_BUSINESS_OAUTH_AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
META_OAUTH_AUTHORIZE_URL = INSTAGRAM_BUSINESS_OAUTH_AUTHORIZE_URL

_PENDING_STATES = {}

class InstagramOAuthService:
    """
    Handles Instagram Business OAuth flow matching Superprofile.bio API specs.
    """

    @classmethod
    def get_app_credentials(cls):
        app_id = getattr(settings, 'META_APP_ID', '1863834171261944') or os.environ.get('META_APP_ID', '1863834171261944')
        app_secret = getattr(settings, 'META_APP_SECRET', '57af518561fb5207289f0b55d241259f') or os.environ.get('META_APP_SECRET', '57af518561fb5207289f0b55d241259f')
        redirect_uri = getattr(settings, 'INSTAGRAM_REDIRECT_URI', 'https://kashiiupdatez.online/instagram/oauth/callback/') or os.environ.get('INSTAGRAM_REDIRECT_URI', 'https://kashiiupdatez.online/instagram/oauth/callback/')
        return app_id, app_secret, redirect_uri

    @classmethod
    def generate_state(cls):
        state = secrets.token_urlsafe(32)
        _PENDING_STATES[state] = timezone.now() + timedelta(minutes=15)
        return state

    @classmethod
    def validate_state(cls, state):
        if not state or state not in _PENDING_STATES:
            return False
        expiry = _PENDING_STATES.pop(state)
        return timezone.now() <= expiry

    def get_authorization_url(self, account_id=None):
        app_id, _, redirect_uri = self.get_app_credentials()
        state = self.generate_state()
        if account_id:
            state = f"{state}:{account_id}"
            
        scopes = [
            'instagram_basic',
            'instagram_manage_comments',
            'instagram_manage_messages',
            'pages_show_list',
            'pages_read_engagement',
            'public_profile'
        ]
        
        params = {
            'client_id': app_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ','.join(scopes),
            'state': state
        }
        return f"https://www.facebook.com/v19.0/dialog/oauth?{urllib.parse.urlencode(params)}", state

    def exchange_code(self, code):
        app_id, app_secret, redirect_uri = self.get_app_credentials()
        # Instagram Business OAuth token exchange uses POST to api.instagram.com/oauth/access_token
        data = {
            'client_id': app_id,
            'client_secret': app_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code': code
        }
        res = requests.post("https://api.instagram.com/oauth/access_token", data=data, timeout=10)
        res_data = res.json()
        if 'error' in res_data or 'error_message' in res_data:
            err_msg = res_data.get('error_message') or res_data.get('error', {}).get('message', str(res_data))
            # Fallback to Meta Graph token exchange if Facebook code was passed
            return self.exchange_code_meta_fallback(code)

        short_token = res_data.get('access_token')
        user_id = res_data.get('user_id')
        return self.get_long_lived_token(short_token)

    def exchange_code_meta_fallback(self, code):
        app_id, app_secret, redirect_uri = self.get_app_credentials()
        params = {
            'client_id': app_id,
            'client_secret': app_secret,
            'redirect_uri': redirect_uri,
            'code': code
        }
        res = requests.get(META_OAUTH_TOKEN_URL, params=params, timeout=10)
        res_data = res.json()
        if 'error' in res_data:
            raise ValueError(f"OAuth Token Exchange Error: {res_data['error'].get('message', res_data['error'])}")
        
        short_token = res_data.get('access_token')
        return self.get_long_lived_token(short_token)

    def get_long_lived_token(self, short_lived_token):
        app_id, app_secret, _ = self.get_app_credentials()
        # Instagram Long-Lived Token Exchange endpoint
        params = {
            'grant_type': 'ig_exchange_token',
            'client_secret': app_secret,
            'access_token': short_lived_token
        }
        res = requests.get("https://graph.instagram.com/access_token", params=params, timeout=10)
        res_data = res.json()
        if 'error' in res_data:
            # Fallback to FB exchange token endpoint
            params_fb = {
                'grant_type': 'fb_exchange_token',
                'client_id': app_id,
                'client_secret': app_secret,
                'fb_exchange_token': short_lived_token
            }
            res = requests.get(f"{META_GRAPH_URL}/oauth/access_token", params=params_fb, timeout=10)
            res_data = res.json()
            if 'error' in res_data:
                raise ValueError(f"Long-Lived Token Exchange Error: {res_data['error'].get('message', res_data['error'])}")

        access_token = res_data.get('access_token')
        expires_in = res_data.get('expires_in', 5184000) # Default 60 days
        expires_at = timezone.now() + timedelta(seconds=expires_in)
        return access_token, expires_at

    def get_instagram_account_data(self, access_token):
        # First try direct Instagram Graph API profile endpoint
        res = requests.get(
            "https://graph.instagram.com/v19.0/me",
            params={'access_token': access_token, 'fields': 'id,username,name,profile_picture_url,account_type'},
            timeout=10
        )
        ig_data = res.json()
        if 'id' in ig_data and 'username' in ig_data:
            return {
                'instagram_user_id': str(ig_data.get('id')),
                'username': ig_data.get('username'),
                'display_name': ig_data.get('name', ig_data.get('username')),
                'profile_picture': ig_data.get('profile_picture_url', ''),
                'account_type': ig_data.get('account_type', 'BUSINESS')
            }

        # Fallback to Meta Facebook Pages discovery endpoint
        res_fb = requests.get(
            f"{META_GRAPH_URL}/me/accounts",
            params={'access_token': access_token, 'fields': 'id,name,instagram_business_account'},
            timeout=10
        )
        data = res_fb.json()
        if 'error' in data:
            raise ValueError(f"Failed to fetch Instagram account info: {data['error'].get('message', data['error'])}")

        pages = data.get('data', [])
        ig_business_id = None
        for page in pages:
            if 'instagram_business_account' in page:
                ig_business_id = page['instagram_business_account']['id']
                break

        if not ig_business_id:
            raise ValueError("No Instagram Business/Creator Account found.")

        ig_res = requests.get(
            f"{META_GRAPH_URL}/{ig_business_id}",
            params={'access_token': access_token, 'fields': 'id,username,name,profile_picture_url'},
            timeout=10
        )
        ig_data = ig_res.json()
        if 'error' in ig_data:
            raise ValueError(f"Failed to fetch Instagram account info: {ig_data['error'].get('message', ig_data['error'])}")

        return {
            'instagram_user_id': ig_data.get('id'),
            'username': ig_data.get('username'),
            'display_name': ig_data.get('name', ''),
            'profile_picture': ig_data.get('profile_picture_url', ''),
            'account_type': 'BUSINESS'
        }

    def connect_account(self, account_data, access_token, expires_at, existing_account_id=None):
        from ..models import InstagramAccount

        user_id = account_data['instagram_user_id']
        account = None
        if existing_account_id:
            account = InstagramAccount.objects.filter(id=existing_account_id).first()

        if not account:
            account = InstagramAccount.objects.filter(instagram_user_id=user_id).first()

        if account:
            account.username = account_data['username']
            account.display_name = account_data['display_name']
            account.profile_picture = account_data['profile_picture']
            account.access_token = access_token
            account.token_expires_at = expires_at
            account.is_connected = True
            account.is_active = True
            account.connection_status = InstagramAccount.ConnectionStatus.CONNECTED
            account.connection_error = ""
            account.last_synced_at = timezone.now()
            account.save()
        else:
            account = InstagramAccount.objects.create(
                instagram_user_id=user_id,
                username=account_data['username'],
                display_name=account_data['display_name'],
                profile_picture=account_data['profile_picture'],
                access_token=access_token,
                token_expires_at=expires_at,
                is_connected=True,
                is_active=True,
                connection_status=InstagramAccount.ConnectionStatus.CONNECTED,
                last_synced_at=timezone.now()
            )
        return account

    def disconnect_account(self, account):
        account.is_connected = False
        account.is_active = False
        account.connection_status = account.ConnectionStatus.DISCONNECTED
        account.access_token = ""
        account.save(update_fields=['is_connected', 'is_active', 'connection_status', 'access_token'])
        return account
