import re
from typing import List, Dict, Any, Optional
from django.db.models import Q
from .models import IndianDemoProject, DiscoveredProject, ResumeGenerationJob


def serialize_demo_project(p: IndianDemoProject) -> Dict[str, Any]:
    """
    Format an IndianDemoProject instance into a clean JSON-serializable dictionary
    suitable for resume builder UI, API clients, and PDF/DOCX templates.
    """
    bullets = p.resume_bullet_templates or []
    tech_stack = p.technical_stack or []
    tech_str = ', '.join(tech_stack) if isinstance(tech_stack, list) else str(tech_stack)
    roles = p.target_job_roles or []

    return {
        'id': p.id,
        'slug': p.slug,
        'title': p.title,
        'fictional_company_name': p.fictional_company_name or 'Demo Labs',
        'company': p.fictional_company_name or 'Portfolio Showcase',
        'location_city': p.location_city,
        'location_state': p.location_state,
        'location_label': f"{p.location_city}, {p.location_state}",
        'industry': p.industry,
        'domain': p.industry,
        'target_job_roles': roles,
        'role': roles[0] if roles else 'Software Engineer',
        'difficulty_level': p.difficulty_level,
        'project_type': p.project_type,
        'description': p.description,
        'problem_statement': p.problem_statement,
        'technical_stack': tech_stack,
        'tech_stack': tech_str,
        'key_features': p.key_features or [],
        'architecture_summary': p.architecture_summary,
        'database_design_summary': p.database_design_summary,
        'api_design_summary': p.api_design_summary,
        'resume_bullet_templates': bullets,
        'bullets': bullets,
        'estimated_duration': p.estimated_duration,
        'learning_outcomes': p.learning_outcomes or [],
        'source_type': p.source_type,
        'is_curated': p.is_curated,
        'is_active': p.is_active,
    }


def match_demo_projects_for_job(
    job_title: str = "",
    job_skills: Any = None,
    preferred_city: str = "",
    difficulty: str = "",
    industry: str = "",
    limit: int = 12
) -> List[Dict[str, Any]]:
    """
    Ranks curated IndianDemoProjects against job requirements using transparent scoring:
    - Role & Title alignment (up to 40 pts)
    - Technical stack overlap (up to 40 pts)
    - Location hub alignment (up to 15 pts)
    - Base curated quality score (5 pts)
    """
    queryset = IndianDemoProject.objects.filter(is_active=True)

    if difficulty:
        queryset = queryset.filter(difficulty_level__iexact=difficulty.strip())
    if industry:
        queryset = queryset.filter(industry__icontains=industry.strip())

    projects = list(queryset)
    if not projects:
        return []

    # Parse candidate/job target skills
    target_skills_set = set()
    if isinstance(job_skills, list):
        for s in job_skills:
            if s:
                target_skills_set.add(str(s).lower().strip())
    elif isinstance(job_skills, str) and job_skills:
        for s in re.split(r'[,|/\n]+', job_skills):
            clean_s = s.strip().lower()
            if clean_s:
                target_skills_set.add(clean_s)

    title_words = set(re.findall(r'\b[a-zA-Z0-9+#.]+\b', (job_title or "").lower()))
    norm_city = (preferred_city or "").lower().strip()

    scored = []
    for p in projects:
        score = 5.0  # Base curated project quality
        matched_skills = []
        matched_roles = []
        evidence_points = []

        # 1. Role / Title Match (up to 40 pts)
        project_roles = [r.lower() for r in (p.target_job_roles or [])]
        role_score = 0.0
        for r in project_roles:
            r_tokens = set(re.findall(r'\b[a-zA-Z0-9+#.]+\b', r))
            overlap = r_tokens.intersection(title_words)
            if overlap:
                matched_roles.append(r)
                role_score = max(role_score, 25.0 + min(15.0, len(overlap) * 5.0))

        # Check title text direct match
        for w in title_words:
            if len(w) >= 3 and w in p.title.lower():
                role_score = min(40.0, role_score + 10.0)

        score += role_score
        if matched_roles:
            evidence_points.append(f"Target role aligns with '{p.target_job_roles[0]}'")

        # 2. Tech Stack Match (up to 40 pts)
        p_tech = [str(t).lower().strip() for t in (p.technical_stack or [])]
        for tech in p_tech:
            tech_clean = tech.strip()
            # Direct match in target skills
            if tech_clean in target_skills_set:
                matched_skills.append(tech)
            # Token match (e.g. "django rest framework" vs "django")
            elif any(w in tech_clean for w in title_words if len(w) >= 3):
                matched_skills.append(tech)
            elif any(ts in tech_clean or tech_clean in ts for ts in target_skills_set if len(ts) >= 3):
                matched_skills.append(tech)

        unique_matched_skills = list(dict.fromkeys(matched_skills))
        tech_score = min(40.0, len(unique_matched_skills) * 10.0)
        score += tech_score

        if unique_matched_skills:
            evidence_points.append(f"Matches {len(unique_matched_skills)} technologies: {', '.join(unique_matched_skills[:3])}")

        # 3. Location Hub Alignment (up to 15 pts)
        if norm_city and norm_city in p.location_city.lower():
            score += 15.0
            evidence_points.append(f"Located in target hub: {p.location_city}")
        elif norm_city and norm_city in p.location_state.lower():
            score += 10.0
            evidence_points.append(f"Located in target state: {p.location_state}")

        final_score = min(100.0, round(score, 1))

        serialized = serialize_demo_project(p)
        serialized['relevance_score'] = final_score
        serialized['score_breakdown'] = {
            'role_score': round(role_score, 1),
            'tech_score': round(tech_score, 1),
            'location_bonus': 15.0 if norm_city and norm_city in p.location_city.lower() else 0.0,
            'curated_quality': 5.0,
        }
        serialized['evidence_summary'] = '. '.join(evidence_points) if evidence_points else f"Demonstrates {p.industry} architecture with {', '.join((p.technical_stack or [])[:3])}"
        scored.append((final_score, serialized))

    # Sort descending by score
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:limit]]


def attach_demo_project_to_generation_job(
    generation_job: ResumeGenerationJob,
    demo_project: IndianDemoProject,
    relationship: str = 'PORTFOLIO',
    is_selected: bool = True
) -> DiscoveredProject:
    """
    Creates or updates a DiscoveredProject entry associated with a ResumeGenerationJob,
    anchored to the curated IndianDemoProject without falsifying real company employment.
    """
    rel = (relationship or 'PORTFOLIO').upper()
    valid_rels = ['PORTFOLIO', 'PRACTICE', 'BUILT', 'CONTRIBUTED', 'RECOMMENDED']
    if rel not in valid_rels:
        rel = 'PORTFOLIO'

    # Fictional repo name format: e.g. "portfolio-demo/hospital-appointment-system"
    company_prefix = (demo_project.fictional_company_name or 'Portfolio').lower().replace(' ', '-')
    repo_name = f"{company_prefix}/{demo_project.slug}"
    repo_url = f"https://github.com/kashichavan/{demo_project.slug}"

    # Tech stack list and primary language
    tech_stack = demo_project.technical_stack or []
    primary_lang = tech_stack[0] if tech_stack else 'Python'

    # Check if this demo project was already attached to this generation job
    existing = generation_job.discovered_projects.filter(
        Q(demo_project=demo_project) | Q(repo_name=repo_name)
    ).first()

    if existing:
        existing.demo_project = demo_project
        existing.repo_name = repo_name
        existing.repo_url = repo_url
        existing.description = demo_project.description
        existing.language = primary_lang
        existing.tech_stack = tech_stack
        existing.candidate_relationship = rel
        existing.is_selected = is_selected
        existing.evidence_summary = (
            f"Curated {demo_project.location_city} {demo_project.industry} portfolio project. "
            f"Includes {len(demo_project.resume_bullet_templates or [])} Google XYZ bullet templates."
        )
        existing.save()
        return existing

    dp = DiscoveredProject.objects.create(
        generation_job=generation_job,
        demo_project=demo_project,
        repo_name=repo_name,
        repo_url=repo_url,
        description=demo_project.description,
        stars=128,  # Curated benchmark
        language=primary_lang,
        tech_stack=tech_stack,
        relevance_score=92.5,
        score_breakdown={
            'role_match': 35.0,
            'stack_match': 35.0,
            'location_hub': 15.0,
            'curated_quality': 7.5
        },
        evidence_summary=(
            f"Curated {demo_project.location_city} {demo_project.industry} portfolio project. "
            f"Includes {len(demo_project.resume_bullet_templates or [])} Google XYZ bullet templates."
        ),
        candidate_relationship=rel,
        is_selected=is_selected
    )
    return dp
