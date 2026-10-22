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
    calculate_token_similarity,
    clean_canonical_job_url,
    normalize_company_name,
    normalize_job_title,
    purge_all_database_duplicates,
)
from requirements.job_aggregator.adapters import (
    JobdexoSourceAdapter,
    NaukriSourceAdapter,
    LinkedInSourceAdapter,
    GreenhousePublicSourceAdapter,
    AshbyPublicSourceAdapter,
    PublicFeedsSourceAdapter,
)
from requirements.job_aggregator.adapters.naukri_adapter import generate_naukri_token
from requirements.job_aggregator.orchestrator import orchestrator
from django.core.management import call_command


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

    def test_linkedin_toggle_via_env(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"LINKEDIN_SCRAPING_ENABLED": "false"}):
            # When disabled via environment
            with patch.object(LinkedInSourceAdapter, 'is_enabled', False):
                adapter = LinkedInSourceAdapter()
                jobs = adapter.fetch_jobs(limit=10)
                self.assertEqual(jobs, [])

        # By default, LinkedIn is enabled for priority scraping
        adapter_default = LinkedInSourceAdapter()
        self.assertTrue(adapter_default.is_enabled)

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

    @patch.object(JobdexoSourceAdapter, 'fetch_jobs')
    def test_orchestrator_execution(self, mock_jd_fetch):
        now = timezone.now()
        mock_jd_fetch.return_value = [
            {
                "source_name": "Jobdexo",
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

        result = orchestrator.run_aggregation(sources=["Jobdexo"], limit_per_source=5)
        self.assertTrue(result["success"])
        self.assertEqual(result["total_discovered"], 1)
        self.assertEqual(result["total_imported"], 1)

        # Verify JobIngestionRun persisted
        run = JobIngestionRun.objects.filter(source_name="Jobdexo").first()
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


class NaukriAndLinkedInAdapterTests(TestCase):
    def test_naukri_token_generation(self):
        token = generate_naukri_token("srp")
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)

    def test_naukri_job_details_parser(self):
        adapter = NaukriSourceAdapter()
        raw_items = [
            {
                "title": "Senior Python Developer",
                "companyName": "Infosys Limited",
                "jobId": "987654321",
                "jdURL": "/job-listings-python-dev-987654321",
                "tagsAndSkills": "Python, Django, AWS, Docker",
                "placeholders": [
                    {"type": "experience", "label": "2-5 Yrs"},
                    {"type": "salary", "label": "12-18 Lacs PA"},
                    {"type": "location", "label": "Bengaluru"}
                ],
                "jobDescription": "<p>Looking for a talented <b>Python Developer</b> with Django experience.</p>",
                "createdDate": 1792582319136,
                "footerPlaceholderLabel": "Just Now",
            }
        ]
        parsed = adapter.parse_naukri_job_details(raw_items)
        self.assertEqual(len(parsed), 1)
        job = parsed[0]
        self.assertEqual(job["source_name"], "Naukri")
        self.assertEqual(job["source_job_id"], "987654321")
        self.assertEqual(job["title"], "Senior Python Developer")
        self.assertEqual(job["company_name"], "Infosys Limited")
        self.assertEqual(job["normalized_city"], "Bengaluru")
        self.assertEqual(job["apply_url"], "https://www.naukri.com/job-listings-python-dev-987654321")
        self.assertEqual(job["stipend_salary"], "12-18 Lacs PA")
        self.assertEqual(job["timestamp_precision"], "EXACT_TIMESTAMP")
        self.assertIn("Python", job["skills_required"])

    def test_linkedin_adapter_enabled_state(self):
        adapter = LinkedInSourceAdapter()
        self.assertTrue(adapter.is_enabled)
        self.assertEqual(adapter.source_name, "LinkedIn")


class CrossSourceDeduplicationAndPurgeTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Engineering", slug="eng")

    def test_url_cleaning_and_normalization(self):
        raw_url = "https://www.naukri.com/job-listings-12345?utm_source=google&utm_medium=cpc&ref=homepage#section"
        clean = clean_canonical_job_url(raw_url)
        self.assertEqual(clean, "https://www.naukri.com/job-listings-12345")

        self.assertEqual(normalize_company_name("Infosys Technologies Pvt. Ltd."), "infosys")
        self.assertEqual(normalize_company_name("Tata Consultancy Services Ltd"), "tcs")
        self.assertEqual(normalize_company_name("Swiggy India Private Limited"), "swiggy")

        self.assertEqual(
            normalize_job_title("Python Developer (Immediate Joiner / Urgent Requirement)"),
            "python developer"
        )

    def test_cross_source_pre_insertion_deduplication(self):
        # 1. First insert from LinkedIn
        job_data_linkedin = {
            'source_name': 'LinkedIn',
            'source_job_id': 'li_101',
            'apply_url': 'https://careers.swiggy.com/job/101?utm_source=linkedin',
            'title': 'Senior Backend Engineer',
            'company_name': 'Swiggy',
            'normalized_city': 'Bengaluru',
            'description': 'Building microservices at scale using Go and Python.',
            'skills_required': 'Python, Go, Redis',
        }
        job1, created1 = merge_or_create_job(job_data_linkedin)
        self.assertTrue(created1)

        # 2. Ingest duplicate from Naukri with corporate suffix and tracking params
        job_data_naukri = {
            'source_name': 'Naukri',
            'source_job_id': 'nk_202',
            'apply_url': 'https://careers.swiggy.com/job/101?utm_source=naukri&tracking=email',
            'title': 'Senior Backend Engineer',
            'company_name': 'Swiggy Private Limited',
            'normalized_city': 'Bengaluru',
            'description': 'Building microservices at scale using Go and Python with comprehensive unit test coverage and high throughput.',
            'skills_required': 'Python, Go, Redis, Kafka, Kubernetes',
        }
        job2, created2 = merge_or_create_job(job_data_naukri)
        # Should be detected as duplicate!
        self.assertFalse(created2)
        self.assertEqual(job1.id, job2.id)

        # Verify metadata upgrade on job1
        job1.refresh_from_db()
        self.assertIn("Kafka", job1.skills_required)

    def test_purge_all_database_duplicates(self):
        now = timezone.now()
        # Create 3 duplicate entries across different sources and variations
        j1 = JobPosting.objects.create(
            title="Full Stack Software Engineer",
            company_name="Razorpay Software Pvt Ltd",
            category=self.cat,
            apply_url="https://jobs.razorpay.com/fs-dev?utm_source=board1",
            location="Bengaluru, Karnataka",
            normalized_city="Bengaluru",
            description="Short snippet description.",
            skills_required="React, Node.js",
            status='ACTIVE',
            source_name="Jobdexo"
        )

        j2 = JobPosting.objects.create(
            title="Full Stack Software Engineer",
            company_name="Razorpay",
            category=self.cat,
            apply_url="https://jobs.razorpay.com/fs-dev?utm_source=board2",
            location="Bengaluru, India",
            normalized_city="Bengaluru",
            description="Comprehensive rich job description detailing full stack responsibilities and architecture.",
            skills_required="React, Node.js, Python, PostgreSQL, AWS",
            status='ACTIVE',
            source_name="Naukri"
        )

        j3 = JobPosting.objects.create(
            title="Full Stack Software Engineer (Hiring / Immediate)",
            company_name="Razorpay Technologies",
            category=self.cat,
            apply_url="https://jobs.razorpay.com/fs-dev",
            location="Bengaluru, Karnataka",
            normalized_city="Bengaluru",
            description="Medium description.",
            skills_required="React, Node.js, TypeScript",
            status='ACTIVE',
            source_name="LinkedIn"
        )

        self.assertEqual(JobPosting.objects.filter(status='ACTIVE').count(), 3)

        # Dry run audit first
        dry_stats = purge_all_database_duplicates(dry_run=True)
        self.assertEqual(dry_stats['duplicate_clusters'], 1)
        self.assertEqual(dry_stats['duplicates_found'], 2)
        self.assertEqual(dry_stats['duplicates_deleted'], 0)
        self.assertEqual(JobPosting.objects.filter(status='ACTIVE').count(), 3)

        # Real purge execution
        real_stats = purge_all_database_duplicates(dry_run=False)
        self.assertEqual(real_stats['duplicate_clusters'], 1)
        self.assertEqual(real_stats['duplicates_deleted'], 2)
        self.assertEqual(JobPosting.objects.filter(status='ACTIVE').count(), 1)

        # Winner should have preserved the richest description
        survivor = JobPosting.objects.filter(status='ACTIVE').first()
        self.assertIn("Comprehensive rich job description", survivor.description)

    def test_deduplicate_jobs_cli_command(self):
        from io import StringIO
        out = StringIO()
        call_command('deduplicate_jobs', '--dry-run', stdout=out)
        output = out.getvalue()
        self.assertIn("Starting comprehensive cross-source job deduplication sweep", output)
        self.assertIn("Deduplication scan finished", output)

    def test_deduplicate_api_endpoint(self):
        # GET dry_run simulation
        res = self.client.get("/api/jobs/deduplicate/?dry_run=true")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("stats", data)
        self.assertTrue(data["stats"]["dry_run"])

        # POST execution
        res_post = self.client.post("/api/jobs/deduplicate/", json.dumps({"dry_run": False}), content_type="application/json")
        self.assertEqual(res_post.status_code, 200)
        data_post = res_post.json()
        self.assertTrue(data_post["success"])
        self.assertFalse(data_post["stats"]["dry_run"])

