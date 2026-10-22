from django.test import TestCase
from unittest.mock import patch, MagicMock
from requirements.github_discovery import (
    extract_keywords_from_job,
    build_search_queries,
    calculate_relevance_score,
    search_github_repositories,
    get_fallback_curated_projects
)

class GitHubDiscoveryUnitTests(TestCase):
    def test_extract_keywords_from_job(self):
        title = "Senior Python Backend Engineer"
        skills = "Python, Django, PostgreSQL, Redis, Docker"
        desc = "Building high-performance REST APIs and microservices using Celery and AWS."
        keywords = extract_keywords_from_job(title, skills, desc)
        self.assertIn("python", keywords)
        self.assertIn("django", keywords)
        self.assertIn("postgresql", keywords)
        self.assertIn("redis", keywords)

    def test_build_search_queries(self):
        queries = build_search_queries("Backend Engineer", ["python", "django", "postgresql"])
        self.assertTrue(len(queries) >= 1)
        self.assertTrue(any("python" in q for q in queries))

    def test_calculate_relevance_score_5_factors(self):
        repo = {
            "name": "enterprise-django-api",
            "description": "Production Django REST API with PostgreSQL, Redis caching, and Docker orchestration.",
            "topics": ["python", "django", "postgresql", "redis", "api"],
            "language": "Python",
            "size": 500,
            "homepage": "https://api.example.com",
            "license": {"key": "mit"},
            "stargazers_count": 120,
            "pushed_at": "2026-01-15T00:00:00Z"
        }
        job_skills = ["python", "django", "postgresql", "redis"]
        result = calculate_relevance_score(
            repo=repo,
            job_skills=job_skills,
            job_description="Looking for Python Django developer with API and Redis expertise.",
            job_title="Python Developer"
        )
        score = result["relevance_score"]
        breakdown = result["score_breakdown"]
        self.assertGreaterEqual(score, 70.0)
        self.assertLessEqual(score, 100.0)
        self.assertIn("technology_overlap", breakdown)
        self.assertIn("responsibility_overlap", breakdown)
        self.assertIn("code_structure", breakdown)
        self.assertIn("documentation", breakdown)
        self.assertIn("maintenance_recency", breakdown)

    @patch('requirements.github_discovery.requests.get')
    def test_search_github_repositories_mocked(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": 101,
                    "name": "fastapi-realworld-example",
                    "full_name": "developer/fastapi-realworld-example",
                    "html_url": "https://github.com/developer/fastapi-realworld-example",
                    "description": "Exemplary real world backend built with FastAPI, PostgreSQL, and Docker.",
                    "topics": ["fastapi", "python", "postgresql"],
                    "language": "Python",
                    "stargazers_count": 850,
                    "size": 300,
                    "pushed_at": "2026-02-01T00:00:00Z"
                }
            ]
        }
        mock_get.return_value = mock_response

        repos = search_github_repositories(
            job_title="FastAPI Developer",
            job_skills="Python, FastAPI, PostgreSQL",
            job_description="Build modern APIs",
            limit=5
        )
        self.assertTrue(len(repos) >= 1)
        first = repos[0]
        self.assertIn("relevance_score", first)
        self.assertIn("evidence_summary", first)
        self.assertIn("Python", first["language"])

    def test_fallback_curated_projects(self):
        fallback = get_fallback_curated_projects(["python", "django"])
        self.assertTrue(len(fallback) >= 2)
        for proj in fallback:
            self.assertIn("relevance_score", proj)
            self.assertIn("tech_stack", proj)
            self.assertEqual(proj["candidate_relationship"], "RECOMMENDED")
