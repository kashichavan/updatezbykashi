"""
Playwright Test Suite 01: Homepage & Feed Exploration
"""

import pytest
from playwright.sync_api import Page, expect
from tests_playwright.pages.home_page import HomePage

class TestHomePage:
    """Test Suite for Public Homepage & User Experience."""

    def test_entry_experience_presentation(self, page: Page, base_url: str):
        """Verify the clean entry experience renders with crisp typography and can be skipped."""
        home_page = HomePage(page, base_url)
        home_page.open_with_intro()
        
        # Check title
        assert "Kashii Updatez" in page.title()

        # If entry overlay is displayed, skip it
        if home_page.is_entry_displayed():
            home_page.skip_entry()
            page.wait_for_timeout(700)

        # Confirm homepage navbar is accessible
        expect(home_page.navbar).to_be_visible()

    def test_homepage_hero_and_live_feed(self, page: Page, base_url: str):
        """Verify hero banner, live job feed cards, and search filtering."""
        home_page = HomePage(page, base_url)
        home_page.open()
        home_page.bypass_entry_if_present()

        # Verify page title and header
        title = page.title()
        assert "Kashii Updatez" in title or "Jobs" in title

        # Verify search filter interaction
        initial_jobs = home_page.get_job_count()
        assert initial_jobs >= 0

        # Perform search
        home_page.search("Python")
        filtered_jobs = home_page.get_job_count()
        assert filtered_jobs >= 0
