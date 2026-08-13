from selenium.webdriver.common.by import By
from .base_page import BasePage

class OwnerPage(BasePage):
    """
    Page Object for Kashii Updatez Executive Owner Portal (/owner/)
    Encapsulates Login Form, Pipeline Tabs, Single Parser, and Job Posting Forms.
    """
    # Login View Locators
    LOGIN_VIEW = (By.ID, "ownerLoginView")
    INPUT_USERNAME = (By.ID, "ownerUser")
    INPUT_PASSWORD = (By.ID, "ownerPass")
    BTN_SUBMIT_LOGIN = (By.CSS_SELECTOR, "#formOwnerLogin button[type='submit']")

    # Dashboard View Locators
    DASHBOARD_VIEW = (By.ID, "ownerDashboardView")
    WORKSPACE_HEADING = (By.ID, "crmWorkspaceHeading")
    KPI_ACTIVE_JOBS = (By.ID, "kpiActiveJobs")
    BTN_LOGOUT = (By.ID, "btnLogoutOwner")

    # Sidebar Tabs
    TAB_SINGLE_PARSER = (By.CSS_SELECTOR, "button[data-tab='tabSmartParse']")
    TAB_POST_JOB = (By.CSS_SELECTOR, "button[data-tab='tabPost']")
    TAB_CATEGORIES = (By.CSS_SELECTOR, "button[data-tab='tabCategory']")

    def __init__(self, driver, base_url="https://kashiiupdatez.online/owner/"):
        super().__init__(driver)
        self.base_url = base_url

    def load(self):
        self.open_url(self.base_url)

    def is_login_screen_displayed(self):
        return self.is_displayed(self.LOGIN_VIEW)

    def login(self, username, password):
        self.type_text(self.INPUT_USERNAME, username)
        self.type_text(self.INPUT_PASSWORD, password)
        self.click(self.BTN_SUBMIT_LOGIN)

    def is_dashboard_displayed(self):
        return self.is_displayed(self.DASHBOARD_VIEW)

    def get_workspace_title(self):
        return self.get_text(self.WORKSPACE_HEADING)

    def switch_to_tab(self, tab_locator):
        self.click(tab_locator)
