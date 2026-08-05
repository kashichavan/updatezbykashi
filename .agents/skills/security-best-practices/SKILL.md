---
name: security-best-practices
description: >-
  Enterprise AppSec and web application security standards.
  Use this skill when implementing authentication, RBAC authorization, input sanitization, OWASP Top 10 defenses, CSRF/XSS protection, HTTP security headers, CORS policy, secrets management, data encryption, rate limiting, and performing security code reviews.
---

# Security Best Practices & AppSec Defense Guide

This skill provides operational security standards and mitigation techniques to secure web applications against top attack vectors (OWASP Top 10, data leakage, account takeover).

---

## 1. OWASP Top 10 Defenses & Code Rules

### A. Injection (SQLi, NoSQLi, Command Injection)
- **Rule**: NEVER construct dynamic SQL strings using concatenation or format strings.
- **Remediation**: Use parameterized queries or ORM abstractions.
```python
# BAD (Vulnerable to SQL Injection)
cursor.execute(f"SELECT * FROM users WHERE email = '{user_email}'")

# GOOD (Parameterized Query)
cursor.execute("SELECT * FROM users WHERE email = %s", [user_email])
```

### B. Broken Authentication & Session Management
- **Password Hashing**: Use Argon2id or bcrypt (cost factor >= 12).
- **Session Tokens**:
  - Store tokens in `HttpOnly`, `Secure`, `SameSite=Strict` cookies.
  - Never store sensitive JWTs in `localStorage` or `sessionStorage` (vulnerable to XSS).
  - Enforce token rotation and maximum session lifespan (e.g., 15-minute access token, 7-day refresh token).

### C. Cross-Site Scripting (XSS)
- **Rule**: Escape and sanitize all untrusted user input before rendering in HTML/DOM context.
- **DOM Injection**: Avoid `element.innerHTML = input`. Use `element.textContent` or trusted sanitizers (e.g., DOMPurify).
- **Content Security Policy (CSP)**: Set strict HTTP response headers to block inline scripts:
  ```http
  Content-Security-Policy: default-src 'self'; script-src 'self' https://trusted.cdn.com; object-src 'none';
  ```

### D. Cross-Site Request Forgery (CSRF)
- **Cookie Strategy**: Use `SameSite=Lax` or `SameSite=Strict` on session cookies.
- **CSRF Tokens**: Pass double-submit cookie or synchronizer CSRF token in state-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`). Include header `X-CSRF-Token`.

---

## 2. Mandatory HTTP Security Headers

Inject these headers on all production web server responses (Nginx, Caddy, Cloudflare, application middleware):

```http
# 1. Force HTTPS for 2 years
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload

# 2. Prevent framing / clickjacking
X-Frame-Options: DENY

# 3. Block MIME-type sniffing
X-Content-Type-Options: nosniff

# 4. Control referrer information leakage
Referrer-Policy: strict-origin-when-cross-origin

# 5. Restrict dangerous browser capabilities
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
```

---

## 3. CORS Policy Configuration

- **Never use `Access-Control-Allow-Origin: *`** alongside authenticated endpoints (`Access-Control-Allow-Credentials: true`).
- Maintain an explicit whitelist of trusted origins:
```python
ALLOWED_ORIGINS = [
    "https://app.yourdomain.com",
    "https://admin.yourdomain.com",
]

def handle_cors(request_origin):
    if request_origin in ALLOWED_ORIGINS:
        return {"Access-Control-Allow-Origin": request_origin}
    return {}
```

---

## 4. API Rate Limiting & Throttling

Protect endpoints against brute-force attacks, credential stuffing, and Denial of Service (DoS):

- **Login / Auth Endpoints**: Maximum 5 attempts per minute per IP.
- **Password Reset / Sensitive Operations**: Maximum 3 requests per hour.
- **Public API Endpoints**: Rate limit via sliding window in Redis:
  ```text
  Key: rate_limit:{ip}:{endpoint} | TTL: 60s
  ```

---

## 5. Secrets Hygiene & Data Encryption

### A. Environment & Secrets Management
- **Never commit secrets** (`.env`, private keys, API tokens) into Git repositories.
- Use `.gitignore` to exclude `.env`, `*.pem`, `secrets.yaml`.
- Run automated secret scanners (`gitleaks`, `trufflehog`) in CI/CD pipelines.

### B. Encryption at Rest & Transit
- **Transit**: Force TLS 1.3 (or minimum TLS 1.2). Disable weak ciphers (SSLv3, TLS 1.0, TLS 1.1).
- **At Rest**: Encrypt sensitive database columns (SSNs, API keys, payment info) using AES-256-GCM.

---

## 6. Security Audit Checklist
- [ ] No hardcoded passwords, secret keys, or private API keys in codebase.
- [ ] All database queries parameterized or safely ORM-wrapped.
- [ ] HTTP Security Headers (HSTS, CSP, X-Frame-Options) enabled.
- [ ] Cookies marked `HttpOnly`, `Secure`, and `SameSite=Lax/Strict`.
- [ ] Authentication endpoints protected with strict rate limiting.
- [ ] CORS policies explicitly set to trusted domains only.
- [ ] Input payload validation active on all request schemas (Zod, Pydantic, Marshmallow).
