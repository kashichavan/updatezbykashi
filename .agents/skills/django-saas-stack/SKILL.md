---
name: django-saas-stack
description: >-
  Specialized production blueprint for building robust SaaS applications using Django, Django REST Framework (DRF) or Django Ninja, Celery, Redis, and PostgreSQL.
  Use this skill when structuring Django SaaS codebases, implementing multi-tenancy, configuring custom user models, integrating Stripe webhooks, managing async task queues, enforcing Django security settings, and deploying via Docker, WhiteNoise, and Gunicorn/Uvicorn.
---

# Django SaaS Stack Architecture & Blueprint

Django is an ideal framework for building SaaS products rapidly. This guide provides production patterns for multi-tenancy, custom user models, Stripe billing, Celery task queues, and security hardening in Django.

---

## 1. Project Structure & App Architecture

Maintain a clean domain-driven Django structure:

```text
my_django_saas/
├── manage.py
├── config/                  # Project configuration root
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py / asgi.py
├── apps/                    # Modular domain apps
│   ├── users/               # Custom User & Auth
│   ├── organizations/       # Multi-tenant logic & memberships
│   ├── billing/             # Stripe checkout, subscriptions, webhooks
│   └── dashboard/           # Core SaaS feature domain
└── templates/               # Global templates (if full-stack/HTMX)
```

---

## 2. Custom User Model & Multi-Tenancy

### A. Custom AbstractUser Model (Setup First)
Always start with a custom user model before running the initial migration:

```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_mfa_enabled = models.BooleanField(default=False)
    avatar_url = models.URLField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
```

```python
# config/settings/base.py
AUTH_USER_MODEL = "users.User"
```

### B. Tenant Scoping Middleware (Row-Level Multi-Tenancy)

```python
# apps/organizations/middleware.py
from django.utils.deprecation import MiddlewareMixin
from apps.organizations.models import OrganizationMember

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.tenant = None
        if request.user.is_authenticated:
            org_id = request.headers.get("X-Organization-ID") or request.COOKIES.get("active_org_id")
            if org_id:
                try:
                    membership = OrganizationMember.objects.get(
                        user=request.user, organization_id=org_id
                    )
                    request.tenant = membership.organization
                    request.user_role = membership.role
                except OrganizationMember.DoesNotExist:
                    pass
```

### C. Base Tenant Model & Manager
```python
# apps/organizations/models.py
from django.db import models

class TenantManager(models.Manager):
    def for_tenant(self, tenant):
        return self.get_queryset().filter(organization=tenant)

class TenantAwareModel(models.Model):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE)
    
    objects = TenantManager()

    class Meta:
        abstract = True
```

---

## 3. Stripe Integration & Webhooks in Django

### A. Stripe Webhook View (DRF / Django View)
```python
# apps/billing/views.py
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from apps.billing.tasks import process_stripe_event

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    # Pass to Celery for async execution to avoid HTTP timeout
    process_stripe_event.delay(event["id"], event["type"], event["data"])

    return HttpResponse(status=200)
```

---

## 4. Async Tasks with Celery & Redis

### A. Celery Configuration (`config/celery.py`)
```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("my_django_saas")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

### B. Background Webhook Processor Task (`apps/billing/tasks.py`)
```python
from celery import shared_task
from apps.organizations.models import Organization

@shared_task(bind=True, max_retries=3)
def process_stripe_event(self, event_id, event_type, event_data):
    obj = event_data["object"]
    customer_id = obj.get("customer")

    if event_type == "customer.subscription.updated":
        status = obj.get("status")
        Organization.objects.filter(stripe_customer_id=customer_id).update(
            subscription_status=status
        )
```

---

## 5. Security Settings for Production (`production.py`)

Always enforce Django's built-in security flags for HTTPS production:

```python
# config/settings/production.py
from .base import *

DEBUG = False

# Security Headers
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000  # 1 Year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# WhiteNoise Static File Serving
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

---

## 6. Production Docker Deployment Blueprint

```dockerfile
# Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

---

## 7. Django SaaS Launch Checklist
- [ ] Custom `AUTH_USER_MODEL` set up prior to first migration.
- [ ] Row-level or schema-based tenant scoping active in all querysets.
- [ ] Stripe webhook endpoint marked `@csrf_exempt` and processing offloaded to Celery.
- [ ] Redis configured as Celery broker and result backend.
- [ ] `DEBUG = False` and `SECURE_*` flags enabled in `production.py`.
- [ ] WhiteNoise configured for serving static assets.
- [ ] `django-cors-headers` configured for frontend API consumption.
