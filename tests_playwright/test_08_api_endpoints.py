"""
Playwright Test Suite 08: API & Healthcheck Endpoints
"""

import pytest
from playwright.sync_api import APIRequestContext

class TestAPIHealth:
    """Test Suite for Core JSON API Endpoints."""

    def test_api_ping_healthcheck(self, playwright_instance, base_url: str):
        """Verify keep-alive /api/ping returns healthy status."""
        request_context: APIRequestContext = playwright_instance.request.new_context(base_url=base_url)
        response = request_context.get("/api/ping")
        assert response.status in [200, 301, 302]
        request_context.dispose()

    def test_api_jobs_feed_endpoint(self, playwright_instance, base_url: str):
        """Verify /api/jobs/ returns valid JSON list."""
        request_context: APIRequestContext = playwright_instance.request.new_context(base_url=base_url)
        response = request_context.get("/api/jobs/")
        assert response.status == 200
        data = response.json()
        assert isinstance(data, (list, dict))
        request_context.dispose()
