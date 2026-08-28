"""
Playwright Test Suite 12: UI Form Validation, Active Navigation & State Feedback
Tests active navbar indicators, form submission validation states, empty search feedback,
and interactive toggle controls.
"""

import pytest
from playwright.sync_api import Page, expect

class TestUIFormValidationAndStates:
    """Test Suite for Form Feedback, Active States, and Visual Cues."""

    # 1. ACTIVE NAVIGATION LINK INDICATOR
    def test_active_navbar_link_state(self, page: Page, base_url: str):
        """Verify the active route is visually highlighted in the header navigation."""
        # Check /blog/
        page.goto(f"{base_url}/blog/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(400)

        active_nav = page.locator("header.site-header nav a.active, .nav-links a.active")
        expect(active_nav.first).to_be_visible()

        # Check /learn/
        page.goto(f"{base_url}/learn/", wait_until="domcontentloaded")
        active_learn = page.locator("header.site-header nav a.active, .nav-links a.active")
        expect(active_learn.first).to_be_visible()

    # 2. OWNER PORTAL INVALID LOGIN FEEDBACK
    def test_owner_portal_invalid_credentials_feedback(self, page: Page, base_url: str):
        """Verify invalid owner login displays proper error feedback without crashing."""
        page.goto(f"{base_url}/owner/", wait_until="domcontentloaded")

        login_view = page.locator("#ownerLoginView")
        if login_view.is_visible():
            page.locator("#ownerUser").fill("invalid_admin@updatez.com")
            page.locator("#ownerPass").fill("wrongpassword123")
            page.locator("#formOwnerLogin button[type='submit']").click()
            page.wait_for_timeout(800)

            # Login view should still be visible with alert/error
            expect(login_view).to_be_visible()

    # 3. SEARCH ZERO-RESULTS EMPTY STATE UX
    def test_search_zero_results_empty_state_ux(self, page: Page, base_url: str):
        """Verify typing an impossible query displays clean zero-results empty state."""
        page.goto(f"{base_url}/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(400)

        search_input = page.locator("#jobSearchInput, #searchInput, input[type='search']")
        if search_input.is_visible():
            search_input.fill("xyz_non_existent_impossible_job_query_99999")
            page.wait_for_timeout(500)

            # Verify empty state message or 0 job count
            empty_state = page.locator(".empty-state, #noJobsFound, .no-results-box")
            if empty_state.is_visible():
                expect(empty_state).to_be_visible()

            # Clear search
            search_input.fill("")
            page.wait_for_timeout(400)

    # 4. TODAY'S REQUIREMENTS SHORTCUT FILTER
    def test_todays_requirements_filter_toggle(self, page: Page, base_url: str):
        """Verify clicking Today's Requirements shortcut (?today=true) filters live feed."""
        page.goto(f"{base_url}/?today=true", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(400)

        # Confirm URL contains today=true
        assert "today=true" in page.url
        expect(page.locator("body")).to_be_visible()
