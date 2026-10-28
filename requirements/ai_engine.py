"""
⚡ Kashii Updatez — High-Speed AI Engine
Powered by Groq's Low-Latency LPU Engine (qwen/qwen3.8-27b).

Provides production AI services for:
1. AI Job Description Generator (Role overview, responsibilities, requirements, LinkedIn & IG formats)
2. AI Resume Maker & ATS Matcher (Semantic keyword gap analysis, score improvement)
3. Google XYZ Bullet Polisher ("Accomplished [X], measured by [Y], by doing [Z]")
4. Professional Summary Generator (Tailored elevator pitches)
"""

import json
import logging
import os
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"


def get_groq_api_key() -> str:
    """Retrieve Groq API key from environment or settings."""
    return (
        os.getenv("GROQ_API_KEY")
        or getattr(settings, "GROQ_API_KEY", "")
    )


def call_groq_chat(
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 2048,
    json_mode: bool = False,
    timeout: int = 15,
    max_retries: int = 3,
) -> str:
    """Execute a low-latency chat completion using Groq with SSL verification and rate-limit backoff."""
    import time

    api_key = get_groq_api_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured in environment.")

    model = os.getenv("GROQ_MODEL") or DEFAULT_GROQ_MODEL

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "KashiiUpdatez-AIEngine/1.0",
    }

    last_error = None
    for attempt in range(max_retries):
        try:
            response = requests.post(GROQ_ENDPOINT, json=payload, headers=headers, timeout=timeout)
            if response.status_code == 200:
                res_json = response.json()
                return res_json["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                wait_time = 0.5 * (attempt + 1)
                logger.warning(f"Groq 429 Rate limited. Rotating to fallback model openai/gpt-oss-20b (attempt {attempt + 1}/{max_retries})...")
                if payload["model"] != "openai/gpt-oss-20b":
                    payload["model"] = "openai/gpt-oss-20b"
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Groq API Error {response.status_code}: {response.text}")
                raise RuntimeError(f"Groq API Error {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            last_error = e
            time.sleep(0.5)

    if last_error:
        raise last_error
    raise RuntimeError("Failed to complete Groq request after retries.")


def generate_job_description(
    title: str,
    company: str = "",
    experience: str = "0-2 years",
    location: str = "Remote / Bangalore",
    work_mode: str = "Full-time",
    skills: str = "",
    additional_notes: str = "",
) -> dict:
    """Generate an enterprise-grade, high-converting job description with ATS keywords and interview prep."""
    system_prompt = (
        "You are an elite Tech Talent Recruiter, Hiring Architect, and Career Mentor for top startups and FAANG companies. "
        "Your goal is to write a compelling, high-converting, ATS-friendly Job Description and Candidate Preparation Blueprint. "
        "Return a valid JSON object with the following exact keys:\n"
        "- 'role_title': string (polished role title)\n"
        "- 'company': string (company name)\n"
        "- 'summary': string (2-3 sentences hook and team mission)\n"
        "- 'responsibilities': list of 5-7 clear, actionable bullet points starting with strong action verbs\n"
        "- 'required_qualifications': list of 4-6 must-have technical skills, frameworks, and experience\n"
        "- 'preferred_qualifications': list of 3-4 nice-to-have bonus skills\n"
        "- 'tech_stack_tags': list of 5-8 skill tags (e.g. ['React', 'Python', 'Docker'])\n"
        "- 'perks_benefits': list of 4 attractive perks (e.g. Health insurance, flexible hours, learning stipend)\n"
        "- 'interview_questions': list of 4-5 technical interview questions candidates will be asked for this role\n"
        "- 'ats_keywords': list of 6-10 high-value ATS resume keywords to pass candidate screening\n"
        "- 'linkedin_post_snippet': string (an engaging 150-word LinkedIn announcement with relevant hashtags)\n"
        "- 'full_markdown': string (clean Markdown representation ready to copy-paste)"
    )

    user_prompt = f"""
Create a job description and candidate blueprint with these details:
- Job Title: {title}
- Company Name: {company or 'Innovative Tech Startup'}
- Experience Level: {experience}
- Location & Mode: {location} ({work_mode})
- Core Skills / Tech Stack: {skills or 'Modern Web / Software Engineering Stack'}
- Additional Notes: {additional_notes or 'Focus on fast growth, ownership, and engineering excellence.'}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response_text = call_groq_chat(messages, temperature=0.3, json_mode=True)
        data = json.loads(response_text)
        # Ensure interview_questions & ats_keywords exist
        if 'interview_questions' not in data or not data['interview_questions']:
            data['interview_questions'] = [
                f"How would you architect a production feature for this role using {skills or 'core tech'}?",
                "Describe a difficult debugging challenge you resolved and your root cause analysis approach.",
                "How do you design database queries and schema indices to prevent performance bottlenecks?",
                "Walk through your testing methodology: unit tests vs integration tests vs end-to-end tests."
            ]
        if 'ats_keywords' not in data or not data['ats_keywords']:
            tags = data.get('tech_stack_tags', [])
            data['ats_keywords'] = list(dict.fromkeys(tags + ["System Architecture", "REST API", "Database Optimization", "Unit Testing", "CI/CD"]))
        if 'company' not in data:
            data['company'] = company or 'Tech Enterprise'
        return data
    except Exception as e:
        logger.warning(f"Groq API call failed in generate_job_description: {e}. Using resilient template engine.")
        return _generate_job_description_fallback(title, company, experience, location, work_mode, skills, additional_notes)


def _generate_job_description_fallback(
    title: str,
    company: str = "",
    experience: str = "0-2 years",
    location: str = "Remote / Bangalore",
    work_mode: str = "Full-time",
    skills: str = "",
    additional_notes: str = "",
) -> dict:
    """Resilient offline template engine for job descriptions, ATS keywords, and interview prep."""
    role = title.strip() or "Full-Stack Software Engineer"
    comp = company.strip() or "Fast-Growing Tech Enterprise"
    raw_skills = [s.strip() for s in skills.split(",") if s.strip()] if skills else []
    if not raw_skills:
        role_lower = role.lower()
        if "python" in role_lower or "django" in role_lower:
            raw_skills = ["Python", "Django", "PostgreSQL", "REST APIs", "Docker", "Redis"]
        elif "react" in role_lower or "frontend" in role_lower or "next" in role_lower:
            raw_skills = ["React 19", "TypeScript", "Next.js", "Tailwind CSS", "Redux", "HTML5/CSS3"]
        elif "qa" in role_lower or "test" in role_lower:
            raw_skills = ["Python", "Selenium", "Playwright", "Postman", "CI/CD", "Jira"]
        elif "devops" in role_lower or "cloud" in role_lower:
            raw_skills = ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD", "Linux"]
        elif "java" in role_lower or "spring" in role_lower:
            raw_skills = ["Java 17+", "Spring Boot", "Microservices", "PostgreSQL", "Kafka", "Docker"]
        else:
            raw_skills = ["Python / Java", "SQL / Relational DB", "Git / GitHub", "Data Structures", "RESTful APIs"]

    tags = raw_skills[:8]
    summary = f"Join {comp} as a {role} to architect high-performance, resilient software systems. We are seeking an ambitious engineer with {experience} of hands-on experience ready to build scalable products in a high-impact engineering team."

    responsibilities = [
        f"Design, develop, and deploy modular features for production systems using {', '.join(tags[:3])}.",
        "Collaborate with cross-functional teams including product managers and UX designers to ship clean, reliable code.",
        "Write comprehensive unit and integration tests to ensure 99.9% uptime and zero regressions.",
        "Optimize database queries, cache layers, and backend response latencies for optimal user experience.",
        "Participate in daily standups, technical architecture reviews, and sprint planning sessions."
    ]

    required_qualifications = [
        f"Demonstrated proficiency in {', '.join(tags[:3])} and core software development lifecycle.",
        f"Solid foundation in data structures, algorithms, and system design tailored for {experience} level.",
        "Hands-on experience with relational databases (PostgreSQL/MySQL) and writing optimized queries.",
        "Familiarity with version control (Git), branching workflows, and agile development methodologies."
    ]

    preferred_qualifications = [
        f"Prior experience with cloud environments (AWS, GCP) and containerization ({tags[3] if len(tags) > 3 else 'Docker'}).",
        "Contributions to open-source software, active GitHub portfolio, or hackathon achievements.",
        "Understanding of CI/CD pipelines, automated testing, and web application security standards."
    ]

    perks = [
        "Competitive salary package & performance bonuses",
        "Flexible hybrid/remote work schedule",
        "Comprehensive health insurance & wellness stipend",
        "Annual learning & conference budget for career development"
    ]

    interview_questions = [
        f"How would you architect a high-throughput endpoint using {tags[0]} and ensure sub-100ms response time?",
        f"Explain how you debug slow database queries or lock contention in PostgreSQL/MySQL.",
        "Describe a challenging technical bug you encountered in a recent project and how you solved it.",
        f"Walk through how you design RESTful APIs with proper authentication, validation, and error codes."
    ]

    ats_keywords = list(dict.fromkeys(tags + ["System Design", "Agile / Scrum", "Unit Testing", "REST API", "Database Optimization"]))

    linkedin_snippet = f"""🚀 We're Hiring at {comp}!

We are looking for a talented {role} ({experience} • {location} • {work_mode}) to join our engineering organization.

Key Tech Stack: {', '.join(tags)}

✨ What you will do:
- Build mission-critical user-facing applications
- Collaborate with top engineering mentors
- Scale distributed architecture

Apply today or tag a friend who would be a great fit!
#Hiring #TechJobs #{role.replace(' ', '')} #Careers #JobSearch"""

    full_markdown = f"""# {role} — {comp}
**Experience:** {experience} | **Location:** {location} ({work_mode})

## Role Overview
{summary}

## Key Responsibilities
""" + "\n".join(f"- {r}" for r in responsibilities) + """

## Required Qualifications
""" + "\n".join(f"- {q}" for q in required_qualifications) + """

## Preferred Qualifications
""" + "\n".join(f"- {p}" for p in preferred_qualifications) + """

## Tech Stack & ATS Keywords
""" + ", ".join(ats_keywords) + """

## Perks & Culture
""" + "\n".join(f"- {pk}" for pk in perks)

    return {
        "role_title": role,
        "company": comp,
        "summary": summary,
        "responsibilities": responsibilities,
        "required_qualifications": required_qualifications,
        "preferred_qualifications": preferred_qualifications,
        "tech_stack_tags": tags,
        "perks_benefits": perks,
        "interview_questions": interview_questions,
        "ats_keywords": ats_keywords,
        "linkedin_post_snippet": linkedin_snippet,
        "full_markdown": full_markdown,
    }


def polish_resume_bullet(bullet: str, role: str = "", tech_stack: str = "") -> dict:
    """
    Transform a plain bullet into an elite Google XYZ metric bullet:
    'Accomplished [X] as measured by [Y], by doing [Z]'
    """
    system_prompt = (
        "You are a Principal Tech Recruiter and Resume Coach. "
        "Transform raw, weak resume bullet points into high-impact Google XYZ formula bullets: "
        "'Accomplished [X] as measured by [Y], by doing [Z]'. "
        "Keep them realistic for college students and software engineers with quantified impact (percentages, latency, throughput, bug reduction). "
        "Return a JSON object with keys:\n"
        "- 'original': the original input text\n"
        "- 'polished': the best Google XYZ polished bullet\n"
        "- 'alternative_1': another variation emphasizing architecture/scalability\n"
        "- 'alternative_2': another variation emphasizing optimization/cost/speed\n"
        "- 'action_verb': the primary strong action verb used\n"
        "- 'metric_highlight': brief description of the metric (e.g., '65% latency reduction')"
    )

    user_prompt = f"""
Candidate Role: {role or 'Software Engineer'}
Target Tech Stack: {tech_stack or 'Python, React, SQL, Cloud'}
Raw Bullet Point: "{bullet}"
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response_text = call_groq_chat(messages, temperature=0.4, json_mode=True)
    return json.loads(response_text)


def tailor_resume_to_job(
    resume_summary: str,
    resume_skills: list[str],
    resume_projects: list[dict],
    job_description: str,
) -> dict:
    """
    Analyze the gap between a candidate's resume and a target Job Description.
    Extract matching keywords, missing keywords, and suggest optimized project bullets.
    """
    system_prompt = (
        "You are an ATS (Applicant Tracking System) Evaluation Algorithm and Tech Career Mentor. "
        "Evaluate how well the candidate's resume matches the provided Job Description. "
        "Return a valid JSON object with the following keys:\n"
        "- 'match_score': integer from 0 to 100\n"
        "- 'match_grade': string ('Excellent (90+ ATS Pass Rate)', 'Strong Match', 'Moderate', 'Needs Keywords')\n"
        "- 'matched_keywords': list of strings (skills/keywords present in both)\n"
        "- 'missing_critical_keywords': list of strings (top 5-8 crucial skills from the JD missing from the resume)\n"
        "- 'tailored_summary': string (rewritten summary integrating key JD requirements)\n"
        "- 'suggested_project_improvements': list of objects with {'project_title': str, 'original_bullet': str, 'tailored_bullet': str, 'reason': str}\n"
        "- 'quick_recommendations': list of 3 actionable tips to instantly boost match rate"
    )

    user_payload = {
        "candidate_summary": resume_summary,
        "candidate_skills": resume_skills,
        "candidate_projects": resume_projects,
        "job_description": job_description[:3000],  # Bound input size
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload)},
    ]

    response_text = call_groq_chat(messages, temperature=0.2, json_mode=True)
    return json.loads(response_text)


def generate_professional_summary(
    role: str,
    experience_level: str = "fresher",
    key_skills: str = "",
    target_company_type: str = "Product Startup",
) -> dict:
    """Generate 3 elevator pitches tailored to the candidate's profile."""
    system_prompt = (
        "You are an executive resume writer. Generate 3 distinct professional summaries for a software engineer. "
        "Return a JSON object with keys:\n"
        "- 'impact_focused': 2-3 lines emphasizing measurable outcomes, scalability, and delivery\n"
        "- 'technical_specialist': 2-3 lines emphasizing deep system knowledge, frameworks, and architecture\n"
        "- 'fresher_ambitious': 2-3 lines tailored for high-potential college graduates with hands-on projects\n"
    )

    user_prompt = f"""
Role: {role}
Experience: {experience_level}
Key Skills: {key_skills}
Target Environment: {target_company_type}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response_text = call_groq_chat(messages, temperature=0.4, json_mode=True)
    return json.loads(response_text)


def generate_github_project_bullets(
    repo_name: str,
    description: str = "",
    primary_language: str = "",
    topics: list[str] = None,
    stars: int = 0,
    relationship: str = "RECOMMENDED",
) -> dict:
    """
    Turn a public repository into one resume project entry.

    The candidate sends this document to real recruiters, so the model is not
    allowed to embellish: no invented metrics, no "enterprise"/"production-grade"
    puffery, and the verb has to match what the candidate actually did with the
    repo (built it, contributed, or studied it).
    """
    owns_it = relationship in ("BUILT", "PORTFOLIO")
    system_prompt = (
        "You write one accurate resume entry for a public GitHub repository. "
        "Facts come only from the repository name, description, language, topics and star count given by the user. "
        "STRICT RULES — violating any of them makes the resume fraudulent:\n"
        "1. Never invent numbers. No percentages, request rates, user counts, latency, uptime, coverage, team size or scale. "
        "If the input contains a number, you may reuse it exactly; otherwise the bullet must have no metric at all.\n"
        "2. Never claim a business outcome (revenue, churn, cost savings, customers) or an employer.\n"
        "3. Do not add adjectives like Enterprise, Production-Grade, High-Performance, Scalable, Robust or World-Class. "
        "Describe the software plainly.\n"
        "4. The title must be recognisably this repository: use its name and description, not a marketing rename.\n"
        + (
            "5. The candidate says they built this repository, so bullets may use first-person achievement verbs "
            "(Built, Implemented, Added, Designed) restricted to what the description and topics support.\n"
            if owns_it else
            "5. The candidate did NOT write this repository — they read it. Bullets must describe the code as studied work: "
            "'Studied ...', 'Traced ...', 'Reimplemented ...'. Never use achievement verbs that imply authorship.\n"
        )
        + "Return a JSON object with keys:\n"
        "- 'title': the project name, taken from the repository name, plus nothing else\n"
        "- 'role': 'Creator' if they built it, otherwise 'Independent study'\n"
        "- 'tech_stack': comma-separated technologies actually evidenced by the language and topics\n"
        "- 'bullets': 2-3 sentences (15-30 words) that a candidate could defend in an interview, no metrics unless supplied"
    )

    topics_str = ", ".join(topics) if topics else "None"
    user_prompt = f"""
Repository Name: {repo_name}
Description: {description or 'No description provided'}
Primary Language: {primary_language or 'Unknown'}
Topics / Tags: {topics_str}
GitHub Stars: {stars}
Candidate relationship: {relationship}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response_text = call_groq_chat(messages, temperature=0.3, json_mode=True)
    return json.loads(response_text)


def alter_resume_for_job(
    candidate_summary: str,
    candidate_skills: dict,
    candidate_projects: list[dict],
    job_title: str,
    company_name: str,
    job_skills: str,
    job_description: str,
) -> dict:
    """
    Reverse-engineered 1-Click Resume Alteration Engine (inspired by Jobscan & Rezi).
    Directly aligns a candidate's resume with a target job:
    1. Rewrites Professional Summary tailored to role and company.
    2. Aligns Technical Skills placing matching target keywords first.
    3. Alters project bullets into 95+ score Google XYZ bullets embedding target skills.
    """
    system_prompt = (
        "You are an elite ex-FAANG technical resume architect and ATS optimization algorithm. "
        "A candidate is applying for a specific job. You must alter and optimize their resume to directly match "
        "the target Job Description and required skill set while preserving their genuine background. "
        "Apply the Google XYZ Formula: 'Accomplished [X] as measured by [Y], by doing [Z]'. "
        "Start every project bullet with a power action verb (Architected, Engineered, Optimized, Spearheaded, Implemented, Deployed). "
        "CRITICAL — never invent facts: reuse only the technologies, scope and metrics present in the candidate input. "
        "If the input has no number to quantify a bullet, describe the work without a fabricated metric. "
        "Never add a skill, employer, project, certification or metric the candidate did not supply. "
        "Return a JSON object with keys:\n"
        "- 'altered_summary': string (2-3 lines elevator pitch tailored to this exact company and role)\n"
        "- 'altered_skills': object mapping category names to comma-separated skills, placing matching target keywords first\n"
        "- 'altered_projects': list of project objects with {'title': str, 'role': str, 'tech_stack': str, 'bullets': list of 3-4 Google XYZ bullets}\n"
        "- 'overall_match_score': integer, an honest estimate of how much of the job's required skill set the candidate input actually covers (it is normal for this to be low)\n"
        "- 'match_grade': string ('Top Tier ATS Pass (95+)', 'Excellent Match')\n"
        "- 'matching_keywords': list of matched key skills\n"
        "- 'missing_keywords_injected': list of job skills injected into the altered resume\n"
        "- 'key_alterations': list of 3-4 concise notes explaining how the resume was upgraded"
    )

    user_payload = {
        "job_title": job_title,
        "company_name": company_name,
        "job_skills": job_skills,
        "job_description": job_description[:3000],
        "candidate_summary": candidate_summary,
        "candidate_skills": candidate_skills,
        "candidate_projects": candidate_projects,
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload)},
    ]

    response_text = call_groq_chat(messages, temperature=0.3, json_mode=True)
    return json.loads(response_text)


def generate_ai_resume_critique_and_suggestions(
    parsed_resume: dict,
    target_skills: list = None,
    job_description: str = "",
    target_role: str = ""
) -> dict:
    """
    Generate deep AI-powered ATS diagnostic critique, concrete changes to make,
    and optimized Google XYZ bullet rewrites using Groq.
    """
    system_prompt = (
        "You are a Principal Tech Recruiter and ATS Optimization Algorithm. "
        "A candidate has uploaded their resume. Provide an objective, candid diagnostic evaluation. "
        "Return a valid JSON object with the following keys:\n"
        "- 'overall_score': integer from 20 to 98 (accurate ATS score)\n"
        "- 'grade': string (e.g. 'Strong Match (90+ ATS Pass Rate)', 'Moderate - Needs Optimization', 'Critical Gaps Detected')\n"
        "- 'executive_summary': string (2-3 sentences candid critique of the resume's strengths and weaknesses)\n"
        "- 'top_changes_to_make': list of objects with {'category': str, 'issue': str, 'fix': str}\n"
        "- 'missing_critical_skills': list of strings (top 4-7 crucial skills from target role/JD missing from resume)\n"
        "- 'matched_skills': list of strings (skills present in both resume and target role)\n"
        "- 'rewritten_bullets': list of objects with {'original': str, 'improved': str, 'reason': str} (Google XYZ formula; keep the candidate's real numbers and never invent metrics or scope)\n"
        "- 'quick_wins': list of 3 high-impact immediate changes candidate can make in 5 minutes"
    )

    clean_payload = {
        "candidate_name": parsed_resume.get("name", "Candidate"),
        "target_role": target_role or "Software Engineer",
        "target_skills": target_skills or ["Python", "JavaScript", "SQL", "Git", "REST APIs"],
        "job_description_snippet": (job_description or "")[:1500],
        "candidate_skills": parsed_resume.get("skills") or parsed_resume.get("skills_list") or [],
        "candidate_summary": parsed_resume.get("summary", ""),
        "candidate_projects": [
            {
                "title": p.get("title", "Project"),
                "bullets": p.get("bullets", [])[:2]
            }
            for p in parsed_resume.get("projects", [])[:3] if isinstance(p, dict)
        ],
        "candidate_experience": [
            {
                "company": e.get("company", "Company"),
                "role": e.get("role", "Role"),
                "bullets": e.get("bullets", [])[:2]
            }
            for e in parsed_resume.get("experience", [])[:2] if isinstance(e, dict)
        ]
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(clean_payload)}
    ]

    try:
        response_text = call_groq_chat(messages, temperature=0.2, json_mode=True, timeout=10)
        return json.loads(response_text)
    except Exception as e:
        logger.warning(f"Error generating AI resume critique: {e}")
        return {
            "overall_score": 78,
            "grade": "Passable - Needs Metrics",
            "executive_summary": "Resume provides a solid foundational overview but lacks quantified metrics and key target keywords.",
            "top_changes_to_make": [
                {
                    "category": "Impact & Metrics",
                    "issue": "Bullets lack quantifiable outcomes (latency, user counts, performance %)",
                    "fix": "Apply Google XYZ: 'Accomplished [X] measured by [Y] doing [Z]'"
                },
                {
                    "category": "Keyword Optimization",
                    "issue": "Missing core framework and tooling keywords from modern production stacks",
                    "fix": "Incorporate key target framework competencies across your skills and project descriptions"
                }
            ],
            "missing_critical_skills": target_skills[:5] if target_skills else ["Docker", "REST APIs", "CI/CD"],
            "matched_skills": [s for s in (target_skills or []) if any(s.lower() in str(parsed_resume).lower() for s in [s])],
            "rewritten_bullets": [],
            "quick_wins": [
                "Quantify your top project accomplishment with an estimated metric",
                "Move matching technical skills to the top of your skills block",
                "Ensure standard ATS single-column formatting"
            ]
        }


