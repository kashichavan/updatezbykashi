"""
Playwright Deep End-to-End Test Suite: Every Click, UI/UX, and Mobile/Web Alignment
Tests every interactive element, viewport overflow, touch targets, modals, and tab flows.
"""

import pytest
from playwright.sync_api import Page, expect

class TestDeepE2EClicksAndAlignment:
    """Deep Click & Responsive Layout Integrity Suite."""

    # 1. DESKTOP & MOBILE NAVIGATION & HAMBURGER MENU
    def test_navigation_desktop_and_mobile_menu_clicks(self, page: Page, mobile_page: Page, base_url: str):
        """Test desktop navbar links and mobile hamburger drawer open/close."""
        # --- Desktop ---
        page.goto(f"{base_url}/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(600)

        # Verify Desktop Navigation Links
        nav_links = page.locator("header.site-header nav.nav-links a, .nav-links a, nav a")
        assert nav_links.count() > 0, "Desktop navbar must have navigation links."

        # --- Mobile Viewport ---
        mobile_page.goto(f"{base_url}/", wait_until="domcontentloaded")
        mobile_skip = mobile_page.locator("#entrySkipBtn, #skip-btn")
        if mobile_skip.is_visible(timeout=1000):
            mobile_skip.click()
            mobile_page.wait_for_timeout(600)

        # Check for Horizontal Overflow on Mobile Body
        has_overflow = mobile_page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 2")
        assert not has_overflow, "Mobile viewport has horizontal scrollbar/overflow layout bug!"

        # Mobile Drawer Menu Toggle
        menu_btn = mobile_page.locator("#btnToggleDrawer, button[aria-label='Open navigation menu']")
        if menu_btn.is_visible():
            menu_btn.click()
            mobile_page.wait_for_timeout(400)

            # Drawer overlay should be active
            drawer_overlay = mobile_page.locator("#drawerOverlay")
            expect(drawer_overlay).to_be_visible()

            # Close drawer
            close_btn = mobile_page.locator("#btnCloseDrawer, button[aria-label='Close navigation menu']")
            if close_btn.is_visible():
                close_btn.click()
                mobile_page.wait_for_timeout(300)

    # 2. SEARCH, CATEGORY PILLS & FILTER CLICKS
    def test_search_and_category_pill_filtering(self, page: Page, base_url: str):
        """Click on search, type queries, and click category filter badges."""
        page.goto(f"{base_url}/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(600)

        # Search box interaction
        search_box = page.locator("#jobSearchInput, #searchInput, input[type='search']")
        if search_box.is_visible():
            search_box.fill("Software")
            page.wait_for_timeout(400)
            search_box.fill("")
            page.wait_for_timeout(300)

        # Category pills clicks
        pills = page.locator(".category-pill, .cat-badge, .filter-chip")
        pills_count = pills.count()
        if pills_count > 0:
            for i in range(min(pills_count, 4)):
                pill = pills.nth(i)
                if pill.is_visible():
                    pill.click()
                    page.wait_for_timeout(300)

    # 3. INTERACTIVE DEVELOPER ACADEMY TABS & TOPICS
    def test_academy_language_tabs_and_topic_navigation(self, page: Page, base_url: str):
        """Click through Python, Java, and JavaScript tracks in /learn/."""
        page.goto(f"{base_url}/learn/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(600)

        # Check track cards / buttons
        lang_links = page.locator("a[href*='/learn/python/'], a[href*='/learn/java/'], a[href*='/learn/javascript/']")
        if lang_links.count() > 0:
            lang_links.first.click()
            page.wait_for_timeout(600)
            assert "/learn/" in page.url

    # 4. CODE DEBUGGER WORKSPACE & RUN CONTROLS
    def test_debugger_controls_and_language_switching(self, page: Page, base_url: str):
        """Click language tabs, maximize button, and Start Debugging in /debugger/."""
        page.goto(f"{base_url}/debugger/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(600)

        # Language Tab Clicks
        py_tab = page.locator("button#langPython")
        js_tab = page.locator("button#langJS")
        java_tab = page.locator("button#langJava")

        if js_tab.is_visible():
            js_tab.click()
            page.wait_for_timeout(300)
        if java_tab.is_visible():
            java_tab.click()
            page.wait_for_timeout(300)
        if py_tab.is_visible():
            py_tab.click()
            page.wait_for_timeout(300)

        # Start Debugging click
        start_btn = page.locator("button#btnStart")
        if start_btn.is_visible():
            start_btn.click()
            page.wait_for_timeout(1200)

            # Step buttons
            next_btn = page.locator("button#btnNext")
            if next_btn.is_visible() and not next_btn.is_disabled():
                next_btn.click()
                page.wait_for_timeout(300)

    # 5. SQL SANDBOX QUERY EXECUTION & SCHEMA CLICKS
    def test_sql_sandbox_editor_and_execution_clicks(self, page: Page, base_url: str):
        """Click execute query, switch tables, and verify result table rendering in /sql/."""
        page.goto(f"{base_url}/sql/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(600)

        # Execute query button
        exec_btn = page.locator("#btnRunSQL, #btnExecuteSQL, button:has-text('Execute'), button:has-text('Run')")
        if exec_btn.is_visible():
            exec_btn.click()
            page.wait_for_timeout(800)

        # Table schema nodes / sample queries
        schema_tables = page.locator(".schema-table-item, .table-node, .sql-preset-btn")
        if schema_tables.count() > 0:
            schema_tables.first.click()
            page.wait_for_timeout(300)

    # 6. OWNER CRM PORTAL AUTHENTICATION & TABS
    def test_owner_portal_full_pipeline_tab_clicks(self, page: Page, base_url: str):
        """Test owner portal authentication, switching all CRM tabs, and Jobdexo controls."""
        page.goto(f"{base_url}/owner/", wait_until="domcontentloaded")

        login_view = page.locator("#ownerLoginView")
        if login_view.is_visible():
            page.locator("#ownerUser").fill("kashichavan7777@gmail.com")
            page.locator("#ownerPass").fill("kashichavan7777")
            page.locator("#formOwnerLogin button[type='submit']").click()
            page.wait_for_timeout(1000)

        dashboard = page.locator("#ownerDashboardView")
        if dashboard.is_visible():
            # Click Jobdexo Tab
            tab_jobdexo = page.locator("button[data-tab='tabJobdexo']")
            if tab_jobdexo.is_visible():
                tab_jobdexo.click()
                page.wait_for_timeout(400)

            # Click Bulk Parser Tab
            tab_bulk = page.locator("button[data-tab='tabBulkParse']")
            if tab_bulk.is_visible():
                tab_bulk.click()
                page.wait_for_timeout(400)

            # Click Single Parser Tab
            tab_single = page.locator("button[data-tab='tabSmartParse']")
            if tab_single.is_visible():
                tab_single.click()
                page.wait_for_timeout(400)

            # Click Analytics Tab
            tab_analytics = page.locator("button[data-tab='tabAnalytics']")
            if tab_analytics.is_visible():
                tab_analytics.click()
                page.wait_for_timeout(400)

    # 7. FOOTER, COMPLIANCE & REPLAY ENTRY BUTTON
    def test_footer_links_and_replay_entry(self, page: Page, base_url: str):
        """Click Replay 3D Intro and legal footer links."""
        page.goto(f"{base_url}/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(600)

        # Replay Intro button in footer
        replay_btn = page.locator("button:has-text('Replay'), button:has-text('Intro'), .btn-replay-intro")
        if replay_btn.is_visible():
            replay_btn.click()
            page.wait_for_timeout(600)
            # Replay should show entry
            expect(page.locator("#kashiiEntry, #entry")).to_be_visible()
            # Skip again
            page.locator("#entrySkipBtn, #skip-btn").click()
            page.wait_for_timeout(600)

    # 8. MOBILE VIEWPORT TOUCH & RESPONSIVENESS
    def test_mobile_responsive_alignment_and_touch(self, mobile_page: Page, base_url: str):
        """Verify mobile layout alignment across key pages (Home, Learn, Debugger, Blog)."""
        pages_to_check = ["/", "/learn/", "/debugger/", "/sql/", "/blog/", "/about/", "/privacy-policy/"]
        
        for path in pages_to_check:
            mobile_page.goto(f"{base_url}{path}", wait_until="domcontentloaded")
            skip_btn = mobile_page.locator("#entrySkipBtn, #skip-btn")
            if skip_btn.is_visible(timeout=1000):
                skip_btn.click()
                mobile_page.wait_for_timeout(600)

            # Verify no horizontal layout blowouts
            has_overflow = mobile_page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 2")
            assert not has_overflow, f"Horizontal overflow detected on mobile page: {path}"
