---
name: sql-sandbox-engine
description: >-
  Enterprise guide and architectural patterns for high-performance isolated SQL execution sandboxes, in-memory database management, schema introspection, query plan analyzers, and automated SQL challenge validation engines.
  Use this skill when building browser-based SQL playgrounds, Monaco SQL IDEs, multi-dataset database sandboxes, EXPLAIN plan visualizers, and interactive LeetCode/HackerRank style SQL interview test runners.
---

# SQL Sandbox Engine & Interactive Database Studio Architecture

This skill provides enterprise patterns for building high-performance, secure, multi-dataset SQL execution engines integrated with Monaco Editor, schema introspection, execution plan visualization, and automated challenge verification.

---

## 1. Core Sandbox Architecture

```text
               ┌─────────────────────────────────────────┐
               │         Monaco SQL Studio (Frontend)    │
               │  - Syntax Highlighting & Autocomplete   │
               │  - Schema Tree & Table Inspector        │
               │  - Query Plan Tree & Results Grid       │
               └────────────────────┬────────────────────┘
                                    │ POST /sql/api/execute/
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Django SQL Sandbox Engine                       │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Session Isolation: Ephemeral in-memory SQLite / temp instance       │
│ 2. Preloaded Enterprise Datasets (FAANG, E-Commerce, Banking, Social)  │
│ 3. Multi-Statement Parser & DDL/DML/DQL execution dispatcher           │
│ 4. Execution Timing (Microsecond precision) & Row-capping (max 1000)   │
│ 5. EXPLAIN QUERY PLAN AST Analyzer & SARGability validator             │
│ 6. Challenge Verification Engine (Ordered row comparison & Diffing)    │
└────────────────────────────────────────────────────────────────────────┘
```
