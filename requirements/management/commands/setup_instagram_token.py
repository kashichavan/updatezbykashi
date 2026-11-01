"""
Connects @ikashii_07: python manage.py setup_instagram_token

Paste a token when prompted (hidden input, so it stays out of shell history):
  IG...  from Instagram > API setup with Instagram login > Generate access tokens
  EA...  from Graph API Explorer, Facebook Login

The token is upgraded to long-lived, checked against the configured account,
and only then written to .env.
"""
import getpass
import os
import re
import sys

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

TIMEOUT = 20


def graph_error(data):
    return data.get('error', {}).get('message', str(data)) if isinstance(data, dict) else str(data)


class Command(BaseCommand):
    help = "Upgrades an Instagram/Meta token to long-lived, verifies the account, and saves it to .env."

    def add_arguments(self, parser):
        parser.add_argument('token', nargs='?', default=None,
                            help='Optional. Leave out to be prompted, which keeps it out of shell history.')
        parser.add_argument('--from-stdin', action='store_true',
                            help='Read the token, then an optional Instagram app secret, one per line.')

    def handle(self, *args, **options):
        self.stdin_lines = sys.stdin.read().splitlines() if options['from_stdin'] else None
        if self.stdin_lines is not None:
            token = self.stdin_lines[0].strip() if self.stdin_lines else ''
        else:
            token = (options['token'] or getpass.getpass('Paste access token (hidden): ')).strip()
        if not token:
            raise CommandError('No token provided.')

        self.version = settings.INSTAGRAM_API_VERSION
        self.expected_id = str(settings.INSTAGRAM_ACCOUNT_ID)
        self.expected_handle = settings.INSTAGRAM_ACCOUNT_HANDLE

        try:
            if token.startswith('IG'):
                final_token, ig_id, username, host = self.instagram_login(token)
            else:
                final_token, ig_id, username, host = self.facebook_login(token)
            self.check_publishing(final_token, ig_id, host)
        except requests.RequestException as exc:
            # str(exc) can contain the request URL, and so the token.
            raise CommandError(f'Network error contacting Meta: {type(exc).__name__}')

        self.write_env({
            'INSTAGRAM_ACCESS_TOKEN': final_token,
            'INSTAGRAM_ACCOUNT_ID': ig_id,
            'INSTAGRAM_ACCOUNT_HANDLE': username,
        })
        self.stdout.write(self.style.SUCCESS(f'Connected @{username} ({ig_id}). Token saved to .env.'))

    def instagram_login(self, token):
        host = 'graph.instagram.com'
        self.stdout.write('[1/3] Instagram Login token. Reading account...')
        resp = requests.get(f'https://{host}/{self.version}/me', timeout=TIMEOUT, params={
            'fields': 'user_id,username,account_type', 'access_token': token})
        me = resp.json()
        if resp.status_code != 200:
            raise CommandError(f'Token rejected: {graph_error(me)}')
        ig_id, username = str(me.get('user_id')), me.get('username', '')
        self.check_account(ig_id, username)
        self.stdout.write(f"      @{username}, {me.get('account_type')}")

        self.stdout.write('[2/3] Upgrading to a 60-day token...')
        secret = settings.INSTAGRAM_APP_SECRET or self.prompt_secret()
        if not secret:
            self.stdout.write(self.style.WARNING(
                '      Skipped. Dashboard tokens may already be long-lived; this was not confirmed.'))
            return token, ig_id, username, host
        resp = requests.get(f'https://{host}/access_token', timeout=TIMEOUT, params={
            'grant_type': 'ig_exchange_token', 'client_secret': secret, 'access_token': token})
        data = resp.json()
        if 'access_token' in data:
            self.stdout.write(f"      Valid for {data.get('expires_in', 0) // 86400} days.")
            return data['access_token'], ig_id, username, host
        self.stdout.write(self.style.WARNING(
            f'      Not upgraded ({graph_error(data)}). Keeping the pasted token; '
            'it may already be long-lived, which was not confirmed.'))
        return token, ig_id, username, host

    def prompt_secret(self):
        if self.stdin_lines is not None:
            return self.stdin_lines[1].strip() if len(self.stdin_lines) > 1 else ''
        return getpass.getpass('Instagram app secret (Business login settings, hidden; Enter to skip): ').strip()

    def facebook_login(self, token):
        host = 'graph.facebook.com'
        base = f'https://{host}/{self.version}'
        app_id, secret = settings.META_APP_ID, settings.META_APP_SECRET
        if not (app_id and secret):
            raise CommandError('META_APP_ID and META_APP_SECRET must be set in .env.')

        self.stdout.write('[1/3] Facebook token. Checking permissions...')
        resp = requests.get(f'{base}/debug_token', timeout=TIMEOUT, params={
            'input_token': token, 'access_token': f'{app_id}|{secret}'})
        info = resp.json().get('data', {})
        if resp.status_code != 200 or not info.get('is_valid'):
            raise CommandError(f"Token rejected: {info.get('error', {}).get('message') or graph_error(resp.json())}")
        if info.get('type') != 'USER':
            raise CommandError(f"Expected a User token, got {info.get('type')}. "
                               'Choose "User Token" in Graph API Explorer.')
        required = {'instagram_basic', 'instagram_content_publish', 'pages_show_list', 'pages_read_engagement'}
        missing = required - set(info.get('scopes', []))
        if missing:
            raise CommandError(f"Token is missing: {', '.join(sorted(missing))}. Add them and regenerate.")

        self.stdout.write('[2/3] Upgrading, then finding the linked Page...')
        resp = requests.get(f'{base}/oauth/access_token', timeout=TIMEOUT, params={
            'grant_type': 'fb_exchange_token', 'client_id': app_id,
            'client_secret': secret, 'fb_exchange_token': token})
        data = resp.json()
        if 'access_token' not in data:
            raise CommandError(f'Long-lived exchange failed: {graph_error(data)}')

        resp = requests.get(f'{base}/me/accounts', timeout=TIMEOUT, params={
            'fields': 'name,access_token,instagram_business_account{id,username}',
            'access_token': data['access_token']})
        pages = resp.json()
        if resp.status_code != 200:
            raise CommandError(f'Could not list Pages: {graph_error(pages)}')
        for page in pages.get('data', []):
            ig = page.get('instagram_business_account') or {}
            if str(ig.get('id')) == self.expected_id:
                self.stdout.write(f"      Page '{page.get('name')}' is linked to @{ig.get('username')}.")
                return page['access_token'], self.expected_id, ig.get('username', ''), host
        raise CommandError(
            f"No Page available to this token is linked to @{self.expected_handle}. Link the account to a "
            'Facebook Page in Instagram settings, then select that Page when authorizing. .env was not changed.')

    def check_account(self, ig_id, username):
        if ig_id != self.expected_id:
            raise CommandError(
                f'Token belongs to @{username} ({ig_id}), expected @{self.expected_handle} '
                f'({self.expected_id}). .env was not changed.')

    def check_publishing(self, token, ig_id, host):
        self.stdout.write('[3/3] Confirming publishing access...')
        resp = requests.get(f'https://{host}/{self.version}/{ig_id}/content_publishing_limit', timeout=TIMEOUT,
                            params={'fields': 'quota_usage', 'access_token': token})
        if resp.status_code != 200:
            raise CommandError(f'Publishing access check failed: {graph_error(resp.json())}. .env was not changed.')

    def write_env(self, updates):
        path = os.path.join(settings.BASE_DIR, '.env')
        content = ''
        if os.path.exists(path):
            with open(path, encoding='utf-8') as fh:
                content = fh.read()
        for key, value in updates.items():
            line = f'{key}={value}'
            content, count = re.subn(rf'^{key}=.*$', lambda _m: line, content, flags=re.MULTILINE)
            if not count:
                content = f"{content.rstrip()}\n{line}\n"
        tmp = f'{path}.tmp'
        with open(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w', encoding='utf-8') as fh:
            fh.write(content)
        os.replace(tmp, path)
