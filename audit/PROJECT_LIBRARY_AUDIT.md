# KashiiUpdatez — Demonstration Project Library Audit

**Repository:** `kashichavan/updatezbykashi`  
**Audit Date:** October 2026  
**Auditor:** Principal Software Architect & Industry Curriculum Specialist  
**Dataset & Engine:** `requirements/indian_dummy_projects.py` & `management/commands/seed_indian_projects.py`  

---

## 1. Project Library Overview

The Indian Market Demonstration Project Library provides 36 realistic, fictional case-study engineering projects tailored to the hiring requirements of Indian tech hubs and multinational service/product firms. 

Each project is defined with Indian business context, enterprise architecture, ATS-friendly Google XYZ resume bullet points, difficulty rating, estimated duration, and clear ethical attribution disclosures.

---

## 2. Technology Stack & City Hub Distribution

| Technology Stack | Project Count | Sample Projects & City Contexts | Primary Technologies |
| :--- | :--- | :--- | :--- |
| **Python / Django** | 8 | Employee Management (Bengaluru), Hospital Appointment (Hyderabad), E-Commerce Inventory (Mumbai), GST Billing (Ahmedabad) | Django, DRF, Celery, Redis, PostgreSQL, Docker |
| **Java / Spring Boot** | 6 | Digital Banking (Mumbai), Microservices E-Commerce (Bengaluru), Insurance Claims (Hyderabad), Logistics Tracking (Chennai) | Spring Boot 3, Spring Cloud, Kafka, PostgreSQL, Kubernetes |
| **React / Full-Stack** | 6 | Job Search Portal (Bengaluru), LMS Platform (Hyderabad), Restaurant Delivery (Chennai), Real Estate (Pune) | React 19, TypeScript, Next.js, Node.js, Tailwind, MongoDB |
| **DevOps / Cloud** | 6 | Docker Microservices CI/CD (Bengaluru), AWS Infrastructure as Code (Hyderabad), GitOps Pipeline (Pune), K8s Observability (Gurugram) | Kubernetes, Terraform, Docker, AWS, Prometheus, Grafana, ArgoCD |
| **Data / AI / ML** | 5 | Customer Churn Predictor (Bengaluru), Indian Financial News Sentiment (Mumbai), Healthcare OCR (Hyderabad) | Python, PyTorch, Scikit-Learn, FastAPI, LangChain, HuggingFace |
| **Mobile Development** | 5 | UPI Payment App (Bengaluru), Hyperlocal Grocery (Mumbai), Fitness Tracker (Pune) | Flutter, Kotlin, Android SDK, Firebase, REST APIs |
| **TOTAL** | **36** | **Covering 15 Indian Technology Hubs** | Enterprise Production Standards |

---

## 3. Ethical Attribution System

To uphold academic and professional integrity, every demonstration project integrates mandatory attribution badges:

1. **`BUILT` (Personally Developed):** The candidate authored the architecture, database schema, and source code as an independent portfolio project.
2. **`CONTRIBUTED` (Open Source Contribution):** The candidate contributed features, bug fixes, or documentation to an existing open-source project or team effort.
3. **`RECOMMENDED` (Architecture & Case Study):** The project is referenced as a study case or system design demonstration without claiming proprietary ownership.

---

## 4. Seeding Command & Idempotence

- **Management Command:** `python manage.py seed_indian_projects`
- **Verification of Flags:**
  * `--dry-run`: Analyzes existing database state without performing writes; reports planned creations and updates.
  * Live Upsert: Uses `IndianProject.objects.update_or_create(slug=...)`.
- **Test Executions:**
  * First run: 36 records created, 0 updated.
  * Second run: 0 records created, 36 updated (100% idempotent).
  * `--dry-run` run: Verified clean dry-run output without side effects.

---

## 5. Job-Tailored Matching Engine

When a candidate views or generates a resume for a specific job posting:
1. The matching engine extracts the job's required tech stack and target city.
2. Projects matching both stack and location are scored highest (e.g. Django + Bengaluru).
3. If no city-specific project matches, the engine falls back to stack matching, ensuring candidates always receive highly relevant portfolio demonstrations.
4. ATS bullet points for selected projects are pre-formatted for direct inclusion into the ReportLab PDF and Word DOCX templates.
