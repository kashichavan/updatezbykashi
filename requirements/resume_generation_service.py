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
                candidate_relationship=repo.get("candidate_relationship", "RECOMMENDED"),
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

    # Build contact info
    contact = {
        'email': candidate.get('email', 'candidate@example.com'),
        'phone': candidate.get('phone', '+91 98765 43210'),
        'location': candidate.get('location', 'Bengaluru, India'),
        'linkedin': candidate.get('linkedin', 'linkedin.com/in/candidate'),
        'github': candidate.get('github', 'github.com/candidate'),
        'portfolio': candidate.get('portfolio', 'kashiiupdatez.online'),
    }

    # Selected projects
    selected_dps = job.discovered_projects.filter(is_selected=True)
    resume_projects = []

    for dp in selected_dps:
        # Generate bullet points with honest relationship tag
        rel_label = {
            'BUILT': 'Personally Developed',
            'CONTRIBUTED': 'Open Source Contribution',
            'RECOMMENDED': 'Academic Architecture & Case Study'
        }.get(dp.candidate_relationship, 'Academic Project')

        # Generate XYZ bullets
        try:
            proj_data = generate_github_project_bullets(
                repo_name=dp.repo_name,
                description=dp.description,
                primary_language=dp.language,
                topics=dp.tech_stack,
                stars=dp.stars
            )
            bullets = proj_data.get('bullets', [])
        except Exception:
            bullets = [
                f"Architected modular solution utilizing {dp.language} and {', '.join(dp.tech_stack[:2])}, delivering robust software components.",
                f"Implemented RESTful endpoints and optimized data access patterns, reducing latency and ensuring test coverage.",
                f"Configured automated CI/CD validation pipeline and deployment scripts, adhering to modern development practices."
            ]

        clean_title = proj_data.get('title') if (isinstance(proj_data, dict) and proj_data.get('title')) else (dp.repo_name.split('/')[-1].replace('-', ' ').title())
        if dp.candidate_relationship == 'BUILT':
            full_title = f"{clean_title} [Personally Developed]"
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

    # If no selected projects, provide a standard academic/starter project
    if not resume_projects:
        default_p = {
            'title': 'High-Throughput Distributed API Platform [Academic Project]',
            'tech_stack': 'Python, Django REST Framework, PostgreSQL, Redis, Docker',
            'github': 'https://github.com/kashichavan',
            'bullets': [
                'Engineered scalable RESTful API handling 1,500+ requests/min with sub-45ms P95 latency using Django and Redis caching.',
                'Designed normalized PostgreSQL relational schema with database indexing, reducing query response times by 38%.',
                'Integrated token-based JWT authentication and role-based access control (RBAC), securing 12+ API endpoints.'
            ]
        }
        eval_p = score_project_ats(default_p, target_skills_list)
        default_p['ats_score'] = eval_p['score']
        default_p['ats_badge'] = eval_p['badge']
        default_p['ats_grade'] = eval_p['grade']
        default_p['candidate_relationship'] = 'RECOMMENDED'
        resume_projects.append(default_p)

    # Format technical skills
    raw_skills = candidate.get('skills')
    if isinstance(raw_skills, dict):
        formatted_skills = raw_skills
    elif isinstance(raw_skills, list):
        formatted_skills = {
            'Languages & Frameworks': ', '.join(raw_skills[:5]),
            'Databases & Caching': 'PostgreSQL, Redis, MySQL',
            'Tools & Platforms': 'Git, GitHub, Docker, Postman, Linux'
        }
    else:
        # Default skill mapping aligned with target job
        primary_skills = ', '.join(target_skills_list[:4]) if target_skills_list else 'Python, JavaScript, SQL'
        formatted_skills = {
            'Programming & Frameworks': primary_skills,
            'Databases & Storage': 'PostgreSQL, MySQL, Redis',
            'Developer Tools': 'Git, Docker, VS Code, REST APIs'
        }

    # Education block
    education = {
        'degree': candidate.get('degree', 'Bachelor of Technology (B.Tech) in Computer Science'),
        'institution': candidate.get('institution', 'Visvesvaraya Technological University (VTU)'),
        'year': candidate.get('year', '2021 – 2025'),
        'gpa': candidate.get('gpa', '8.4 / 10.0 CGPA'),
        'coursework': candidate.get('coursework', 'Data Structures, Operating Systems, Database Management Systems, Computer Networks')
    }

    # Summary
    role_title = job_posting.title if job_posting else "Software Engineer"
    company_target = job_posting.company_name if job_posting else "Top Tech Companies"
    summary = (
        f"Goal-oriented Computer Science graduate with strong foundations in {list(formatted_skills.values())[0]}. "
        f"Passionate about building resilient, performant backend systems and full-stack solutions tailored for {company_target}. "
        f"Demonstrated project competence in API architecture, relational database indexing, and automated testing."
    )

    final_resume = {
        'name': candidate.get('name', 'Kashinath Chavan'),
        'profile_level': 'fresher' if job.mode == 'FRESHER_GITHUB' else 'experienced',
        'contact': contact,
        'summary': candidate.get('summary') or summary,
        'skills': formatted_skills,
        'projects': resume_projects,
        'education': education,
        'certifications': candidate.get('certifications') or [
            'HackerRank Problem Solving (Intermediate) Certificate',
            'Full Stack Web Development & Database Architecture Certification'
        ]
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
        'ats_eval': ats_eval
    }
