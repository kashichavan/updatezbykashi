# KashiiUpdatez — SQL Practice Sandbox Audit

**Repository:** `kashichavan/updatezbykashi`  
**Audit Date:** October 2026  
**Auditor:** Principal Database & Security Architect  
**Subsystem:** `sqlsandbox/` (`engine.py`, `views.py`)  

---

## 1. Sandbox Architecture

The SQL Sandbox is an interactive browser-based database environment allowing students and job seekers to practice relational queries, multi-table joins, subqueries, and window functions on realistic industry datasets without impacting production storage.

```
Candidate SQL Input
         │
         ▼
[sqlsandbox.engine: execute_sql_sandbox]
         │
         ├── Fresh In-Memory SQLite Database (:memory:)
         ├── Seed Standard Dataset Schema & Data
         ├── Install Strict SQLite Authorizer (Blocks ATTACH / DETACH)
         ├── Install 3.0s Execution Timeout Progress Handler
         ├── Run EXPLAIN QUERY PLAN (on read queries)
         └── Execute Statements & Truncate Output (Max 500 rows)
         │
         ▼
JSON Execution Result
[Columns, Rows, Query Plan, Execution Time, Schema Metadata]
         │
         ▼
Interactive Data Table & Schema Visualizer
```

---

## 2. Curated Standard Datasets

| Dataset ID | Name | Core Tables | Scenario Context |
| :--- | :--- | :--- | :--- |
| `scott_tiger` | Classic Scott/Tiger | `emp`, `dept`, `salgrade`, `bonus` | Oracle standard benchmark; employee/manager hierarchy. |
| `faang` | FAANG Tech Corp | `models`, `gpu_clusters`, `training_runs` | AI compute infrastructure costs and training run metrics. |
| `fintech` | FinTech & Banking | `branches`, `accounts`, `transactions` | High-volume financial ledgers, balance tracking, loans. |
| `ecommerce` | Indian E-Commerce | `users`, `products`, `orders`, `order_items` | Cart abandonment, GST billing, inventory depletion. |
| `hospital` | Healthcare & Clinic | `patients`, `doctors`, `appointments` | Clinic scheduling, doctor specialties, patient history. |

---

## 3. Security Hardening & Remediation Evidence

### 3.1 SQLite Authorizer (`_sandbox_authorizer`)
- **Vulnerability (SEC-002):** Unrestricted SQLite memory connections allowed attackers to execute `ATTACH DATABASE 'db.sqlite3' AS prod;` and read server data files.
- **Remediation:** Installed a SQLite authorizer hook:
  ```python
  def _sandbox_authorizer(action, arg1, arg2, dbname, source):
      if action in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH):
          return sqlite3.SQLITE_DENY
      return sqlite3.SQLITE_OK
  ```
- **Verification:** Verified via `test_sql_sandbox_blocks_attach_database` that unauthorized attach attempts raise `Execution Error: not authorized`.

### 3.2 Runaway Query Timeout Handler
- **Risk:** Recursive Common Table Expressions (`WITH RECURSIVE c(x) AS (...)`) can create infinite loops that lock the thread.
- **Remediation:** Installed `conn.set_progress_handler` checking elapsed time against a 3.0-second limit.
- **Verification:** Verified via `test_sql_sandbox_terminates_runaway_cte` that recursive CTEs are killed with `OperationalError: interrupted` within 3.00 seconds.

---

## 4. Query Plan & Performance Introspection

- For all read queries (`SELECT`, `WITH`), the engine executes `EXPLAIN QUERY PLAN` and returns structured query plan steps.
- Students receive real-time feedback showing whether queries perform full table scans (`SCAN TABLE`) or leverage indexes (`SEARCH TABLE USING INDEX`).

---

## 5. Audit Verdict

The SQL Sandbox subsystem is **VERIFIED AND SECURED**. Memory isolation is guaranteed on every execution cycle.
