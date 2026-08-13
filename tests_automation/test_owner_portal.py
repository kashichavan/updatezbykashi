import pytest
from tests_automation.pages.owner_page import OwnerPage

class TestOwnerPortal:
    """
    Automated Test Suite for Executive Owner CRM Portal Authentication & Dashboard
    """

    def test_owner_login_screen_loads(self, driver):
        owner_page = OwnerPage(driver)
        owner_page.load()
        assert owner_page.is_login_screen_displayed() or owner_page.is_dashboard_displayed()

    def test_owner_successful_login(self, driver):
        owner_page = OwnerPage(driver)
        owner_page.load()

        if owner_page.is_login_screen_displayed():
            owner_page.login("kashichavan7777@gmail.com", "kashichavan7777")
        
        assert owner_page.is_dashboard_displayed() is True, "Owner dashboard should be visible after valid login."
        workspace_title = owner_page.get_workspace_title()
        assert "Opportunity Pipeline CRM" in workspace_title
