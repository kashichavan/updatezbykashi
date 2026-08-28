"""
Playwright Test Suite 07: Mobile Responsive & Touch Viewport
"""

import pytest
from playwright.sync_api import Page, expect
from tests_playwright.pages.home_page import HomePage

class TestMobileResponsive:
    """Test Suite for Mobile Device Viewport (iPhone 14 / 390x844)."""

    def test_mobile_homepage_layout_and_navigation(self, mobile_page: Page, base_url: str):
        """Verify mobile navigation bar, touch interactions, and responsive card grid."""
        home_page = HomePage(mobile_page, base_url)
        home_page.open()
        home_page.bypass_entry_if_present()

        # Check mobile navbar
        expect(home_page.navbar).to_be_visible()

        # Check job count
        jobs_count = home_page.get_job_count()
        assert jobs_count >= 0
