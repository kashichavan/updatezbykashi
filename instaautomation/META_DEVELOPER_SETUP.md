# Meta / Instagram Developer Setup Guide

This document outlines the step-by-step procedure for configuring Meta Developer Application, Instagram Graph API, OAuth Direct Callback, Webhook Verification, and Local Tunneling for testing your `instaautomation` Django app.

---

## 1. META DEVELOPER APPLICATION SETUP

1. Go to [Meta for Developers](https://developers.facebook.com/) and log in with your Facebook account.
2. Click **My Apps** → **Create App**.
3. Select App Type: **Business** or **Consumer** (Business is recommended for Instagram Graph API access).
4. Enter your App Name (e.g., `Kashii Updatez Instagram Automation`) and Contact Email. Click **Create App**.

---

## 2. ADD INSTAGRAM GRAPH API PRODUCT

1. In your App Dashboard, scroll to **Add Products to Your App**.
2. Find **Instagram Graph API** and click **Set Up**.
3. Add **Facebook Login for Business** product as well to handle official OAuth permissions.

---

## 3. CONFIGURE OAUTH REDIRECT URIS

1. Under **Facebook Login for Business** → **Settings**:
2. Scroll to **Valid OAuth Redirect URIs**.
3. Add your production domain callback URL:
   ```text
   https://kashiiupdatez.online/instagram/oauth/callback/
   ```
4. For local testing (using ngrok or Cloudflare Tunnel):
   ```text
   https://your-ngrok-subdomain.ngrok-free.app/instagram/oauth/callback/
   ```
5. Save Changes.

---

## 4. CONFIGURE WEBHOOK VERIFICATION

1. In the Meta App Dashboard, go to **Webhooks** (or under **Instagram** → **Configuration**).
2. Select **Instagram** from the dropdown menu.
3. Click **Subscribe to this object**.
4. Enter **Callback URL**:
   ```text
   https://kashiiupdatez.online/instagram/api/instagram/webhook/
   ```
   *(Or your ngrok HTTPS URL during local development)*
5. Enter **Verify Token**:
   ```text
   kashii_insta_verify_token_2026
   ```
   *(Ensure `META_VERIFY_TOKEN` in your environment or Django `settings.py` matches this string exactly)*.
6. Click **Verify and Save**.
7. Under Webhook Subscriptions, subscribe to the following fields:
   * `comments` (Triggers on public comments)
   * `messages` (Triggers on Direct Messages)

---

## 5. REQUIRED META PERMISSIONS

Ensure your Meta App requests the following permissions during OAuth:

* `instagram_basic`
* `instagram_manage_comments`
* `instagram_manage_messages`
* `pages_show_list`
* `pages_read_engagement`
* `pages_manage_metadata`
* `public_profile`

---

## 6. LOCAL DEVELOPMENT & WEBHOOK TUNNELING

To test Meta Webhooks locally on your computer (`localhost:8000`):

### Option A: Using ngrok
1. Start your local Django server:
   ```bash
   python manage.py runserver 8000
   ```
2. In a separate terminal, launch ngrok:
   ```bash
   ngrok http 8000
   ```
3. Copy the generated HTTPS Forwarding URL (e.g. `https://abc123.ngrok-free.app`).
4. Update your `.env` settings:
   ```env
   META_APP_ID="your_meta_app_id"
   META_APP_SECRET="your_meta_app_secret"
   META_VERIFY_TOKEN="kashii_insta_verify_token_2026"
   INSTAGRAM_REDIRECT_URI="https://abc123.ngrok-free.app/instagram/oauth/callback/"
   ```
5. Set Meta Webhook Callback URL to `https://abc123.ngrok-free.app/instagram/api/instagram/webhook/`.

---

## 7. TESTING THE END-TO-END AUTOMATION FLOW

1. Open `https://kashiiupdatez.online/instagram/` in your browser.
2. Click **Connect Instagram via Meta OAuth**.
3. Log in with your Facebook account connected to your Instagram Business/Creator account and authorize permissions.
4. Upon redirection back to `/instagram/`, verify your account displays **🟢 Connected**.
5. Click **+ Create Automation Rule**:
   * Name: `Python Guide`
   * Keywords: `python, guide`
   * Comment Reply: `Thanks! 👋 Check your DM.`
   * Initial DM: `Hey {{username}} 👋 Follow us and reply DONE to receive the Python guide.`
   * Confirmation Keyword: `DONE`
   * Final DM: `Awesome! 🎉 Here is your guide: {{resource_url}}`
   * Resource URL: `https://kashiiupdatez.online/category/software-tech/`
6. Post a comment saying **"python"** from a test Instagram account on any post of your connected account.
7. Observe automatic comment reply & instant DM triggering!
