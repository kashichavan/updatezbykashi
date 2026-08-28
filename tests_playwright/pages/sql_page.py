"""
SQL Sandbox Playground Page Object Model
"""

from playwright.sync_api import Page, expect
from .base_page import BasePage

class SQLSandboxPage(BasePage):
    """Page Object for Interactive SQL Execution Sandbox (/sql/)."""

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)

        # Locators
        self.sql_editor = page.locator("#sqlEditor, textarea#sqlQuery, .sql-editor-container")
        self.btn_execute = page.locator("#btnRunSQL, #btnExecuteSQL, button:has-text('Execute'), button:has-text('Run')")
        self.btn_reset_db = page.locator("#btnResetDB, button:has-text('Reset')")
        
        self.schema_panel = page.locator("#schemaTree, .schema-panel, #tablesList")
        self.result_table = page.locator("#sqlResultsTable, .query-results-table, table.sql-table")
        self.execution_status = page.locator("#executionStatus, .sql-status-badge, #statusMessage")

    def open(self):
        """Opens SQL sandbox page."""
        self.navigate("/sql/")
        self.bypass_entry_if_present()

    def run_query(self, query: str = ""):
        """Executes a SQL query."""
        if query and self.sql_editor.is_visible():
            self.sql_editor.fill(query)
        if self.btn_execute.is_visible():
            self.btn_execute.click()
            self.page.wait_for_timeout(800)

    def is_schema_displayed(self) -> bool:
        """Checks if database schema table tree is visible."""
        return self.schema_panel.is_visible()
