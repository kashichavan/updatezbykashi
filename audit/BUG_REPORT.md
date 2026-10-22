# KashiiUpdatez — Comprehensive Bug & Defect Report

**Repository:** `kashichavan/updatezbykashi`  
**Audit Date:** October 2026  
**Auditor:** Principal Software Architect & AppSec Auditor  

---

## 1. Defect Classification & Severity Standards

- **P0 — Critical / Blocker:** Remote code execution, arbitrary file access, database compromise, or catastrophic data loss.
- **P1 — High Priority:** Service denial, thread starvation, unhandled crash in core user journey, or bypass of core business rules.
- **P2 — Medium Priority:** Concurrency race condition, incorrect metric tracking, or edge-case validation failure.
- **P3 — Low / Cosmetic:** Minor UI misalignment, non-critical log warning, or non-breaking API schema omission.

---

## 2. Summary of Identified Defects

| ID | Title | Severity | Component | Status |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-001** | Python Tracer Sandbox Escape & Arbitrary File Access | **P0** | `debugger/python_tracer.py` | **FIXED & VERIFIED** |
| **SEC-002** | SQLite Sandbox Disk DB Attachment Vulnerability | **P0** | `sqlsandbox/engine.py` | **FIXED & VERIFIED** |
| **BUG-001** | Job Application Counter Concurrency Race Condition | **P2** | `requirements/views.py` | **FIXED & VERIFIED** |
| **BUG-002** | Python Execution Tracer Infinite Loop Denial-of-Service | **P1** | `debugger/python_tracer.py` | **FIXED & VERIFIED** |
| **BUG-003** | Scraping Daemon Memory Growth on Continuous Loops | **P2** | `job_aggregator.py` | **DOCUMENTED FOR REVIEW** |
| **BUG-004** | Missing Connection Closing in SQLite Sandbox on Syntax Error | **P3** | `sqlsandbox/engine.py` | **FIXED (finally block verified)** |

---

## 3. Detailed Defect Analysis & Fix Evidence

### SEC-001: Python Tracer Sandbox Escape & Arbitrary File Access (P0)
- **Vulnerability Description:** The Python execution tracer evaluated user-submitted code in an execution context where the standard `builtins` module was passed directly without sanitization, and the AST validator only checked a limited set of function names (`eval`, `exec`, `__import__`, `compile`). Consequently, users could invoke `open('.env').read()`, `import os`, or traverse dunders (`__subclasses__`) to read server files, inspect environment variables, or execute arbitrary OS commands.
- **Reproduction Proof:**
  ```python
  code = "with open('.env.example', 'r') as f: text = f.read()"
  tracer = PythonExecutionTracer(code)
  res = tracer.execute()
  # Succeeded and loaded environment secrets into variable inspector!
  ```
- **Remediation Applied:**
  1. Updated `FORBIDDEN_FUNCTIONS` to include `'open', 'eval', 'exec', '__import__', 'compile', 'breakpoint', 'help', 'exit', 'quit', 'globals', 'locals', 'vars'`.
  2. Enforced module whitelist `ALLOWED_MODULES = {'math', 'random', 'string', 'itertools', 'collections', 'heapq', 'bisect', 're', 'datetime', 'time', 'copy', 'json'}` in AST validation for both `ast.Import` and `ast.ImportFrom`.
  3. Added AST check blocking dangerous dunder attribute traversal.
  4. Sanitized `__builtins__` in `exec()`, injecting a restricted import hook and stripping `open`.
- **Verification Evidence:** `test_debugger_tracer_blocks_open`, `test_debugger_tracer_blocks_os_import`, and `test_debugger_tracer_blocks_dunder_traversal` in `requirements/tests_audit_security_fixes.py` all **PASS**.

---

### SEC-002: SQLite Sandbox Disk Database Attachment (P0)
- **Vulnerability Description:** `sqlsandbox/engine.py` created an in-memory SQLite connection (`:memory:`) to execute student SQL challenges. However, it did not install a SQLite authorizer (`conn.set_authorizer()`). An attacker could execute `ATTACH DATABASE 'db.sqlite3' AS prod;` to mount the production database file from disk and query sensitive user records, password hashes, and session tokens.
- **Reproduction Proof:**
  ```python
  execute_sql_sandbox("ATTACH DATABASE 'db.sqlite3' AS prod; SELECT count(*) FROM prod.requirements_jobposting;")
  # Succeeded and returned count of all jobs in local database!
  ```
- **Remediation Applied:**
  1. Implemented `_sandbox_authorizer` blocking `SQLITE_ATTACH` and `SQLITE_DETACH`.
  2. Installed the authorizer in `get_sandboxed_connection()` and `execute_sql_sandbox()`.
  3. Installed a progress handler (`conn.set_progress_handler`) with a 3.0-second execution deadline to abort runaway recursive CTEs.
- **Verification Evidence:** `test_sql_sandbox_blocks_attach_database`, `test_sql_sandbox_blocks_detach_database`, and `test_sql_sandbox_terminates_runaway_cte` all **PASS**.

---

### BUG-001: Job Application Counter Concurrency Race Condition (P2)
- **Defect Description:** In `job_apply_redirect_view` (`requirements/views.py`), the application counter was updated using `JobPosting.objects.filter(pk=job.pk).update(applications_count=job.applications_count + 1)`. Under concurrent clicks, this in-memory read-modify-write pattern causes lost updates.
- **Remediation Applied:**
  Replaced the in-memory counter increment with Django's atomic database `F()` expression:
  ```python
  from django.db.models import F
  JobPosting.objects.filter(pk=job.pk).update(applications_count=F('applications_count') + 1)
  ```
- **Verification Evidence:** `test_job_apply_redirect_increments_atomically` verified that `applications_count` increments atomically.

---

### BUG-002: Python Execution Tracer Infinite Loop Denial-of-Service (P1)
- **Defect Description:** In `debugger/python_tracer.py`, `trace_callback()` recorded every execution step into `self.steps` without an upper bound. A user submitting `while True: pass` caused runaway memory allocation and CPU consumption, hanging the Gunicorn worker thread until timeout.
- **Remediation Applied:**
  Enforced `MAX_STEPS = 500`. In `trace_callback`, if `len(self.steps) >= self.MAX_STEPS`, a `RuntimeError("Execution step limit exceeded (500 steps)")` is raised, terminating execution cleanly and capturing the exception in the trace log.
- **Verification Evidence:** `test_debugger_tracer_terminates_infinite_loop` verifies that infinite loops are halted at step 501 with an informative message.
