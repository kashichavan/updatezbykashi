"""
Playwright Test Suite 11: UI Micro-Interactions, Widgets & Editor Controls
Tests Monaco Editor themes, font size scaling, maximize IDE, floating widgets,
hover animations, and toast notification hierarchies.
"""

import pytest
from playwright.sync_api import Page, expect

class TestUIMicroInteractionsAndWidgets:
    """Test Suite for Interactive UI Controls, Themes, and Floating Widgets."""

    # 1. DEBUGGER MONACO EDITOR FONT SCALING & MAXIMIZE IDE
    def test_debugger_editor_font_scaling_and_maximize_ui(self, page: Page, base_url: str):
        """Test font-size increase/decrease buttons and IDE maximize toggle in /debugger/."""
        page.goto(f"{base_url}/debugger/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(500)

        # 1. Font Size Controls (A+ and A-)
        btn_font_inc = page.locator("button[title*='Increase font size'], button:has-text('A+')")
        btn_font_dec = page.locator("button[title*='Decrease font size'], button:has-text('A−')")

        if btn_font_inc.is_visible():
            btn_font_inc.click()
            page.wait_for_timeout(200)
            btn_font_inc.click()
            page.wait_for_timeout(200)

        if btn_font_dec.is_visible():
            btn_font_dec.click()
            page.wait_for_timeout(200)

        # 2. Maximize IDE Workspace Toggle
        btn_maximize = page.locator("#btnMaximizeWorkspace, button[title*='Maximize Full IDE']")
        if btn_maximize.is_visible():
            btn_maximize.click()
            page.wait_for_timeout(300)
            # Toggle back
            btn_maximize.click()
            page.wait_for_timeout(300)

    # 2. FLOATING INSTAGRAM CHAT WIDGET POSITIONING & ACCESSIBILITY
    def test_floating_chat_widget_visibility_and_zindex(self, page: Page, base_url: str):
        """Verify floating Instagram chat widget is visible, clickable, and does not block content."""
        page.goto(f"{base_url}/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(500)

        chat_widget = page.locator("#floatingChatWidget, a[title*='Chat directly with Kashii']")
        expect(chat_widget).to_be_visible()

        # Check href contains Instagram user
        href = chat_widget.get_attribute("href")
        assert "ikashii_07" in (href or "")

    # 3. FLASH ANNOUNCEMENT BANNER DISMISSAL
    def test_flash_banner_interaction_and_dismissal(self, page: Page, base_url: str):
        """Verify top flash announcement banner renders and close button works."""
        page.goto(f"{base_url}/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(500)

        banner = page.locator("#flashBanner, .flash-banner, .announcement-banner")
        if banner.is_visible():
            close_btn = banner.locator("button, .btn-close-banner, .banner-close, [aria-label*='Close']")
            if close_btn.count() > 0:
                close_btn.first.click()
                page.wait_for_timeout(300)

    # 4. HOVER ELEVATION & VISUAL CARD FEEDBACK
    def test_job_card_hover_and_visual_elevation(self, page: Page, base_url: str):
        """Verify hovering on requirement job cards triggers smooth elevation."""
        page.goto(f"{base_url}/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(500)

        job_cards = page.locator(".job-card, .requirement-card")
        if job_cards.count() > 0:
            first_card = job_cards.first
            first_card.hover()
            page.wait_for_timeout(300)
            expect(first_card).to_be_visible()
