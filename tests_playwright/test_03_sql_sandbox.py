"""
Playwright Test Suite 03: Interactive SQL Sandbox Playground
"""

import pytest
from playwright.sync_api import Page, expect
from tests_playwright.pages.sql_page import SQLSandboxPage

class TestSQLSandbox:
    """Test Suite for SQL Sandbox Playground (/sql/)."""

    def test_sql_sandbox_loads_and_executes_query(self, page: Page, base_url: str):
        """Verify schema preview and executing a SELECT SQL query."""
        sql_page = SQLSandboxPage(page, base_url)
        sql_page.open()

        # Check title
        title = sql_page.get_title()
        assert "SQL" in title or "Sandbox" in title or "Kashii" in title

        # Verify execute button is visible
        expect(sql_page.btn_execute).to_be_visible()

        # Run query
        sql_page.run_query("SELECT 1 AS test_col;")
