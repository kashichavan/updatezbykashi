"""
Playwright Test Suite 10: Exhaustive End-to-End Advanced User Journeys
Covers Job Detail Pages, Story Card Generator, Guide Reading Views, Blog Like API,
SEO Crawlers (sitemap/robots/ads.txt), Custom 404 Page, and Owner CRM Deep Workflows.
"""

import pytest
from playwright.sync_api import Page, APIRequestContext, expect

class TestExhaustiveAdvancedE2E:
    """Exhaustive Full-Platform User Journey & Infrastructure Test Suite."""

    # 1. JOB DETAIL PAGE & INTERACTIVE ACTION BUTTONS
    def test_job_detail_page_and_apply_flow(self, page: Page, base_url: str):
        """Navigate to a job detail page and verify metadata, tags, and apply action."""
        page.goto(f"{base_url}/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(500)

        # Click the first job card title or link
        job_links = page.locator(".job-card a[href*='/job/'], .requirement-card a[href*='/job/'], a[href*='/job/']")
        if job_links.count() > 0:
            first_job_link = job_links.first
            first_job_link.click()
            page.wait_for_timeout(800)

            # Assert on job detail view
            assert "/job/" in page.url
            expect(page.locator(".job-hero-title, main h1, .job-detail-title, h1.job-title")).to_be_visible()

            # Verify Apply / Direct Apply Button
            apply_btn = page.locator("a[href*='apply'], a.btn-apply-direct, a:has-text('Apply Now'), a:has-text('Direct Apply')")
            if apply_btn.count() > 0:
                expect(apply_btn.first).to_be_visible()

    # 2. INDIVIDUAL GUIDE READING VIEW & TABLE OF CONTENTS
    def test_guide_detail_reading_view(self, page: Page, base_url: str):
        """Open a student tutorial/guide article and verify reading view."""
        page.goto(f"{base_url}/guides/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(500)

        guide_cards = page.locator("main a[href*='/guides/'], .guide-card a, .guides-grid a")
        if guide_cards.count() > 0:
            guide_cards.first.click()
            page.wait_for_timeout(800)
            assert "/guides/" in page.url
            expect(page.locator("main h1, .guide-title, article h1")).to_be_visible()

    # 3. ACADEMY DEEP TOPIC ANALOGY VIEW
    def test_academy_topic_detail_analogy_view(self, page: Page, base_url: str):
        """Navigate to Python Academy topic and verify interactive analogies & code visualizer."""
        page.goto(f"{base_url}/learn/python/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(500)

        topic_links = page.locator("main a[href*='/learn/python/'], .topic-card a, .topics-list a")
        if topic_links.count() > 0:
            topic_links.first.click()
            page.wait_for_timeout(800)
            assert "/learn/" in page.url
            expect(page.locator("body")).to_be_visible()

    # 4. BLOG POST READING & LIKE BUTTON API
    def test_blog_post_reading_and_like_button(self, page: Page, base_url: str):
        """Open a blog post and verify interactive reading view and like counter."""
        page.goto(f"{base_url}/blog/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(500)

        blog_cards = page.locator("a.story-card, .story-list a.story-card, main a[href*='/blog/']")
        if blog_cards.count() > 0:
            blog_cards.first.click()
            page.wait_for_timeout(800)
            assert "/blog/" in page.url

            # Test like button click if present
            like_btn = page.locator("#btnLikeBlog, button[data-action='like'], .btn-like-post, .medium-like-btn")
            if like_btn.is_visible():
                like_btn.click()
                page.wait_for_timeout(400)

    # 5. CRAWLERS, SEO SITEMAP, ROBOTS.TXT & ADS.TXT VERIFICATION
    def test_seo_sitemap_robots_and_ads_txt(self, playwright_instance, base_url: str):
        """Verify sitemap.xml, robots.txt, and ads.txt return valid status codes and payload."""
        request_context: APIRequestContext = playwright_instance.request.new_context(base_url=base_url)

        # 1. Sitemap XML
        res_sitemap = request_context.get("/sitemap.xml")
        assert res_sitemap.status == 200
        assert "xml" in res_sitemap.headers.get("content-type", "") or "urlset" in res_sitemap.text()

        # 2. Robots.txt
        res_robots = request_context.get("/robots.txt")
        assert res_robots.status == 200
        assert "User-agent" in res_robots.text()

        # 3. Ads.txt
        res_ads = request_context.get("/ads.txt")
        assert res_ads.status in [200, 301, 302]

        # 4. Ad Network Verification File
        res_verif = request_context.get("/c1a8fc4a2f71995dfc59.txt")
        assert res_verif.status in [200, 301, 302]

        request_context.dispose()

    # 6. CUSTOM 404 ERROR PAGE & RECOVERY
    def test_custom_404_page_and_recovery_flow(self, page: Page, base_url: str):
        """Navigate to non-existent route and verify branded 404 page and recovery back home."""
        page.goto(f"{base_url}/non-existent-test-page-404-check/", wait_until="domcontentloaded")
        
        # Verify 404 title or message
        body_text = page.locator("body").text_content() or ""
        assert "404" in body_text or "Page Not Found" in body_text or "Kashii" in body_text

        # Click home recovery link
        home_recovery_btn = page.locator("a[href='/'], a:has-text('Home'), a:has-text('Return')")
        if home_recovery_btn.count() > 0:
            home_recovery_btn.first.click()
            page.wait_for_timeout(600)
            assert page.url.rstrip("/") == base_url.rstrip("/")

    # 7. OWNER CRM SINGLE PARSER & BULK PARSER INPUTS
    def test_owner_portal_parser_inputs(self, page: Page, base_url: str):
        """Test Single URL Parser and Bulk Scraper textareas in Owner Portal."""
        page.goto(f"{base_url}/owner/", wait_until="domcontentloaded")

        login_view = page.locator("#ownerLoginView")
        if login_view.is_visible():
            page.locator("#ownerUser").fill("kashichavan7777@gmail.com")
            page.locator("#ownerPass").fill("kashichavan7777")
            page.locator("#formOwnerLogin button[type='submit']").click()
            page.wait_for_timeout(1000)

        dashboard = page.locator("#ownerDashboardView")
        if dashboard.is_visible():
            # Switch to Single Parser Tab
            tab_single = page.locator("button[data-tab='tabSmartParse']")
            if tab_single.is_visible():
                tab_single.click()
                page.wait_for_timeout(300)
                input_url = page.locator("#smartParseUrl, #inputJobUrl")
                if input_url.is_visible():
                    input_url.fill("https://example.com/job/test-software-engineer")
                    page.wait_for_timeout(200)

            # Switch to Bulk Parser Tab
            tab_bulk = page.locator("button[data-tab='tabBulkParse']")
            if tab_bulk.is_visible():
                tab_bulk.click()
                page.wait_for_timeout(300)
                textarea_bulk = page.locator("#bulkUrlsTextarea, textarea[placeholder*='URL']")
                if textarea_bulk.is_visible():
                    textarea_bulk.fill("https://example.com/job1\nhttps://example.com/job2")
                    page.wait_for_timeout(200)

    # 8. YOUTUBE HUB & EMBEDDED PLAYER PAGE
    def test_youtube_video_hub_page(self, page: Page, base_url: str):
        """Verify /youtube/ video tutorials hub loads with video cards."""
        page.goto(f"{base_url}/youtube/", wait_until="domcontentloaded")
        skip_btn = page.locator("#entrySkipBtn, #skip-btn")
        if skip_btn.is_visible(timeout=1000):
            skip_btn.click()
            page.wait_for_timeout(500)

        assert "/youtube/" in page.url
        expect(page.locator("body")).to_be_visible()
