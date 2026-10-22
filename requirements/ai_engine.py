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
                wait_time = 1.0 * (attempt + 1)
                logger.warning(f"Groq 429 Rate limited. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
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
    """Generate an enterprise-grade, high-converting job description."""
    system_prompt = (
        "You are an elite Tech Talent Recruiter and Hiring Architect for top startups and FAANG companies. "
        "Your goal is to write a compelling, high-converting, ATS-friendly Job Description. "
        "Return a valid JSON object with the following exact keys:\n"
        "- 'role_title': string (polished role title)\n"
        "- 'summary': string (2-3 sentences hook and team mission)\n"
        "- 'responsibilities': list of 5-7 clear, actionable bullet points starting with strong action verbs\n"
        "- 'required_qualifications': list of 4-6 must-have technical skills, frameworks, and experience\n"
        "- 'preferred_qualifications': list of 3-4 nice-to-have bonus skills\n"
        "- 'tech_stack_tags': list of 5-8 skill tags (e.g. ['React', 'Python', 'Docker'])\n"
        "- 'perks_benefits': list of 4 attractive perks (e.g. Health insurance, flexible hours, learning stipend)\n"
        "- 'linkedin_post_snippet': string (an engaging 150-word LinkedIn announcement with relevant hashtags)\n"
        "- 'full_markdown': string (clean Markdown representation ready to copy-paste)"
    )

    user_prompt = f"""
Create a job description with these details:
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

    response_text = call_groq_chat(messages, temperature=0.3, json_mode=True)
    return json.loads(response_text)


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
) -> dict:
    """Transform a GitHub project repository into a production-grade enterprise project entry with Google XYZ bullets."""
    system_prompt = (
        "You are an elite technical resume coach and ex-FAANG hiring manager. "
        "Transform a GitHub project repository into a production-grade enterprise project entry for a software engineering resume. "
        "Use the Google XYZ Formula: 'Accomplished [X], measured by [Y], by doing [Z]'. "
        "Include realistic metrics (e.g. latency reduction %, throughput req/sec, test coverage %, memory footprint). "
        "Return a valid JSON object with the following keys:\n"
        "- 'title': A clean, impressive professional project title\n"
        "- 'role': e.g. 'Creator & Lead Architect' or 'Full Stack Contributor'\n"
        "- 'tech_stack': comma-separated list of technologies, frameworks, and databases inferred from the repo\n"
        "- 'bullets': list of 3 high-impact Google XYZ bullet points (30-45 words each) starting with strong action verbs (Architected, Engineered, Optimized, Implemented, Deployed)"
    )

    topics_str = ", ".join(topics) if topics else "None"
    user_prompt = f"""
Repository Name: {repo_name}
Description: {description or 'Open-source software application'}
Primary Language: {primary_language or 'Python / TypeScript'}
Topics / Tags: {topics_str}
GitHub Stars: {stars}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response_text = call_groq_chat(messages, temperature=0.3, json_mode=True)
    return json.loads(response_text)

