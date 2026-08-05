---
name: saas-development
description: >-
  Comprehensive guide and architecture patterns for building scalable, production-ready SaaS (Software-as-a-Service) applications.
  Use this skill when designing multi-tenant architectures, subscription billing engines (Stripe/LemonSqueezy), auth & RBAC systems, organization/team management, usage-based metering, onboarding flows, and SaaS analytics.
---

# SaaS Architecture & Development Guide

Building a modern SaaS requires robust multi-tenancy, secure user and team authorization, automated billing cycles, resilient webhook management, and clear operational telemetry.

---

## 1. Multi-Tenancy Architecture

Choose the multi-tenancy model based on security requirements, compliance, and budget.

### A. Row-Level Isolation (Shared Database, Shared Schema)
- **Best for**: Standard B2B/B2C SaaS with millions of tenants. High resource efficiency.
- **Pattern**: Every tenant-bound database table includes a `tenant_id` / `organization_id` foreign key.
- **Enforcement**:
  - Middleware injects `current_tenant` into application request context.
  - ORM querysets / repositories MUST automatically append `.filter(tenant_id=current_tenant.id)`.
  - Database Row Level Security (RLS) in PostgreSQL as a secondary defense layer:
    ```sql
    CREATE POLICY tenant_isolation_policy ON user_data
      USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    ```

### B. Schema-per-Tenant (Shared Database, Separate Schemas)
- **Best for**: Enterprise B2B SaaS needing data isolation without dedicated server costs.
- **Pattern**: PostgreSQL schema per tenant (`tenant_acme`, `tenant_globex`).
- **Enforcement**: Set DB search path on request: `SET search_path TO tenant_acme, public;`.

### C. Database-per-Tenant (Isolated Databases)
- **Best for**: Strict compliance (HIPAA, SOC2 Type II, enterprise custom SLAs).
- **Pattern**: Dynamic DB connection routing per request.

---

## 2. Authentication & RBAC (Role-Based Access Control)

### Domain Model
```text
User (id, email, hashed_password, mfa_enabled)
 └── OrganizationMember (id, user_id, organization_id, role_id)
      ├── Organization (id, name, slug, plan_id, stripe_customer_id)
      └── Role (id, name: "Owner" | "Admin" | "Member" | "Viewer")
           └── RolePermissions (role_id, permission: "billing:write" | "projects:delete")
```

### Authorization Rules
- **Never rely on client-side state** for access decisions.
- Pass `X-Organization-Id` or route parameters `/api/v1/orgs/{org_slug}/...` and explicitly verify membership and permission on every endpoint.
- Implement explicit permission checks: `has_permission(user, org, "project:create")`.

---

## 3. Subscription & Billing Engine (Stripe Integration)

### Core Subscription Lifecycle
1. **Checkout**: Redirect user to Stripe Checkout or create PaymentIntent via Stripe Elements.
2. **Provisioning**: Activate plan ONLY upon receiving verified webhook event `checkout.session.completed` or `customer.subscription.created`.
3. **Status Tracking**: Maintain local cache of tenant subscription status (`active`, `past_due`, `canceled`, `unpaid`, `trialing`).
4. **Grace Period**: Allow 3-7 day grace period on `past_due` status with prominent UI banners before blocking access.

### Resilient Webhook Handler Pattern
- **Verification**: Verify signature (`stripe-signature` header) with endpoint secret.
- **Idempotency**: Record `event_id` in database table before processing. If `event_id` exists, return HTTP 200 immediately.
- **Async Execution**: Offload heavy webhook processing (sending emails, updating secondary systems) to background tasks (Celery/Redis/Worker queues).

```python
# Webhook Processing Checklist
1. Extract signature & verify payload.
2. Check DB: Has event.id been processed? If yes -> return 200.
3. Process event type:
   - customer.subscription.created / updated -> Sync plan & status
   - customer.subscription.deleted -> Downgrade tenant to free tier
   - invoice.payment_failed -> Trigger dunning email & set past_due status
4. Save event.id to processed_events table.
5. Return HTTP 200 OK.
```

---

## 4. Usage-Based Metering & Limits

- Define feature flags & quota limits per pricing tier (e.g., Free: 1,000 API calls/mo; Pro: 100,000 API calls/mo).
- Rate limit via Redis sliding window algorithm:
  ```text
  Key: rate:{tenant_id}:{feature}:{YYYY-MM-DD}
  ```
- Gracefully handle quota exhaustion with HTTP status `429 Too Many Requests` and standard JSON error response:
  ```json
  {
    "error": "quota_exceeded",
    "message": "Monthly API request limit reached. Please upgrade your plan.",
    "upgrade_url": "/billing/upgrade"
  }
  ```

---

## 5. User Onboarding & Org Workspace Creation

- **Zero-Friction Signup**: Allow single-click social auth (Google/GitHub/OAuth2) or magic links.
- **Auto-Provision Workspace**: Automatically create default personal organization upon user registration (`{User}'s Workspace`).
- **Team Invitations**: Secure tokenized email invites with expiration timestamps (72h expiry).

---

## 6. SaaS Telemetry & Key Metrics

Track essential SaaS operational metrics in database/analytics views:
- **MRR (Monthly Recurring Revenue)**: Sum of active recurring subscriptions.
- **ARR (Annual Recurring Revenue)**: `MRR * 12`.
- **Churn Rate**: Percentage of canceled subscribers in period.
- **ARPU (Average Revenue Per User)**: `Total Revenue / Active Tenants`.
- **Audit Logging**: Maintain immutable log (`timestamp`, `actor_id`, `org_id`, `action`, `ip_address`).

---

## 7. SaaS Checklist Before Launch
- [ ] Multi-tenant scoping verified across 100% of data endpoints.
- [ ] Stripe webhook signature validation and idempotency handling active.
- [ ] Password reset, MFA, and OAuth workflows tested.
- [ ] Failed payment dunning notifications configured.
- [ ] Rate limits and resource throttling active on external endpoints.
- [ ] Audit logs and error monitoring (e.g., Sentry) installed.
