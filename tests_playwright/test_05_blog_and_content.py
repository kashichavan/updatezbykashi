"""
Playwright Test Suite 05: Blog, YouTube Hub & Compliance Pages
"""

import pytest
from playwright.sync_api import Page, expect
from tests_playwright.pages.base_page import BasePage

class TestBlogAndCompliance:
    """Test Suite for Blog Engine and Compliance Pages."""

    def test_blog_list_page(self, page: Page, base_url: str):
        """Verify blog engineering articles hub loads."""
        base = BasePage(page, base_url)
        base.navigate("/blog/")
        base.bypass_entry_if_present()

        title = base.get_title()
        assert "Blog" in title or "Kashii" in title or "Articles" in title

    def test_legal_and_compliance_pages(self, page: Page, base_url: str):
        """Verify AdSense policy mandatory compliance pages (Privacy Policy, Terms, Disclaimer, Contact)."""
        base = BasePage(page, base_url)

        for path in ["/privacy-policy/", "/terms/", "/disclaimer/", "/contact/", "/about/"]:
            base.navigate(path)
            base.bypass_entry_if_present()
            assert page.url.rstrip("/").endswith(path.rstrip("/"))
            expect(page.locator("body")).to_be_visible()
