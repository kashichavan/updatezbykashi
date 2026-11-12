import json
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase

from requirements import ai_engine
from requirements.resume_prompts import build_blueprint_messages, build_fit_messages

JD = (
    "Backend Developer\n"
    "We need Python, Django and PostgreSQL. Docker is required. "
    "Experience with Kafka is a plus. You will build REST API services."
)

BLUEPRINT = {
    "target_title": "Backend Developer", "seniority": "junior", "domain": "",
    "must_have": ["Python", "Django", "PostgreSQL", "Docker", "Terraform"],
    "good_to_have": ["Kafka"], "implied": [], "soft_skills": [], "duties": ["Build REST API services"],
}

CANDIDATE = {
    "summary": "Computer science graduate who builds web backends.",
    "skills": {"Languages": "Python, SQL", "Frameworks": "Django"},
    "projects": [
        {"title": "Notes App", "role": "Creator", "tech_stack": "HTML, CSS",
         "bullets": ["Made a notes page with HTML and CSS."]},
        {"title": "Order API", "role": "Creator", "tech_stack": "Python, Django, MySQL",
         "bullets": ["Made an order API with Django and MySQL for 3 client apps."]},
    ],
    "experience": [
        {"company": "Acme", "role": "Intern", "period": "2024",
         "bullets": ["Worked on Python scripts for report generation."]},
    ],
}


def fake_model(fit):
    """Answers the blueprint call, then the fit call."""
    return patch.object(ai_engine, "call_groq_chat", side_effect=[json.dumps(BLUEPRINT), json.dumps(fit)])


class PromptMessageTests(SimpleTestCase):
    def test_messages_carry_the_inputs_as_json(self):
        blueprint_msgs = build_blueprint_messages(JD, "Backend Developer", "Acme", ["Python", " "])
        self.assertEqual(json.loads(blueprint_msgs[1]["content"])["job_skills"], "Python")
        fit_msgs = build_fit_messages(BLUEPRINT, CANDIDATE, ["Docker", ""])
        payload = json.loads(fit_msgs[1]["content"])
        self.assertEqual(payload["confirmed_skills"], ["Docker"])
        self.assertEqual(payload["blueprint"]["target_title"], "Backend Developer")


class BlueprintTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_terms_the_posting_never_mentions_are_dropped_and_result_is_cached(self):
        with patch.object(ai_engine, "call_groq_chat", return_value=json.dumps(BLUEPRINT)) as model:
            first = ai_engine.reverse_engineer_job(JD, "Backend Developer")
            second = ai_engine.reverse_engineer_job(JD, "Backend Developer")
        self.assertEqual(model.call_count, 1)
        self.assertEqual(first, second)
        self.assertNotIn("Terraform", first["must_have"])
        self.assertEqual(first["must_have"], ["Python", "Django", "PostgreSQL", "Docker"])
        self.assertEqual(first["good_to_have"], ["Kafka"])

    def test_model_failure_falls_back_to_listed_skills(self):
        with patch.object(ai_engine, "call_groq_chat", side_effect=RuntimeError("down")):
            blueprint = ai_engine.reverse_engineer_job(JD, "Backend Developer", job_skills="Python, Django")
        self.assertIs(blueprint["ai"], False)
        self.assertEqual(blueprint["must_have"], ["Python", "Django"])

    def test_coverage_weighs_must_haves_and_never_rounds_up(self):
        blueprint = {"must_have": ["Python", "Docker"], "good_to_have": ["Search Engine Optimization (SEO)"]}
        coverage = ai_engine.blueprint_coverage(blueprint, "Python developer who did SEO work with JavaScript")
        self.assertEqual(coverage["must_have_missing"], ["Docker"])
        self.assertEqual(coverage["good_to_have_found"], ["Search Engine Optimization (SEO)"])
        self.assertEqual(coverage["score"], 57)

    def test_a_skill_written_without_its_space_still_counts(self):
        coverage = ai_engine.blueprint_coverage({"must_have": ["Power BI", "Node JS"]}, "Built PowerBI dashboards")
        self.assertEqual(coverage["must_have_found"], ["Power BI"])


class FitResumeTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_reworded_bullets_are_kept_and_invented_ones_are_not(self):
        fit = {
            "altered_summary": "Computer science graduate targeting a Backend Developer role, building Python and Django web backends.",
            "altered_skills": {"Languages": "Python, SQL", "Frameworks": "Django", "DevOps": "Docker, Kafka"},
            "altered_projects": [
                {"title": "Order API", "tech_stack": "Python, Django, PostgreSQL, Docker", "bullets": [
                    "Built an order API with Django and MySQL serving 3 client apps.",
                    "Deployed the service with Docker, cutting latency by 40%.",
                    "Tuned PostgreSQL indexes for the order tables in the service.",
                ]},
                {"title": "Payment Gateway", "bullets": ["Built a payment gateway handling card transactions."]},
            ],
            "altered_experience": [
                {"company": "Acme", "role": "Senior Engineer", "period": "2020-2024",
                 "bullets": ["Led a team as a senior engineer with 5 years of Python work."]},
            ],
            "section_order": ["Summary", "Skills", "Projects", "Hobbies"],
            "skills_to_confirm": [{"skill": "Docker", "question": "Have you containerised an app with Docker?"}],
        }
        with fake_model(fit):
            result = ai_engine.fit_resume_to_job(JD, CANDIDATE, job_title="Backend Developer")

        self.assertIs(result["ai"], True)
        self.assertIs(result["changed"], True)
        self.assertIn("Backend Developer", result["altered_summary"])

        # The relevant project now leads, with identity fields copied from the candidate.
        order_api, notes = result["altered_projects"]
        self.assertEqual(order_api["title"], "Order API")
        self.assertEqual(order_api["tech_stack"], "Python, Django, MySQL")
        self.assertEqual(order_api["bullets"], ["Built an order API with Django and MySQL serving 3 client apps."])
        self.assertEqual(notes, CANDIDATE["projects"][0])
        self.assertEqual(len(result["altered_projects"]), 2)

        # An invented role, dates and seniority leave the candidate's entry untouched.
        self.assertEqual(result["altered_experience"], CANDIDATE["experience"])

        skills_text = json.dumps(result["altered_skills"])
        self.assertNotIn("Docker", skills_text)
        self.assertNotIn("Kafka", skills_text)
        for skill in ("Python", "SQL", "Django"):
            self.assertIn(skill, skills_text)

        self.assertEqual(result["section_order"], ["Summary", "Skills", "Projects"])
        self.assertEqual(result["missing_keywords"], ["PostgreSQL", "Docker", "Kafka"])
        self.assertEqual(result["match_score"], 46)
        self.assertEqual(result["match_score"], result["match_score_before"])
        docker = next(row for row in result["skills_to_confirm"] if row["skill"] == "Docker")
        self.assertEqual(docker["question"], "Have you containerised an app with Docker?")
        self.assertEqual(docker["priority"], "must_have")
        self.assertNotIn("40%", json.dumps(result))

    def test_a_fact_from_another_project_is_not_moved_into_this_one(self):
        fit = {"altered_projects": [{"title": "Notes App", "bullets": [
            "Built a notes page with Django and MySQL serving 3 client apps.",
            "Built a notes page with HTML and CSS for personal use.",
        ]}]}
        with fake_model(fit):
            result = ai_engine.fit_resume_to_job(JD, CANDIDATE, job_title="Backend Developer")
        notes = next(p for p in result["altered_projects"] if p["title"] == "Notes App")
        self.assertEqual(notes["bullets"], ["Built a notes page with HTML and CSS for personal use."])

    def test_a_confirmed_skill_is_added_and_raises_the_score(self):
        fit = {"altered_skills": {"Languages": "Python, SQL", "Frameworks": "Django", "DevOps": "Docker"}}
        with fake_model(fit):
            result = ai_engine.fit_resume_to_job(
                JD, CANDIDATE, job_title="Backend Developer", confirmed_skills=["Docker"])
        self.assertIn("Docker", json.dumps(result["altered_skills"]))
        self.assertGreater(result["match_score"], result["match_score_before"])
        self.assertNotIn("Docker", [row["skill"] for row in result["skills_to_confirm"]])

    def test_a_summary_that_adds_claims_is_replaced_by_the_candidates_own(self):
        fit = {"altered_summary": "Seasoned Backend Developer with 5 years of Docker experience."}
        with fake_model(fit):
            result = ai_engine.fit_resume_to_job(JD, CANDIDATE, job_title="Backend Developer")
        self.assertEqual(result["altered_summary"], CANDIDATE["summary"])

    def test_model_failure_returns_the_resume_as_supplied(self):
        with patch.object(ai_engine, "call_groq_chat", side_effect=RuntimeError("down")):
            result = ai_engine.fit_resume_to_job(JD, CANDIDATE, job_title="Backend Developer")
        self.assertIs(result["ai"], False)
        self.assertEqual(result["altered_projects"], CANDIDATE["projects"])
        self.assertEqual(result["altered_summary"], CANDIDATE["summary"])
        self.assertIsNotNone(result["match_score"])


class AtsReadabilityTests(SimpleTestCase):
    """The exported files are read back the way an ATS reads them."""

    RESUME = {
        "name": "Asha Rao",
        "contact": {"email": "asha@example.com", "phone": "9876543210"},
        "summary": "Computer science graduate targeting a Backend Developer role.",
        "skills": {"Languages": "Python, SQL", "Frameworks": "Django"},
        "experience": [{"company": "Acme", "role": "Intern", "period": "2024",
                        "bullets": ["Wrote Python scripts for report generation."]}],
        "projects": [{"title": "Order API", "role": "Creator", "tech_stack": "Python, Django, MySQL",
                      "bullets": ["Built an order API with Django and MySQL serving 3 client apps."]}],
        "education": {"degree": "B.Tech", "institution": "XYZ College", "year": "2025"},
    }
    KEYWORDS = ["Python", "Django", "SQL", "MySQL"]

    def test_exported_pdf_and_docx_keep_every_field_and_keyword(self):
        from requirements.resume_docx import generate_ats_resume_docx
        from requirements.resume_parser import check_ats_readability
        from requirements.resume_pdf import generate_ats_resume_pdf

        for filename, content in (
            ("resume.pdf", generate_ats_resume_pdf(self.RESUME)),
            ("resume.docx", generate_ats_resume_docx(self.RESUME)),
        ):
            report = check_ats_readability(content, filename, self.RESUME, self.KEYWORDS)
            self.assertTrue(report["readable"], (filename, report))
            self.assertEqual(report["keywords_lost"], [])

    def test_a_keyword_missing_from_the_file_is_reported(self):
        from requirements.resume_parser import check_ats_readability
        from requirements.resume_pdf import generate_ats_resume_pdf

        report = check_ats_readability(generate_ats_resume_pdf(self.RESUME), "resume.pdf", self.RESUME, ["Kafka"])
        self.assertFalse(report["readable"])
        self.assertEqual(report["keywords_lost"], ["Kafka"])


class FitResumeEndpointTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_endpoint_reports_real_coverage_and_asks_about_gaps(self):
        fit = {"altered_projects": [{"title": "Order API", "bullets": [
            "Built an order API with Django and MySQL serving 3 client apps.",
            "Shipped it on Docker to 50,000 users.",
        ]}]}
        with fake_model(fit):
            response = self.client.post(
                "/api/ai/fit-resume/",
                json.dumps({"job_title": "Backend Developer", "job_description": JD, "candidate": CANDIDATE}),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["match_score"], 46)
        self.assertEqual(data["match_grade"], "2 of 5 job keywords found")
        self.assertIn("Docker", [row["skill"] for row in data["skills_to_confirm"]])
        self.assertNotIn("50,000", response.content.decode())

    def test_endpoint_needs_a_job(self):
        response = self.client.post(
            "/api/ai/fit-resume/", json.dumps({"candidate": CANDIDATE}), content_type="application/json")
        self.assertEqual(response.status_code, 400)


class TimeBudgetTests(SimpleTestCase):
    """A bad minute at the AI providers must end quickly, not hang the page."""

    def test_backup_provider_is_skipped_when_the_budget_is_spent(self):
        with patch.object(ai_engine, "get_groq_api_key", return_value="k"), \
                patch.object(ai_engine, "get_nvidia_api_key", return_value="k"), \
                patch.object(ai_engine, "_call_groq_chat", side_effect=RuntimeError("429")), \
                patch.object(ai_engine, "_call_nvidia_chat") as backup:
            with self.assertRaises(RuntimeError):
                ai_engine.call_groq_chat([], budget=1)
        backup.assert_not_called()

    def test_backup_provider_gets_only_the_time_that_is_left(self):
        with patch.object(ai_engine, "get_groq_api_key", return_value="k"), \
                patch.object(ai_engine, "get_nvidia_api_key", return_value="k"), \
                patch.object(ai_engine, "_call_groq_chat", side_effect=RuntimeError("429")), \
                patch.object(ai_engine, "_call_nvidia_chat", return_value="{}") as backup:
            self.assertEqual(ai_engine.call_groq_chat([], budget=10), "{}")
        self.assertLessEqual(backup.call_args.kwargs["timeout"], 10)

    def test_fitting_skips_the_rewrite_when_the_blueprint_used_the_time(self):
        cache.clear()
        with patch.object(ai_engine, "FIT_TIME_BUDGET", 0), \
                patch.object(ai_engine, "call_groq_chat", return_value=json.dumps(BLUEPRINT)) as model:
            result = ai_engine.fit_resume_to_job(JD, CANDIDATE, job_title="Backend Developer")
        self.assertEqual(model.call_count, 1)
        self.assertIs(result["ai"], False)
        self.assertEqual(result["altered_projects"], CANDIDATE["projects"])
        self.assertTrue(result["skills_to_confirm"])


class SkillEvidenceAndTitleTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_a_skill_can_be_written_into_the_project_the_candidate_names(self):
        fit = {"altered_projects": [
            {"title": "Order API", "bullets": ["Built an order API with Django and MySQL, packaged with Docker."]},
            {"title": "Notes App", "bullets": ["Built a notes page with HTML and CSS, packaged with Docker."]},
        ]}
        with fake_model(fit):
            result = ai_engine.fit_resume_to_job(
                JD, CANDIDATE, job_title="Backend Developer",
                confirmed_skills=["Docker"], skill_evidence={"Docker": "Order API", "Kafka": "Order API"})
        order_api = next(p for p in result["altered_projects"] if p["title"] == "Order API")
        notes = next(p for p in result["altered_projects"] if p["title"] == "Notes App")
        self.assertEqual(order_api["tech_stack"], "Python, Django, MySQL, Docker")
        self.assertEqual(order_api["bullets"], ["Built an order API with Django and MySQL, packaged with Docker."])
        # Docker was not claimed for the other project, and Kafka was never confirmed.
        self.assertEqual(notes["bullets"], CANDIDATE["projects"][0]["bullets"])
        self.assertNotIn("Kafka", json.dumps(result["altered_projects"]))

    def test_evidence_on_a_job_reaches_the_model_but_not_the_resume(self):
        fit = {"altered_experience": [{"company": "Acme", "role": "Intern", "bullets": [
            "Wrote Python scripts for report generation, run in Docker containers."]}]}
        with fake_model(fit):
            result = ai_engine.fit_resume_to_job(
                JD, CANDIDATE, job_title="Backend Developer",
                confirmed_skills=["Docker"], skill_evidence={"Docker": "Intern at Acme"})
        entry = result["altered_experience"][0]
        self.assertEqual(entry["bullets"], ["Wrote Python scripts for report generation, run in Docker containers."])
        self.assertNotIn("tools_used", entry)

    def test_a_summary_may_aim_at_a_title_but_not_claim_it(self):
        source = json.dumps(CANDIDATE)
        claims = ai_engine._claims_unheld_title
        self.assertTrue(claims("Backend Developer skilled in Python and Django.", "Backend Developer", source))
        self.assertTrue(claims("Detail-oriented Backend Developer with Django projects.", "Backend Developer", source))
        self.assertFalse(claims("Graduate targeting a Backend Developer role with Python.", "Backend Developer", source))
        self.assertFalse(claims("Graduate seeking a junior Backend Developer position.", "Backend Developer", source))
        self.assertFalse(claims("Intern with Python scripting work.", "Intern", source))

    def test_a_summary_claiming_the_title_is_not_used(self):
        fit = {"altered_summary": "Backend Developer skilled in Python and Django web backends."}
        with fake_model(fit):
            result = ai_engine.fit_resume_to_job(JD, CANDIDATE, job_title="Backend Developer")
        self.assertEqual(result["altered_summary"], CANDIDATE["summary"])
        self.assertIs(result["changed"], False)


class DownloadReadabilityTests(SimpleTestCase):
    def test_downloads_report_the_read_back_check(self):
        resume = dict(AtsReadabilityTests.RESUME)
        for url in ("/api/resume/download-pdf/", "/api/resume/download-docx/"):
            response = self.client.post(url, json.dumps({"resume": resume}), content_type="application/json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["X-ATS-Readable"], "yes", url)
            passed, total = response["X-ATS-Checks"].split("/")
            self.assertEqual(passed, total)


class HonestEvaluatorTests(SimpleTestCase):
    """The ATS score treats every role alike and never claims a pass."""

    MARKETER = {
        "name": "Riya", "contact": {"email": "riya@example.com", "phone": "9876543210",
                                    "linkedin": "linkedin.com/in/riya"},
        "summary": "BBA graduate who ran social media and wrote content for a college fest of 3000 visitors.",
        "skills": {"Skills": "SEO, Canva, Instagram, Content Writing, Google Analytics, Excel, Copywriting, Email Marketing"},
        "experience": [{"company": "College Fest Committee", "role": "Social Media Head", "period": "2024", "bullets": [
            "Grew the Instagram page from 400 to 2100 followers in 3 months.",
            "Wrote 12 blog posts using SEO keyword research for the fest website.",
            "Designed 40 posters in Canva for the fest campaign.",
            "Tracked campaign traffic in Google Analytics and reported it weekly in Excel.",
        ]}],
        "education": {"degree": "BBA", "institution": "ABC University", "year": "2025"},
    }

    def test_a_non_tech_resume_is_not_marked_down_for_lacking_tech_words(self):
        from requirements.resume_parser import evaluate_uploaded_resume_ats
        result = evaluate_uploaded_resume_ats(self.MARKETER)
        pillars = {p["id"]: p for p in result["pillars"]}
        self.assertEqual(pillars["tech_skills"]["score"], 16)
        self.assertGreaterEqual(pillars["architecture_depth"]["score"], 6)
        self.assertGreaterEqual(result["score"], 75)

    def test_grades_never_claim_an_ats_pass(self):
        from requirements.resume_parser import evaluate_uploaded_resume_ats
        for resume in (self.MARKETER, {"summary": "x"}):
            grade = evaluate_uploaded_resume_ats(resume)["grade"]
            self.assertNotIn("Pass", grade)
            self.assertNotIn("ATS", grade)

    def test_skills_only_in_the_list_are_flagged(self):
        from requirements.resume_parser import evaluate_uploaded_resume_ats
        resume = dict(self.MARKETER, skills={"Skills": "Kafka, Docker, Kubernetes, Terraform"})
        result = evaluate_uploaded_resume_ats(resume)
        shown = next(p for p in result["pillars"] if p["id"] == "architecture_depth")
        self.assertEqual(shown["score"], 0)
        self.assertTrue(any("Mention where you used" in tip for tip in result["improvements"]))

    def test_a_job_with_a_blueprint_is_scored_by_it(self):
        from requirements.models import JobPosting
        job = JobPosting(skills_required="Python, Django",
                         ats_blueprint={"must_have": ["Python", "Power BI"], "good_to_have": ["Jira"]})
        self.assertEqual(job.ats_target_skills(), ["Python", "Power BI", "Jira"])
        self.assertEqual(JobPosting(skills_required="Python, Django").ats_target_skills(), ["Python", "Django"])


class NoFakeContactTests(SimpleTestCase):
    def test_missing_contact_details_are_not_filled_in_before_scoring(self):
        resume = dict(HonestEvaluatorTests.MARKETER, contact={})
        response = self.client.post(
            "/api/resume/evaluate/",
            json.dumps({"resume": resume, "job_skills": ["SEO", "Canva"]}),
            content_type="application/json",
        )
        contact = next(p for p in response.json()["pillars"] if p["id"] == "contact_header")
        self.assertEqual(contact["score"], 0)
        self.assertNotIn("example.com", response.content.decode())
