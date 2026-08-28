"""
Playwright Test Suite 02: Interactive Code Execution Debugger
"""

import pytest
from playwright.sync_api import Page, expect
from tests_playwright.pages.debugger_page import DebuggerPage

class TestDebugger:
    """Test Suite for Multi-Language Code Debugger (/debugger/)."""

    def test_debugger_interface_loads(self, page: Page, base_url: str):
        """Verify code editor workspace, language selector, and trace execution controls load."""
        debugger = DebuggerPage(page, base_url)
        debugger.open()

        # Check title and page readiness
        title = debugger.get_title()
        assert "Debugger" in title or "Debug" in title or "Kashii" in title

        # Verify Start Debugging button exists and is clickable
        expect(debugger.btn_run).to_be_visible()
        expect(debugger.lang_python_btn).to_be_visible()

    def test_python_trace_execution(self, page: Page, base_url: str):
        """Verify Python execution trace runs without unhandled errors."""
        debugger = DebuggerPage(page, base_url)
        debugger.open()

        debugger.select_language("python")
        debugger.execute_trace()

        # Output console or trace state should be present
        expect(debugger.output_console).to_be_visible()
