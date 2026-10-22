# KashiiUpdatez — Comprehensive Security Audit Report

**Repository:** `kashichavan/updatezbykashi`  
**Audit Date:** October 2026  
**Auditor:** Principal Security Engineer & AppSec Lead  
**Scope:** Application-wide Source Code, Sandboxes, Authentication, Secret Handling, OWASP Top 10  

---

## 1. Executive Security Summary

A comprehensive application security audit was performed across all endpoints, background processes, sandboxes, and database access layers. Two critical (P0) security vulnerabilities were identified in the interactive playgrounds:
1. **Python Tracer Sandbox Escape & File Disclosure (SEC-001)**
2. **SQLite Sandbox Disk Database Attachment (SEC-002)**

Both vulnerabilities were patched, verified with regression tests, and confirmed closed prior to completing this report.

The remainder of the application demonstrates high baseline security: Django's ORM prevents SQL injection in standard business routes, authentication in the owner administration portal is strictly enforced across all 19 endpoints, and CSRF protection is active across state-changing views.

---

## 2. OWASP Top 10 Risk Assessment

### A01: Broken Access Control
- **Owner Administration Portal:** Tested all 19 `api_owner_` view endpoints. Unauthenticated requests are immediately denied with 401 Unauthorized or redirected to `/owner/login/`.
- **Job Posting & Resume Studio:** Resumes and jobs are addressed using cryptographically secure UUIDv4 tokens (`uuid.uuid4()`), preventing sequential ID harvesting or horizontal privilege escalation.
- **Status:** **PASS**

### A02: Cryptographic Failures & Secrets Management
- **Secret Keys & Credentials:** `reqpulse/settings.py` uses `os.getenv('DJANGO_SECRET_KEY')` with a random runtime fallback for local development. `DATABASE_URL`, `GROQ_API_KEY`, and `OPENAI_API_KEY` are read exclusively from environment variables.
- **Repository Cleanliness:** No production database passwords, private certificates, or live API keys were committed to Git history.
- **Status:** **PASS**

### A03: Injection (SQL & Remote Code Execution)
- **Django ORM:** All job searches, category queries, and blog filters use parameterized Django ORM queries (`filter()`, `exclude()`, `annotate()`). Raw SQL queries with string interpolation are completely absent.
- **SQL Practice Sandbox:** Previously vulnerable to `ATTACH DATABASE` (SEC-002). Resolved by implementing `conn.set_authorizer()` denying `SQLITE_ATTACH` and `SQLITE_DETACH`.
- **Python Execution Playground:** Previously vulnerable to `open()` and `import os` (SEC-001). Resolved via AST filtering of imports, dunder attributes, and sanitization of `__builtins__`.
- **Status:** **PASS (Mitigated)**

### A04: Insecure Design & Rate Limiting
- **External AI Integration:** AI resume bullet generation queries Groq. To prevent denial-of-service or budget exhaustion, requests implement automatic fallback to secondary models (`openai/gpt-oss-20b`) and graceful error handling on HTTP 429 rate limits.
- **Status:** **PASS**

### A05: Security Misconfiguration
- **Production Settings:** `settings.py` reads `DJANGO_DEBUG` from environment variables, defaulting to `False` in production.
- **Host & CSRF Restrictions:** `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are dynamically loaded from environment variables with production domains (`kashiiupdatez.online`, `kashiiupdatez.com`, `*.onrender.com`).
- **Static Assets:** Handled via WhiteNoise (`whitenoise.middleware.WhiteNoiseMiddleware`) with cache-busting manifest storage (`CompressedManifestStaticFilesStorage`).
- **Status:** **PASS**

### A06: Vulnerable and Outdated Components
- **Core Frameworks:** Running on modern, supported releases: Django 6.0.8, django-ninja 1.6.3, Pydantic 2.12.5, psycopg 3.3.4, and ReportLab 5.1.0.
- **Status:** **PASS**

### A07: Identification and Authentication Failures
- **Owner Login:** Authenticates against Django's standard hashed passwords (`pbkdf2_sha256`). Session cookies are configured with `HttpOnly` flags.
- **Status:** **PASS**

### A08: Software and Data Integrity Failures
- **Deserialization:** All incoming JSON payloads are deserialized using standard `json.loads` or Pydantic schemas. `pickle`, `yaml.load`, and `eval` are not used on untrusted user inputs.
- **Status:** **PASS**

### A09: Security Logging and Monitoring Failures
- **Scraper & Sync Logging:** Scraper tasks and background daemons log execution counts, duplicates skipped, and errors to standard output for Render dashboard capture.
- **Status:** **PASS**

### A10: Server-Side Request Forgery (SSRF)
- **Resume Uploads:** Candidate resumes are parsed directly from memory buffers or temporary file handles (`request.FILES`). The application does not fetch user-provided URLs server-side.
- **Job Redirection:** Apply links use explicit HTTP 302 client redirects (`redirect(job.apply_url)`), preventing server-side SSRF.
- **Status:** **PASS**

---

## 3. Residual Risk & Recommendations

1. **Production Process Isolation:** While the Python tracer AST restrictions and sanitized builtins prevent common sandbox escapes, running user code on multi-tenant production web workers always carries low residual risk in CPython. In a high-traffic production tier, consider isolating playground execution in short-lived, ephemeral Docker containers or WebAssembly (Pyodide in the browser).
2. **CORS Policy:** Verify that production CORS headers restrict origin access strictly to `kashiiupdatez.online`.
