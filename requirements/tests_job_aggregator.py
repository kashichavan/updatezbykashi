import json
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.utils import timezone
from zoneinfo import ZoneInfo

from requirements.models import Category, JobPosting, JobIngestionRun
from requirements.job_aggregator.constants import INDIAN_CITY_CANONICAL_MAP
from requirements.job_aggregator.normalizer import (
    normalize_indian_location,
    classify_industry_domain,
    classify_experience_tier,
    parse_job_timestamps
)
from requirements.job_aggregator.deduplicator import (
    find_existing_job_duplicate,
    merge_or_create_job,
    calculate_token_similarity
)
from requirements.job_aggregator.adapters import (
    GreenhousePublicSourceAdapter,
    AshbyPublicSourceAdapter,
    PublicFeedsSourceAdapter,
    LinkedInSourceAdapter
)
from requirements.job_aggregator.orchestrator import orchestrator


class LocationAndTaxonomyTests(TestCase):
    def test_indian_location_normalization(self):
        city, is_remote, valid = normalize_indian_location("Bangalore, Karnataka")
        self.assertEqual(city, "Bengaluru")
        self.assertFalse(is_remote)
        self.assertTrue(valid)

        city, is_remote, valid = normalize_indian_location("Hitec City, Cyberabad")
        self.assertEqual(city, "Hyderabad")
        self.assertTrue(valid)

        city, is_remote, valid = normalize_indian_location("Gurgaon / Noida")
        self.assertIn(city, ["Gurugram", "Noida", "Delhi NCR"])
        self.assertTrue(valid)

        city, is_remote, valid = normalize_indian_location("Work from Home - Pan India")
        self.assertTrue(is_remote)
        self.assertTrue(valid)

        # Foreign exclusive
        city, is_remote, valid = normalize_indian_location("London, United Kingdom")
        self.assertFalse(valid)

    def test_industry_domain_classification(self):
        self.assertEqual(classify_industry_domain("Senior Python Backend Engineer", "Django, AWS"), "TECHNICAL")
        self.assertEqual(classify_industry_domain("React Frontend Developer", "JavaScript, Next.js"), "TECHNICAL")
        self.assertEqual(classify_industry_domain("Digital Marketing Specialist", "SEO, Social Media, Google Ads"), "NON_TECHNICAL")
        self.assertEqual(classify_industry_domain("Talent Acquisition & HR Executive", "Recruitment, Sourcing"), "NON_TECHNICAL")
        self.assertEqual(classify_industry_domain("Financial Analyst", "Accounting, Balance Sheets"), "NON_TECHNICAL")

    def test_experience_tier_classification(self):
        self.assertEqual(classify_experience_tier("Software Engineering Intern - Summer 2026"), "INTERNSHIP")
        self.assertEqual(classify_experience_tier("Junior Python Developer (0-1 Years)"), "FRESHER")
        self.assertEqual(classify_experience_tier("Frontend Engineer (1-3 Years)"), "EARLY_CAREER")
        self.assertEqual(classify_experience_tier("Full Stack Developer (3-5 Years)"), "MID_LEVEL")
        self.assertEqual(classify_experience_tier("Lead Architect / Principal Engineer"), "SENIOR_LEVEL")


class TimestampAndLastHourTests(TestCase):
    def test_timestamp_parsing(self):
        now = timezone.now()
        
        # Relative minutes
        parsed_dt, precision = parse_job_timestamps("25 minutes ago")
        self.assertEqual(precision, "APPROXIMATE_TIME")
        diff_sec = (now - parsed_dt).total_seconds()
        self.assertGreaterEqual(diff_sec, 24 * 60)
        self.assertLessEqual(diff_sec, 26 * 60)

        # Relative hours
        parsed_dt, precision = parse_job_timestamps("2 hours ago")
        self.assertEqual(precision, "APPROXIMATE_TIME")
        self.assertGreaterEqual((now - parsed_dt).total_seconds(), 7000)

        # ISO format
        parsed_dt, precision = parse_job_timestamps("2026-10-22T08:00:00Z")
        self.assertEqual(precision, "EXACT_TIMESTAMP")
        self.assertEqual(parsed_dt.year, 2026)

    def test_last_hour_and_ist_display(self):
        now = timezone.now()
        cat = Category.objects.create(name="Tech", slug="tech")

        # Job inside last hour
        job_recent = JobPosting.objects.create(
            title="FastAPI Developer",
            company_name="CredFlow",
            category=cat,
            source_published_at=now - timedelta(minutes=20),
            first_seen_at=now - timedelta(minutes=15),
            timestamp_precision='EXACT_TIMESTAMP'
        )
        self.assertTrue(job_recent.is_last_hour())
        self.assertEqual(job_recent.get_freshness_badge()['is_last_hour'], True)
        self.assertIn("m ago", job_recent.get_relative_time_display())

        # Job outside last hour
        job_old = JobPosting.objects.create(
            title="Java Engineer",
            company_name="OldCorp",
            category=cat,
            source_published_at=now - timedelta(hours=3),
            first_seen_at=now - timedelta(hours=3),
            timestamp_precision='EXACT_TIMESTAMP'
        )
        self.assertFalse(job_old.is_last_hour())

        # Test IST Time Conversion
        ist_str = job_recent.get_ist_published_time()
        self.assertTrue(len(ist_str) > 0)


class DeduplicationTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Tech", slug="tech")
        self.existing = JobPosting.objects.create(
            title="Backend Engineer (Python)",
            company_name="Swiggy",
            category=self.cat,
            location="Bengaluru, India",
            normalized_city="Bengaluru",
            apply_url="https://jobdexo.com/redirect/123",
            source_name="Jobdexo",
            source_job_id="swiggy-101",
            timestamp_precision="DATE_ONLY"
        )

    def test_find_duplicate_by_source_id(self):
        job_data = {
            "source_name": "Jobdexo",
            "source_job_id": "swiggy-101",
            "title": "Different Title",
            "company_name": "Swiggy"
        }
        dup = find_existing_job_duplicate(job_data)
        self.assertIsNotNone(dup)
        self.assertEqual(dup.id, self.existing.id)

    def test_find_duplicate_by_token_similarity(self):
        sim = calculate_token_similarity("Backend Engineer Python", "Python Backend Software Engineer")
        self.assertGreaterEqual(sim, 0.70)

        job_data = {
            "source_name": "Greenhouse",
            "source_job_id": "gh-999",
            "title": "Backend Software Engineer - Python",
            "company_name": "Swiggy",
            "normalized_city": "Bengaluru"
        }
        dup = find_existing_job_duplicate(job_data)
        self.assertIsNotNone(dup)

    def test_merge_or_create_upgrades_clean_url(self):
        job_data = {
            "source_name": "Greenhouse",
            "source_job_id": "swiggy-101",
            "title": "Backend Engineer (Python)",
            "company_name": "Swiggy",
            "apply_url": "https://boards.greenhouse.io/swiggy/jobs/101",
            "source_published_at": timezone.now(),
            "timestamp_precision": "EXACT_TIMESTAMP"
        }
        job, created = merge_or_create_job(job_data)
        self.assertFalse(created)
        self.assertEqual(job.id, self.existing.id)
        # Verify apply_url upgraded from jobdexo redirect to official greenhouse link
        self.assertEqual(job.apply_url, "https://boards.greenhouse.io/swiggy/jobs/101")
        self.assertEqual(job.timestamp_precision, "EXACT_TIMESTAMP")


class SourceAdaptersAndOrchestratorTests(TestCase):
    @patch('requirements.job_aggregator.base_adapter.requests.Session.get')
    def test_greenhouse_adapter_mocked(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jobs": [
                {
                    "id": 55512,
                    "title": "Software Engineer II - Payments",
                    "location": {"name": "Bengaluru, India"},
                    "content": "Work on high-throughput payment rails.",
                    "updated_at": "2026-10-22T08:30:00Z",
                    "absolute_url": "https://boards.greenhouse.io/razorpay/jobs/55512"
                }
            ]
        }
        mock_get.return_value = mock_response

        adapter = GreenhousePublicSourceAdapter()
        jobs = adapter.fetch_jobs(limit=5)
        self.assertTrue(len(jobs) >= 1)
        first = jobs[0]
        self.assertEqual(first["source_name"], "Greenhouse")
        self.assertEqual(first["normalized_city"], "Bengaluru")
        self.assertEqual(first["industry_domain"], "TECHNICAL")

    def test_linkedin_disabled_by_default(self):
        adapter = LinkedInSourceAdapter()
        self.assertFalse(adapter.is_enabled)
        jobs = adapter.fetch_jobs(limit=10)
        self.assertEqual(jobs, [])

    def test_linkedin_guest_parser_mocked(self):
        sample_html = """
        <li>
          <div class="base-card" data-entity-urn="urn:li:jobPosting:3890123456">
            <h3 class="base-search-card__title">Software Engineer - Backend (Python)</h3>
            <h4 class="base-search-card__subtitle"><a href="#">PhonePe</a></h4>
            <span class="job-search-card__location">Bengaluru, Karnataka, India</span>
            <time class="job-search-card__listdate" datetime="2026-10-22">20 minutes ago</time>
          </div>
        </li>
        """
        adapter = LinkedInSourceAdapter()
        parsed = adapter.parse_linkedin_guest_html(sample_html, limit=5)
        self.assertEqual(len(parsed), 1)
        job = parsed[0]
        self.assertEqual(job["source_name"], "LinkedIn")
        self.assertEqual(job["source_job_id"], "3890123456")
        self.assertEqual(job["title"], "Software Engineer - Backend (Python)")
        self.assertEqual(job["company_name"], "PhonePe")
        self.assertEqual(job["normalized_city"], "Bengaluru")
        self.assertEqual(job["industry_domain"], "TECHNICAL")
        self.assertIn("3890123456", job["apply_url"])

    @patch.object(GreenhousePublicSourceAdapter, 'fetch_jobs')
    def test_orchestrator_execution(self, mock_gh_fetch):
        now = timezone.now()
        mock_gh_fetch.return_value = [
            {
                "source_name": "Greenhouse",
                "source_job_id": "test-mock-01",
                "source_url": "https://example.com/job/01",
                "apply_url": "https://example.com/apply/01",
                "title": "Cloud DevOps Engineer",
                "company_name": "Meesho",
                "description": "Kubernetes, AWS, Terraform",
                "location": "Bengaluru, India",
                "normalized_city": "Bengaluru",
                "is_remote": False,
                "job_type": "FULL_TIME",
                "industry_domain": "TECHNICAL",
                "experience_tier": "EARLY_CAREER",
                "skills_required": "Kubernetes, AWS",
                "stipend_salary": "Best in Industry",
                "source_published_at": now - timedelta(minutes=10),
                "timestamp_precision": "EXACT_TIMESTAMP",
            }
        ]

        result = orchestrator.run_aggregation(sources=["Greenhouse"], limit_per_source=5)
        self.assertTrue(result["success"])
        self.assertEqual(result["total_discovered"], 1)
        self.assertEqual(result["total_imported"], 1)

        # Verify JobIngestionRun persisted
        run = JobIngestionRun.objects.filter(source_name="Greenhouse").first()
        self.assertIsNotNone(run)
        self.assertEqual(run.status, "SUCCESS")


class JobAggregationAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Category.objects.create(name="Engineering", slug="engineering")
        now = timezone.now()

        # Job 1: Technical, Bengaluru, Last Hour
        self.job1 = JobPosting.objects.create(
            title="Python Django Developer",
            company_name="Zomato",
            category=self.cat,
            location="Bengaluru, Karnataka",
            normalized_city="Bengaluru",
            industry_domain="TECHNICAL",
            experience_tier="FRESHER",
            source_name="Greenhouse",
            source_published_at=now - timedelta(minutes=15),
            first_seen_at=now - timedelta(minutes=15),
            timestamp_precision="EXACT_TIMESTAMP"
        )

        # Job 2: Non-Technical, Mumbai, 5 hours ago
        self.job2 = JobPosting.objects.create(
            title="Digital Marketing Associate",
            company_name="Nykaa",
            category=self.cat,
            location="Mumbai, Maharashtra",
            normalized_city="Mumbai",
            industry_domain="NON_TECHNICAL",
            experience_tier="EARLY_CAREER",
            source_name="Ashby",
            source_published_at=now - timedelta(hours=5),
            first_seen_at=now - timedelta(hours=5),
            timestamp_precision="EXACT_TIMESTAMP"
        )

    def test_api_jobs_list_filters(self):
        # Filter technical
        res = self.client.get("/api/jobs/?domain=TECHNICAL")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(any(j["title"] == "Python Django Developer" for j in data["jobs"]))

        # Filter city
        res = self.client.get("/api/jobs/?city=Mumbai")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(any(j["company_name"] == "Nykaa" for j in data["jobs"]))

        # Filter time_window=1h
        res = self.client.get("/api/jobs/?time_window=1h")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data["jobs"]), 1)
        self.assertEqual(data["jobs"][0]["company_name"], "Zomato")

    def test_api_jobs_last_hour(self):
        res = self.client.get("/api/jobs/last-hour/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["last_hour_count"], 1)
        self.assertEqual(data["jobs"][0]["company_name"], "Zomato")

    def test_api_jobs_ingestion_status(self):
        res = self.client.get("/api/jobs/ingestion-status/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("active_sources", data)
        self.assertIn("metrics", data)
