"""
Background Resume Generation & GitHub Project Discovery Service for Kashii Updatez.
Safely runs asynchronous pipeline without external Celery dependency on Render.
"""

import logging
import threading
from typing import Dict, Any, List

from django.utils import timezone
from .models import ResumeGenerationJob, DiscoveredProject, JobPosting
from .github_discovery import search_github_repositories
from .resume_parser import evaluate_uploaded_resume_ats, parse_resume_into_structured_json
from .resume_engine import score_project_ats, RESUME_ROLES
from .ai_engine import generate_github_project_bullets, alter_resume_for_job

logger = logging.getLogger(__name__)


def start_generation_pipeline_async(job_uuid: str):
    """Launch the resume generation and repository discovery worker in a daemon thread."""
    thread = threading.Thread(target=run_generation_pipeline, args=(job_uuid,), daemon=True)
    thread.start()


def run_generation_pipeline(job_uuid: str):
    """
    Main background pipeline execution:
    1. EXTRACTING_SKILLS: Analyze job posting and candidate profile
    2. SEARCHING_REPOSITORIES: Discover relevant public GitHub repositories
    3. RANKING_PROJECTS: Score repositories via 5-factor relevance formula
    4. Transition to AWAITING_SELECTION (or auto-synthesize if existing upload)
    """
    from django.db import connections
    connections.close_all()
    try:
        job = ResumeGenerationJob.objects.filter(uuid=job_uuid).first()
        if not job:
            logger.error(f"ResumeGenerationJob {job_uuid} not found.")
            return

        # Phase 1: Extracting skills & requirements
        job.status = 'EXTRACTING_SKILLS'
        job.progress_pct = 15
        job.stage_message = 'Analyzing job requirements and required technology stack...'
        job.save(update_fields=['status', 'progress_pct', 'stage_message', 'updated_at'])

        job_posting = job.job
        job_title = job_posting.title if job_posting else "Software Engineer"
        job_skills = job_posting.skills_required if job_posting else ""
        job_desc = job_posting.description if job_posting else ""

        # Phase 2: Searching public GitHub repositories
        job.status = 'SEARCHING_REPOSITORIES'
        job.progress_pct = 40
        job.stage_message = f'Searching public GitHub repositories for {job_title} skills...'
        job.save(update_fields=['status', 'progress_pct', 'stage_message', 'updated_at'])

        discovered_repos = search_github_repositories(
            job_title=job_title,
            job_skills=job_skills,
            job_description=job_desc,
            limit=8
        )

        # Phase 3: Ranking projects & storing in database
        job.status = 'RANKING_PROJECTS'
        job.progress_pct = 65
        job.stage_message = f'Ranking {len(discovered_repos)} repositories against target job relevance...'
        job.save(update_fields=['status', 'progress_pct', 'stage_message', 'updated_at'])

        # Clear any existing discovered projects for this job
        job.discovered_projects.all().delete()

        created_projects = []
        for idx, repo in enumerate(discovered_repos):
            # Select top 2 by default as recommended
            is_def_selected = (idx < 2)
            dp = DiscoveredProject.objects.create(
                generation_job=job,
                repo_name=repo["repo_name"],
                repo_url=repo["repo_url"],
                description=repo["description"],
                stars=repo["stars"],
                language=repo["language"],
                tech_stack=repo["tech_stack"],
                relevance_score=repo["relevance_score"],
                score_breakdown=repo["score_breakdown"],
                evidence_summary=repo["evidence_summary"],
                candidate_relationship=repo.get("candidate_relationship", "BUILT"),
                is_selected=is_def_selected
            )
            created_projects.append(dp)

        # If fresher with GitHub discovery, pause here for candidate project selection
        if job.mode == 'FRESHER_GITHUB':
            job.status = 'AWAITING_SELECTION'
            job.progress_pct = 75
            job.stage_message = 'Projects discovered. Ready for candidate selection and review.'
            job.save(update_fields=['status', 'progress_pct', 'stage_message', 'updated_at'])
            return

        # For existing upload or scratch mode, continue to synthesis immediately
        finalize_resume_synthesis(job.uuid)

    except Exception as e:
        logger.exception(f"Error in run_generation_pipeline for job {job_uuid}:")
        try:
            job = ResumeGenerationJob.objects.filter(uuid=job_uuid).first()
            if job:
                job.status = 'FAILED'
                job.error_message = str(e)
                job.stage_message = f'Failed: {str(e)}'
                job.save(update_fields=['status', 'error_message', 'stage_message', 'updated_at'])
        except Exception:
            pass


def finalize_resume_synthesis(job_uuid: str) -> Dict[str, Any]:
    """
    Synthesizes the tailored resume:
    1. Formats candidate details (education, contact, skills).
    2. Incorporates selected projects with ethical badges & XYZ metrics.
    3. Runs honest ATS evaluation.
    4. Sets job status to COMPLETED.
    """
    job = ResumeGenerationJob.objects.filter(uuid=job_uuid).first()
    if not job:
        raise ValueError(f"Job {job_uuid} not found")

    job.status = 'GENERATING_RESUME'
    job.progress_pct = 85
    job.stage_message = 'Synthesizing professional resume bullets and structure...'
    job.save(update_fields=['status', 'progress_pct', 'stage_message', 'updated_at'])

    candidate = job.candidate_data or {}
    job_posting = job.job
    target_skills_list = job_posting.get_skills_list() if job_posting else []

    # Build contact info.
    # Never substitute a placeholder: this document gets sent to recruiters, so a
    # fabricated email or phone number is worse than a blank field. The UI collects
    # the real values and lists whatever is still missing.
    def _clean(value):
        return (value or '').strip() if isinstance(value, str) else ''

    contact = {
        'email': _clean(candidate.get('email')),
        'phone': _clean(candidate.get('phone')),
        'location': _clean(candidate.get('location')),
        'linkedin': _clean(candidate.get('linkedin')),
        'github': _clean(candidate.get('github')),
        'portfolio': _clean(candidate.get('portfolio')),
    }
    missing_fields = [label for key, label in (
        ('name', 'Full name'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('degree', 'Degree'),
    ) if not _clean(candidate.get(key))]

    # Selected projects
    selected_dps = job.discovered_projects.filter(is_selected=True)
    resume_projects = []

    for dp in selected_dps:
        # Generate bullet points with honest relationship tag
        rel_label = {
            'BUILT': 'Personally Developed',
            'PORTFOLIO': 'Personal Portfolio Project',
            'PRACTICE': 'Guided Practice / Case Study',
            'CONTRIBUTED': 'Open Source Contribution',
            'RECOMMENDED': 'Academic Architecture & Case Study'
        }.get(dp.candidate_relationship, 'Academic Project')

        # Generate XYZ bullets
        if dp.demo_project and dp.demo_project.resume_bullet_templates:
            bullets = list(dp.demo_project.resume_bullet_templates)
            clean_title = dp.demo_project.title
        else:
            # `proj_data` must exist before the try: when the AI call raises we
            # still read it below for the title, and an unbound name turned a
            # recoverable AI failure into a 500 on the whole request.
            proj_data = {}
            try:
                proj_data = generate_github_project_bullets(
                    repo_name=dp.repo_name,
                    description=dp.description,
                    primary_language=dp.language,
                    topics=dp.tech_stack,
                    stars=dp.stars
                ) or {}
                bullets = proj_data.get('bullets', [])
            except Exception:
                # Describe only what the repository metadata actually supports.
                # The previous fallback asserted latency wins, test coverage and
                # a CI/CD pipeline that nobody had verified.
                bullets = []
                desc_line = (dp.description or '').strip().split('. ')[0].strip().rstrip('.')
                if desc_line:
                    bullets.append(desc_line + '.')
                stack_bits = []
                for bit in [dp.language] + list(dp.tech_stack or [])[:3]:
                    if bit and bit not in stack_bits:
                        stack_bits.append(bit)
                if stack_bits:
                    bullets.append(f"Studied the codebase and its use of {', '.join(stack_bits)}.")
                if not bullets:
                    bullets = [f"Studied the architecture of {dp.repo_name}."]
            clean_title = proj_data.get('title') if (isinstance(proj_data, dict) and proj_data.get('title')) else (dp.repo_name.split('/')[-1].replace('-', ' ').title())

        if dp.candidate_relationship == 'BUILT':
            full_title = f"{clean_title} [Personally Developed]"
        elif dp.candidate_relationship == 'PORTFOLIO':
            full_title = f"{clean_title} [Personal Portfolio Project]"
        elif dp.candidate_relationship == 'PRACTICE':
            full_title = f"{clean_title} [Practice Case Study]"
        elif dp.candidate_relationship == 'CONTRIBUTED':
            full_title = f"{clean_title} [Open Source Contribution]"
        else:
            full_title = f"{clean_title} [Architecture & Case Study]"

        # Rate project ATS score
        proj_dict = {
            'title': full_title,
            'tech_stack': ', '.join(dp.tech_stack) if isinstance(dp.tech_stack, list) else dp.tech_stack,
            'github': dp.repo_url,
            'bullets': bullets
        }
        ats_p = score_project_ats(proj_dict, target_skills_list)
        proj_dict['ats_score'] = ats_p['score']
        proj_dict['ats_badge'] = ats_p['badge']
        proj_dict['ats_grade'] = ats_p['grade']
        proj_dict['candidate_relationship'] = dp.candidate_relationship
        resume_projects.append(proj_dict)

    # No selected projects is a valid, honest state: an empty projects section.
    # Previously this injected a fabricated project pointing at someone else's
    # GitHub account, which the candidate would then send to a recruiter.
    if not resume_projects:
        missing_fields.append('Projects (select at least one repository)')

    # Format technical skills — only the skills the candidate confirmed.
    raw_skills = candidate.get('skills')
    if isinstance(raw_skills, dict):
        formatted_skills = {k: v for k, v in raw_skills.items() if v}
    elif isinstance(raw_skills, list):
        cleaned = [str(s).strip() for s in raw_skills if str(s).strip()]
        formatted_skills = {'Technical Skills': ', '.join(cleaned)} if cleaned else {}
    elif isinstance(raw_skills, str):
        cleaned = [s.strip() for s in raw_skills.split(',') if s.strip()]
        formatted_skills = {'Technical Skills': ', '.join(cleaned)} if cleaned else {}
    else:
        formatted_skills = {}

    if not formatted_skills:
        missing_fields.append('Skills')

    # Education block — no invented university, years or CGPA.
    education = {
        'degree': _clean(candidate.get('degree')),
        'institution': _clean(candidate.get('institution')),
        'year': _clean(candidate.get('year')),
        'gpa': _clean(candidate.get('gpa')),
        'coursework': _clean(candidate.get('coursework')),
    }

    # Summary
    role_title = job_posting.title if job_posting else "Software Engineer"
    company_target = job_posting.company_name if job_posting else "Top Tech Companies"
    skill_phrase = ''
    if formatted_skills:
        raw_first = str(next(iter(formatted_skills.values()), ''))
        top_skills = [s.strip() for s in raw_first.split(',') if s.strip()][:4]
        skill_phrase = ', '.join(top_skills)
    summary = (
        f"{'Fresher' if not skill_phrase else 'Early-career engineer'} targeting the {role_title} role at {company_target}."
        + (f" Working with {skill_phrase}." if skill_phrase else "")
        + " Built the selected projects listed below and is looking for a first full-time engineering role."
    )

    final_resume = {
        'name': _clean(candidate.get('name')),
        'profile_level': 'fresher' if job.mode == 'FRESHER_GITHUB' else 'experienced',
        'contact': contact,
        'summary': _clean(candidate.get('summary')) or summary,
        'skills': formatted_skills,
        'projects': resume_projects,
        'education': education,
        'certifications': candidate.get('certifications') or [],
    }

    # Phase 5: Honest ATS evaluation
    job.status = 'EVALUATING_ATS'
    job.progress_pct = 95
    job.stage_message = 'Calculating verified ATS compatibility score...'
    job.save(update_fields=['status', 'progress_pct', 'stage_message', 'updated_at'])

    ats_eval = evaluate_uploaded_resume_ats(final_resume, target_skills_list)

    # Save to model
    job.generated_resume = final_resume
    job.ats_evaluation = ats_eval
    job.status = 'COMPLETED'
    job.progress_pct = 100
    job.stage_message = 'Resume generation completed successfully.'
    job.save(update_fields=['generated_resume', 'ats_evaluation', 'status', 'progress_pct', 'stage_message', 'updated_at'])

    return {
        'resume': final_resume,
        'ats_eval': ats_eval,
        'missing_fields': missing_fields,
    }
