from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase

from requirements.job_aggregator.adapters import linkedin_adapter
from requirements.job_aggregator.adapters.linkedin_adapter import LinkedInSourceAdapter, SEARCH_KEYWORDS
from requirements.models import Category, JobPosting

JD = "<div class='show-more-less-html__markup'>" + ("Build and ship backend services in Python. " * 10) + "</div>"


def card(job_id, title, company):
    return f"""
    <li><div class="base-card" data-entity-urn="urn:li:jobPosting:{job_id}">
      <h3 class="base-search-card__title">{title}</h3>
      <h4 class="base-search-card__subtitle"><a href="#">{company}</a></h4>
      <span class="job-search-card__location">Bengaluru, Karnataka, India</span>
      <time class="job-search-card__listdate" datetime="2026-11-10">1 hour ago</time>
    </div></li>"""


def response(text):
    res = MagicMock()
    res.status_code = 200
    res.text = text
    return res


class LinkedInKeywordRotationTests(TestCase):
    def setUp(self):
        cache.delete(linkedin_adapter._KEYWORD_CURSOR_KEY)

    def _run(self, search_html, **kwargs):
        searched = []

        def fake_get(url, params=None, headers=None):
            if "jobPosting" in url:
                return response(JD)
            searched.append(params["keywords"])
            return response(search_html if params["start"] == 0 else "")

        adapter = LinkedInSourceAdapter()
        with patch.object(LinkedInSourceAdapter, "is_enabled", True), \
             patch.object(adapter, "safe_get", side_effect=fake_get):
            jobs = adapter.fetch_jobs(limit=8, last_hours=1, **kwargs)
        return jobs, searched

    def test_each_cycle_searches_the_next_roles(self):
        _, first = self._run("")
        _, second = self._run("")
        self.assertEqual(first, SEARCH_KEYWORDS[0:3])
        self.assertEqual(second, SEARCH_KEYWORDS[3:6])

    def test_skips_stored_jobs_and_repeated_roles(self):
        cat = Category.objects.create(name="Software Engineering", slug="software-engineering")
        JobPosting.objects.create(
            category=cat, title="Old Role", company_name="Acme", source_name="LinkedIn",
            source_job_id="111", description="x", apply_url="https://www.linkedin.com/jobs/view/111",
        )
        html = (
            card("111", "Old Role", "Acme")             # already stored
            + card("222", "Backend Engineer", "Zeta")
            + card("333", "Backend Engineer", "Zeta")   # same job, second ID
            + card("444", "Data Analyst", "Groww")
        )
        jobs, _ = self._run(html, keywords="python developer")
        self.assertEqual([j["source_job_id"] for j in jobs], ["222", "444"])
