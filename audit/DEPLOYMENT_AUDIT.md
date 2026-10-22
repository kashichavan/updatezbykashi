# KashiiUpdatez — Render Cloud & Production Deployment Audit

**Repository:** `kashichavan/updatezbykashi`  
**Audit Date:** October 2026  
**Auditor:** Principal DevOps Engineer & Cloud Architect  
**Production Hosting:** Render Web Service (`https://kashiiupdatez.online`)  
**Configuration Files:** `render.yaml`, `Procfile`, `build.sh`, `reqpulse/settings.py`  

---

## 1. Cloud Architecture Overview

KashiiUpdatez is provisioned on Render as a containerized Python Web Service backed by managed PostgreSQL storage.

```
                      Internet User / Web Traffic
                                 │
                                 ▼
                     Render TLS & Edge Proxy (HTTPS)
                                 │
                                 ▼
         Gunicorn WSGI Application Server (reqpulse.wsgi)
         [1 Master Worker, 4 gthread Worker Threads, timeout 60s]
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       WhiteNoise Middleware             Django 6.0 Engine
    (Compressed Static Assets)           (Business Logic)
                                                 │
                                                 ▼
                                     Render Managed PostgreSQL
                                     (or SQLite Local / Test)
```

---

## 2. Configuration File Inspection

### 2.1 `render.yaml`
```yaml
services:
  - type: web
    name: kashii-updatez
    env: python
    plan: free
    buildCommand: "./build.sh"
    startCommand: "gunicorn reqpulse.wsgi:application --workers 1 --threads 4 --worker-class gthread --max-requests 500 --max-requests-jitter 50 --keep-alive 5 --timeout 60"
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.0
      - key: DJANGO_SETTINGS_MODULE
        value: reqpulse.settings
      - key: SECRET_KEY
        generateValue: true
```
- **Concurrency Model:** Uses `gthread` worker class with 1 process and 4 threads. This provides thread concurrency suitable for Render free/starter tiers with 512 MB RAM without worker OOM crashes.
- **Worker Recycling:** `--max-requests 500 --max-requests-jitter 50` automatically recycles threads after 500 requests, preventing memory fragmentation over extended runtimes.

### 2.2 `build.sh` Pipeline
The deployment script is structured into robust, fault-tolerant build phases:
1. `pip install -r requirements.txt`: Dependency resolution.
2. `collectstatic --noinput`: Compiles and pre-compresses static assets with WhiteNoise.
3. Proactive SQLite check: Verifies SQLite header integrity if using SQLite file storage.
4. `migrate --noinput`: Applies all pending database migrations with 5-iteration retry logic.
5. Snapshot restore fallback: Auto-seeds 442 baseline records if database is freshly initialized.
6. Initializer scripts: Seeds production owner, blog posts, and guides.
7. Deduplication sweep: Merges duplicate job postings via `cleanup_all_database_duplicates()`.
8. Project Library Seeding: Automatically seeds all 36 curated Indian market demonstration projects via `seed_indian_projects`.

---

## 3. Environment Variable Checklist

| Variable Name | Required? | Production Value / Pattern | Sensitive? | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `DJANGO_SETTINGS_MODULE` | Yes | `reqpulse.settings` | No | Django settings discovery |
| `DJANGO_SECRET_KEY` / `SECRET_KEY` | Yes | High-entropy random string | **YES** | Cryptographic signatures |
| `DJANGO_DEBUG` | Yes | `false` | No | Disables debug mode in production |
| `DATABASE_URL` | Yes | `postgres://user:pass@host:5432/db` | **YES** | PostgreSQL connection string |
| `ALLOWED_HOSTS` | Yes | `kashiiupdatez.online,*.onrender.com` | No | Host header validation |
| `CSRF_TRUSTED_ORIGINS` | Yes | `https://kashiiupdatez.online,https://*.onrender.com` | No | Cross-origin form security |
| `GROQ_API_KEY` | Optional | `gsk_...` | **YES** | AI resume bullet generation |
| `OPENAI_API_KEY` | Optional | `sk-...` | **YES** | Secondary AI model fallback |

---

## 4. Production Readiness Assessment

- **Static Asset Serving:** **READY (WhiteNoise manifest storage active)**.
- **Database Resilience:** **READY (Auto-retry migrations + snapshot recovery active)**.
- **Memory Footprint:** **READY (Threaded Gunicorn with max-requests recycling configured)**.
- **Sandbox Security:** **READY (SEC-001 and SEC-002 patches active)**.
