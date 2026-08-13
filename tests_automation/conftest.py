import pytest
import os
from datetime import datetime
from tests_automation.utils.driver_factory import DriverFactory

@pytest.fixture(scope="function")
def driver(request):
    """
    Pytest fixture to initialize and quit Chrome WebDriver for each test.
    Automatically captures screenshot on test failure.
    """
    # Default to headless mode, or headed if pytest flag is passed
    headless = True
    driver = DriverFactory.get_driver(headless=headless)
    
    yield driver

    # Capture failure screenshot if test fails
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        screenshots_dir = os.path.join(os.path.dirname(__file__), "reports", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        filename = f"failed_{request.node.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        driver.save_screenshot(os.path.join(screenshots_dir, filename))

    driver.quit()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to attach test call outcome to request node for screenshot fixture."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
