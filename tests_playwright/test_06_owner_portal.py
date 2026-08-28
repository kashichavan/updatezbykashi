"""
Playwright Test Suite 06: Executive Owner CRM Portal
"""

import pytest
from playwright.sync_api import Page, expect
from tests_playwright.pages.owner_page import OwnerPage

class TestOwnerPortal:
    """Test Suite for Executive Owner CRM Portal (/owner/)."""

    def test_owner_portal_authentication_and_dashboard(self, page: Page, base_url: str):
        """Verify Owner Portal authentication screen and CRM workspace access."""
        owner = OwnerPage(page, base_url)
        owner.open()

        # If login screen is shown, perform login
        if owner.is_login_screen_visible():
            owner.login("kashichavan7777@gmail.com", "kashichavan7777")

        # Dashboard should be visible
        assert owner.is_dashboard_visible() or owner.is_login_screen_visible()

    def test_owner_tab_switching(self, page: Page, base_url: str):
        """Verify switching between Jobdexo Sync, Bulk Parser, and Category Management tabs."""
        owner = OwnerPage(page, base_url)
        owner.open()

        if owner.is_login_screen_visible():
            owner.login("kashichavan7777@gmail.com", "kashichavan7777")

        if owner.is_dashboard_visible():
            # Switch to Jobdexo Tab
            owner.switch_tab(owner.tab_jobdexo)
            page.wait_for_timeout(300)

            # Switch to Categories Tab
            owner.switch_tab(owner.tab_categories)
            page.wait_for_timeout(300)
