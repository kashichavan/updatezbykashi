---
name: meta-instagram-automation
description: >-
  Enterprise guide for configuring Meta Developer App, Instagram Graph API 
  credentials, webhook subscriptions, and OAuth token exchanges.
---

# Meta & Instagram API Automation Skill

Use this skill when setting up, troubleshooting, or updating Meta Instagram Graph API credentials, OAuth tokens, and webhook handlers.

## App Credentials & Webhook Setup

- **App ID**: `1699121034511579`
- **App Secret**: set `META_APP_SECRET` in `.env`
- **Verify Token**: set `META_VERIFY_TOKEN` in `.env`
- **OAuth Callback URL**: `https://kashiiupdatez.online/instagram/oauth/callback/`
- **Webhook Endpoint**: `https://kashiiupdatez.online/instagram/api/instagram/webhook/`

## Webhook Subscription Objects

In **Meta Dashboard** → **Webhooks** → **Instagram**:
1. Subscribe to `comments` (auto-reply to post comments)
2. Subscribe to `messages` (auto-send Instagram DMs)
