#!/usr/bin/env python3
"""
One-Click Instagram OAuth Token Fetcher for KashiiUpdatez.

Usage:
    python get_instagram_token.py

What it does:
1. Opens your browser to Instagram's OAuth authorization page.
2. Starts a local HTTP server on port 8765 to catch the redirect.
3. Exchanges the auth code for a short-lived access token.
4. Upgrades it to a long-lived (~60 day) token.
5. Discovers your Instagram Professional/Creator account.
6. Writes INSTAGRAM_ACCESS_TOKEN to .env automatically.
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

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
META_APP_ID = os.environ['INSTAGRAM_APP_ID']
META_APP_SECRET = os.environ['INSTAGRAM_APP_SECRET']
LOCAL_PORT = 8765
REDIRECT_URI = f'http://localhost:{LOCAL_PORT}/callback'
API_VERSION = 'v26.0'

# Instagram Business Login permissions
# These are the permissions needed for story publishing
SCOPES = [
    'instagram_business_basic',
    'instagram_business_content_publish',
]

# ─────────────────────────────────────────────
# Token exchange functions
# ─────────────────────────────────────────────

def exchange_code_for_token(code: str) -> dict:
    """Exchange the authorization code for a short-lived access token."""
    print("\n⏳ Exchanging authorization code for access token...")
    resp = requests.post(
        'https://api.instagram.com/oauth/access_token',
        data={
            'client_id': META_APP_ID,
            'client_secret': META_APP_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'code': code,
        },
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"❌ Token exchange failed: {resp.status_code}")
        print(f"   Response: {resp.text}")
        # Try Facebook Graph API as fallback
        print("\n⏳ Trying Facebook Graph API token exchange...")
        resp2 = requests.get(
            f'https://graph.facebook.com/{API_VERSION}/oauth/access_token',
            params={
                'client_id': META_APP_ID,
                'client_secret': META_APP_SECRET,
                'redirect_uri': REDIRECT_URI,
                'code': code,
            },
            timeout=30,
        )
        if resp2.status_code == 200:
            return resp2.json()
        print(f"❌ Facebook token exchange also failed: {resp2.status_code}")
        print(f"   Response: {resp2.text}")
        sys.exit(1)
    return resp.json()


def exchange_for_long_lived_token(short_token: str) -> dict:
    """Exchange short-lived token for a long-lived (~60 day) token."""
    print("⏳ Upgrading to long-lived token (~60 days)...")

    # Try Instagram endpoint first
    resp = requests.get(
        'https://graph.instagram.com/access_token',
        params={
            'grant_type': 'ig_exchange_token',
            'client_secret': META_APP_SECRET,
            'access_token': short_token,
        },
        timeout=30,
    )
    if resp.status_code == 200:
        data = resp.json()
        if 'access_token' in data:
            days = data.get('expires_in', 5184000) // 86400
            print(f"✅ Long-lived token acquired (valid ~{days} days)")
            return data

    # Fallback to Facebook endpoint
    resp2 = requests.get(
        f'https://graph.facebook.com/{API_VERSION}/oauth/access_token',
        params={
            'grant_type': 'fb_exchange_token',
            'client_id': META_APP_ID,
            'client_secret': META_APP_SECRET,
            'fb_exchange_token': short_token,
        },
        timeout=30,
    )
    if resp2.status_code == 200:
        data = resp2.json()
        if 'access_token' in data:
            days = data.get('expires_in', 5184000) // 86400
            print(f"✅ Long-lived token acquired via Facebook (valid ~{days} days)")
            return data

    print("⚠️  Could not upgrade to long-lived token. Using short-lived token.")
    return {'access_token': short_token, 'expires_in': 3600}


def discover_instagram_account(access_token: str) -> dict:
    """Find the Instagram Professional/Creator account linked to this token."""
    print("⏳ Discovering linked Instagram account...")

    # Strategy 1: Direct Instagram /me endpoint
    try:
        resp = requests.get(
            f'https://graph.instagram.com/{API_VERSION}/me',
            params={
                'access_token': access_token,
                'fields': 'id,user_id,username,name,account_type,profile_picture_url,followers_count,media_count',
            },
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            if 'username' in data:
                ig_id = data.get('user_id') or data.get('id')
                print(f"✅ Found Instagram account: @{data['username']} (ID: {ig_id})")
                return {
                    'id': str(ig_id),
                    'username': data['username'],
                    'name': data.get('name', ''),
                    'account_type': data.get('account_type', ''),
                }
    except Exception as e:
        print(f"   Direct IG lookup skipped: {e}")

    # Strategy 2: Facebook Pages → Instagram Business Account
    try:
        resp = requests.get(
            f'https://graph.facebook.com/{API_VERSION}/me/accounts',
            params={
                'access_token': access_token,
                'fields': 'id,name,instagram_business_account{id,username,name,profile_picture_url}',
                'limit': 50,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            for page in resp.json().get('data', []):
                ig = page.get('instagram_business_account')
                if ig and ig.get('username'):
                    print(f"✅ Found Instagram account via Page: @{ig['username']} (ID: {ig['id']})")
                    return {
                        'id': str(ig['id']),
                        'username': ig['username'],
                        'name': ig.get('name', ''),
                        'page_id': page['id'],
                    }
    except Exception as e:
        print(f"   FB Pages lookup skipped: {e}")

    # Strategy 3: Direct Facebook /me
    try:
        resp = requests.get(
            f'https://graph.facebook.com/{API_VERSION}/me',
            params={'access_token': access_token, 'fields': 'id,name'},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Authenticated as: {data.get('name', 'Unknown')} (FB ID: {data['id']})")
            return {'id': data['id'], 'username': '', 'name': data.get('name', '')}
    except Exception:
        pass

    print("⚠️  Could not discover Instagram account details, but token is valid.")
    return {}


def update_env_file(token: str, ig_id: str = '', ig_username: str = ''):
    """Write the token (and optionally IG account info) to .env file."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

    if not os.path.exists(env_path):
        print(f"⚠️  No .env file found at {env_path}. Creating one.")
        with open(env_path, 'w') as f:
            f.write(f'INSTAGRAM_ACCESS_TOKEN={token}\n')
        return

    with open(env_path, 'r') as f:
        content = f.read()

    # Update or add INSTAGRAM_ACCESS_TOKEN
    if 'INSTAGRAM_ACCESS_TOKEN=' in content:
        content = re.sub(
            r'^INSTAGRAM_ACCESS_TOKEN=.*$',
            f'INSTAGRAM_ACCESS_TOKEN={token}',
            content,
            flags=re.MULTILINE,
        )
    else:
        content = content.rstrip('\n') + f'\nINSTAGRAM_ACCESS_TOKEN={token}\n'

    # Update INSTAGRAM_ACCOUNT_ID if discovered
    if ig_id:
        if 'INSTAGRAM_ACCOUNT_ID=' in content:
            content = re.sub(
                r'^INSTAGRAM_ACCOUNT_ID=.*$',
                f'INSTAGRAM_ACCOUNT_ID={ig_id}',
                content,
                flags=re.MULTILINE,
            )
        else:
            content = content.rstrip('\n') + f'\nINSTAGRAM_ACCOUNT_ID={ig_id}\n'

    # Update INSTAGRAM_ACCOUNT_HANDLE if discovered
    if ig_username:
        if 'INSTAGRAM_ACCOUNT_HANDLE=' in content:
            content = re.sub(
                r'^INSTAGRAM_ACCOUNT_HANDLE=.*$',
                f'INSTAGRAM_ACCOUNT_HANDLE={ig_username}',
                content,
                flags=re.MULTILINE,
            )
        else:
            content = content.rstrip('\n') + f'\nINSTAGRAM_ACCOUNT_HANDLE={ig_username}\n'

    with open(env_path, 'w') as f:
        f.write(content)

    print(f"✅ Token saved to {env_path}")


# ─────────────────────────────────────────────
# Local OAuth callback server
# ─────────────────────────────────────────────

class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Handles the OAuth redirect callback on localhost."""

    token_result = None
    use_fb_exchange = False  # Set True for Facebook Login flow

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == '/callback':
            params = parse_qs(parsed.query)

            # Check for errors
            if 'error' in params:
                error = params['error'][0]
                desc = params.get('error_description', ['Unknown'])[0]
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(f"""
                <html><body style="font-family:system-ui;text-align:center;padding:60px;background:#1a1a2e;color:#fff">
                <h1>❌ Authorization Failed</h1>
                <p style="color:#ff6b6b;font-size:18px">{error}: {desc}</p>
                <p>Close this tab and try again.</p>
                </body></html>
                """.encode())
                print(f"\n❌ Authorization denied: {error} — {desc}")
                OAuthCallbackHandler.token_result = {'error': error}
                return

            # Get the authorization code
            code = params.get('code', [None])[0]
            if not code:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(b"""
                <html><body style="font-family:system-ui;text-align:center;padding:60px;background:#1a1a2e;color:#fff">
                <h1>&#x26A0; No Authorization Code</h1>
                <p>No code was received in the callback. Please try again.</p>
                </body></html>
                """)
                OAuthCallbackHandler.token_result = {'error': 'no_code'}
                return

            # Success — exchange the code
            try:
                if OAuthCallbackHandler.use_fb_exchange:
                    # Facebook Login flow — exchange via Facebook Graph API
                    token_data = {}
                    resp = requests.get(
                        f'https://graph.facebook.com/{API_VERSION}/oauth/access_token',
                        params={
                            'client_id': META_APP_ID,
                            'client_secret': META_APP_SECRET,
                            'redirect_uri': REDIRECT_URI,
                            'code': code,
                        },
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        token_data = resp.json()
                    else:
                        raise ValueError(f"FB token exchange failed: {resp.status_code} {resp.text}")
                else:
                    token_data = exchange_code_for_token(code)
                short_token = token_data.get('access_token')
                if not short_token:
                    raise ValueError(f"No access_token in response: {token_data}")

                # Upgrade to long-lived token
                long_data = exchange_for_long_lived_token(short_token)
                final_token = long_data.get('access_token', short_token)

                # Discover Instagram account
                ig_info = discover_instagram_account(final_token)

                # Save to .env
                update_env_file(
                    token=final_token,
                    ig_id=ig_info.get('id', ''),
                    ig_username=ig_info.get('username', ''),
                )

                ig_name = ig_info.get('username', 'your account')

                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(f"""
                <html><body style="font-family:system-ui;text-align:center;padding:60px;background:#0d1117;color:#e6edf3">
                <div style="max-width:600px;margin:0 auto;background:#161b22;border:1px solid #30363d;border-radius:12px;padding:40px">
                <h1 style="color:#3fb950;margin-bottom:24px">✅ Instagram Connected!</h1>
                <p style="font-size:18px;color:#8b949e">Account: <strong style="color:#58a6ff">@{ig_name}</strong></p>
                <p style="font-size:16px;color:#8b949e">Token saved to <code style="background:#21262d;padding:4px 8px;border-radius:4px">.env</code></p>
                <p style="font-size:14px;color:#6e7681;margin-top:24px">You can close this tab now.</p>
                <p style="font-size:14px;color:#6e7681">Restart your Django server to pick up the new token.</p>
                </div>
                </body></html>
                """.encode())

                OAuthCallbackHandler.token_result = {
                    'token': final_token,
                    'ig_info': ig_info,
                }

                print(f"\n{'='*60}")
                print(f"🎉 SUCCESS! Instagram token acquired and saved!")
                print(f"   Account: @{ig_name}")
                print(f"   Token: {final_token[:20]}...{final_token[-10:]}")
                print(f"   Saved to: .env")
                print(f"{'='*60}")

            except Exception as e:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(f"""
                <html><body style="font-family:system-ui;text-align:center;padding:60px;background:#1a1a2e;color:#fff">
                <h1>❌ Token Exchange Failed</h1>
                <p style="color:#ff6b6b;font-size:16px">{str(e)}</p>
                <p>Check the terminal for details.</p>
                </body></html>
                """.encode())
                print(f"\n❌ Error during token exchange: {e}")
                OAuthCallbackHandler.token_result = {'error': str(e)}

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default HTTP log messages."""
        pass


def main():
    print("=" * 60)
    print("  🔗 KashiiUpdatez Instagram Token Setup")
    print("=" * 60)
    print(f"\n  App ID:       {META_APP_ID}")
    print(f"  Redirect URI: {REDIRECT_URI}")

    # ── IMPORTANT: Check if redirect URI is registered ──
    print(f"\n{'─'*60}")
    print("  ⚠️  BEFORE PROCEEDING, you need TWO things in your")
    print("     Meta Developer Console:")
    print()
    print("  1️⃣  ADD 'Instagram' product to your app:")
    print(f"     → https://developers.facebook.com/apps/{META_APP_ID}/add-product/")
    print("     → Find 'Instagram' and click 'Set Up'")
    print()
    print("  2️⃣  ADD this redirect URI to your Instagram app settings:")
    print(f"     → https://developers.facebook.com/apps/{META_APP_ID}/instagram-business/basic-display/")
    print(f"     → Under 'Valid OAuth Redirect URIs' add:")
    print(f"       {REDIRECT_URI}")
    print(f"{'─'*60}")

    print("\nChoose auth flow:")
    print("  [1] Instagram Business Login (recommended)")
    print("  [2] Facebook Login (fallback — if Instagram product isn't added)")
    print("  [3] Manual token paste (if you already have a token)")

    choice = input("\nEnter choice (1/2/3): ").strip()

    if choice == '3':
        token = input("\n📋 Paste your access token: ").strip()
        if not token:
            print("❌ No token provided.")
            sys.exit(1)

        # Validate the token
        print("⏳ Validating token...")
        ig_info = discover_instagram_account(token)

        # Try upgrading to long-lived
        long_data = exchange_for_long_lived_token(token)
        final_token = long_data.get('access_token', token)

        update_env_file(
            token=final_token,
            ig_id=ig_info.get('id', ''),
            ig_username=ig_info.get('username', ''),
        )

        print("\n✅ All done! Restart your Django server to use the new token.")
        print("   Run: cd /Users/kashinath/Desktop/updatezbykashi && env/bin/python manage.py runserver")
        return

    if choice == '2':
        # Facebook Login flow — works even without Instagram product
        OAuthCallbackHandler.use_fb_exchange = True
        fb_scopes = [
            'pages_show_list',
            'pages_read_engagement',
            'instagram_basic',
            'instagram_content_publish',
        ]
        auth_params = {
            'client_id': META_APP_ID,
            'redirect_uri': REDIRECT_URI,
            'scope': ','.join(fb_scopes),
            'response_type': 'code',
            'state': 'kashiiupdatez_fb_login',
        }
        auth_url = f'https://www.facebook.com/v18.0/dialog/oauth?{urlencode(auth_params)}'
        print(f"\n  ⚠️  For Facebook Login flow, add this redirect URI in:")
        print(f"     → https://developers.facebook.com/apps/{META_APP_ID}/fb-login/settings/")
        print(f"     → Valid OAuth Redirect URIs: {REDIRECT_URI}")
    else:
        # Instagram Business Login flow
        auth_params = {
            'client_id': META_APP_ID,
            'redirect_uri': REDIRECT_URI,
            'scope': ','.join(SCOPES),
            'response_type': 'code',
            'state': 'kashiiupdatez_token_setup',
        }
        auth_url = f'https://www.instagram.com/oauth/authorize?{urlencode(auth_params)}'

    input(f"\n  Press Enter when you've added the redirect URI, or Ctrl+C to cancel...")

    # Start local server
    server = http.server.HTTPServer(('localhost', LOCAL_PORT), OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"\n🌐 Local callback server started on http://localhost:{LOCAL_PORT}")

    # Open browser
    print(f"🔓 Opening browser for authorization...")
    print(f"   URL: {auth_url}\n")
    webbrowser.open(auth_url)

    print("⏳ Waiting for authorization... (press Ctrl+C to cancel)\n")

    try:
        while OAuthCallbackHandler.token_result is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user.")
        server.shutdown()
        sys.exit(0)

    server.shutdown()

    if OAuthCallbackHandler.token_result.get('error'):
        print(f"\n❌ Failed. Error: {OAuthCallbackHandler.token_result['error']}")
        sys.exit(1)

    print("\n✅ All done! Restart your Django server to use the new token.")
    print("   Run: cd /Users/kashinath/Desktop/updatezbykashi && env/bin/python manage.py runserver")


if __name__ == '__main__':
    main()
