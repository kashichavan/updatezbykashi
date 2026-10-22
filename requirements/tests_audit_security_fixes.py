"""
Regression tests for Audit Security & Concurrency Fixes:
- SEC-001: Python Tracer AST & Builtin Sandbox Protections (open, OS import, dunder access)
- SEC-002: SQLite Sandbox Authorizer & Progress Handler Protections (ATTACH DATABASE, infinite CTE)
- BUG-001: Atomic Application Counter Increment using F() expression
- BUG-002: Step Limit Termination in Python Tracer Infinite Loops
"""

import sqlite3
from django.test import TestCase, Client
from django.utils import timezone
from requirements.models import JobPosting, Category
from debugger.python_tracer import PythonExecutionTracer
from sqlsandbox.engine import execute_sql_sandbox


class AuditSecurityAndBugFixesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Engineering", slug="engineering")
        self.job = JobPosting.objects.create(
            title="Backend Engineer",
            company_name="Acme Corp",
            category=self.category,
            location="Bengaluru, India",
            apply_url="https://example.com/apply/backend-engineer",
            status="ACTIVE",
            applications_count=5,
            deadline=timezone.now() + timezone.timedelta(days=14)
        )

    # ─────────────────────────────────────────────────────────────
    # SEC-001 & BUG-002: Python Tracer Sandbox Tests
    # ─────────────────────────────────────────────────────────────
    def test_debugger_tracer_blocks_open(self):
        """SEC-001: open() must be rejected during AST validation."""
        tracer = PythonExecutionTracer("with open('.env', 'r') as f: content = f.read()")
        res = tracer.execute()
        self.assertEqual(res['status'], 'error')
        self.assertIn("Function 'open()' is restricted", res['message'])

    def test_debugger_tracer_blocks_os_import(self):
        """SEC-001: Disallowed module imports like 'os' or 'subprocess' must be rejected."""
        tracer = PythonExecutionTracer("import os\nos.system('echo hacked')")
        res = tracer.execute()
        self.assertEqual(res['status'], 'error')
        self.assertIn("Module 'os' is restricted", res['message'])

    def test_debugger_tracer_blocks_dunder_traversal(self):
        """SEC-001: Dunder attribute traversal like __subclasses__ must be blocked."""
        tracer = PythonExecutionTracer("x = ().__class__.__bases__[0].__subclasses__()")
        res = tracer.execute()
        self.assertEqual(res['status'], 'error')
        self.assertIn("Dunder attribute", res['message'])

    def test_debugger_tracer_terminates_infinite_loop(self):
        """BUG-002: Runaway loops must be terminated at MAX_STEPS without exhausting memory."""
        code = (
            "count = 0\n"
            "while True:\n"
            "    count += 1\n"
        )
        tracer = PythonExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertGreaterEqual(res['total_steps'], tracer.MAX_STEPS)
        last_step = res['steps'][-1]
        self.assertEqual(last_step['event_type'], 'exception')
        self.assertIn("Execution step limit exceeded", last_step['ai_explanation'])

    def test_debugger_tracer_normal_code_succeeds(self):
        """Safe Python math and data structure logic must execute cleanly."""
        code = (
            "import math\n"
            "arr = [3, 1, 4, 1, 5]\n"
            "arr.sort()\n"
            "val = math.sqrt(16)\n"
        )
        tracer = PythonExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertEqual(res['steps'][-1]['variables']['val']['raw'], '4.0')

    # ─────────────────────────────────────────────────────────────
    # SEC-002: SQL Sandbox Isolation Tests
    # ─────────────────────────────────────────────────────────────
    def test_sql_sandbox_blocks_attach_database(self):
        """SEC-002: SQLite ATTACH DATABASE statements must be rejected by authorizer."""
        res = execute_sql_sandbox("ATTACH DATABASE 'db.sqlite3' AS leaked_db;")
        self.assertFalse(res['success'])
        self.assertIn("not authorized", res['error'])

    def test_sql_sandbox_blocks_detach_database(self):
        """SEC-002: SQLite DETACH statements must be rejected by authorizer."""
        res = execute_sql_sandbox("DETACH DATABASE dummy;")
        self.assertFalse(res['success'])
        self.assertIn("not authorized", res['error'])

    def test_sql_sandbox_terminates_runaway_cte(self):
        """SEC-002: Infinite recursive CTE queries must be terminated by progress handler."""
        res = execute_sql_sandbox("WITH RECURSIVE loop(n) AS (VALUES(1) UNION ALL SELECT n+1 FROM loop) SELECT count(*) FROM loop;")
        self.assertFalse(res['success'])
        self.assertIn("interrupted", res['error'])

    def test_sql_sandbox_valid_query_succeeds(self):
        """Legitimate student queries must execute successfully."""
        res = execute_sql_sandbox("SELECT ename, job, sal FROM emp WHERE sal >= 3000 ORDER BY sal DESC;", dataset_id='scott_tiger')
        self.assertTrue(res['success'])
        self.assertGreaterEqual(len(res['rows']), 2)
        self.assertEqual(res['columns'], ['ename', 'job', 'sal'])

    # ─────────────────────────────────────────────────────────────
    # BUG-001: Job Apply Concurrency Test
    # ─────────────────────────────────────────────────────────────
    def test_job_apply_redirect_increments_atomically(self):
        """BUG-001: Clicking apply must increment applications_count atomically."""
        initial_count = self.job.applications_count
        resp = self.client.get(f"/job/{self.job.uuid}/apply/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, self.job.apply_url)

        self.job.refresh_from_db()
        self.assertEqual(self.job.applications_count, initial_count + 1)

    # ─────────────────────────────────────────────────────────────
    # Additional Verification: Healthcheck & Tracer Memory Stability
    # ─────────────────────────────────────────────────────────────
    def test_api_ping_healthcheck(self):
        """Verify centralized /api/ping responds with 200 OK and status."""
        resp = self.client.get("/api/ping")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "ok")

    def test_javascript_tracer_memory_stability(self):
        """Verify JavaScript tracer preserves variable mem_addr across function calls."""
        from debugger.javascript_tracer import JavaScriptExecutionTracer
        code = (
            "function inc(n) {\n"
            "  let r = n + 1;\n"
            "  return r;\n"
            "}\n"
            "let a = inc(10);\n"
            "let b = inc(a);\n"
        )
        tracer = JavaScriptExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        addrs = [s['variables']['a']['mem_addr'] for s in res['steps'] if 'a' in s['variables']]
        self.assertTrue(len(addrs) > 0)
        self.assertTrue(all(addr == addrs[0] for addr in addrs), f"Addresses unstable: {addrs}")

    def test_java_tracer_memory_stability(self):
        """Verify Java tracer maintains stable variable mem_addr across multiple method invocations."""
        from debugger.java_tracer import JavaExecutionTracer
        code = (
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        int a = square(3);\n"
            "        int b = square(4);\n"
            "    }\n"
            "    static int square(int n) {\n"
            "        int r = n * n;\n"
            "        return r;\n"
            "    }\n"
            "}\n"
        )
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        n_addrs = [s['variables']['n']['mem_addr'] for s in res['steps'] if 'n' in s['variables']]
        self.assertTrue(len(n_addrs) > 0)
        self.assertTrue(all(addr == n_addrs[0] for addr in n_addrs), f"Java addresses unstable: {n_addrs}")

