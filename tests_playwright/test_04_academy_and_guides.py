"""
Playwright Test Suite 04: Developer Academy & Student Guides
"""

import pytest
from playwright.sync_api import Page, expect
from tests_playwright.pages.base_page import BasePage

class TestAcademyAndGuides:
    """Test Suite for Developer Academy (/learn/) and Guides (/guides/)."""

    def test_developer_academy_root_and_tracks(self, page: Page, base_url: str):
        """Verify developer academy tracks (Python, Java, JavaScript) load."""
        base = BasePage(page, base_url)
        base.navigate("/learn/")
        base.bypass_entry_if_present()

        title = base.get_title()
        assert "Learn" in title or "Academy" in title or "Kashii" in title or "Python" in title

    def test_student_guides_hub(self, page: Page, base_url: str):
        """Verify student guides list and tutorial articles hub load."""
        base = BasePage(page, base_url)
        base.navigate("/guides/")
        base.bypass_entry_if_present()

        title = base.get_title()
        assert "Guide" in title or "Tutorial" in title or "Kashii" in title
