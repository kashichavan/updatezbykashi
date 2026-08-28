"""
Home Page Object Model for Playwright Tests
"""

from playwright.sync_api import Page, expect
from .base_page import BasePage

class HomePage(BasePage):
    """Page Object for Kashii Updatez Homepage."""

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)

        # Locators
        self.entry_overlay = page.locator("#kashiiEntry, #entry")
        self.entry_skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        self.entry_wordmark = page.locator("#entryWordmark, .entry-brand-typography")
        
        self.navbar = page.locator("nav.site-navbar, header.site-header, .navbar")
        self.navbar_brand = page.locator(".nav-brand, a.brand-logo, .brand-title")
        self.hero_title = page.locator("h1.hero-title, .hero-heading, #heroHeading")
        
        self.search_input = page.locator("#jobSearchInput, #searchInput, input[type='search'], input[placeholder*='Search']")
        self.job_cards = page.locator(".job-card, .requirement-card, article.job-item")
        self.category_pills = page.locator(".category-pill, .filter-chip, .cat-badge")
        self.stat_badges = page.locator(".stat-badge, .metric-counter, .stats-strip")
        self.chat_widget = page.locator("#floatingChatWidget, a[title*='Chat directly']")

    def open(self):
        """Opens homepage."""
        self.navigate("/")

    def open_with_intro(self):
        """Opens dedicated intro or forces intro sequence."""
        self.navigate("/intro/")

    def is_entry_displayed(self) -> bool:
        """Checks if entry experience overlay is visible."""
        return self.entry_overlay.is_visible()

    def skip_entry(self):
        """Clicks skip button on entry overlay."""
        if self.entry_skip_btn.is_visible():
            self.entry_skip_btn.click()

    def get_hero_text(self) -> str:
        """Returns hero banner title text."""
        return self.hero_title.text_content() or ""

    def search(self, query: str):
        """Enters search term into the jobs search box."""
        if self.search_input.is_visible():
            self.search_input.fill(query)
            self.page.wait_for_timeout(400)

    def get_job_count(self) -> int:
        """Returns the number of visible job cards."""
        return self.job_cards.count()

    def click_first_job(self):
        """Clicks on the first available job posting card."""
        if self.job_cards.count() > 0:
            self.job_cards.first.click()
