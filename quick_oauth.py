#!/usr/bin/env python3
"""
Quick Instagram OAuth — opens browser + catches callback on localhost:8765.
Automatically exchanges code, upgrades to long-lived token, saves to .env.

Usage: python quick_oauth.py [--fb]
  --fb    Use Facebook Login flow instead of Instagram Business Login
"""

import http.server
import json
import os
import re
import sys
import threading
import time
import webbrowser
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
USE_FB = '--fb' in sys.argv

# Config: Facebook Login uses the Meta app; Instagram Login uses the Instagram app.
APP_ID = os.environ['META_APP_ID' if USE_FB else 'INSTAGRAM_APP_ID']
APP_SECRET = os.environ['META_APP_SECRET' if USE_FB else 'INSTAGRAM_APP_SECRET']
PORT = 8765
REDIRECT = f'http://localhost:{PORT}/callback'
API_VER = 'v26.0'

result_holder = {'done': False, 'data': None}


def save_to_env(token, ig_id='', ig_user=''):
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write(f'INSTAGRAM_ACCESS_TOKEN={token}\n')
        return
    with open(env_path, 'r') as f:
        c = f.read()
    if 'INSTAGRAM_ACCESS_TOKEN=' in c:
        c = re.sub(r'^INSTAGRAM_ACCESS_TOKEN=.*$', f'INSTAGRAM_ACCESS_TOKEN={token}', c, flags=re.MULTILINE)
    else:
        c += f'\nINSTAGRAM_ACCESS_TOKEN={token}\n'
    if ig_id:
        if 'INSTAGRAM_ACCOUNT_ID=' in c:
            c = re.sub(r'^INSTAGRAM_ACCOUNT_ID=.*$', f'INSTAGRAM_ACCOUNT_ID={ig_id}', c, flags=re.MULTILINE)
        else:
            c += f'\nINSTAGRAM_ACCOUNT_ID={ig_id}\n'
    if ig_user:
        if 'INSTAGRAM_ACCOUNT_HANDLE=' in c:
            c = re.sub(r'^INSTAGRAM_ACCOUNT_HANDLE=.*$', f'INSTAGRAM_ACCOUNT_HANDLE={ig_user}', c, flags=re.MULTILINE)
        else:
            c += f'\nINSTAGRAM_ACCOUNT_HANDLE={ig_user}\n'
    with open(env_path, 'w') as f:
        f.write(c)
    print(f'✅ Saved to {env_path}')


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != '/callback':
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)
        if 'error' in params:
            msg = params.get('error_description', params['error'])[0]
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(f'<html><body style="font-family:sans-serif;text-align:center;padding:80px;background:#111;color:#f44"><h1>❌ {msg}</h1></body></html>'.encode())
            print(f'❌ Auth error: {msg}')
            result_holder['done'] = True
            result_holder['data'] = {'error': msg}
            return

        code = params.get('code', [None])[0]
        if not code:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body>No code received</body></html>')
            result_holder['done'] = True
            result_holder['data'] = {'error': 'no_code'}
            return

        try:
            # Exchange code for token
            print('⏳ Exchanging code for token...')
            if USE_FB:
                r = requests.get(f'https://graph.facebook.com/{API_VER}/oauth/access_token', params={
                    'client_id': APP_ID, 'client_secret': APP_SECRET,
                    'redirect_uri': REDIRECT, 'code': code
                }, timeout=30)
            else:
                r = requests.post('https://api.instagram.com/oauth/access_token', data={
                    'client_id': APP_ID, 'client_secret': APP_SECRET,
                    'grant_type': 'authorization_code',
                    'redirect_uri': REDIRECT, 'code': code
                }, timeout=30)

            if r.status_code != 200:
                # Fallback to FB endpoint
                r = requests.get(f'https://graph.facebook.com/{API_VER}/oauth/access_token', params={
                    'client_id': APP_ID, 'client_secret': APP_SECRET,
                    'redirect_uri': REDIRECT, 'code': code
                }, timeout=30)

            td = r.json()
            token = td.get('access_token')
            if not token:
                raise ValueError(f'No token in response: {td}')
            print(f'✅ Got short-lived token: {token[:20]}...')

            # Upgrade to long-lived
            print('⏳ Upgrading to long-lived token...')
            lr = requests.get('https://graph.instagram.com/access_token', params={
                'grant_type': 'ig_exchange_token',
                'client_secret': APP_SECRET,
                'access_token': token,
            }, timeout=30)
            if lr.status_code == 200 and 'access_token' in lr.json():
                token = lr.json()['access_token']
                print(f'✅ Long-lived token acquired')
            else:
                lr2 = requests.get(f'https://graph.facebook.com/{API_VER}/oauth/access_token', params={
                    'grant_type': 'fb_exchange_token',
                    'client_id': APP_ID, 'client_secret': APP_SECRET,
                    'fb_exchange_token': token,
                }, timeout=30)
                if lr2.status_code == 200 and 'access_token' in lr2.json():
                    token = lr2.json()['access_token']
                    print(f'✅ Long-lived token (FB) acquired')
                else:
                    print('⚠️  Using short-lived token')

            # Discover IG account
            ig_id = ig_user = ''
            print('⏳ Discovering Instagram account...')
            # Try direct IG /me
            ir = requests.get(f'https://graph.instagram.com/{API_VER}/me', params={
                'access_token': token,
                'fields': 'id,user_id,username,name,account_type',
            }, timeout=15)
            if ir.status_code == 200 and 'username' in ir.json():
                d = ir.json()
                ig_id = str(d.get('user_id') or d.get('id'))
                ig_user = d['username']
                print(f'✅ Instagram: @{ig_user} (ID: {ig_id})')
            else:
                # Try FB Pages
                pr = requests.get(f'https://graph.facebook.com/{API_VER}/me/accounts', params={
                    'access_token': token,
                    'fields': 'id,name,instagram_business_account{id,username}',
                }, timeout=15)
                if pr.status_code == 200:
                    for p in pr.json().get('data', []):
                        ig = p.get('instagram_business_account')
                        if ig:
                            ig_id = str(ig['id'])
                            ig_user = ig.get('username', '')
                            print(f'✅ Instagram via Page: @{ig_user} (ID: {ig_id})')
                            break
                if not ig_user:
                    # Try FB /me
                    mr = requests.get(f'https://graph.facebook.com/{API_VER}/me', params={
                        'access_token': token, 'fields': 'id,name'
                    }, timeout=15)
                    if mr.status_code == 200:
                        d = mr.json()
                        print(f'✅ Authenticated as: {d.get("name")} (ID: {d["id"]})')

            save_to_env(token, ig_id, ig_user)

            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(f'''
            <html><body style="font-family:system-ui;text-align:center;padding:60px;background:#0d1117;color:#e6edf3">
            <div style="max-width:550px;margin:0 auto;background:#161b22;border:1px solid #30363d;border-radius:12px;padding:40px">
            <h1 style="color:#3fb950">✅ Connected!</h1>
            <p style="font-size:18px;color:#8b949e">Account: <b style="color:#58a6ff">@{ig_user or "unknown"}</b></p>
            <p style="font-size:16px;color:#8b949e">Token saved to <code>.env</code></p>
            <p style="font-size:14px;color:#6e7681;margin-top:20px">You can close this tab.</p>
            </div></body></html>
            '''.encode())

            print(f'\n{"="*50}')
            print(f'🎉 SUCCESS!')
            print(f'   Token: {token[:25]}...{token[-10:]}')
            print(f'   Account: @{ig_user}')
            print(f'   ID: {ig_id}')
            print(f'{"="*50}')
            result_holder['done'] = True
            result_holder['data'] = {'token': token, 'ig_id': ig_id, 'ig_user': ig_user}

        except Exception as e:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(f'<html><body style="font-family:sans-serif;text-align:center;padding:80px;background:#111;color:#f44"><h1>❌ {e}</h1></body></html>'.encode())
            print(f'❌ Error: {e}')
            result_holder['done'] = True
            result_holder['data'] = {'error': str(e)}

    def log_message(self, *a):
        pass


# Build auth URL
if USE_FB:
    scopes = 'pages_show_list,pages_read_engagement,instagram_basic,instagram_content_publish'
    url = f'https://www.facebook.com/{API_VER}/dialog/oauth?{urlencode({"client_id": APP_ID, "redirect_uri": REDIRECT, "scope": scopes, "response_type": "code"})}'
else:
    scopes = 'instagram_business_basic,instagram_business_content_publish'
    url = f'https://www.instagram.com/oauth/authorize?{urlencode({"client_id": APP_ID, "redirect_uri": REDIRECT, "scope": scopes, "response_type": "code"})}'

print(f'\n{"="*50}')
print(f'🔗 Instagram Token Setup')
print(f'{"="*50}')
print(f'Mode: {"Facebook Login" if USE_FB else "Instagram Business Login"}')
print(f'Redirect: {REDIRECT}')
print(f'\n⚠️  Make sure {REDIRECT}')
print(f'   is in your app\'s Valid OAuth Redirect URIs!')
if USE_FB:
    print(f'   → https://developers.facebook.com/apps/{APP_ID}/fb-login/settings/')
else:
    print(f'   → https://developers.facebook.com/apps/{APP_ID}/instagram-business/basic-display/')
print()

# Start server
srv = http.server.HTTPServer(('localhost', PORT), Handler)
t = threading.Thread(target=srv.serve_forever, daemon=True)
t.start()
print(f'🌐 Callback server: http://localhost:{PORT}')
print(f'🔓 Opening browser...\n')
webbrowser.open(url)
print(f'⏳ Waiting for authorization (Ctrl+C to cancel)...\n')

try:
    while not result_holder['done']:
        time.sleep(0.5)
except KeyboardInterrupt:
    print('\n⚠️ Cancelled.')

srv.shutdown()
