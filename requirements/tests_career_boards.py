"""Official career boards + Adzuna: parsing, India/JD rules, no invented data, upgrades."""
import importlib
import os
from unittest import mock

from django.apps import apps as django_apps
from django.test import TestCase

from requirements.job_aggregator.adapters.adzuna_adapter import AdzunaSourceAdapter
from requirements.job_aggregator.adapters.indian_startup_adapter import (
    IndianStartupSourceAdapter,
    extract_eligibility,
    html_to_text,
)
from requirements.job_aggregator.deduplicator import merge_or_create_job
from requirements.job_aggregator.normalizer import classify_experience_tier
from requirements.models import JobPosting

JD = ("<p>Build backend services in Python and Django for millions of users.</p>"
      "<h3>Requirements</h3><ul><li>0-1 years of experience or final-year students</li>"
      "<li>Strong Python, SQL and REST API fundamentals</li></ul>"
      "<p>You will work with a small team shipping weekly, own features end to end, "
      "write tests, review code and learn from senior engineers every day.</p>")


class FakeRes:
    def __init__(self, data, status=200):
        self._data, self.status_code = data, status

    def json(self):
        return self._data


def router(table):
    def safe_get(url, params=None, headers=None):
        for key, val in table.items():
            if key in url:
                return FakeRes(val) if not isinstance(val, FakeRes) else val
        return FakeRes({}, 404)
    return safe_get


class CareerBoardParsingTests(TestCase):
    def setUp(self):
        self.a = IndianStartupSourceAdapter()

    def test_greenhouse_keeps_real_jd_and_filters_india(self):
        data = {"jobs": [
            {"id": 1, "title": "Backend Engineer", "location": {"name": "Bengaluru, India"},
             "content": JD.replace("<", "&lt;").replace(">", "&gt;"),  # Greenhouse double-encodes
             "absolute_url": "https://job-boards.greenhouse.io/acme/jobs/1", "first_published": "2026-11-01T10:00:00Z"},
            {"id": 2, "title": "Backend Engineer", "location": {"name": "Berlin, Germany"}, "content": JD,
             "absolute_url": "https://x/2", "first_published": "2026-11-01T10:00:00Z"},
            {"id": 3, "title": "Data Analyst", "location": {"name": "Pune"}, "content": "<p>Short.</p>",
             "absolute_url": "https://x/3", "first_published": "2026-11-01T10:00:00Z"},
        ]}
        with mock.patch.object(self.a, "safe_get", side_effect=router({"greenhouse.io": data})):
            jobs = self.a.fetch_board({"ats": "greenhouse", "slug": "acme", "company": "Acme"})
        self.assertEqual(len(jobs), 1)  # non-India and no-JD postings skipped
        j = jobs[0]
        self.assertIn("Build backend services", j["description"])
        self.assertNotIn("<p>", j["description"])
        self.assertEqual(j["source_job_id"], "su_gh_acme_1")
        self.assertEqual(j["stipend_salary"], "Not disclosed")
        self.assertIn("0-1 years", j["eligibility"])
        self.assertNotRegex(j["description"] + j["eligibility"], r"\+91")

    def test_lever_builds_jd_from_sections_and_uses_real_salary(self):
        data = [{
            "id": "abc", "text": "SDE Intern", "categories": {"location": "Bangalore", "commitment": "Intern"},
            "openingPlain": "", "descriptionPlain": "We are hiring interns to build our payments platform end to end.",
            "lists": [{"text": "What we're looking for", "content": "<li>Final-year B.Tech students</li><li>Python or Java</li>"}],
            "additionalPlain": "Stipend and mentorship provided. Work from our Bengaluru office five days a week with the core team.",
            "hostedUrl": "https://jobs.lever.co/acme/abc", "createdAt": 1762000000000,
            "salaryRange": {"currency": "INR", "min": 40000, "max": 50000, "interval": "per-month"},
        }]
        with mock.patch.object(self.a, "safe_get", side_effect=router({"lever.co": data})):
            jobs = self.a.fetch_board({"ats": "lever", "slug": "acme", "company": "Acme"})
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j["job_type"], "INTERNSHIP")
        self.assertIn("Final-year B.Tech students", j["eligibility"])
        self.assertIn("40,000", j["stipend_salary"])

    def test_ashby_skips_unlisted_and_hidden_compensation(self):
        base = {"title": "ML Engineer", "location": "Bengaluru", "descriptionPlain": html_to_text(JD),
                "jobUrl": "https://jobs.ashbyhq.com/acme/1", "publishedAt": "2026-11-01T10:00:00Z",
                "employmentType": "FullTime", "shouldDisplayCompensationOnJobPostings": False,
                "compensation": {"scrapeableCompensationSalarySummary": "₹30L"}}
        data = {"jobs": [dict(base, id="1"), dict(base, id="2", isListed=False)]}
        with mock.patch.object(self.a, "safe_get", side_effect=router({"ashbyhq.com": data})):
            jobs = self.a.fetch_board({"ats": "ashby", "slug": "acme", "company": "Acme"})
        self.assertEqual([j["source_job_id"] for j in jobs], ["su_ashby_acme_1"])
        self.assertEqual(jobs[0]["stipend_salary"], "Not disclosed")  # employer chose not to display it

    def test_smartrecruiters_uses_detail_sections(self):
        listing = {"totalFound": 1, "content": [{
            "id": "77", "name": "Business Analyst", "releasedDate": "2026-11-01T10:00:00Z",
            "location": {"country": "in", "fullLocation": "Mumbai, MH, India"},
            "typeOfEmployment": {"label": "Full-time"}}]}
        detail = {"postingUrl": "https://jobs.smartrecruiters.com/ACME/77-ba", "jobAd": {"sections": {
            "jobDescription": {"title": "Job Description", "text": JD},
            "qualifications": {"title": "Qualifications", "text": "<li>MBA or B.Com, 0-2 years</li>"}}}}
        with mock.patch.object(self.a, "safe_get", side_effect=router({"/postings/77": detail, "/postings": listing})):
            jobs = self.a.fetch_board({"ats": "smartrecruiters", "slug": "ACME", "company": "Acme"})
        self.assertEqual(len(jobs), 1)
        self.assertIn("MBA or B.Com", jobs[0]["eligibility"])
        self.assertEqual(jobs[0]["apply_url"], "https://jobs.smartrecruiters.com/ACME/77-ba")

    def test_round_robin_visits_every_board(self):
        boards = [{"ats": "lever", "slug": f"b{i}", "company": f"B{i}"} for i in range(5)]
        seen = []
        self.a.boards_per_run = 2
        with mock.patch("requirements.job_aggregator.adapters.indian_startup_adapter.load_boards", return_value=boards), \
             mock.patch.object(self.a, "fetch_board", side_effect=lambda b, **kw: seen.append(b["slug"]) or []):
            for _ in range(3):
                self.a.fetch_jobs()
        self.assertEqual(set(seen), {f"b{i}" for i in range(5)})


class ExperienceTierTests(TestCase):
    def test_internal_is_not_internship(self):
        self.assertNotEqual(classify_experience_tier("Assistant Manager - Internal Audit", "", "international teams"), "INTERNSHIP")
        self.assertEqual(classify_experience_tier("Software Engineer Intern"), "INTERNSHIP")

    def test_jd_mentioning_interns_does_not_make_job_an_internship(self):
        self.assertNotEqual(classify_experience_tier("Backend Engineer", "", "You will mentor interns. 2-4 years."), "INTERNSHIP")


class EligibilityTests(TestCase):
    def test_extracts_requirements_section(self):
        text = html_to_text(JD)
        self.assertIn("Strong Python", extract_eligibility(text))

    def test_falls_back_without_inventing(self):
        self.assertEqual(extract_eligibility("No headings here at all."), "See the job description for eligibility.")


@mock.patch.dict(os.environ, {"ADZUNA_APP_ID": "id123", "ADZUNA_APP_KEY": "key456"})
class AdzunaTests(TestCase):
    item = {"id": "999", "title": "<strong>Python Developer</strong>", "description": html_to_text(JD),
            "redirect_url": "https://www.adzuna.in/land/ad/999?se=abc&utm_medium=api&utm_source=id123&v=1",
            "company": {"display_name": "Acme"}, "location": {"display_name": "Bengaluru, Karnataka"},
            "created": "2026-11-09T10:00:00Z", "salary_min": 600000, "salary_max": 600000, "salary_is_predicted": "1"}

    def test_disabled_without_keys(self):
        with mock.patch.dict(os.environ, {"ADZUNA_APP_ID": "", "ADZUNA_APP_KEY": ""}):
            self.assertEqual(AdzunaSourceAdapter().fetch_jobs(), [])

    def test_parses_result_and_ignores_estimated_salary(self):
        j = AdzunaSourceAdapter().parse_result(self.item)
        self.assertEqual(j["title"], "Python Developer")
        self.assertEqual(j["stipend_salary"], "Not disclosed")  # Adzuna estimate, not employer data
        self.assertEqual(j["source_job_id"], "adzuna_999")

    def test_redirect_url_stored_verbatim(self):
        job, created = merge_or_create_job(AdzunaSourceAdapter().parse_result(self.item))
        self.assertTrue(created)
        self.assertIn("utm_source=id123", job.apply_url)


class UpgradeAndScrubTests(TestCase):
    def _placeholder(self):
        from requirements.job_aggregator.deduplicator import get_or_create_standard_categories  # noqa: F401
        job, _ = merge_or_create_job({
            "source_name": "Startup", "source_job_id": "su_lever_acme_abc", "title": "SDE",
            "company_name": "Acme", "apply_url": "https://jobs.lever.co/acme/abc",
            "description": "SDE opening at Acme. Official startup career requirement in Bengaluru. HR Contact Helpline: +91 98450 12890.",
            "stipend_salary": "Startup Package (Competitive + Benefits)", "eligibility": "Open to matching candidates",
            "location": "Bengaluru, India", "industry_domain": "TECHNICAL", "experience_tier": "MID_LEVEL",
        })
        return job

    def test_real_jd_replaces_placeholder_and_its_fields(self):
        self._placeholder()
        real = IndianStartupSourceAdapter()._build(
            {"slug": "acme", "company": "Acme"}, ats_key="lever", posting_id="abc", title="SDE",
            raw_location="Bengaluru", jd=html_to_text(JD), apply_url="https://jobs.lever.co/acme/abc",
            published="2026-11-01T10:00:00Z")
        job, created = merge_or_create_job(real)
        self.assertFalse(created)
        job.refresh_from_db()
        self.assertIn("Build backend services", job.description)
        self.assertEqual(job.stipend_salary, "Not disclosed")
        self.assertEqual(job.contact_phone, "")

    def test_migration_scrubs_invented_phone_and_salary(self):
        job = self._placeholder()
        self.assertTrue(job.contact_phone)  # the fake number was being shown as HR contact
        mig = importlib.import_module("requirements.migrations.0026_scrub_invented_startup_details")
        mig.scrub(django_apps, None)
        job.refresh_from_db()
        self.assertEqual(job.contact_phone, "")
        self.assertNotIn("Helpline", job.description)
        self.assertEqual(job.stipend_salary, "Not disclosed")


class DedupeTests(TestCase):
    def _job(self, sid, title, status="ACTIVE"):
        job, _ = merge_or_create_job({
            "source_name": "Startup", "source_job_id": sid, "title": title, "company_name": "HighRadius",
            "apply_url": f"https://job-boards.greenhouse.io/highradius/jobs/{sid}", "description": "x" * 300,
            "location": "Hyderabad, India", "normalized_city": "Hyderabad",
        })
        if status != "ACTIVE":
            JobPosting.objects.filter(pk=job.pk).update(status=status)
        return job

    def test_similar_titles_on_same_board_stay_separate(self):
        a = self._job("su_gh_highradius_1", "Software Engineer - Java")
        b = self._job("su_gh_highradius_2", "Senior Software Engineer - Java")
        self.assertNotEqual(a.pk, b.pk)

    def test_listed_posting_reopens_expired_row_but_not_closed(self):
        exp = self._job("su_gh_highradius_3", "Data Analyst", status="EXPIRED")
        closed = self._job("su_gh_highradius_4", "QA Engineer", status="CLOSED")
        self._job("su_gh_highradius_3", "Data Analyst")
        self._job("su_gh_highradius_4", "QA Engineer")
        exp.refresh_from_db(); closed.refresh_from_db()
        self.assertEqual(exp.status, "ACTIVE")
        self.assertEqual(closed.status, "CLOSED")


class CanonicalUrlTests(TestCase):
    def test_job_id_params_survive_cleaning(self):
        from requirements.job_aggregator.deduplicator import clean_canonical_job_url
        a = clean_canonical_job_url("https://www.highradius.com/careers/?gh_jid=111&utm_source=x")
        b = clean_canonical_job_url("https://www.highradius.com/careers/?gh_jid=222")
        self.assertIn("gh_jid=111", a)
        self.assertNotIn("utm_source", a)
        self.assertNotEqual(a, b)
