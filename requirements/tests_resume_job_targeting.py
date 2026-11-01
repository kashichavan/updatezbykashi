import io
import json
import tempfile
from datetime import timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from pypdf import PdfReader

from . import resume_generation_service as service
from .models import Category, JobGroup, JobPosting, ResumeGenerationJob
from .resume_engine import calculate_ats_score, has_keyword, pick_role_for_skills, resume_text
from .resume_parser import evaluate_uploaded_resume_ats as evaluate
from .resume_pdf import generate_ats_resume_pdf


def resume(**over):
    data = {
        'name': 'Asha Rao',
        'contact': {'email': 'asha@go.dev', 'phone': '9876543210', 'linkedin': 'linkedin.com/in/asha', 'github': 'github.com/java-kafka'},
        'summary': 'Frontend developer building web interfaces with React and JavaScript for retail apps.',
        'skills': {'Languages': 'JavaScript, HTML, CSS'},
        'projects': [{'title': 'Shop UI', 'tech_stack': 'JavaScript, React', 'bullets': ['Built a storefront with React.', 'Developed a cart in JavaScript.']}],
        'education': {'degree': 'B.E', 'institution': 'RVCE'},
    }
    data.update(over)
    return data


class KeywordMatchTests(SimpleTestCase):
    def test_whole_words_only(self):
        self.assertFalse(has_keyword('Java', 'JavaScript and TypeScript'))
        self.assertFalse(has_keyword('C', 'Cloud, CSS'))
        self.assertFalse(has_keyword('R', 'Docker and Terraform experience'))
        self.assertFalse(has_keyword('SQL', 'NoSQL'))
        self.assertFalse(has_keyword('Go', 'I go to Google'))

    def test_forms_people_write(self):
        self.assertTrue(has_keyword('REST APIs', 'Built a REST API'))
        self.assertTrue(has_keyword('Core Java', 'Java 17'))
        self.assertTrue(has_keyword('Python/Java', 'Skilled in Java'))
        self.assertTrue(has_keyword('Kubernetes', 'k8s, Helm'))
        self.assertTrue(has_keyword('Node.js', 'Node, Express'))
        self.assertTrue(has_keyword('CI/CD', 'Set up CI/CD'))
        self.assertTrue(has_keyword('C++', 'C++ and Rust'))
        self.assertTrue(has_keyword('Go', 'Go, Rust'))
        self.assertFalse(has_keyword('C', 'C++ only'))

    def test_contact_links_are_not_skills(self):
        text = resume_text(resume())
        self.assertFalse(has_keyword('Kafka', text))
        self.assertFalse(has_keyword('Go', text))


class ScoreTests(SimpleTestCase):
    def test_empty_resume_scores_zero(self):
        self.assertEqual(evaluate({}, [])['score'], 0)
        self.assertEqual(evaluate({}, ['Java'])['score'], 0)

    def test_wrong_stack_is_reported_and_capped(self):
        result = evaluate(resume(), ['Java', 'Spring Boot', 'Kafka', 'SQL'])
        self.assertEqual(result['matched_skills'], [])
        self.assertEqual(result['job_match'], 0)
        self.assertLessEqual(result['score'], 40)

    def test_same_resume_scores_higher_for_the_job_it_fits(self):
        fit = evaluate(resume(), ['React', 'JavaScript', 'HTML'])
        wrong = evaluate(resume(), ['Java', 'Spring Boot', 'Kafka'])
        self.assertEqual(fit['job_match'], 100)
        self.assertGreater(fit['score'], wrong['score'] + 20)

    def test_no_guaranteed_claims_and_one_scorer(self):
        result = calculate_ats_score(resume(), 'full-stack')
        self.assertNotIn('Guaranteed', json.dumps(result))
        self.assertEqual(result['matched_keywords'], result['matched_skills'])


class RolePickTests(SimpleTestCase):
    def test_picks_by_job_skills(self):
        self.assertEqual(pick_role_for_skills(['Core Java', 'Spring Boot', 'Kafka']), 'java-sde')
        self.assertEqual(pick_role_for_skills(['Kubernetes', 'Terraform']), 'devops-cloud')
        self.assertEqual(pick_role_for_skills(['Pandas', 'Tableau']), 'data-analyst')
        self.assertEqual(pick_role_for_skills(['Salesforce', 'Cold Calling']), '')


class JobResumeTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Software Engineering', slug='software-engineering')

    def job(self, skills):
        return JobPosting.objects.create(
            title='Developer', company_name="O'Neil & Co", category=self.category, description='Role',
            stipend_salary='Paid', skills_required=skills, deadline=timezone.now() + timedelta(days=5),
        )

    def test_java_job_opens_java_template_without_sample_college(self):
        job = self.job('Core Java, Spring Boot, Apache Kafka')
        page = self.client.get(f'/resume-builder/?job_id={job.uuid}')
        self.assertEqual(page.status_code, 200)
        initial = page.context['initial_resume']
        self.assertIn('Java', initial['projects'][0]['tech_stack'])
        self.assertEqual(initial['education']['institution'], '')

    def test_job_no_template_fits_opens_blank(self):
        job = self.job('Salesforce, Cold Calling')
        initial = self.client.get(f'/resume-builder/?job_id={job.uuid}').context['initial_resume']
        self.assertEqual(initial['projects'], [])
        self.assertEqual(initial['skills'], {})

    def test_skill_text_cannot_break_the_page_script(self):
        job = self.job("Bob's Tool, </script><img src=x>")
        html = self.client.get(f'/resume-builder/?job_id={job.uuid}').content.decode()
        self.assertNotIn('</script><img', html)

    def test_typed_role_is_what_edits_score_against(self):
        gen = ResumeGenerationJob.objects.create(
            mode='FRESHER_GITHUB', candidate_data={}, generated_resume=resume(),
            target_profile={'title': 'SRE', 'skills': 'Linux, Go'},
        )
        html = self.client.get(f'/resume-builder/?gen_id={gen.uuid}').content.decode()
        self.assertIn('"skills_list": ["Linux", "Go"]', html)

    def _finalize(self, job, candidate, mode='EXISTING_UPLOAD'):
        gen = ResumeGenerationJob.objects.create(mode=mode, job=job, candidate_data=candidate)
        with patch('requirements.ai_engine.write_tailored_summary', return_value=''):
            return service.finalize_resume_synthesis(gen.uuid)['resume']

    def test_generated_resume_keeps_experience_and_leads_with_job_skills(self):
        job = self.job('Spring Boot, Java')
        built = self._finalize(job, {
            'name': 'Asha', 'skills': 'HTML, Git, Java, Spring Boot',
            'experience': [{'company': 'Infosys', 'role': 'SDE', 'period': '2023-2025', 'bullets': ['Built a payment service in Java.']}, {}],
        })
        self.assertEqual([e['company'] for e in built['experience']], ['Infosys'])
        self.assertEqual(built['skills']['Technical Skills'], 'Java, Spring Boot, HTML, Git')

    def test_pdf_text_is_machine_readable_in_order(self):
        built = self._finalize(self.job('Java'), {
            'name': 'Asha Rao', 'email': 'a@b.co', 'phone': '9876543210', 'skills': 'Java',
            'experience': [{'company': 'Infosys', 'role': 'SDE', 'period': '2023', 'bullets': ['Built a payment service in Java.']}],
        })
        pdf = generate_ats_resume_pdf(built)
        text = '\n'.join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)
        self.assertIn('Infosys', text)
        self.assertLess(text.index('ASHA RAO'), text.index('Infosys'))


class ReviewScoreLimitTests(TestCase):
    def _review(self, skills, score=95):
        fake = {'overall_score': score, 'grade': 'Strong', 'checks': [], 'fixes': [], 'missing_skills': [], 'project_scores': {}}
        with patch('requirements.ai_engine.review_resume_with_ai', return_value=fake):
            response = self.client.post(
                '/api/ai/resume-review/',
                json.dumps({'resume': resume(), 'job_skills': skills}),
                content_type='application/json',
            )
        return response.json()

    def test_model_cannot_score_a_wrong_stack_resume_highly(self):
        data = self._review(['Java', 'Spring Boot', 'Kafka'])
        self.assertEqual(data['overall_score'], 40)
        self.assertEqual(data['grade'], 'Weak')

    def test_full_match_keeps_the_model_score(self):
        self.assertEqual(self._review(['React', 'JavaScript'])['overall_score'], 95)


class RestoreKeepsExpiryTests(TestCase):
    def test_old_group_expires_but_keeps_link_and_jobs(self):
        category = Category.objects.create(name='Software Engineering', slug='software-engineering')
        job = JobPosting.objects.create(
            title='Dev', company_name='Acme', category=category, description='x', stipend_salary='Paid',
            deadline=timezone.now() + timedelta(days=5),
        )
        group = JobGroup.objects.create(name='Sep', slug='sep-drive', posted_date='2026-09-25')
        group.jobs.add(job)
        snapshot = [{'model': 'requirements.jobgroup', 'pk': group.pk, 'fields': {
            'name': 'Changed', 'slug': 'sep-drive', 'posted_date': '2026-09-25', 'jobs': [],
        }}]
        with tempfile.NamedTemporaryFile('w', suffix='.json') as handle:
            json.dump(snapshot, handle)
            handle.flush()
            call_command('restore_snapshot', file=handle.name)
        group.refresh_from_db()
        self.assertFalse(group.is_active)
        self.assertEqual(group.name, 'Sep')
        self.assertEqual(group.jobs.count(), 1)
        self.assertEqual(self.client.get('/group/sep-drive/').status_code, 200)
