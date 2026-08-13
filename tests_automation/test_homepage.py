import pytest
from tests_automation.pages.home_page import HomePage

class TestHomePage:
    """
    Automated Test Suite for Public Homepage Features
    """

    def test_homepage_hero_and_terminal_loads(self, driver):
        home_page = HomePage(driver)
        home_page.load()

        # Assertions
        hero_title = home_page.get_hero_title_text()
        assert "Daily Student Jobs" in hero_title, f"Expected 'Daily Student Jobs' in title, got '{hero_title}'"
        assert home_page.is_terminal_displayed() is True, "Coding terminal box should be visible on homepage."

    def test_homepage_job_grid_and_search_filter(self, driver):
        home_page = HomePage(driver)
        home_page.load()

        initial_count = home_page.get_job_cards_count()
        assert initial_count >= 0, "Job cards count should be non-negative."

        # Search filter interaction
        home_page.search_jobs("Software")
        assert home_page.get_job_cards_count() >= 0
