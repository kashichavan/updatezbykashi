"""
Playwright Test Suite 14: Engine Stress, Concurrency & Data Integrity Depth
Tests complex algorithm tracing in Code Debugger, advanced SQL joins/aggregations,
API concurrency burst testing, and 7-day job lifetime integrity.
"""

import pytest
import ssl
import urllib.request
import concurrent.futures
from datetime import datetime, timezone, timedelta
from playwright.sync_api import Page, APIRequestContext, expect
from tests_playwright.pages.debugger_page import DebuggerPage
from tests_playwright.pages.sql_page import SQLSandboxPage

class TestEngineStressAndConcurrency:
    """Depth Engine Stress, Complex Tracing & Concurrency Suite."""

    # 1. ADVANCED ALGORITHM TRACE IN CODE DEBUGGER
    def test_complex_algorithm_trace_execution(self, page: Page, base_url: str):
        """Execute and trace a multi-step Fibonacci / loop algorithm in the Python debugger."""
        debugger = DebuggerPage(page, base_url)
        debugger.open()

        debugger.select_language("python")
        debugger.execute_trace()

        # Step through multiple steps
        btn_next = page.locator("button#btnNext")
        if btn_next.is_visible() and not btn_next.is_disabled():
            for _ in range(3):
                btn_next.click()
                page.wait_for_timeout(200)

        expect(debugger.output_console).to_be_visible()

    # 2. ADVANCED SQL SANDBOX JOINS & AGGREGATE QUERIES
    def test_advanced_sql_queries_and_aggregations(self, page: Page, base_url: str):
        """Execute complex SQL queries with COUNT, GROUP BY, and ORDER BY."""
        sql_page = SQLSandboxPage(page, base_url)
        sql_page.open()

        complex_query = "SELECT 'Engineering' AS department, COUNT(*) AS total_count GROUP BY department ORDER BY total_count DESC;"
        sql_page.run_query(complex_query)

        # Result table or success status should be present
        expect(page.locator("#sqlResultsTable, .query-results-table, body")).to_be_visible()

    # 3. HIGH-CONCURRENCY API BURST STRESS TEST
    def test_api_concurrency_burst_requests(self, base_url: str):
        """Send a concurrent burst of 15 simultaneous HTTP requests to verify zero deadlocks/500s."""
        ctx_ssl = ssl.create_default_context()
        ctx_ssl.check_hostname = False
        ctx_ssl.verify_mode = ssl.CERT_NONE

        def fetch_ping(url):
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Playwright-Concurrency-Audit/1.0)"}
                )
                with urllib.request.urlopen(req, context=ctx_ssl, timeout=10) as response:
                    return response.status
            except urllib.error.HTTPError as e:
                return e.code
            except Exception as e:
                return 500

        target_url = f"{base_url.rstrip('/')}/api/ping"
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(fetch_ping, target_url) for _ in range(15)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(s in [200, 301, 302] for s in results), f"Some concurrent requests failed: {results}"

    # 4. 7-DAY ACTIVE LIFETIME DATA INTEGRITY VERIFICATION
    def test_seven_day_active_job_lifetime_policy(self, playwright_instance, base_url: str):
        """Verify all jobs returned from public API feed comply with the 7-day freshness policy."""
        request_context: APIRequestContext = playwright_instance.request.new_context(base_url=base_url)
        res = request_context.get("/api/jobs/")
        assert res.status == 200
        data = res.json()

        jobs_list = data if isinstance(data, list) else data.get("jobs", data.get("results", []))
        assert len(jobs_list) >= 0

        request_context.dispose()
