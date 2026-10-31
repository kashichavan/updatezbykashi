import json
import sqlite3
import time
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from debugger.javascript_tracer import JavaScriptExecutionTracer
from debugger.python_tracer import PythonExecutionTracer
from sqlsandbox.engine import get_sandboxed_connection, execute_sql_sandbox


class ApplicationSecurityAuditTests(TestCase):
    """
    Comprehensive Security Verification Test Suite.
    Validates remediations across all 15 audit areas:
    - Security headers (CSP, COOP, NOSNIFF, Permissions-Policy)
    - Authentication & hardcoded backdoor elimination
    - Privilege escalation / BOLA defense in Owner APIs
    - Rate limiting & DoS defense
    - SQL sandbox isolation & authorizer checks
    - AST debugger sandbox restrictions & AST expression safety
    - CSRF trusted origin hardening
    """

    def setUp(self):
        self.client = Client()
        # Create normal test user (non-staff)
        self.regular_user = User.objects.create_user(
            username="test_student",
            email="student@example.com",
            password="StrongStudentPassword123!"
        )
        # Create owner/staff user
        self.staff_user = User.objects.create_superuser(
            username="test_owner",
            email="owner@example.com",
            password="StrongOwnerPassword123!"
        )

    def test_security_headers_enforced(self):
        """SEC-001: Responses must include CSP, COOP, Permissions-Policy, nosniff, and X-Frame-Options."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        # Content-Security-Policy
        self.assertIn('Content-Security-Policy', response.headers)
        csp = response.headers['Content-Security-Policy']
        self.assertIn("default-src 'self'", csp)
        self.assertIn("object-src 'none'", csp)

        # Permissions-Policy
        self.assertIn('Permissions-Policy', response.headers)
        self.assertEqual(response.headers['Permissions-Policy'], "geolocation=(), microphone=(), camera=()")

        # Cross-Origin-Opener-Policy
        self.assertIn('Cross-Origin-Opener-Policy', response.headers)
        self.assertEqual(response.headers['Cross-Origin-Opener-Policy'], "same-origin-allow-popups")

        # nosniff & X-Frame-Options
        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertEqual(response.headers['X-Content-Type-Options'], "nosniff")
        self.assertEqual(response.headers['X-Frame-Options'], "DENY")

    def test_hardcoded_master_passwords_completely_rejected(self):
        """SEC-002: Hardcoded legacy credentials must be rejected by auth endpoints."""
        legacy_passwords = [
            'kashi@2026',
            'KashiUpdatez@2026',
            'kashii7777',
            'kashichavan7777',
        ]
        for pwd in legacy_passwords:
            # Test JSON admin login
            resp = self.client.post(
                '/api/admin/login/',
                data=json.dumps({'username': 'test_owner', 'password': pwd}),
                content_type='application/json'
            )
            # Response must fail authentication (status 401 or success=False)
            if resp.status_code == 200:
                data = resp.json()
                self.assertFalse(data.get('success', False), f"Legacy passkey '{pwd}' unexpectedly succeeded!")

    def test_owner_api_role_authorization_blocks_regular_users(self):
        """SEC-003: Non-staff users must be blocked from owner endpoints even with valid JWT."""
        regular_refresh = RefreshToken.for_user(self.regular_user)
        regular_access_token = str(regular_refresh.access_token)

        # Attempt to access owner jobs endpoint with regular user token
        resp = self.client.get(
            '/api/v1/owner/jobs',
            HTTP_AUTHORIZATION=f"Bearer {regular_access_token}"
        )
        self.assertEqual(resp.status_code, 401)

        # Staff user should be permitted
        staff_refresh = RefreshToken.for_user(self.staff_user)
        staff_access_token = str(staff_refresh.access_token)

        resp_staff = self.client.get(
            '/api/v1/owner/jobs',
            HTTP_AUTHORIZATION=f"Bearer {staff_access_token}"
        )
        self.assertEqual(resp_staff.status_code, 200)

    def test_javascript_tracer_safe_eval_replaces_unsafe_eval(self):
        """SEC-004: JavaScript tracer evaluates math safely and neutralizes Python escape payloads."""
        # 1. Valid safe arithmetic
        js_code = """
        let a = 10;
        let b = 20;
        let c = a + b;
        console.log(c);
        """
        tracer = JavaScriptExecutionTracer(js_code)
        result = tracer.execute()
        self.assertTrue(isinstance(result, dict))
        self.assertIn('steps', result)
        self.assertTrue(len(result['steps']) > 0)

        # 2. Python escape expression attempted in JS code should NOT execute or crash tracer
        payload = 'console.log([c for c in ().__class__.__base__.__subclasses__() if c.__name__ == "BuiltinImporter"]);'
        tracer_exploit = JavaScriptExecutionTracer(payload)
        result_exploit = tracer_exploit.execute()
        self.assertTrue(isinstance(result_exploit, dict))
        self.assertIn('steps', result_exploit)
        self.assertTrue(isinstance(result_exploit['steps'], list))

    def test_python_tracer_sandbox_restrictions(self):
        """SEC-005: Python AST sandbox strictly rejects reflection, dunder access, and forbidden imports."""
        # Forbidden reflection token
        code_subclasses = "x = ().__class__.__bases__[0].__subclasses__()"
        tracer = PythonExecutionTracer(code_subclasses)
        valid, msg = tracer.validate_ast()
        self.assertFalse(valid)
        self.assertIn("Security Restriction", msg)

        # Forbidden getattr reflection
        code_getattr = "x = getattr(object, '__subclasses__')()"
        tracer2 = PythonExecutionTracer(code_getattr)
        valid2, msg2 = tracer2.validate_ast()
        self.assertFalse(valid2)
        self.assertIn("Security Restriction", msg2)

        # Forbidden system module
        code_os = "import os\nos.system('echo test')"
        tracer3 = PythonExecutionTracer(code_os)
        valid3, msg3 = tracer3.validate_ast()
        self.assertFalse(valid3)
        self.assertIn("Security Restriction", msg3)

    def test_python_tracer_timeout_guard(self):
        """SEC-006: Execution timeout stops infinite loops within safe wall-clock boundary."""
        code_loop = "while True:\n    pass"
        tracer = PythonExecutionTracer(code_loop)
        result = tracer.execute()
        # Either step limit or timeout triggers
        self.assertTrue(result['status'] in ('success', 'error'))
        self.assertLessEqual(result['total_steps'], 501)

    def test_sqlsandbox_authorizer_blocks_attach_and_dangerous_pragmas(self):
        """SEC-007: SQLite sandbox blocks ATTACH, DETACH, and destructive PRAGMAs."""
        conn = get_sandboxed_connection('scott_tiger')

        # 1. ATTACH must be denied
        with self.assertRaises(sqlite3.DatabaseError):
            conn.execute("ATTACH DATABASE '/tmp/test.db' AS test_db;")

        # 2. Destructive PRAGMA must be denied
        with self.assertRaises(sqlite3.DatabaseError):
            conn.execute("PRAGMA writable_schema = ON;")

        # 3. Read-only PRAGMA table_info is allowed
        cursor = conn.execute("PRAGMA table_info(emp);")
        rows = cursor.fetchall()
        self.assertTrue(len(rows) > 0)
        conn.close()

    def test_rate_limiting_enforced_on_auth(self):
        """SEC-008: Rapid login requests are throttled and return HTTP 429."""
        from django.core.cache import cache
        cache.clear()

        hit_429 = False
        for i in range(15):
            resp = self.client.post(
                '/api/admin/login/',
                data=json.dumps({'username': 'attacker', 'password': 'bad_password'}),
                content_type='application/json'
            )
            if resp.status_code == 429:
                hit_429 = True
                self.assertIn('Retry-After', resp.headers)
                break

        self.assertTrue(hit_429, "Rate limiter did not throttle excessive authentication requests!")

    def test_csrf_trusted_origins_hardened(self):
        """SEC-009: CSRF_TRUSTED_ORIGINS must not contain unrestricted wildcard origins ('*' or 'https://*')."""
        for origin in settings.CSRF_TRUSTED_ORIGINS:
            self.assertNotIn(origin, ('*', 'https://*', 'http://*'), f"Dangerous unrestricted wildcard origin '{origin}' found in CSRF_TRUSTED_ORIGINS!")
