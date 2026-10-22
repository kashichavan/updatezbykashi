# KashiiUpdatez — Comprehensive Job Aggregation & Scraper Audit

**Repository:** `kashichavan/updatezbykashi`  
**Audit Date:** October 2026  
**Auditor:** Principal Backend & Data Pipeline Engineer  
**Pipeline Engine:** `requirements/job_aggregator.py` & `requirements/jobdexo_service.py`  

---

## 1. Aggregation Engine Overview

The job aggregation pipeline automates the ingestion, normalization, deduplication, and lifecycle management of tech job postings across India. It supports both scheduled hourly background synchronization and on-demand trigger views from the owner portal.

---

## 2. Ingestion Sources & Parsers

| Source Name | Ingestion Method | Parser Implementation | Target Technologies / Roles | Resiliency & Headers |
| :--- | :--- | :--- | :--- | :--- |
| **Naukri** | Web scraping & RSS | `scrape_naukri_jobs()` | Python, Java, Full Stack, DevOps, Cloud, AI | Rotated User-Agents, exponential backoff |
| **LinkedIn** | Public Job Postings API / HTML | `scrape_linkedin_jobs()` | Fresher & Junior Software Engineers | Rate limit detection, session cookie support |
| **Jobdexo** | REST Feed / Webhook | `auto_import_from_jobdexo()` | Off-campus drives, batch hiring | Schema validation, duplicate ID hashing |
| **Indian Startups** | Career portal feeds | `scrape_startup_jobs()` | Django, FastAPI, React, Node.js | Direct JSON parsing, fallback HTML |

---

## 3. Data Transformation & Normalization Pipeline

### 3.1 Company Name Resolution (`requirements/company_resolver.py`)
- Standardizes noisy employer strings (e.g., `"TCS Ltd."`, `"Tata Consultancy Services India Pvt Ltd"`, `"TCS Careers"`) into canonical brand names (`"Tata Consultancy Services"`).
- Normalizes corporate suffixes (`Inc.`, `LLC`, `Private Limited`, `Pvt Ltd`).

### 3.2 Indian Tech Hub Normalization
- Extracts and normalizes location strings into 15 official Indian technology hubs:
  * Bengaluru, Karnataka
  * Hyderabad, Telangana
  * Pune, Maharashtra
  * Mumbai, Maharashtra
  * Chennai, Tamil Nadu
  * Gurugram / Noida / Delhi NCR
  * Ahmedabad, Kochi, Kolkata, Coimbatore, Jaipur, Indore, Bhubaneswar
- Flags remote roles with `is_remote=True`.

### 3.3 Salary & Experience Parsing
- Extracts compensation ranges formatted in Lakhs Per Annum (`LPA`) or INR figures.
- Normalizes experience brackets (e.g. `0-2 years`, `Freshers eligible`, `2024 / 2025 / 2026 Batch`).

---

## 4. Deduplication & Database Integrity

1. **Unique Fingerprinting:** Each ingested record computes a SHA-256 hash based on `(normalized_company, title_slug, location_slug)` in addition to tracking `source_job_id`.
2. **Upsert Logic:** When a job posting already exists, the aggregator updates the `last_seen_at` timestamp and status without creating redundant duplicate rows.
3. **Database Population:** Verified 479 active job postings in the database baseline.
4. **Cleanup Utility:** `cleanup_all_database_duplicates()` sweeps the database to merge accidental duplicates created by concurrent crawler runs.

---

## 5. Daemon Lifecycle & Resource Management

- **Command:** `python manage.py run_job_aggregator`
- **Execution Architecture:** Continuous loop running with a configurable sleep interval (default: 3600 seconds / 1 hour with +/- 10% random jitter).
- **Process Guard:** Implements a filesystem lockfile (`/tmp/job_aggregator.lock` or configurable) to prevent multiple scraper processes from running simultaneously.
- **Connection Health:** Explicitly calls `django.db.reset_queries()` and `connection.close()` at the end of each iteration to prevent memory leaks and orphaned database connections during long uptimes on Render.
