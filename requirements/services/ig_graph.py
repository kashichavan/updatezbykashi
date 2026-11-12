"""Instagram Graph API (Instagram Login) for Updatez's own Meta app.

Covers OAuth, token refresh, publishing stories/reels, comment replies, private replies,
DMs with buttons, follow checks and webhook subscription. Tokens stay server-side.
"""
import logging
import time
from datetime import timedelta
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

SCOPES = [
    'instagram_business_basic',
    'instagram_business_content_publish',
    'instagram_business_manage_comments',
    'instagram_business_manage_messages',
]
WEBHOOK_FIELDS = 'comments,messages,messaging_postbacks'


class IGError(Exception):
    def __init__(self, message, code=None, needs_reconnect=False):
        super().__init__(message)
        self.code = code
        self.needs_reconnect = needs_reconnect


def _ver():
    return getattr(settings, 'INSTAGRAM_API_VERSION', 'v26.0')


def _base():
    return f"https://graph.instagram.com/{_ver()}"


def _check(resp, fallback):
    try:
        data = resp.json()
    except ValueError:
        data = {}
    if resp.status_code == 200 and 'error' not in data:
        return data
    err = data.get('error') or {}
    msg = err.get('message') or f"{fallback} (HTTP {resp.status_code})"
    code = err.get('code')
    raise IGError(msg, code=code, needs_reconnect=code in (190, 10, 200, 3) or 'permission' in msg.lower())


# --------------------------------------------------------------------------- OAuth

def authorize_url(state):
    params = {
        'client_id': settings.INSTAGRAM_APP_ID,
        'redirect_uri': settings.INSTAGRAM_REDIRECT_URI,
        'response_type': 'code',
        'scope': ','.join(SCOPES),
        'state': state,
        'force_reauth': 'true',  # show the account picker so a second account can be connected
    }
    return f"https://www.instagram.com/oauth/authorize?{urlencode(params)}"


def exchange_code(code):
    """code → long-lived token + profile. Returns dict(access_token, expires_at, ig_user_id, username)."""
    code = (code or '').split('#')[0]
    short = _check(requests.post('https://api.instagram.com/oauth/access_token', data={
        'client_id': settings.INSTAGRAM_APP_ID,
        'client_secret': settings.INSTAGRAM_APP_SECRET,
        'grant_type': 'authorization_code',
        'redirect_uri': settings.INSTAGRAM_REDIRECT_URI,
        'code': code,
    }, timeout=30), 'Code exchange failed')
    long = _check(requests.get('https://graph.instagram.com/access_token', params={
        'grant_type': 'ig_exchange_token',
        'client_secret': settings.INSTAGRAM_APP_SECRET,
        'access_token': short['access_token'],
    }, timeout=30), 'Long-lived token exchange failed')
    token = long['access_token']
    me = _check(requests.get(f"{_base()}/me", params={
        'fields': 'user_id,username', 'access_token': token}, timeout=20), 'Profile lookup failed')
    return {
        'access_token': token,
        'expires_at': timezone.now() + timedelta(seconds=int(long.get('expires_in') or 5184000)),
        'ig_user_id': str(me.get('user_id') or me.get('id')),
        'username': me.get('username', ''),
    }


def refresh_if_needed(account, days=10):
    """Long-lived tokens last 60 days; refresh when fewer than `days` remain."""
    if account.token_expires_at and account.token_expires_at - timezone.now() > timedelta(days=days):
        return account
    try:
        data = _check(requests.get('https://graph.instagram.com/refresh_access_token', params={
            'grant_type': 'ig_refresh_token', 'access_token': account.access_token}, timeout=20), 'Token refresh failed')
        account.access_token = data['access_token']
        account.token_expires_at = timezone.now() + timedelta(seconds=int(data.get('expires_in') or 5184000))
        account.refreshed_at = timezone.now()
        account.save(update_fields=['access_token', 'token_expires_at', 'refreshed_at'])
    except IGError as exc:
        logger.warning("Token refresh failed for @%s: %s", account.username, exc)
    return account


def subscribe_webhooks(token):
    try:
        data = _check(requests.post(f"{_base()}/me/subscribed_apps", params={
            'subscribed_fields': WEBHOOK_FIELDS, 'access_token': token}, timeout=15), 'Webhook subscription failed')
        return bool(data.get('success')), 'subscribed'
    except IGError as exc:
        return False, str(exc)


# --------------------------------------------------------------------------- Publishing

def publish_media(account, *, media_type, image_url='', video_url='', caption='', wait_seconds=None):
    """Create a container (STORIES / REELS), wait for processing, publish. Returns the media id."""
    token = account.access_token
    payload = {'media_type': media_type, 'access_token': token}
    if video_url:
        payload['video_url'] = video_url
    else:
        payload['image_url'] = image_url
    if media_type == 'REELS':
        payload['caption'] = caption[:2200]
        payload['share_to_feed'] = 'true'
    container = _check(requests.post(f"{_base()}/{account.ig_user_id}/media", data=payload, timeout=60),
                       'Container creation failed')['id']

    deadline = time.time() + (wait_seconds or (240 if video_url else 60))
    status = 'IN_PROGRESS'
    while time.time() < deadline:
        st = _check(requests.get(f"{_base()}/{container}", params={
            'fields': 'status_code,status', 'access_token': token}, timeout=30), 'Status check failed')
        status = st.get('status_code') or 'UNKNOWN'
        if status == 'FINISHED':
            break
        if status in ('ERROR', 'EXPIRED'):
            raise IGError(f"Instagram could not process the media: {st.get('status') or status}")
        time.sleep(4)
    else:
        raise IGError(f"Media not ready in time (status {status})")

    return str(_check(requests.post(f"{_base()}/{account.ig_user_id}/media_publish", data={
        'creation_id': container, 'access_token': token}, timeout=60), 'Publish failed')['id'])


# --------------------------------------------------------------------------- Comments & DMs

def reply_to_comment(account, comment_id, message):
    return _check(requests.post(f"{_base()}/{comment_id}/replies", data={
        'message': message[:2200], 'access_token': account.access_token}, timeout=20), 'Comment reply failed')


def send_message(account, recipient, text, buttons=None):
    """recipient: {'id': igsid} or {'comment_id': id} (private reply). buttons: [{'title','url'|'payload'}]."""
    message = {'text': text[:1000]}
    if buttons:
        btns = []
        for b in buttons[:3]:
            if b.get('url'):
                btns.append({'type': 'web_url', 'url': b['url'], 'title': b['title'][:20]})
            else:
                btns.append({'type': 'postback', 'payload': b['payload'], 'title': b['title'][:20]})
        message = {'attachment': {'type': 'template', 'payload': {
            'template_type': 'button', 'text': text[:640], 'buttons': btns}}}
    url = f"{_base()}/me/messages"
    headers = {'Authorization': f"Bearer {account.access_token}"}
    resp = requests.post(url, headers=headers, json={'recipient': recipient, 'message': message}, timeout=20)
    if resp.status_code == 200:
        return resp.json()
    if buttons:  # template rejected: fall back to plain text with links appended
        fallback = text + ''.join(f"\n\n👉 {b['title']}: {b['url']}" for b in buttons if b.get('url'))
        resp = requests.post(url, headers=headers, json={'recipient': recipient, 'message': {'text': fallback[:1000]}},
                             timeout=20)
    return _check(resp, 'Message send failed')


def follows_us(account, igsid):
    """True only if Instagram confirms the user follows the account (needs an open conversation)."""
    try:
        data = _check(requests.get(f"{_base()}/{igsid}", params={
            'fields': 'username,is_user_follow_business', 'access_token': account.access_token}, timeout=15),
            'Follow check failed')
        return bool(data.get('is_user_follow_business'))
    except IGError as exc:
        logger.info("Follow check failed for %s: %s", igsid, exc)
        return False
