# KashiiUpdatez — Comprehensive Database & Data Integrity Audit

**Repository:** `kashichavan/updatezbykashi`  
**Audit Date:** October 2026  
**Auditor:** Principal Database Engineer & Architect  
**Engines Supported:** PostgreSQL 16+ (Production on Render) & SQLite 3 (Local Development & Testing)  

---

## 1. Schema & Model Architecture

The data architecture is structured across two primary Django applications: `requirements` (jobs, projects, resumes) and `blog` (career guides).

### Primary Entity Relationships

```
Category ───< (1:N) ─── JobPosting ───< (1:N) ─── ResumeGenerationJob
                             │
                             └───< (1:N) ─── DiscoveredProject
                                                    │
                                                    ├── GitHub Repositories
                                                    └── Curated Indian Market Projects (IndianProject)
```

---

## 2. Model Inventory & Integrity Constraints

| Model | Table Name | Key Constraints & Indexes | Integrity Notes |
| :--- | :--- | :--- | :--- |
| `Category` | `requirements_category` | `slug` (unique, db_index=True) | Taxonomy taxonomy index for fast category filtering. |
| `JobPosting` | `requirements_jobposting` | `uuid` (unique, db_index=True), `source_job_id` (index), `created_at` (index) | Deduplication index on `(source_name, source_job_id)`. Soft delete via `is_active` / `status`. |
| `ResumeGenerationJob` | `requirements_resumegenerationjob` | `uuid` (unique, db_index=True), FK to `JobPosting` | Stores parsed candidate profile, target job, ATS scores, and selected projects. |
| `DiscoveredProject` | `requirements_discoveredproject` | FK to `ResumeGenerationJob`, FK to `JobPosting` | Stores repository matches, matching scores, and attribution mode (`BUILT`, `CONTRIBUTED`, `RECOMMENDED`). |
| `IndianProject` | `requirements_indianproject` | `slug` (unique, db_index=True), `target_stack` (index), `city` (index) | Curated Indian market dummy project library with 36 seeded records. |
| `JobGroup` | `requirements_jobgroup` | `slug` (unique), `name` | Clustering model for batched hiring announcements. |
| `GuideArticle` | `requirements_guidearticle` | `slug` (unique), `category` | In-app career and interview preparation articles. |
| `BlogPost` | `blog_blogpost` | `slug` (unique), `published_at` (index) | Tech blog articles with Markdown content and tags. |

---

## 3. Query Performance & Optimization

### 3.1 N+1 Query Elimination
- In `requirements/views.py:home_view` and `job_list_view`, the query for job postings utilizes:
  ```python
  JobPosting.objects.filter(status='ACTIVE')
                    .select_related('category')
                    .prefetch_related('discovered_projects')
                    .order_by('-created_at')[:50]
  ```
- **Finding:** Categories are eagerly joined using `select_related`, eliminating N+1 queries during homepage rendering.

### 3.2 Atomic Concurrency on Counters
- Previously, `job_apply_redirect_view` updated `applications_count` using Python in-memory values.
- As part of the audit fix (BUG-001), all counter updates now execute through the database engine using `F('applications_count') + 1`:
  ```python
  JobPosting.objects.filter(pk=job.pk).update(applications_count=F('applications_count') + 1)
  ```
- This guarantees transactional atomicity even under high concurrency.

### 3.3 Large Table Pagination
- The job board implements pagination (50 jobs per page) with database `OFFSET` / `LIMIT`, preventing unbounded query loads on the PostgreSQL cluster.

---

## 4. Migration History & Consistency

- **Requirements Migrations:** 19 migrations (`0001_initial` through `0019_add_indian_project_library`).
- **Blog Migrations:** 4 migrations (`0001_initial` through `0004_tags`).
- **Graph State:** The migration dependency graph is linear with zero branch conflicts or unapplied migrations.
- **Verification:** `python manage.py showmigrations` confirmed all 23 application migrations are synchronized with the database schema.

---

## 5. Database Recommendations

1. **Composite Index for Multi-filter Search:** Consider adding a composite index on `JobPosting(status, normalized_city, created_at)` to optimize multi-faceted city and freshness queries.
2. **Connection Pooling:** In production Render environments, verify that `CONN_MAX_AGE` is configured in `settings.py` (e.g. 60–300 seconds) to reuse database connections across Gunicorn worker threads.
