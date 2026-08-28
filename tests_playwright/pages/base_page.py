"""
Base Page Object Model for Playwright Tests
"""

from playwright.sync_api import Page, expect

class BasePage:
    """Encapsulates common page interactions, navigations, and assertions."""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")

    def navigate(self, path: str = ""):
        """Navigates to a subpath under the base URL."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        self.page.goto(url, wait_until="domcontentloaded")

    def wait_for_network(self):
        """Waits for network to settle."""
        self.page.wait_for_load_state("networkidle")

    def bypass_entry_if_present(self):
        """Skips the entry overlay if it is showing."""
        try:
            skip_btn = self.page.locator("#entrySkipBtn, #skip-btn")
            if skip_btn.is_visible(timeout=1500):
                skip_btn.click()
                self.page.wait_for_selector("#kashiiEntry, #entry", state="hidden", timeout=3000)
        except Exception:
            pass

    def get_title(self) -> str:
        """Returns the page document title."""
        return self.page.title()

    def get_current_url(self) -> str:
        """Returns the current URL."""
        return self.page.url
