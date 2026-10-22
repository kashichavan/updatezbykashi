# KashiiUpdatez — Duplicate Code & Architectural Redundancy Report

**Repository:** `kashichavan/updatezbykashi`  
**Audit Date:** October 2026  
**Auditor:** Principal Software Architect  

---

## 1. Executive Summary

Static analysis, AST inspection, and route auditing revealed several areas of duplicate logic, overlapping route handlers, and parallel data transformers. While some duplication is benign (such as fallback parsers), other instances risk drift between the server-rendered template views and the REST API.

---

## 2. Inventory of Duplicated Patterns & Redundancies

### 2.1 Overlapping SEO & Ping Routes (High Redundancy)
- **Locations:**
  - `reqpulse/urls.py`: Lines 25–35 (`sitemap.xml`, `robots.txt`, `rss.xml`, `feed.xml`, `api/ping`)
  - `requirements/urls.py`: Lines 15–25 (`sitemap.xml`, `robots.txt`, `rss.xml`, `feed.xml`, `api/ping`)
- **Analysis:** Both files define route handlers for search engine crawlers and monitoring health pings. Because `reqpulse/urls.py` includes `requirements.urls` at root (`path('', include('requirements.urls'))`), the top-level route takes precedence, rendering the handlers inside `requirements/urls.py` redundant.
- **Risk Level:** Low (No operational failure, but potential route ambiguity during refactoring).
- **Recommendation:** Maintain the centralized routing in `reqpulse/urls.py` and deprecate identical endpoints in `requirements/urls.py`.

---

### 2.2 Salary & Experience Regex Extraction Logic
- **Locations:**
  - `requirements/job_aggregator.py`: `extract_salary()`, `extract_experience_years()`
  - `requirements/views.py`: Inline regex matching in `api_parse_job()` and scraper importers.
- **Analysis:** Regular expressions for Indian compensation packages (`(\d+(?:\.\d+)?)\s*(?:LPA|L|Lakhs|Lakh)`) and experience ranges (`(\d+)\s*(?:-|to)\s*(\d+)\s*(?:yrs|years)`) are repeated with slight variations.
- **Risk Level:** Medium (Changes to salary detection formats in one module will not reflect in the other).
- **Recommendation:** Refactor both call sites to use a shared utility `requirements/normalizers.py`.

---

### 2.3 PDF Resume Extraction Fallback Chains
- **Locations:**
  - `requirements/views.py`: `api_resume_upload_view`
  - `requirements/tests_production_fixes.py` & `requirements/resume_pdf.py`
- **Analysis:** Both `pypdf.PdfReader` and regex header sniffers are duplicated when attempting to extract raw text from candidate resume uploads.
- **Risk Level:** Low (Defensive programming against corrupted stream headers).
- **Recommendation:** Encapsulate resume parsing into `requirements/resume_parser.py` returning a structured `ParsedResume` dataclass.

---

### 2.4 Dual Frontend Architectures (Django Templates vs. Next.js)
- **Locations:**
  - `requirements/templates/` & `blog/templates/`: Active Django server-side rendered UI with Tailwind CSS.
  - `nextjs-frontend/`: Decoupled Next.js 14 React application.
- **Analysis:** `nextjs-frontend/` contains React components (`Header.tsx`, `JobCard.tsx`, `ResumeBuilder.tsx`) that replicate the UI of the Django templates. However, `nextjs-frontend/` is not built or deployed by Render (`build.sh` only installs Python dependencies and collects Django static files).
- **Risk Level:** Medium (Maintenance overhead; developers might modify Next.js code expecting it to update production).
- **Recommendation:** Formally archive or document `nextjs-frontend/` as a decoupled prototype, or create an independent CI/CD pipeline for Vercel/Render static site deployment.

---

## 3. Structural Duplication Summary Matrix

| Subsystem | Duplicated Component | File A | File B | Recommended Action |
| :--- | :--- | :--- | :--- | :--- |
| **Routing** | SEO & Health Ping | `reqpulse/urls.py` | `requirements/urls.py` | Consolidate to `reqpulse/urls.py` |
| **Parsing** | Salary/Experience Regex | `requirements/job_aggregator.py` | `requirements/views.py` | Extract to `requirements/normalizers.py` |
| **Resume** | PDF Text Extraction | `requirements/views.py` | `requirements/tests_production_fixes.py` | Consolidate to `resume_parser.py` |
| **Frontend** | Job Cards & Navigation | `requirements/templates/` | `nextjs-frontend/` | Archive Next.js or setup Vercel deploy |
| **Admin** | Job Expiry Logic | `requirements/views.py` (`owner_view`) | `requirements/management/commands/expire_jobs.py` | Call shared model manager method |
