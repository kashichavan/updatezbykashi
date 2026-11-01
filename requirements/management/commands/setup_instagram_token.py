import os
import re
import requests
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Validates, exchanges for a 60-day long-lived token, and auto-saves Instagram credentials to .env."

    def add_arguments(self, parser):
        parser.add_argument('token', type=str, help='Meta Access Token from Graph API Explorer or Facebook Login')
        parser.add_argument('--app-id', type=str, default=None, help='Override Meta App ID')
        parser.add_argument('--app-secret', type=str, default=None, help='Override Meta App Secret')

    def handle(self, *args, **options):
        input_token = options['token'].strip()
        app_id = (options['app_id'] or getattr(settings, 'META_APP_ID', '')).strip()
        app_secret = (options['app_secret'] or getattr(settings, 'META_APP_SECRET', '')).strip()
        api_ver = getattr(settings, 'INSTAGRAM_API_VERSION', 'v18.0')
        base_graph_url = f"https://graph.facebook.com/{api_ver}"

        self.stdout.write(self.style.NOTICE("\n======================================================="))
        self.stdout.write(self.style.NOTICE("🚀 META / INSTAGRAM TOKEN AUTO-SETUP WIZARD"))
        self.stdout.write(self.style.NOTICE("=======================================================\n"))

        # ── Step 1: Validate input token with Meta ──
        self.stdout.write("🔍 [1/4] Inspecting access token with Meta Graph API...")
        try:
            me_resp = requests.get(
                f"{base_graph_url}/me",
                params={'access_token': input_token, 'fields': 'id,name'},
                timeout=15
            )
            me_data = me_resp.json()
            if 'error' in me_data:
                err_msg = me_data['error'].get('message', 'Unknown error')
                raise CommandError(f"Token validation failed: {err_msg}")
            
            user_id = me_data.get('id')
            user_name = me_data.get('name', 'User')
            self.stdout.write(self.style.SUCCESS(f"  ✓ Valid token authenticated for: {user_name} (ID: {user_id})"))
        except requests.RequestException as e:
            raise CommandError(f"Network error contacting Meta: {e}")

        # ── Step 2: Attempt Long-Lived Token Exchange (60 Days) ──
        active_token = input_token
        if app_id and app_secret:
            self.stdout.write("\n🔄 [2/4] Exchanging for 60-Day Long-Lived Token...")
            try:
                ex_resp = requests.get(
                    f"{base_graph_url}/oauth/access_token",
                    params={
                        'grant_type': 'fb_exchange_token',
                        'client_id': app_id,
                        'client_secret': app_secret,
                        'fb_exchange_token': input_token,
                    },
                    timeout=20
                )
                ex_data = ex_resp.json()
                if 'access_token' in ex_data:
                    active_token = ex_data['access_token']
                    expires_in = ex_data.get('expires_in', 5184000) // 86400
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Successfully upgraded to Long-Lived Token! Valid for ~{expires_in} days."))
                else:
                    self.stdout.write(self.style.WARNING(f"  ⚠ Note: Token exchange response: {ex_data.get('error', {}).get('message', 'proceeding with user token')}"))
            except Exception as ex_err:
                self.stdout.write(self.style.WARNING(f"  ⚠ Exchange skipped ({ex_err}), using direct token."))

        # ── Step 3: Discover Connected Instagram Business Accounts & Pages ──
        self.stdout.write("\n📡 [3/4] Discovering Instagram Business Accounts linked to Pages...")
        ig_user_id = None
        ig_username = None
        page_token = None

        try:
            pages_resp = requests.get(
                f"{base_graph_url}/me/accounts",
                params={
                    'access_token': active_token,
                    'fields': 'id,name,access_token,instagram_business_account{id,username}'
                },
                timeout=15
            )
            pages_data = pages_resp.json()
            pages_list = pages_data.get('data', [])

            for p in pages_list:
                p_name = p.get('name')
                ig_info = p.get('instagram_business_account')
                if ig_info:
                    ig_user_id = ig_info.get('id')
                    ig_username = ig_info.get('username')
                    page_token = p.get('access_token') or active_token
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Found Page '{p_name}' linked to Instagram: @{ig_username} (ID: {ig_user_id})"))
                    if ig_username == 'ikashii_07':
                        break

            if not ig_user_id:
                # Direct check if user token itself is direct Instagram User ID
                self.stdout.write(self.style.WARNING("  ⚠ No Instagram Business Account returned from /me/accounts."))
                self.stdout.write("  Defaulting to configured INSTAGRAM_ACCOUNT_ID: 17841475393977759 (@ikashii_07)")
                ig_user_id = getattr(settings, 'INSTAGRAM_ACCOUNT_ID', '17841475393977759')
                ig_username = getattr(settings, 'INSTAGRAM_ACCOUNT_HANDLE', 'ikashii_07')

        except Exception as p_err:
            self.stdout.write(self.style.WARNING(f"  ⚠ Error reading /me/accounts: {p_err}"))
            ig_user_id = getattr(settings, 'INSTAGRAM_ACCOUNT_ID', '17841475393977759')
            ig_username = getattr(settings, 'INSTAGRAM_ACCOUNT_HANDLE', 'ikashii_07')

        # Use page access token if available, as Page tokens for posting do not expire
        final_token = page_token or active_token

        # ── Step 4: Automatically Write to .env ──
        self.stdout.write("\n💾 [4/4] Writing configuration directly to .env...")
        env_path = os.path.join(settings.BASE_DIR, '.env')

        env_content = ""
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env_content = f.read()

        updates = {
            'INSTAGRAM_ACCESS_TOKEN': final_token,
            'INSTAGRAM_ACCOUNT_ID': str(ig_user_id),
            'INSTAGRAM_ACCOUNT_HANDLE': str(ig_username or 'ikashii_07'),
            'INSTAGRAM_AUTO_POST_STORY': 'True',
        }
        if app_id:
            updates['META_APP_ID'] = app_id
        if app_secret:
            updates['META_APP_SECRET'] = app_secret

        for key, val in updates.items():
            pattern = rf'^{key}=.*$'
            new_line = f"{key}={val}"
            if re.search(pattern, env_content, flags=re.MULTILINE):
                env_content = re.sub(pattern, new_line, env_content, flags=re.MULTILINE)
            else:
                env_content += f"\n{new_line}"

        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)

        self.stdout.write(self.style.SUCCESS(f"  ✓ Updated {env_path} successfully!"))
        self.stdout.write(self.style.SUCCESS(f"  ✓ INSTAGRAM_ACCOUNT_ID = {ig_user_id}"))
        self.stdout.write(self.style.SUCCESS(f"  ✓ INSTAGRAM_ACCOUNT_HANDLE = {ig_username}"))
        self.stdout.write(self.style.SUCCESS("  ✓ INSTAGRAM_AUTO_POST_STORY = True"))
        self.stdout.write(self.style.SUCCESS("  ✓ INSTAGRAM_ACCESS_TOKEN = Saved securely."))

        self.stdout.write(self.style.NOTICE("\n======================================================="))
        self.stdout.write(self.style.SUCCESS("🎉 SETUP COMPLETE! Instagram Stories Automation is LIVE!"))
        self.stdout.write(self.style.NOTICE("=======================================================\n"))
