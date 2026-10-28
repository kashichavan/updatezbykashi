"""
Tests for the source-linked recruiter discovery engine.

The single most important guarantee: the engine must never invent an email
address. Every assertion here exists to keep that promise enforceable.
"""

from __future__ import annotations

import base64
import urllib.parse
from unittest.mock import patch

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from requirements.models import Category, JobPosting
from requirements.services import recruiter_finder as rf


class RecruiterFinderCoreTests(TestCase):
    def setUp(self):
        cache.clear()

    # ------------------------------------------------------------------
    # No fabrication
    # ------------------------------------------------------------------

    def test_unknown_person_returns_not_found_without_guessing(self):
        with patch.object(rf, "search_web", return_value={"provider": "", "results": [], "errors": []}), \
             patch.object(rf, "_github_commit_lookup", return_value=([], [])), \
             patch.object(rf, "_github_profile_lookup", return_value=([], [])), \
             patch.object(rf, "_company_site_lookup", return_value=([], [])):
            result = rf.discover_recruiter_contact(
                name="Qwerv Zzzyx",
                company="Nonexistent Widgets Private Limited",
                deep_search=True,
                force_refresh=True,
            )

        self.assertEqual(result["status"], "not_found")
        self.assertEqual(result["emails"], [])
        self.assertIsNone(result["best_email"])
        self.assertFalse(result["has_personal_email"])
        self.assertIn("will not invent", result["message"])
        # The classic fake pattern must never appear anywhere in the payload.
        blob = str(result).lower()
        self.assertNotIn("qwerv.zzzyx@", blob)
        self.assertNotIn("recruiter@", blob)

    def test_invalid_input_is_reported_without_network_calls(self):
        result = rf.discover_recruiter_contact(name="", company="", deep_search=True)
        self.assertEqual(result["status"], "invalid_input")
        self.assertEqual(result["emails"], [])

    def test_compat_wrapper_never_returns_a_pattern_guess(self):
        with patch.object(rf, "discover_recruiter_contact", return_value={
            "best_email": None,
            "emails": [],
            "recruiter": {"name": "Test Person", "title": "Recruiter"},
            "company": {"clean_name": "Acme", "domain": "acme.com"},
            "message": "No public email.",
            "searched_at": "2026-01-01T00:00:00Z",
        }):
            wrapped = rf.scrape_original_recruiter_email_from_linkedin(
                "https://www.linkedin.com/in/test-person/", "Acme"
            )
        self.assertEqual(wrapped["email"], "")
        self.assertFalse(wrapped["verified"])
        self.assertEqual(wrapped["status"], "No public email found")

    # ------------------------------------------------------------------
    # Job post extraction
    # ------------------------------------------------------------------

    def test_email_published_in_job_post_is_extracted(self):
        job = JobPosting(
            title="Backend Intern",
            company_name="Acme Corp",
            description="Send your resume to careers@acmecorp.com with the job ID.",
            apply_url="https://acmecorp.com/careers/backend-intern",
            referral_instructions="Questions? hiring@acmecorp.com",
        )
        candidates = rf.extract_job_contact_emails(job)
        emails = {c.email for c in candidates}
        self.assertIn("careers@acmecorp.com", emails)
        self.assertIn("hiring@acmecorp.com", emails)
        for candidate in candidates:
            self.assertEqual(candidate.source, "job_post")
            self.assertTrue(candidate.source_url)
            self.assertFalse(candidate.is_personal)
        self.assertTrue(all(rf.is_role_inbox(c.email) for c in candidates))

    def test_recruiter_intelligence_is_network_free(self):
        job = JobPosting(
            title="Frontend Intern",
            company_name="Acme Corp",
            description="Apply through the portal.",
            apply_url="https://acmecorp.com/careers",
        )
        with patch.object(rf, "search_web", side_effect=AssertionError("network call")), \
             patch.object(rf, "_github_get", side_effect=AssertionError("network call")), \
             patch.object(rf, "_fetch_page_text", side_effect=AssertionError("network call")):
            intel = rf.get_recruiter_intelligence_for_job(job)

        self.assertEqual(intel["active_recruiter"]["email"], "")
        self.assertFalse(intel["has_public_email"])
        self.assertTrue(intel["sourcing_links"]["google_xray_url"])

    # ------------------------------------------------------------------
    # Email classification helpers
    # ------------------------------------------------------------------

    def test_role_inbox_classification(self):
        self.assertTrue(rf.is_role_inbox("careers@acmecorp.com"))
        self.assertTrue(rf.is_role_inbox("talent.acquisition@acmecorp.com"))
        self.assertFalse(rf.is_role_inbox("priya.sharma@acmecorp.com"))

    def test_blocked_and_undeliverable_domains_are_rejected(self):
        candidates = rf.extract_email_candidates(
            "Contact someone@example.com or noreply@acmecorp.com or priya@acmecorp.com",
            name="Priya Sharma",
            company_domain="acmecorp.com",
            source="web",
            source_url="https://acmecorp.com/team",
            require_person=False,
        )
        emails = {c.email for c in candidates}
        self.assertNotIn("someone@example.com", emails)
        self.assertNotIn("noreply@acmecorp.com", emails)
        self.assertIn("priya@acmecorp.com", emails)

    def test_syntax_validation(self):
        self.assertTrue(rf.is_valid_email_syntax("priya@acmecorp.com"))
        self.assertFalse(rf.is_valid_email_syntax("priya@acmecorp"))
        self.assertFalse(rf.is_valid_email_syntax("priya@@acmecorp.com"))
        self.assertFalse(rf.is_valid_email_syntax("not-an-email"))

    # ------------------------------------------------------------------
    # GitHub provider
    # ------------------------------------------------------------------

    def test_github_commit_email_is_source_backed(self):
        payload = {
            "items": [
                {
                    "html_url": "https://github.com/acme/api/commit/abc123",
                    "commit": {
                        "author": {
                            "name": "Priya Sharma",
                            "email": "priya.sharma@acmecorp.com",
                        }
                    },
                },
                {
                    "html_url": "https://github.com/acme/api/commit/def456",
                    "commit": {
                        "author": {
                            "name": "Someone Else",
                            "email": "someone@acmecorp.com",
                        }
                    },
                },
            ]
        }
        with patch.object(rf, "_github_get", return_value=payload):
            candidates, errors = rf._github_commit_lookup("Priya Sharma", "acmecorp.com")

        self.assertEqual(errors, [])
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.email, "priya.sharma@acmecorp.com")
        self.assertEqual(candidate.source, "github_commit")
        self.assertEqual(candidate.source_url, "https://github.com/acme/api/commit/abc123")
        self.assertTrue(candidate.is_personal)

    def test_github_noreply_addresses_are_ignored(self):
        payload = {
            "items": [
                {
                    "html_url": "https://github.com/acme/api/commit/abc123",
                    "commit": {
                        "author": {
                            "name": "Priya Sharma",
                            "email": "12345+priya@users.noreply.github.com",
                        }
                    },
                }
            ]
        }
        with patch.object(rf, "_github_get", return_value=payload):
            candidates, _ = rf._github_commit_lookup("Priya Sharma", "acmecorp.com")
        self.assertEqual(candidates, [])

    # ------------------------------------------------------------------
    # Search providers
    # ------------------------------------------------------------------

    def test_search_prefers_configured_api_provider(self):
        fake = [{"title": "Acme team", "url": "https://acmecorp.com/team", "snippet": "Priya Sharma"}]
        with patch.object(rf, "_search_serper", return_value=fake) as serper, \
             patch.object(rf, "_search_jina_bing") as jina:
            payload = rf.search_web("unique-query-prefers-api", limit=5)

        self.assertEqual(payload["provider"], "serper")
        self.assertEqual(payload["results"], fake)
        serper.assert_called_once()
        jina.assert_not_called()

    def test_search_falls_back_through_providers(self):
        fake = [{"title": "Acme", "url": "https://acmecorp.com", "snippet": "hello"}]
        with patch.object(rf, "_search_serper", return_value=[]), \
             patch.object(rf, "_search_brave", return_value=[]), \
             patch.object(rf, "_search_searxng", return_value=[]), \
             patch.object(rf, "_search_jina_bing", return_value=fake), \
             patch.object(rf, "_search_bing_rss") as rss:
            payload = rf.search_web("unique-query-fallback", limit=5)

        self.assertEqual(payload["provider"], "jina_bing")
        self.assertEqual(payload["results"], fake)
        rss.assert_not_called()

    def test_search_results_are_cached(self):
        fake = [{"title": "Acme", "url": "https://acmecorp.com", "snippet": "hello"}]
        with patch.object(rf, "_search_serper", return_value=fake) as serper:
            rf.search_web("unique-query-cached", limit=5)
            rf.search_web("unique-query-cached", limit=5)
        self.assertEqual(serper.call_count, 1)

    def test_bing_rss_parser(self):
        rss = """<?xml version="1.0"?>
        <rss version="2.0"><channel><title>Bing</title>
          <item>
            <title>Priya Sharma - Recruiter at Acme</title>
            <link>https://acmecorp.com/team/priya</link>
            <description>Reach Priya Sharma at priya.sharma@acmecorp.com</description>
          </item>
        </channel></rss>"""

        class FakeResponse:
            content = rss.encode("utf-8")
            status_code = 200

        with patch.object(rf, "_request", return_value=FakeResponse()):
            results = rf._search_bing_rss("Priya Sharma Acme", limit=5)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "https://acmecorp.com/team/priya")
        self.assertIn("priya.sharma@acmecorp.com", results[0]["snippet"])

    def test_jina_markdown_parser_decodes_bing_redirects(self):
        target = "https://acmecorp.com/team/priya"
        encoded = base64.urlsafe_b64encode(target.encode()).decode().rstrip("=")
        redirect = "https://www.bing.com/ck/a?!&&p=abc&u=a1" + encoded
        markdown = (
            "Title: test\n\nMarkdown Content:\n"
            f"1.   ## [Priya Sharma - Acme]({redirect})\n\n"
            "Priya Sharma is a recruiter. Email priya.sharma@acmecorp.com\n"
            "## [Another result](https://acmecorp.com/contact)\n\nContact page.\n"
        )

        results = rf._parse_jina_markdown(markdown, limit=5)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["url"], target)
        self.assertEqual(results[0]["title"], "Priya Sharma - Acme")
        self.assertIn("priya.sharma@acmecorp.com", results[0]["snippet"])
        self.assertEqual(results[1]["url"], "https://acmecorp.com/contact")

    def test_jina_parser_drops_search_engine_links(self):
        markdown = (
            "## [Bing](https://www.bing.com/search?q=test)\n\n"
            "## [Real](https://acmecorp.com/team)\n\nTeam page.\n"
        )
        results = rf._parse_jina_markdown(markdown, limit=5)
        self.assertEqual([r["url"] for r in results], ["https://acmecorp.com/team"])

    def test_data_broker_pages_are_not_evidence(self):
        results = [
            {"title": "Priya Sharma email", "url": "https://contactout.com/priya", "snippet": "priya@acmecorp.com"},
            {"title": "Priya Sharma", "url": "https://acmecorp.com/team", "snippet": "priya@acmecorp.com"},
        ]
        candidates = rf._collect_from_results(
            results, name="Priya Sharma", company_domain="acmecorp.com", source="web"
        )
        self.assertEqual([c.source_url for c in candidates], ["https://acmecorp.com/team"])

    def test_linkedin_profile_url_parsing(self):
        parsed = rf.parse_linkedin_profile_url("https://www.linkedin.com/in/priya-sharma-123/?trk=public")
        self.assertEqual(parsed["slug"], "priya-sharma-123")
        self.assertEqual(parsed["full_name"], "Priya Sharma")
        self.assertIsNone(rf.parse_linkedin_profile_url("https://example.com/not-linkedin"))

    def test_sourcing_links_are_generated_without_scraping(self):
        links = rf.build_sourcing_links("Priya Sharma", "Acme Corp", "https://www.linkedin.com/in/priya-sharma/")
        self.assertIn("linkedin.com", links["linkedin_search_url"])
        self.assertIn("google.com", links["google_xray_url"])
        self.assertIn("mail.google.com", links["gmail_search_url"])
        self.assertIn("Priya", urllib.parse.unquote(links["google_xray_url"]))

    # ------------------------------------------------------------------
    # Company linkage (namesake protection)
    # ------------------------------------------------------------------

    def test_domain_match_ignores_punctuation_and_tld(self):
        self.assertTrue(rf._domain_matches("hello@linux-foundation.org", "linuxfoundation.com"))
        self.assertTrue(rf._domain_matches("hello@sub.acmecorp.com", "acmecorp.com"))
        self.assertFalse(rf._domain_matches("hello@gmail.com", "acmecorp.com"))

    def test_empty_company_has_no_domain(self):
        self.assertEqual(rf.resolve_company_domain(""), "")
        self.assertEqual(rf.resolve_company_domain("   "), "")
        self.assertEqual(rf.resolve_company_domain("BAY6.AI"), "bay6.ai")

    def test_namesake_without_company_link_is_hidden(self):
        namesake = rf.EmailCandidate(
            email="priyasharma40819@gmai.com",
            label="Public commit email",
            confidence="medium",
            source="github_commit",
            source_url="https://github.com/random/repo/commit/abc",
            is_personal=True,
            company_linked=False,
        )
        with patch.object(rf, "search_web", return_value={"provider": "", "results": [], "errors": []}), \
             patch.object(rf, "_github_commit_lookup", return_value=([namesake], [])), \
             patch.object(rf, "_github_profile_lookup", return_value=([], [])), \
             patch.object(rf, "_company_site_lookup", return_value=([], [])):
            result = rf.discover_recruiter_contact(
                name="Priya Sharma", company="BAY6 AI", deep_search=True, force_refresh=True
            )

        self.assertEqual(result["status"], "not_found")
        self.assertEqual(result["emails"], [])
        self.assertEqual(result["ignored_namesakes"], 1)
        self.assertIn("hidden", result["message"])

    def test_company_linked_email_is_shown(self):
        linked = rf.EmailCandidate(
            email="priya.sharma@bay6.ai",
            label="Public work email",
            confidence="high",
            source="github_commit",
            source_url="https://github.com/bay6ai/api/commit/abc",
            is_personal=True,
            company_linked=True,
        )
        with patch.object(rf, "search_web", return_value={"provider": "", "results": [], "errors": []}), \
             patch.object(rf, "_github_commit_lookup", return_value=([linked], [])), \
             patch.object(rf, "_github_profile_lookup", return_value=([], [])), \
             patch.object(rf, "_company_site_lookup", return_value=([], [])):
            result = rf.discover_recruiter_contact(
                name="Priya Sharma", company="BAY6 AI", deep_search=True, force_refresh=True
            )

        self.assertEqual(result["status"], "found")
        self.assertEqual(result["best_email"]["email"], "priya.sharma@bay6.ai")
        self.assertEqual(result["ignored_namesakes"], 0)

    def test_refine_domain_replaces_dead_guess(self):
        def fake_mx(domain):
            return {"checked": True, "mx": domain == "linux-foundation.org", "accepts_mail": domain == "linux-foundation.org"}

        with patch.object(rf, "check_domain_mx", side_effect=fake_mx):
            refined = rf._refine_company_domain("Linux Foundation", "linuxfoundation.com")
        self.assertEqual(refined, "linux-foundation.org")

    def test_jina_search_sends_first_page_param(self):
        captured = {}

        class FakeResponse:
            text = "## [Acme](https://acmecorp.com/team)\n\nTeam page.\n"

        def fake_request(method, url, **kwargs):
            captured["url"] = url
            captured["headers"] = kwargs.get("headers", {})
            return FakeResponse()

        with patch.object(rf, "_request", side_effect=fake_request):
            results = rf._search_jina_bing("Priya Sharma Acme", limit=5)

        self.assertIn("first=1", captured["url"])
        self.assertIn("r.jina.ai", captured["url"])
        self.assertEqual(results[0]["url"], "https://acmecorp.com/team")


class RecruiterApiAndPageTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.category = Category.objects.create(name="Engineering", slug="engineering")
        self.job = JobPosting.objects.create(
            title="Backend Engineer",
            company_name="Acme Corp",
            category=self.category,
            description="We are hiring a backend engineer.",
            eligibility="Open to all",
            location="Remote",
            apply_url="https://acmecorp.com/careers/backend",
            referrer_name="Priya Sharma",
            referrer_linkedin="https://www.linkedin.com/in/priya-sharma/",
            status="ACTIVE",
        )

    def test_page_renders(self):
        response = self.client.get(reverse("job_recruiter", kwargs={"uuid": self.job.uuid}))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        self.assertIn("Priya Sharma", body)
        self.assertIn("recruiter", body.lower())

    def test_api_returns_local_bundle_without_query(self):
        response = self.client.get(reverse("api_recruiter_intel", kwargs={"job_uuid": self.job.uuid}))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("sourcing_links", payload["data"])

    def test_api_rejects_non_linkedin_url(self):
        response = self.client.get(
            reverse("api_recruiter_intel", kwargs={"job_uuid": self.job.uuid}),
            {"linkedin_url": "https://example.com/in/priya"},
        )
        self.assertEqual(response.status_code, 400)

    def test_api_returns_discovery_payload(self):
        fake_result = {
            "status": "found",
            "message": "Found 1 public email address.",
            "emails": [{"email": "priya.sharma@acmecorp.com", "source": "github_commit"}],
            "best_email": {"email": "priya.sharma@acmecorp.com"},
            "has_personal_email": True,
            "checked_sources": ["job_post", "github", "web_search"],
            "errors": [],
            "sourcing_links": {},
            "recruiter": {"name": "Priya Sharma"},
            "company": {"name": "Acme Corp"},
            "from_cache": False,
        }
        with patch("requirements.views.discover_recruiter_contact", return_value=fake_result, create=True):
            with patch.object(rf, "discover_recruiter_contact", return_value=fake_result):
                response = self.client.get(
                    reverse("api_recruiter_intel", kwargs={"job_uuid": self.job.uuid}),
                    {"name": "Priya Sharma", "deep": "0"},
                )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["data"]["best_email"]["email"], "priya.sharma@acmecorp.com")

    def test_api_404_for_missing_job(self):
        response = self.client.get(
            reverse("api_recruiter_intel", kwargs={"job_uuid": "11111111-1111-1111-1111-111111111111"})
        )
        self.assertEqual(response.status_code, 404)
