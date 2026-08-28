"""
Playwright Automation Test Fixtures & Configuration
Configured for Kashii Updatez End-to-End Test Suite.
"""

import os
import pytest
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE_URL_DEFAULT = os.environ.get("BASE_URL", "https://kashiiupdatez.online")

@pytest.fixture(scope="session")
def base_url():
    """Returns the target base URL from environment or default production URL."""
    return os.environ.get("BASE_URL", BASE_URL_DEFAULT).rstrip("/")

@pytest.fixture(scope="session")
def playwright_instance():
    """Session-scoped Playwright instance."""
    with sync_playwright() as playwright:
        yield playwright

@pytest.fixture(scope="session")
def browser(playwright_instance):
    """Session-scoped Chromium browser instance."""
    headless = os.environ.get("HEADED", "0") != "1"
    slow_mo = int(os.environ.get("SLOWMO", "0"))
    browser = playwright_instance.chromium.launch(
        headless=headless,
        slow_mo=slow_mo,
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )
    yield browser
    browser.close()

@pytest.fixture(scope="function")
def context(browser):
    """Function-scoped browser context with 1920x1080 desktop viewport."""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ignore_https_errors=True
    )
    yield context
    context.close()

@pytest.fixture(scope="function")
def page(context, request):
    """Function-scoped Playwright Page fixture with automatic failure screenshot capture."""
    page = context.new_page()
    page.set_default_timeout(15000)

    yield page

    # Failure screenshot capture
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        screenshots_dir = os.path.join(os.path.dirname(__file__), "reports", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"failed_{request.node.name}_{timestamp}.png"
        filepath = os.path.join(screenshots_dir, filename)
        try:
            page.screenshot(path=filepath, full_page=True)
            print(f"\n[Screenshot Saved]: {filepath}")
        except Exception as e:
            print(f"\n[Screenshot Failed]: {e}")

    page.close()

@pytest.fixture(scope="function")
def mobile_page(browser, request):
    """Mobile viewport (iPhone 14 / 390x844) fixture."""
    context = browser.new_context(
        viewport={"width": 390, "height": 844},
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
        is_mobile=True,
        has_touch=True,
        ignore_https_errors=True
    )
    page = context.new_page()
    page.set_default_timeout(15000)

    yield page

    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        screenshots_dir = os.path.join(os.path.dirname(__file__), "reports", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"failed_mobile_{request.node.name}_{timestamp}.png"
        filepath = os.path.join(screenshots_dir, filename)
        try:
            page.screenshot(path=filepath, full_page=True)
        except Exception:
            pass

    page.close()
    context.close()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to attach test outcome for screenshot fixture."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
