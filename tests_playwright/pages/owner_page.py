"""
Executive Owner Portal Page Object Model
"""

from playwright.sync_api import Page, expect
from .base_page import BasePage

class OwnerPage(BasePage):
    """Page Object for Kashii Updatez Executive Owner CRM Portal (/owner/)."""

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)

        # Login Screen Locators
        self.login_view = page.locator("#ownerLoginView")
        self.input_username = page.locator("#ownerUser")
        self.input_password = page.locator("#ownerPass")
        self.btn_submit_login = page.locator("#formOwnerLogin button[type='submit'], button#btnLoginSubmit")

        # Dashboard View Locators
        self.dashboard_view = page.locator("#ownerDashboardView")
        self.workspace_heading = page.locator("#crmWorkspaceHeading, .crm-header-title")
        self.kpi_active_jobs = page.locator("#kpiActiveJobs, .kpi-counter")
        self.btn_logout = page.locator("#btnLogoutOwner")

        # Sidebar Tabs
        self.tab_jobdexo = page.locator("button[data-tab='tabJobdexo'], #navTabJobdexo")
        self.tab_single_parser = page.locator("button[data-tab='tabSmartParse']")
        self.tab_bulk_parser = page.locator("button[data-tab='tabBulkParse']")
        self.tab_categories = page.locator("button[data-tab='tabCategory']")
        self.tab_analytics = page.locator("button[data-tab='tabAnalytics']")

    def open(self):
        """Opens owner portal."""
        self.navigate("/owner/")

    def is_login_screen_visible(self) -> bool:
        """Checks if login screen is displayed."""
        return self.login_view.is_visible()

    def is_dashboard_visible(self) -> bool:
        """Checks if owner dashboard is displayed."""
        return self.dashboard_view.is_visible()

    def login(self, username: str = "kashichavan7777@gmail.com", password: str = "kashichavan7777"):
        """Performs owner authentication."""
        if self.is_login_screen_visible():
            self.input_username.fill(username)
            self.input_password.fill(password)
            self.btn_submit_login.click()
            self.page.wait_for_timeout(1000)

    def switch_tab(self, tab_locator):
        """Switches between CRM workspace tabs."""
        if tab_locator.is_visible():
            tab_locator.click()
            self.page.wait_for_timeout(300)
