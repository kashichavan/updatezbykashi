# KashiiUpdatez — Comprehensive Resume Studio & ATS Engine Audit

**Repository:** `kashichavan/updatezbykashi`  
**Audit Date:** October 2026  
**Auditor:** Principal Software Architect & Document Engineering Specialist  
**Core Modules:** `requirements/resume_pdf.py`, `requirements/resume_docx.py`, `requirements/views.py`  

---

## 1. Resume Studio Architecture

The KashiiUpdatez Resume Studio is an end-to-end career toolkit that enables candidates to upload existing resumes, calculate real-time ATS job-match compatibility scores, generate Google XYZ-formula bullet points via LLM inference, incorporate curated demonstration projects, and export publication-ready multi-page PDFs and DOCX files.

---

## 2. Ingestion & ATS Scoring Pipeline

```
Candidate File (PDF/DOCX)
           │
           ▼
[Format Sniffer & Magic Bytes]
           │
           ├── (PDF)  ──► pypdf.PdfReader (with binary fallback)
           └── (DOCX) ──► python-docx document parser
           │
           ▼
[Extracted Text Normalization]
           │
           ├── Contact Extractor (Email, Phone, LinkedIn, GitHub)
           ├── Section Header Segmenter (Summary, Skills, Experience, Education)
           └── Skill Extractor (Matches against 120+ tech keywords)
           │
           ▼
[Job-Tailored ATS Scoring Engine]
           │
           ├── Skill Keyword Match Rate (Weight: 45%)
           ├── Experience & Seniority Alignment (Weight: 20%)
           ├── Action Verb & Quantifiable Metrics Rate (Weight: 20%)
           └── Formatting & Section Structure Compliance (Weight: 15%)
           │
           ▼
Final Score (0-100%) + Missing Critical Keywords + Section Feedback
```

---

## 3. AI Google XYZ Bullet Generation

- **Formula Standard:** Google XYZ methodology: *"Accomplished [X] as measured by [Y], by doing [Z]"*.
- **Inference Client:** Direct integration with Groq API using streaming and JSON completion modes.
- **Model Fallback Chain:**
  1. Primary Model: `llama-3.3-70b-versatile` (high quality, structured reasoning).
  2. Fallback Model 1: `llama-3.1-8b-instant` (low-latency fallback).
  3. Fallback Model 2: `openai/gpt-oss-20b` (secondary provider fallback).
- **Rate Limit Resilience:** When Groq returns HTTP 429 Too Many Requests, the handler catches the exception, logs model rotation, and seamlessly completes the prompt using the backup model.

---

## 4. Multi-Page ReportLab PDF Generation (`requirements/resume_pdf.py`)

### 4.1 Flowable Architecture & Multi-Page Support
- **Custom Canvas (`NumberedCanvas`):** Implements a two-pass canvas to dynamically compute and print `"Page X of Y"` footers cleanly on every page.
- **Page Budgeting & Flow Control:** Uses `KeepTogether` and `keepWithNext=True` on section headers and project blocks, preventing orphaned headings or split bullet points across page breaks.
- **Typography & Proportions:**
  * Margins: 0.5 in (36 pt) top/bottom, 0.5 in left/right for maximum ATS readable space.
  * Typography: Helvetica and Helvetica-Bold hierarchy (16 pt Name, 11 pt Section Headers, 9.5 pt Body / Bullets, 8 pt Meta text).
  * Color Palette: Deep Slate (`#1e293b`), Navy Accent (`#1d4ed8`), Charcoal Body (`#334155`).
- **Verified Behavior:** Resumes dynamically expand across 1, 2, or 3 pages based on candidate experience volume without text overlap or clipping.

---

## 5. Word DOCX Generation (`requirements/resume_docx.py`)

- **ATS Compatibility:** Standard Word `.docx` structure generated using `python-docx`.
- **Formatting Guarantees:**
  * Uses standard single-column layout without nested text boxes or floating frames (which commonly crash enterprise ATS parsers like Workday, Taleo, and Greenhouse).
  * Standard bullet styles (`List Bullet`) with native indentation.
  * Hyperlinked contact details (LinkedIn, GitHub, Portfolio).

---

## 6. Audit Verification Verdict

- **PDF Generation Tests:** `test_resume_pdf_generation_single_and_multi_page` **PASS**.
- **DOCX Generation Tests:** `test_resume_docx_export_validity` **PASS**.
- **ATS Evaluation Tests:** `test_resume_upload_endpoint` **PASS**.
- **Bullet Generator Fallback Tests:** `test_ai_bullet_generator_fallback_chain` **PASS**.
