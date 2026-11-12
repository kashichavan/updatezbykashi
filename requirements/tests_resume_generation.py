import json
import uuid
from unittest.mock import patch
from django.test import TestCase, Client
from requirements.models import Category, JobPosting, ResumeGenerationJob, DiscoveredProject
from requirements.resume_generation_service import finalize_resume_synthesis

class ResumeGenerationPipelineTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Engineering", slug="engineering")
        self.job = JobPosting.objects.create(
            title="Junior Python Engineer",
            company_name="Acme Corp",
            category=self.category,
            skills_required="Python, Django, PostgreSQL, Docker",
            description="We are seeking a junior python developer proficient with Django and relational databases."
        )

    def test_resume_generation_job_model(self):
        job = ResumeGenerationJob.objects.create(
            job=self.job,
            mode='FRESHER_GITHUB',
            candidate_data={"name": "Alice Tester", "skills": "Python, Django"},
            status='PENDING'
        )
        self.assertIsNotNone(job.uuid)
        self.assertEqual(job.status, 'PENDING')
        self.assertEqual(job.progress_pct, 0)

        dp = DiscoveredProject.objects.create(
            generation_job=job,
            repo_name="acme/api-starter",
            repo_url="https://github.com/acme/api-starter",
            description="Sample starter project",
            stars=42,
            language="Python",
            tech_stack=["Python", "Django"],
            relevance_score=88.5,
            candidate_relationship="RECOMMENDED",
            is_selected=True
        )
        self.assertEqual(job.discovered_projects.count(), 1)
        self.assertEqual(dp.candidate_relationship, "RECOMMENDED")

    def test_finalize_resume_synthesis(self):
        gen_job = ResumeGenerationJob.objects.create(
            job=self.job,
            mode='FRESHER_GITHUB',
            candidate_data={
                "name": "Jane Developer",
                "email": "jane@example.com",
                "phone": "+91 91234 56789",
                "location": "Bengaluru",
                "degree": "B.Tech in Computer Science",
                "institution": "VTU Engineering",
                "gpa": "8.7 / 10.0",
                "skills": ["Python", "Django", "PostgreSQL", "Docker"]
            },
            status='AWAITING_SELECTION'
        )

        DiscoveredProject.objects.create(
            generation_job=gen_job,
            repo_name="jane/django-task-manager",
            repo_url="https://github.com/jane/django-task-manager",
            description="Scalable task management platform",
            stars=15,
            language="Python",
            tech_stack=["Python", "Django", "PostgreSQL"],
            relevance_score=91.0,
            candidate_relationship="BUILT",
            is_selected=True
        )

        result = finalize_resume_synthesis(str(gen_job.uuid))
        gen_job.refresh_from_db()

        self.assertEqual(gen_job.status, 'COMPLETED')
        self.assertEqual(gen_job.progress_pct, 100)
        self.assertIn("resume", result)
        self.assertIn("ats_eval", result)
        
        resume = result["resume"]
        self.assertEqual(resume["name"], "Jane Developer")
        self.assertTrue(len(resume["projects"]) >= 1)
        self.assertIn("Personally Developed", resume["projects"][0]["title"])
        self.assertIn("ats_score", resume["projects"][0])

    @patch('requirements.resume_generation_service.start_generation_pipeline_async')
    def test_api_resume_generation_create(self, mock_async):
        payload = {
            "mode": "FRESHER_GITHUB",
            "job_id": str(self.job.uuid),
            "candidate_data": {
                "name": "Bob Fresher",
                "degree": "B.Tech CSE"
            }
        }
        res = self.client.post(
            "/api/resume/generations/",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("job_id", data)
        mock_async.assert_called_once()

        # Test status polling
        job_id = data["job_id"]
        status_res = self.client.get(f"/api/resume/generations/{job_id}/")
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.json()
        self.assertTrue(status_data["success"])
        self.assertIn("status", status_data)

    def test_api_resume_github_discovery_direct(self):
        res = self.client.get(
            f"/api/resume/github-discovery/?job_skills=Python,Django&job_title=Python+Engineer"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertTrue(len(data["projects"]) >= 1)


class ResumeStudioStandaloneTests(TestCase):
    """
    /resume-studio/ builds a resume without requiring a JobPosting.

    The point of the page is that resume creation is not a sub-feature of one job
    detail page, so the no-job path is the one that matters most here.
    """

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Engineering", slug="engineering")
        self.job = JobPosting.objects.create(
            title="Backend Engineer",
            company_name="Acme Corp",
            category=self.category,
            skills_required="Python, Django, PostgreSQL",
            description="Build and operate backend services.",
            status='ACTIVE',
        )

    def test_studio_page_renders_without_a_job(self):
        res = self.client.get('/resume-studio/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode()
        self.assertIn('rs-page', html)
        self.assertIn('Type it myself', html)
        self.assertIsNone(res.context['target_job'])
        self.assertEqual(res.context['skills_list'], [])
        # The picker offers active postings, the page still works without one.
        self.assertIn(self.job, res.context['recent_jobs'])

    def test_studio_page_prefills_target_from_job_id(self):
        res = self.client.get(f'/resume-studio/?job_id={self.job.uuid}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['target_job'], self.job)
        self.assertEqual(res.context['skills_list'], ['Python', 'Django', 'PostgreSQL'])
        self.assertIn(str(self.job.uuid), res.context['studio_editor_url'])
        html = res.content.decode()
        # The target is locked to the posting instead of showing the whole picker.
        self.assertIn('id="rsTargetLock"', html)
        self.assertIn('TARGET LOCKED', html)

    def test_studio_page_without_a_job_shows_the_picker(self):
        res = self.client.get('/resume-studio/')
        html = res.content.decode()
        self.assertNotIn('id="rsTargetLock"', html)
        self.assertIn('id="rsTargetPickerWrap"', html)

    def test_studio_page_ignores_a_malformed_job_id(self):
        res = self.client.get('/resume-studio/?job_id=not-a-uuid')
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.context['target_job'])

    def test_named_route_for_job_resolves_to_the_same_view(self):
        from django.urls import reverse
        res = self.client.get(reverse('resume_studio_for_job', args=[self.job.uuid]))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['target_job'], self.job)

    def test_target_profile_is_persisted_when_no_job_is_given(self):
        payload = {
            "mode": "FRESHER_GITHUB",
            "candidate_data": {"name": "Ada Lovelace", "email": "ada@example.com"},
            "target_profile": {
                "title": "Backend Engineer",
                "company": "",
                "skills": "Python, SQL",
                "description": "APIs and data pipelines",
            },
        }
        with patch('requirements.resume_generation_service.start_generation_pipeline_async'):
            res = self.client.post(
                '/api/resume/generations/',
                data=json.dumps(payload),
                content_type='application/json',
            )
        self.assertEqual(res.status_code, 201)
        gen = ResumeGenerationJob.objects.get(uuid=res.json()['job_id'])
        self.assertIsNone(gen.job)
        self.assertEqual(gen.target_profile['title'], 'Backend Engineer')
        self.assertEqual(gen.target_profile['skills'], 'Python, SQL')

    def test_resolve_target_profile_prefers_the_posting(self):
        from requirements.resume_generation_service import resolve_target_profile
        gen = ResumeGenerationJob.objects.create(
            job=self.job,
            mode='FRESHER_GITHUB',
            target_profile={'title': 'Ignored', 'skills': 'Rust'},
        )
        target = resolve_target_profile(gen)
        self.assertEqual(target['title'], 'Backend Engineer')
        self.assertEqual(target['company'], 'Acme Corp')
        self.assertEqual(target['skills_list'], ['Python', 'Django', 'PostgreSQL'])
        self.assertTrue(target['has_posting'])

    def test_resolve_target_profile_reads_the_free_form_target(self):
        from requirements.resume_generation_service import resolve_target_profile
        gen = ResumeGenerationJob.objects.create(
            mode='FRESHER_GITHUB',
            target_profile={
                'title': 'Data Engineer',
                'company': '',
                'skills': ['Python', 'Airflow'],
                'description': 'Own the warehouse',
            },
        )
        target = resolve_target_profile(gen)
        self.assertIsNone(gen.job)
        self.assertEqual(target['title'], 'Data Engineer')
        self.assertEqual(target['company'], '')
        self.assertEqual(target['skills_list'], ['Python', 'Airflow'])
        self.assertFalse(target['has_posting'])


class ResumeStudioSynthesisWithoutJobTests(TestCase):
    """Synthesis must not depend on job.job existing."""

    def setUp(self):
        self.gen = ResumeGenerationJob.objects.create(
            mode='FRESHER_GITHUB',
            candidate_data={
                'name': 'Grace Hopper',
                'email': 'grace@example.com',
                'phone': '+1 555 0100',
                'skills': 'Python, SQL',
            },
            target_profile={
                'title': 'Platform Engineer',
                'company': '',
                'skills': 'Python, Kubernetes',
            },
            status='AWAITING_SELECTION',
        )
        DiscoveredProject.objects.create(
            generation_job=self.gen,
            repo_name='grace/compiler',
            repo_url='https://github.com/grace/compiler',
            description='A small compiler',
            stars=3,
            language='Python',
            tech_stack=['Python'],
            relevance_score=80.0,
            candidate_relationship='BUILT',
            is_selected=True,
        )

    def test_synthesis_uses_the_free_form_target(self):
        result = finalize_resume_synthesis(str(self.gen.uuid))
        self.gen.refresh_from_db()
        self.assertEqual(self.gen.status, 'COMPLETED')
        resume = result['resume']
        self.assertEqual(resume['name'], 'Grace Hopper')
        self.assertIn('Platform Engineer', resume['summary'])
        # No company was supplied, so the summary must not say "at None"/"at ".
        self.assertNotIn('at None', resume['summary'])
        self.assertNotIn('role at .', resume['summary'])
        self.assertIn('ats_eval', result)


class ProjectBulletHonestyTests(TestCase):
    """
    Recruiters ask about numbers on a resume. Every metric on a generated project
    must be traceable to the repository metadata it came from.
    """

    def setUp(self):
        self.category = Category.objects.create(name="Engineering", slug="eng-honest")
        self.gen = ResumeGenerationJob.objects.create(
            mode='FRESHER_GITHUB',
            candidate_data={'name': 'Test Person', 'email': 't@example.com', 'phone': '+1 555 0000'},
            target_profile={'title': 'Backend Engineer', 'skills': 'Python'},
        )
        self.dp = DiscoveredProject.objects.create(
            generation_job=self.gen,
            repo_name='ansible/awx',
            repo_url='https://github.com/ansible/awx',
            description='AWX provides a web-based interface for Ansible.',
            stars=14000,
            language='Python',
            tech_stack=['Python', 'Django'],
            relevance_score=70.0,
            candidate_relationship='RECOMMENDED',
            is_selected=True,
        )

    def test_invented_metrics_are_dropped(self):
        from requirements.resume_generation_service import sanitize_project_bullets
        bullets = [
            'Architected a task engine reducing job latency by 40% for 5,000 users.',
            'Studied the Django models that back the Ansible job templates.',
        ]
        kept = sanitize_project_bullets(bullets, self.dp)
        self.assertEqual(kept, ['Studied the Django models that back the Ansible job templates.'])

    def test_numbers_present_in_the_repository_are_kept(self):
        from requirements.resume_generation_service import sanitize_project_bullets
        # 14000 stars is part of the metadata, so this number is not invented.
        kept = sanitize_project_bullets(['A 14000-star project used to drive Ansible runs.'], self.dp)
        self.assertEqual(len(kept), 1)

    def test_puffery_is_dropped(self):
        from requirements.resume_generation_service import sanitize_project_bullets
        kept = sanitize_project_bullets(
            ['Built an enterprise, production-grade automation platform.', 'Read the job launch code path.'],
            self.dp,
        )
        self.assertEqual(kept, ['Read the job launch code path.'])

    def test_title_must_still_name_the_repository(self):
        from requirements.resume_generation_service import honest_project_title
        self.assertEqual(
            honest_project_title('Enterprise Automation Orchestration Platform', self.dp),
            'Awx',
        )
        self.assertEqual(honest_project_title('AWX job runner internals', self.dp), 'AWX job runner internals')

    def test_synthesis_falls_back_to_metadata_when_every_bullet_is_fabricated(self):
        invention = {
            'title': 'Enterprise Ansible Orchestration Platform',
            'bullets': [
                'Architected a scalable engine cutting latency by 40%.',
                'Engineered a robust pipeline serving 12,000 req/sec.',
            ],
        }
        with patch('requirements.resume_generation_service.generate_github_project_bullets', return_value=invention):
            result = finalize_resume_synthesis(str(self.gen.uuid))

        project = result['resume']['projects'][0]
        joined = ' '.join(project['bullets'])
        self.assertNotIn('40%', joined)
        self.assertNotIn('12,000', joined)
        self.assertIn('AWX provides a web-based interface for Ansible', joined)
        self.assertIn('[Architecture & Case Study]', project['title'])
        self.assertNotIn('Enterprise', project['title'])

    def test_a_string_of_bullets_is_split_not_iterated_as_characters(self):
        from requirements.resume_generation_service import sanitize_project_bullets
        kept = sanitize_project_bullets(
            'Studied the job lifecycle code. Read the Django model layer.',
            self.dp,
        )
        self.assertEqual(len(kept), 2)
        self.assertTrue(all(len(b) > 20 for b in kept))


class AlteredResumeHonestyTests(TestCase):
    """
    /api/ai/alter-resume/ is the address older copies of the resume page call.
    It now runs the same fitting engine as /api/ai/fit-resume/: the candidate's
    own facts reworded, nothing added, and a score that is measured.
    """

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.client = Client()
        self.projects = [{
            'title': 'Order service',
            'role': 'Backend',
            'tech_stack': 'Python, Redis',
            'bullets': ['Cut p95 latency from 185ms to 24ms with Redis caching.'],
        }]

    def _post(self, model_reply, **extra):
        body = {
            'job_title': 'Backend Engineer',
            'job_skills': 'Python, Redis, Docker, Kafka',
            'candidate_summary': 'Backend engineer.',
            'candidate_skills': {'Languages': 'Python'},
            'candidate_projects': self.projects,
        }
        body.update(extra)
        with patch('requirements.ai_engine.call_groq_chat', return_value=json.dumps(model_reply)):
            return self.client.post('/api/ai/alter-resume/', data=json.dumps(body), content_type='application/json')

    def test_the_candidates_own_metric_is_kept_and_an_invented_one_is_dropped(self):
        res = self._post({
            'altered_summary': 'Backend engineer working with Python.',
            'altered_projects': [{'title': 'Order service', 'tech_stack': 'Python, Redis, Docker, PostgreSQL', 'bullets': [
                'Cut checkout latency by 40% with Redis caching.',
                'Reduced p95 latency from 185ms to 24ms by adding Redis caching.',
            ]}],
            'overall_match_score': 95,
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()['data']
        project = data['altered_projects'][0]
        self.assertEqual(project['bullets'], ['Reduced p95 latency from 185ms to 24ms by adding Redis caching.'])
        self.assertEqual(project['tech_stack'], 'Python, Redis')
        # Two of the four skills the job lists are on the resume, so the score says so.
        self.assertEqual(data['match_score'], 50)
        self.assertEqual(data['match_grade'], '2 of 4 job keywords found')
        self.assertEqual(data['missing_keywords'], ['Docker', 'Kafka'])
        self.assertNotIn('40%', res.content.decode())

    def test_invented_seniority_and_skills_are_removed(self):
        data = self._post({
            'altered_summary': 'Senior backend engineer with 5+ years of experience.',
            'altered_skills': {'Backend': 'Docker, Python'},
        }).json()['data']
        self.assertEqual(data['altered_summary'], 'Backend engineer.')
        self.assertNotIn('Docker', json.dumps(data['altered_skills']))
        self.assertIn('Python', json.dumps(data['altered_skills']))
        self.assertEqual(data['suggested_skills'], data['altered_skills'])

    def test_project_with_empty_bullets_keeps_the_original(self):
        data = self._post({
            'altered_summary': 'Backend engineer.',
            'altered_projects': [{'title': 'Order service', 'bullets': ['', '   ']}],
        }).json()['data']
        self.assertEqual(data['altered_projects'], self.projects)

    def test_a_named_posting_supplies_the_job_and_keeps_its_blueprint(self):
        """
        The browser may hold a shortened copy, and a caller could send anything.
        When `job_id` is present, tailoring uses the posting itself, and what the
        posting searches for is stored on it for the next visitor.
        """
        category = Category.objects.create(name="Telephony", slug="telephony")
        posting = JobPosting.objects.create(
            title="VoIP Developer",
            company_name="Talent Corner",
            category=category,
            skills_required="FreeSWITCH, SIP, Linux",
            description="Operate FreeSWITCH and Asterisk telephony systems on Linux.",
            status='ACTIVE',
        )
        blueprint = {'target_title': 'VoIP Developer', 'must_have': ['FreeSWITCH', 'Asterisk', 'Kubernetes'],
                     'good_to_have': [], 'implied': [], 'soft_skills': [], 'duties': []}
        res = self._post(
            blueprint, job_id=str(posting.uuid), job_title='Wrong title',
            job_skills='WrongSkill', job_description='A different, unrelated role.',
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()['data']
        self.assertEqual(data['blueprint']['target_title'], 'VoIP Developer')
        # Asterisk is in the posting, Kubernetes is not; the listed skills are always required.
        self.assertEqual(data['blueprint']['must_have'], ['FreeSWITCH', 'Asterisk', 'SIP', 'Linux'])
        self.assertNotIn('WrongSkill', json.dumps(data))
        posting.refresh_from_db()
        self.assertEqual(posting.ats_blueprint['must_have'], ['FreeSWITCH', 'Asterisk', 'SIP', 'Linux'])

        # The next visitor reuses the stored blueprint without another model call.
        from django.core.cache import cache
        cache.clear()
        with patch('requirements.ai_engine.call_groq_chat', side_effect=RuntimeError('busy')) as model:
            again = self.client.post(
                '/api/ai/fit-resume/',
                data=json.dumps({'job_id': str(posting.uuid), 'candidate': {'skills': {'Tools': 'Linux'}}}),
                content_type='application/json',
            ).json()['data']
        self.assertEqual(again['blueprint']['must_have'], ['FreeSWITCH', 'Asterisk', 'SIP', 'Linux'])
        self.assertEqual(again['matching_keywords'], ['Linux'])
        model.assert_not_called()

    def test_a_role_name_alone_improves_wording_without_a_score(self):
        res = self._post(
            {'altered_projects': [{'title': 'Order service', 'bullets': [
                'Reduced p95 latency from 185ms to 24ms by adding Redis caching.']}]},
            job_skills='', job_title='Backend Engineer',
        )
        data = res.json()['data']
        self.assertIsNone(data['match_score'])
        self.assertEqual(data['skills_to_confirm'], [])
        self.assertEqual(
            data['altered_projects'][0]['bullets'],
            ['Reduced p95 latency from 185ms to 24ms by adding Redis caching.'])


class RewriteHonestyTests(TestCase):
    """Polish and tailor endpoints may reword the candidate's text, not extend it."""

    def setUp(self):
        self.client = Client()

    def test_polish_drops_variants_with_new_numbers(self):
        fake = {
            'original': 'Worked on testing APIs with Postman.',
            'polished': 'Tested 120 API endpoints with Postman, cutting regression bugs by 40%.',
            'alternative_1': 'Tested APIs with Postman before release.',
            'alternative_2': 'Built a Postman collection covering 45 endpoints.',
            'action_verb': 'Tested',
            'metric_highlight': '40% bug reduction',
        }
        with patch('requirements.ai_engine.polish_resume_bullet', return_value=fake):
            res = self.client.post(
                '/api/ai/polish-bullet/',
                data=json.dumps({'bullet': 'Worked on testing APIs with Postman.'}),
                content_type='application/json',
            )
        data = res.json()['data']
        self.assertEqual(data['polished'], '')
        self.assertEqual(data['alternative_1'], 'Tested APIs with Postman before release.')
        self.assertEqual(data['alternative_2'], '')
        self.assertEqual(data['metric_highlight'], '')

    def test_tailor_drops_summary_and_bullets_with_new_numbers(self):
        fake = {
            'match_score': 74,
            'match_grade': 'Moderate',
            'matched_keywords': ['Python'],
            'missing_critical_keywords': ['Kubernetes'],
            'tailored_summary': 'Backend engineer who improved throughput by 60%.',
            'suggested_project_improvements': [{
                'project_title': 'Order service',
                'original_bullet': 'Cut p95 latency from 185ms to 24ms.',
                'tailored_bullet': 'Cut p95 latency from 185ms to 24ms for 10,000 users.',
                'reason': 'Mentions scale',
            }],
            'quick_recommendations': ['Add Kubernetes.'],
        }
        with patch('requirements.ai_engine.tailor_resume_to_job', return_value=fake):
            res = self.client.post(
                '/api/ai/tailor-resume/',
                data=json.dumps({
                    'job_description': 'Backend role with Kubernetes.',
                    'resume_summary': 'Backend engineer.',
                    'resume_skills': ['Python'],
                    'resume_projects': [{
                        'title': 'Order service',
                        'bullets': ['Cut p95 latency from 185ms to 24ms.'],
                    }],
                }),
                content_type='application/json',
            )
        data = res.json()['data']
        self.assertEqual(data['tailored_summary'], '')
        self.assertEqual(data['suggested_project_improvements'], [])


class AlteredResumeJobAlignmentTests(TestCase):
    """Tailoring to a posting reports what is really on the resume, whatever the model claims."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.client = Client()
        self.category = Category.objects.create(name="Engineering", slug="engineering")
        self.job = JobPosting.objects.create(
            title="Senior Python Backend Developer",
            company_name="Acme Corp",
            category=self.category,
            experience_tier="experienced",
            skills_required="Python, Django, FastAPI, Docker, REST APIs, SQL, PostgreSQL, Redis",
            description="We are seeking a Senior Python Developer with strong Django, FastAPI, Docker, PostgreSQL and Redis skills."
        )
        self.projects = [{
            "title": "Inventory Management", "role": "Developer",
            "tech_stack": "Python, SQLite", "bullets": ["Built simple product tracking catalog"],
        }]

    def _post(self):
        return self.client.post(
            "/api/ai/alter-resume/",
            data=json.dumps({
                "job_id": str(self.job.uuid),
                "candidate_summary": "Python student.",
                "candidate_skills": {"Languages": "Python"},
                "candidate_projects": self.projects,
            }),
            content_type="application/json",
        )

    def test_ai_failure_leaves_the_resume_alone_and_still_reports_coverage(self):
        with patch("requirements.ai_engine.call_groq_chat", side_effect=RuntimeError("busy")):
            data = self._post().json()["data"]
        self.assertIs(data["ai"], False)
        self.assertEqual(data["altered_summary"], "Python student.")
        self.assertEqual(data["altered_projects"], self.projects)
        self.assertEqual(data["matching_keywords"], ["Python"])
        self.assertEqual(data["match_grade"], "1 of 8 job keywords found")

    @patch("requirements.ai_engine.call_groq_chat")
    def test_a_model_that_invents_a_matching_resume_does_not_raise_the_score(self, groq):
        groq.return_value = json.dumps({
            "altered_summary": "Senior Python developer with 6 years of Django and FastAPI backends.",
            "altered_skills": {"Backend": "Python, Django, FastAPI, Docker, REST APIs, SQL, PostgreSQL, Redis"},
            "altered_projects": [{
                "title": "Inventory Management",
                "tech_stack": "Python, Django, FastAPI, Docker, REST APIs, SQL, PostgreSQL, Redis",
                "bullets": [
                    "Built a product catalog with Django REST APIs, reducing lookup time by 40%.",
                    "Deployed the FastAPI service with Docker, cutting setup time by 30%.",
                    "Implemented Redis caching for stock lookups, reducing database load by 35%.",
                ],
            }],
            "overall_match_score": 95,
        })
        res = self._post()
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["altered_summary"], "Python student.")
        self.assertEqual(data["altered_projects"], self.projects)
        self.assertEqual(data["match_score"], data["match_score_before"])
        self.assertLess(data["match_score"], 20)
        self.assertEqual(data["match_grade"], "1 of 8 job keywords found")
        asked = [row["skill"] for row in data["skills_to_confirm"]]
        self.assertIn("Django", asked)
        self.assertIn("Docker", asked)
        body = res.content.decode()
        for invented in ("40%", "30%", "35%", "6 years"):
            self.assertNotIn(invented, body)
