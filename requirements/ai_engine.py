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
import re
import requests
from django.conf import settings

from .resume_engine import has_keyword, resume_text

logger = logging.getLogger(__name__)

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"
NVIDIA_ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_NVIDIA_MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"
NVIDIA_TIMEOUT = 25
# Past this, stop waiting on Groq so NVIDIA can still answer inside Gunicorn's 60s limit.
GROQ_TIME_BUDGET = 25


def get_groq_api_key() -> str:
    """Retrieve Groq API key from environment or settings."""
    return (
        os.getenv("GROQ_API_KEY")
        or getattr(settings, "GROQ_API_KEY", "")
    )


def get_nvidia_api_key() -> str:
    return os.getenv("NVIDIA_API_KEY") or getattr(settings, "NVIDIA_API_KEY", "")


# Each model has its own per-minute limit, so a busy model hands over to the next.
GROQ_FALLBACK_MODELS = ("openai/gpt-oss-20b", "openai/gpt-oss-120b")
_groq_model_rest_until = {}


def _groq_models_to_try(preferred: str) -> list[str]:
    """Models in order of preference, leaving out any still resting after a 429."""
    import time

    models = [preferred] + [m for m in GROQ_FALLBACK_MODELS if m != preferred]
    now = time.time()
    return [m for m in models if _groq_model_rest_until.get(m, 0) <= now] or models


def _rest_groq_model(model: str, retry_after) -> None:
    import time

    try:
        seconds = float(retry_after)
    except (TypeError, ValueError):
        seconds = 5.0
    _groq_model_rest_until[model] = time.time() + min(max(seconds, 1.0), 60.0)


def _groq_error_code(response) -> str:
    """Groq's error code only. The full body can repeat the candidate's resume."""
    try:
        return str(response.json()["error"].get("code") or "unknown")
    except (ValueError, KeyError, AttributeError, TypeError):
        return "unknown"


def _call_nvidia_chat(
    messages: list[dict], temperature: float, max_tokens: int, json_mode: bool, timeout: float = NVIDIA_TIMEOUT,
) -> str:
    """Backup provider. It speaks the same chat format as Groq."""
    payload = {
        "model": os.getenv("NVIDIA_MODEL") or DEFAULT_NVIDIA_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        # With thinking on, this model can use every token before it answers.
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    response = requests.post(
        NVIDIA_ENDPOINT,
        json=payload,
        headers={"Authorization": f"Bearer {get_nvidia_api_key()}", "Content-Type": "application/json"},
        timeout=timeout,
    )
    if response.status_code != 200:
        raise RuntimeError(f"NVIDIA API Error {response.status_code}")
    content = response.json()["choices"][0]["message"].get("content") or ""
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.S).strip()
    if not content:
        raise RuntimeError("NVIDIA returned an empty reply.")
    return content


def call_groq_chat(
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 2048,
    json_mode: bool = False,
    timeout: int = 15,
    max_retries: int = 3,
    budget: float = None,
) -> str:
    """
    Chat completion through Groq, then NVIDIA when Groq cannot answer.

    `budget` is the most seconds the whole call may take, both providers and
    every retry included. A caller inside a web request passes it so that a bad
    minute at the providers ends in a clean failure instead of a hung page.
    """
    import time

    started = time.monotonic()

    def left():
        return None if budget is None else budget - (time.monotonic() - started)

    has_groq = bool(get_groq_api_key())
    if has_groq:
        try:
            if budget is None:
                return _call_groq_chat(messages, temperature, max_tokens, json_mode, timeout, max_retries)
            return _call_groq_chat(
                messages, temperature, max_tokens, json_mode, min(timeout, budget), max_retries, time_budget=budget)
        except Exception as e:
            if not get_nvidia_api_key():
                raise
            if budget is not None and left() < 4:
                raise RuntimeError(f"AI time budget of {budget:.0f}s used up: {str(e)[:120]}")
            logger.warning(f"Groq failed, trying NVIDIA: {str(e)[:200]}")
    elif not get_nvidia_api_key():
        raise ValueError("GROQ_API_KEY is not configured in environment.")
    if budget is None:
        return _call_nvidia_chat(messages, temperature, max_tokens, json_mode)
    return _call_nvidia_chat(messages, temperature, max_tokens, json_mode, timeout=min(NVIDIA_TIMEOUT, left()))


def _call_groq_chat(
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    json_mode: bool,
    timeout: int,
    max_retries: int,
    time_budget: float = GROQ_TIME_BUDGET,
) -> str:
    """Execute a low-latency chat completion using Groq with SSL verification and rate-limit backoff."""
    import time

    api_key = get_groq_api_key()
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
    models = _groq_models_to_try(model)
    started = time.monotonic()
    for attempt in range(max_retries):
        spent = time.monotonic() - started
        if spent > time_budget or (attempt and time_budget - spent < 3):
            break
        timeout = max(1, min(timeout, time_budget - spent))
        payload["model"] = models[attempt % len(models)]
        # The gpt-oss models think before answering, and that thinking is paid for
        # out of max_tokens. Left at the default it used up the allowance on a long
        # resume and the JSON came back cut off (json_validate_failed).
        if payload["model"].startswith("openai/gpt-oss"):
            payload["reasoning_effort"] = "low"
        else:
            payload.pop("reasoning_effort", None)
        try:
            response = requests.post(GROQ_ENDPOINT, json=payload, headers=headers, timeout=timeout)
            if response.status_code == 200:
                res_json = response.json()
                return res_json["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                _rest_groq_model(payload["model"], response.headers.get("retry-after"))
                logger.warning(f"Groq 429 on {payload['model']} (attempt {attempt + 1}/{max_retries}).")
                time.sleep(0.2)
                continue
            error_code = _groq_error_code(response)
            message = f"Groq API Error {response.status_code}: {error_code} on {payload['model']}"
            if error_code == "json_validate_failed":
                # The model broke its own JSON, so another model may well succeed.
                logger.warning(message)
                last_error = RuntimeError(message)
                continue
            logger.error(message)
            raise RuntimeError(message)
        except requests.exceptions.RequestException as e:
            last_error = e
            time.sleep(0.5)

    if last_error:
        raise last_error
    raise RuntimeError("Failed to complete Groq request after retries.")


def _generate_ats_fallback_bullets(title: str, tech_stack: str, role: str) -> list[str]:
    """Draft bullets for when the model is unavailable. Facts only, so no metrics."""
    tech_parts = [t.strip() for t in (tech_stack or "").split(',') if t.strip()]
    stack = ', '.join(tech_parts[:3]) or "the project's core stack"
    clean_t = title or "this project"
    bullets = [
        f"Built {clean_t} using {stack}, delivering the core features end to end.",
        f"Implemented the main application logic for {clean_t} and connected its components.",
        "Tested and debugged the project, then documented how to set it up and run it.",
    ]
    return bullets


def generate_project_ats_bullets(
    title: str,
    tech_stack: str = "",
    role: str = "",
    description: str = "",
    target_skills: list = None,
) -> dict:
    """
    Generate 3-4 enterprise-grade, Google XYZ formula project accomplishment bullets
    from the candidate's own facts. Output with invented numbers is discarded.
    """
    from .resume_engine import score_project_ats
    from .resume_generation_service import sanitize_rewrite

    clean_title = (title or "Software Engineering Project").strip()
    clean_role = (role or "Software Engineer").strip()
    clean_tech = (tech_stack or "").strip()

    system_prompt = (
        "You are an elite Staff Software Engineer and ATS Resume Optimization Specialist (Resume Worded & Jobscan standards). "
        "Generate 3-4 powerful, technical, highly quantified accomplishment bullets for a software project to score 95-100/100 ATS. "
        "STRICT ATS EVALUATION RULES FOR EVERY BULLET:\n"
        "1. FIRST WORD MUST BE a strong action verb: 'Architected', 'Engineered', 'Developed', 'Optimized', 'Built', 'Spearheaded', 'Deployed', 'Automated', 'Integrated', 'Refactored', 'Orchestrated', or 'Scaled'.\n"
        "2. GOOGLE XYZ FORMULA: State what was accomplished, the architectural mechanism/technologies used, and the measurable outcome.\n"
        "3. OUTCOME KEYWORDS: Include words like 'reducing', 'slashing', 'increasing', 'improving', 'cutting', 'preventing', 'delivering', 'accelerating', 'scaling'.\n"
        "4. NEVER INVENT FACTS: Use only numbers, technologies and outcomes found in the input. If the input has no number, write the bullet with no metric.\n"
        "5. KEEP IT TRUE: Do not add technologies that are not in the Tech Stack or notes. The candidate must be able to defend every word in an interview.\n"
        "Return a valid JSON object with keys:\n"
        "- 'title': refined title\n"
        "- 'role': candidate role\n"
        "- 'tech_stack': comma-separated technologies\n"
        "- 'bullets': array of 3-4 string bullets meeting the formula exactly"
    )

    user_prompt = f"""
Project Title: {clean_title}
Candidate Role: {clean_role}
Tech Stack: {clean_tech or 'Not specified'}
Existing Context / Notes: {description or 'None provided'}
Target Skills: {', '.join(target_skills) if target_skills else 'Software Engineering'}
"""

    bullets = []
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw_res = call_groq_chat(messages, temperature=0.3, json_mode=True, timeout=12)
        parsed = json.loads(raw_res)
        if isinstance(parsed, dict) and parsed.get('bullets') and isinstance(parsed['bullets'], list):
            allowed = ' '.join([clean_title, clean_tech, clean_role, description or ''])
            bullets = [sanitize_rewrite(b, allowed) for b in parsed['bullets'] if isinstance(b, str) and len(b.strip()) > 15]
            bullets = [b for b in bullets if b]
            if parsed.get('tech_stack') and not clean_tech:
                clean_tech = parsed['tech_stack']
    except Exception as e:
        logger.warning(f"Groq project bullets generation error, using fallback: {e}")

    # Fallback deterministic generator if Groq is unavailable or produced fewer than 3 bullets
    if not bullets or len(bullets) < 3:
        bullets = _generate_ats_fallback_bullets(clean_title, clean_tech, clean_role)

    # Validate with scoring engine
    proj_eval = score_project_ats({
        'title': clean_title,
        'tech_stack': clean_tech,
        'bullets': bullets,
    }, target_skills)

    return {
        'title': clean_title,
        'role': clean_role,
        'tech_stack': clean_tech,
        'bullets': bullets,
        'ats_eval': proj_eval,
    }


# Tools a rewrite may not introduce unless the bullet or project already names them.
_POLISH_TECH_TERMS = (
    'redis', 'docker', 'kubernetes', 'celery', 'kafka', 'rabbitmq', 'postgresql', 'postgres',
    'mysql', 'mongodb', 'aws', 'azure', 'gcp', 'microservice', 'microservices', 'graphql',
    'nginx', 'jenkins', 'terraform', 'react', 'angular', 'vue', 'django', 'flask', 'fastapi',
    'spring', 'node.js', 'typescript', 'ci/cd', 'cache', 'caching', 'queue',
)

_WEAK_BULLET_OPENERS = (
    ('responsible for ', 'Handled '),
    ('worked on ', 'Developed '),
    ('working on ', 'Developed '),
    ('helped with ', 'Supported '),
    ('helped ', 'Supported '),
    ('made ', 'Built '),
    ('did ', 'Completed '),
    ('used ', 'Applied '),
)


def _adds_unlisted_tech(text: str, source: str) -> bool:
    """True when `text` names a tool that `source` never mentions."""
    lowered_text = text.lower()
    lowered_source = source.lower()
    for term in _POLISH_TECH_TERMS:
        pattern = rf'(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])'
        if re.search(pattern, lowered_text) and term not in lowered_source:
            return True
    return False


def _basic_bullet_cleanup(bullet: str) -> str:
    """Offline rewrite: fix the opener and punctuation, never add facts."""
    body = bullet.lstrip('•-* ').strip().rstrip('.')
    if not body:
        return ''
    lowered = body.lower()
    for weak, strong in _WEAK_BULLET_OPENERS:
        if lowered.startswith(weak):
            body = strong + body[len(weak):]
            break
    else:
        first = lowered.split()[0]
        if not (first.endswith('ed') or first in ('built', 'led', 'wrote', 'ran', 'made')):
            body = 'Developed ' + body[0].lower() + body[1:]
    return body[0].upper() + body[1:] + '.'


def polish_resume_bullet(bullet: str, role: str = "", tech_stack: str = "", include_metrics: bool = True) -> dict:
    """
    Rewrite a plain bullet in clearer, stronger language.

    Every suggestion is checked before it is returned: it may not add numbers,
    hype words or tools the bullet and project do not already contain. The
    response sets `ai` to False when the offline cleanup was used instead.
    """
    from .resume_generation_service import sanitize_rewrite

    clean_bullet = (bullet or "").strip()
    clean_role = (role or "Software Engineer").strip()
    clean_tech = (tech_stack or "").strip()
    source = f"{clean_bullet} {clean_tech}"

    system_prompt = (
        "You rewrite one resume bullet so a recruiter understands it quickly.\n"
        "RULES:\n"
        "1. One sentence, 12 to 24 words, starting with a past-tense action verb.\n"
        "2. Use only facts in the bullet and the listed tech stack. Say what was built and how.\n"
        "3. Copy existing numbers exactly. Never add a number, percentage, user count or result.\n"
        "4. Never name a tool that is not in the bullet or tech stack.\n"
        "5. Never use: robust, scalable, enterprise, high-performance, production-grade, "
        "production ready, world-class, cutting-edge, state-of-the-art, mission-critical, best-in-class.\n"
        "Return a JSON object with keys 'polished', 'alternative_1', 'alternative_2' and 'action_verb'. "
        "Make the three versions genuinely different in wording."
    )
    user_prompt = (
        f"Candidate role: {clean_role}\n"
        f"Tech stack: {clean_tech or 'not provided'}\n"
        f"Bullet: {clean_bullet}"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for attempt in range(2):
        try:
            data = json.loads(call_groq_chat(messages, temperature=0.35, json_mode=True, timeout=10))
        except Exception as e:
            logger.warning(f"Groq polish_resume_bullet fallback: {e}")
            break
        if not isinstance(data, dict):
            continue

        options = []
        for key in ('polished', 'alternative_1', 'alternative_2'):
            kept = sanitize_rewrite(data.get(key), source)
            if kept and not _adds_unlisted_tech(kept, source) and kept not in options:
                options.append(kept)
        if options:
            padded = options + ['', '']
            return {
                'original': clean_bullet,
                'polished': padded[0],
                'alternative_1': padded[1],
                'alternative_2': padded[2],
                'action_verb': options[0].split()[0],
                'metric_highlight': '',
                'bullets': options,
                'ai': True,
            }
        if attempt == 0:
            messages.append({
                "role": "user",
                "content": "Those were rejected for a banned word or an added number or tool. Follow every rule and try again.",
            })

    polished = _basic_bullet_cleanup(clean_bullet) or clean_bullet
    return {
        'original': clean_bullet,
        'polished': polished,
        'alternative_1': '',
        'alternative_2': '',
        'action_verb': polished.split()[0] if polished else '',
        'metric_highlight': '',
        'bullets': [polished] if polished else [],
        'ai': False,
    }


def tailor_resume_to_job(
    resume_summary: str,
    resume_skills: list[str],
    resume_projects: list[dict],
    job_description: str,
) -> dict:
    """
    Analyze the gap between a candidate's resume and a target Job Description.
    Extract matching keywords, missing keywords, and suggest optimized project bullets and skills.
    """
    system_prompt = (
        "You are an ATS (Applicant Tracking System) Evaluation Algorithm and Tech Career Mentor. "
        "Evaluate how well the candidate's resume matches the provided Job Description and generate tailored ATS enhancements.\n"
        "Return a valid JSON object with the following keys:\n"
        "- 'match_score': integer from 0 to 100\n"
        "- 'match_grade': string ('Excellent', 'Strong Match', 'Moderate', 'Needs Keywords')\n"
        "- 'matched_keywords': list of strings (skills/keywords present in both)\n"
        "- 'missing_critical_keywords': list of strings (top 5-8 crucial skills from the JD missing from the resume)\n"
        "- 'tailored_summary': string (rewritten summary integrating key JD requirements and target role)\n"
        "- 'tailored_skills': dictionary of categorized skills (e.g. {'Languages': '...', 'Frameworks & Libraries': '...', 'Databases': '...', 'Cloud & DevOps': '...', 'Tools & Concepts': '...'}) combining candidate skills with missing critical ATS keywords\n"
        "- 'suggested_project_improvements': list of objects with {'project_title': str, 'original_bullet': str, 'tailored_bullet': str, 'reason': str} — rewrite bullets into Google XYZ accomplishment statements ('Accomplished [X] measured by [Y] by doing [Z]') incorporating JD keywords and action verbs\n"
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
        "Never invent numbers, employers, metrics or achievements: use only the role, experience level and skills given. "
        "Return a JSON object with keys:\n"
        "- 'impact_focused': 2-3 lines about the work the candidate does, without invented metrics\n"
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


def write_tailored_summary(
    candidate_summary: str, role: str, company: str, skills: str, projects: str, budget: float = None,
) -> str:
    """Two lines aimed at the role, or '' if the model is unavailable or adds facts."""
    from .resume_generation_service import sanitize_rewrite

    source = f"{candidate_summary} {role} {company} {skills} {projects}"
    messages = [
        {"role": "system", "content": (
            "You write the summary at the top of a resume. Write 2 sentences, 25 to 45 words, with no first-person "
            "pronouns, and use the exact target role in the first sentence. "
            "Use only the facts given. Never add a number, employer, result, tool or years of experience. "
            "If a project was studied rather than built, do not claim the candidate built it. "
            "Never use: robust, scalable, enterprise, high-performance, production-grade, world-class, cutting-edge. "
            "Return a JSON object with the key 'summary'."
        )},
        {"role": "user", "content": (
            f"Target role: {role}\nTarget company: {company or 'not given'}\nCandidate's own summary: "
            f"{candidate_summary or 'none'}\nSkills: {skills or 'none'}\nProjects: {projects or 'none'}"
        )},
    ]
    try:
        data = json.loads(call_groq_chat(
            messages, temperature=0.3, max_tokens=400, json_mode=True, timeout=12, budget=budget))
    except Exception as e:
        logger.warning(f"AI summary unavailable: {e}")
        return ""
    kept = sanitize_rewrite(data.get("summary") if isinstance(data, dict) else "", source)
    if not kept or role.lower() not in kept.lower() or _adds_unlisted_tech(kept, source):
        return ""
    return kept


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


def _clean_critique(critique: dict, parsed_resume: dict, sections_present: list) -> dict:
    """Remove model claims the parsed resume disproves, and rewrites with invented numbers."""
    from .resume_generation_service import sanitize_rewrite

    def wrongly_missing(change: dict) -> bool:
        text = f"{change.get('issue', '')} {change.get('category', '')}".lower()
        if 'missing' not in text and 'lack' not in text and 'no ' not in text:
            return False
        named = [name for name in ("education", "experience", "skills", "summary", "projects") if name in text]
        return bool(named) and all(name in sections_present or (name == 'experience' and 'projects' in sections_present)
                                   for name in named)

    critique['top_changes_to_make'] = [
        c for c in critique.get('top_changes_to_make') or [] if isinstance(c, dict) and not wrongly_missing(c)
    ]
    rewrites = []
    for item in critique.get('rewritten_bullets') or []:
        if isinstance(item, dict) and sanitize_rewrite(item.get('improved'), str(item.get('original', ''))):
            rewrites.append(item)
    critique['rewritten_bullets'] = rewrites
    return critique


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
        "'sections_present' lists what the resume contains: never call any of those sections missing. "
        "Fresher resumes may have projects instead of work experience, which is acceptable. "
        "Be honest in all advice: never tell the candidate to add a skill, tool, course or number they do not have. "
        "List such gaps as things to learn, and never put made-up numbers in an example. "
        "Return a valid JSON object with the following keys:\n"
        "- 'overall_score': integer from 20 to 98 (accurate ATS score)\n"
        "- 'grade': string (e.g. 'Strong match', 'Moderate - needs keywords', 'Critical gaps'). Never claim an ATS pass or pass rate: nobody can know one from outside.\n"
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
        "candidate_education": parsed_resume.get("education") or {},
        "sections_present": [
            name for name in ("summary", "skills", "experience", "projects", "education", "certifications")
            if parsed_resume.get(name)
        ],
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
        critique = json.loads(response_text)
        return _clean_critique(critique, parsed_resume, clean_payload["sections_present"])
    except Exception as e:
        logger.warning(f"Error generating AI resume critique: {e}")
        return {
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
            "matched_skills": [s for s in (target_skills or []) if has_keyword(s, resume_text(parsed_resume))],
            "rewritten_bullets": [],
            "quick_wins": [
                "Quantify your top project accomplishment with an estimated metric",
                "Move matching technical skills to the top of your skills block",
                "Ensure standard ATS single-column formatting"
            ]
        }


# The resume builder scores with these bands. Totals are added up here so the
# number on screen always equals the parts shown under it.
REVIEW_CHECKS = (
    ('Clarity and impact', 30),
    ('Keywords for the role', 25),
    ('Proof in projects and experience', 25),
    ('Structure and completeness', 20),
)
REVIEW_PROJECT_DIMENSIONS = (
    ('action_verbs', 25),
    ('google_xyz', 25),
    ('quantified_metrics', 20),
    ('tech_relevance', 20),
    ('architecture_scale', 10),
)
_UNEARNED_CLAIMS = re.compile(r'\b(years?|experienced|expert|seasoned|veteran|proven)\b', re.IGNORECASE)


def _bounded_int(value, maximum: int) -> int:
    try:
        return max(0, min(maximum, int(round(float(value)))))
    except (TypeError, ValueError):
        return 0


def review_grade(score: int) -> str:
    if score >= 85:
        return 'Strong'
    if score >= 70:
        return 'Good'
    if score >= 50:
        return 'Needs work'
    return 'Weak'


def _resume_for_ai(resume: dict) -> dict:
    """The resume without identity: the model scores the content, not the person."""
    contact = resume.get('contact') if isinstance(resume.get('contact'), dict) else {}
    return {
        'has_contact_details': {key: bool(contact.get(key)) for key in ('email', 'phone', 'linkedin', 'github')},
        'summary': resume.get('summary') or '',
        'skills': resume.get('skills') or [],
        'experience': [
            {'role': e.get('role', ''), 'bullets': e.get('bullets') or []}
            for e in resume.get('experience') or [] if isinstance(e, dict)
        ],
        'projects': [
            {
                'index': position,
                'title': p.get('title', ''),
                'tech_stack': p.get('tech_stack', ''),
                'bullets': p.get('bullets') or [],
            }
            for position, p in enumerate(resume.get('projects') or []) if isinstance(p, dict)
        ],
        'education': resume.get('education') or [],
        'certifications': resume.get('certifications') or [],
    }


def review_resume_with_ai(resume: dict, target_skills: list = None, role_title: str = "") -> dict:
    """
    Score a resume with the model. Raises when the model cannot give a usable
    answer, so the caller can say the score did not come from AI.
    """
    bands = ', '.join(f"'{name}' out of {maximum}" for name, maximum in REVIEW_CHECKS)
    dimensions = ', '.join(f"'{name}' 0-{maximum}" for name, maximum in REVIEW_PROJECT_DIMENSIONS)
    system_prompt = (
        "You are an expert technical recruiter scoring a resume against target role requirements. Judge accurately and objectively based on what is written.\n"
        "Fresher resumes may feature high-impact technical projects and no work experience; that is completely acceptable.\n"
        "Reward specific, believable work that names the tools used and states results the candidate could defend in an interview. Do not reward numbers that look invented, such as round percentages with no stated baseline. A resume that shows most of the target skills inside described work, with clear structure and strong verbs, scores 85 or more; one missing core skills or giving no specifics scores 50 to 75.\n"
        "Return a JSON object with exactly these keys:\n"
        f"- 'checks': list of objects with 'name', 'score' and 'detail' for these bands: {bands}. "
        "'detail' is one plain sentence naming what you saw.\n"
        "- 'fixes': up to 4 short, specific things only the candidate can do, such as adding a real result.\n"
        "- 'missing_skills': up to 6 skills from target_skills that the resume does not show.\n"
        f"- 'projects': one object per project with 'index' and {dimensions}."
    )
    user_prompt = json.dumps({
        'target_role': role_title or 'Software Engineer',
        'target_skills': (target_skills or [])[:30],
        'resume': _resume_for_ai(resume),
    }, default=str)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    data = json.loads(call_groq_chat(messages, temperature=0, max_tokens=1200, json_mode=True, timeout=12, max_retries=3))

    answered = {
        str(item.get('name', '')).lower(): item
        for item in data.get('checks') or [] if isinstance(item, dict)
    }
    checks = []
    for name, maximum in REVIEW_CHECKS:
        item = answered.get(name.lower())
        if item is None:
            raise ValueError(f"AI review left out '{name}'")
        checks.append({
            'name': name,
            'score': _bounded_int(item.get('score'), maximum),
            'max_score': maximum,
            'detail': str(item.get('detail') or '')[:220],
        })

    plain_resume = resume_text(_resume_for_ai(resume))
    project_count = len(resume.get('projects') or [])
    project_scores = {}
    for item in data.get('projects') or []:
        if not isinstance(item, dict):
            continue
        position = _bounded_int(item.get('index'), max(project_count - 1, 0))
        breakdown = {name: _bounded_int(item.get(name), maximum) for name, maximum in REVIEW_PROJECT_DIMENSIONS}
        project_scores[position] = {'score': sum(breakdown.values()), 'breakdown': breakdown}

    score = sum(check['score'] for check in checks)
    return {
        'overall_score': score,
        'grade': review_grade(score),
        'checks': checks,
        'fixes': [str(fix)[:200] for fix in (data.get('fixes') or []) if isinstance(fix, str)][:4],
        # The model can name a skill the resume already shows, so check it here.
        'missing_skills': [
            str(skill)[:40] for skill in (data.get('missing_skills') or [])
            if isinstance(skill, str) and not has_keyword(skill, plain_resume)
        ][:6],
        'project_scores': project_scores,
    }


def enhance_resume_items(items: list, target_skills: list = None, role_title: str = "", allow_metrics: bool = False) -> dict:
    """
    Rewrite resume text in place to maximize ATS compatibility. `items` are {'id', 'kind', 'text', 'source'}, where
    `source` is everything the candidate wrote that the rewrite may draw on.
    Returns {id: rewrite} and weaves in relevant target ATS keywords.
    """
    from .resume_generation_service import sanitize_rewrite

    if not items:
        return {}
    system_prompt = (
        "You are an ATS Resume Optimizer. Improve the candidate's resume text to maximize ATS scoring and recruiter impact.\n"
        "RULES:\n"
        "1. A bullet is one punchy sentence of 12 to 28 words starting with a strong past-tense action verb (e.g. Engineered, Architected, Developed, Implemented, Optimized, Deployed).\n"
        "2. A summary is 2 professional sentences targeting the role and highlighting core technical capabilities.\n"
        "3. Incorporate relevant target skills (ATS keywords) naturally into the bullets and summary where appropriate.\n"
        "4. Follow the Google XYZ formula: Accomplished [X] measured by [Y] by doing [Z], using realistic technical metrics (e.g. latency, throughput, scale, %, ms, test coverage) where applicable.\n"
        "5. Avoid filler words: robust, cutting-edge, state-of-the-art, rockstar, passionate.\n"
        "Return a JSON object with key 'rewrites': a list of objects with 'id' and 'text', one per item."
    )
    user_prompt = json.dumps({
        'target_role': role_title or 'Software Engineer',
        'target_skills': (target_skills or [])[:20],
        'items': [{'id': i['id'], 'kind': i['kind'], 'text': i['text'], 'source': i['source']} for i in items],
    }, default=str)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    data = json.loads(call_groq_chat(messages, temperature=0.3, max_tokens=1200, json_mode=True, timeout=12, max_retries=3))

    by_id = {item['id']: item for item in items}
    target_skills_str = ' '.join(str(s) for s in (target_skills or []))
    kept = {}
    for rewrite in data.get('rewrites') or []:
        if not isinstance(rewrite, dict):
            continue
        item = by_id.get(rewrite.get('id'))
        text = re.sub(r'[<>]', '', str(rewrite.get('text') or '')).strip()
        if item is None or not text or text == item['text'] or len(text) > 480:
            continue
        allowed = f"{item['text']} {item['source']} {target_skills_str}".strip()
        if allow_metrics:
            cleaned_text = sanitize_rewrite(text, allowed, allow_metrics=True) or text.strip()
        else:
            cleaned_text = sanitize_rewrite(text, allowed, allow_metrics=False)
            if not cleaned_text or _adds_unlisted_tech(cleaned_text, allowed):
                continue
        if _UNEARNED_CLAIMS.search(cleaned_text) and not _UNEARNED_CLAIMS.search(allowed):
            continue
        kept[item['id']] = cleaned_text
    return kept


# Skills we can recognise in a job description, grouped the way a resume lists them.
JD_SKILL_MAP = {
    'Languages': [
        'Python', 'JavaScript', 'TypeScript', 'Java', 'Golang', 'C++', 'C#', 'Rust', 'SQL',
        'PHP', 'Ruby', 'Swift', 'Kotlin', 'Scala', 'Bash', 'HTML', 'CSS',
    ],
    'Frameworks & Libraries': [
        'Django', 'FastAPI', 'Flask', 'React', 'Next.js', 'Node.js', 'Express.js', 'Spring Boot',
        'Angular', 'Vue.js', 'Redux', 'Tailwind CSS', 'GraphQL', 'gRPC', 'PyTorch', 'TensorFlow',
        'Pandas', 'NumPy', 'Scikit-Learn', 'Selenium', 'Playwright', 'Flutter', 'React Native',
    ],
    'Databases & Caching': [
        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Cassandra', 'Elasticsearch', 'DynamoDB',
        'SQLite', 'Oracle', 'Snowflake', 'BigQuery',
    ],
    'Cloud & DevOps': [
        'Docker', 'Kubernetes', 'AWS', 'GCP', 'Azure', 'CI/CD', 'GitHub Actions', 'Jenkins',
        'Terraform', 'Linux', 'Nginx', 'Kafka', 'Celery', 'RabbitMQ', 'Prometheus', 'Grafana', 'Git',
    ],
    'Tools & Concepts': [
        'Microservices', 'REST API', 'Distributed Systems', 'System Design', 'JWT',
        'Unit Testing', 'Agile', 'Scrum', 'Power BI', 'Tableau', 'Excel', 'Machine Learning',
    ],
}


def _mentions_skill(skill: str, text: str) -> bool:
    return re.search(rf'(?<![a-z0-9+#.]){re.escape(skill.lower())}(?![a-z0-9+#])', text) is not None


def extract_jd_skills(job_description: str) -> list:
    """Skills named in the job description, in the order of JD_SKILL_MAP."""
    lowered = (job_description or '').lower()
    return [
        skill
        for group in JD_SKILL_MAP.values()
        for skill in group
        if _mentions_skill(skill, lowered)
    ]


def detect_job_title(job_description: str) -> str:
    """Best-effort title from the first short line of the posting."""
    for line in (job_description or '').splitlines():
        line = line.strip(' \t:-*#')
        if 4 <= len(line) <= 70 and re.search(
            r'engineer|developer|analyst|intern|designer|manager|tester|architect|consultant|scientist|sdet',
            line, re.I,
        ):
            return re.sub(r'^(job title|title|role|position)\s*[:\-]\s*', '', line, flags=re.I)
    return ''


def _candidate_skill_groups(candidate: dict) -> dict:
    skills = candidate.get('skills') or {}
    if isinstance(skills, list):
        return {'Skills': [str(item).strip() for item in skills if str(item).strip()]}
    groups = {}
    for name, value in skills.items():
        items = value if isinstance(value, list) else str(value or '').split(',')
        cleaned = [str(item).strip() for item in items if str(item).strip()]
        if cleaned:
            groups[name] = cleaned
    return groups


def analyse_job_for_candidate(job_description: str, candidate: dict) -> dict:
    """Split the job's skills into those the candidate already lists and the rest."""
    required = extract_jd_skills(job_description)
    candidate_text = json.dumps(candidate or {}, default=str).lower()
    matched = [skill for skill in required if _mentions_skill(skill, candidate_text)]
    return {
        'required': required,
        'matched': matched,
        'missing': [skill for skill in required if skill not in matched],
    }


def _job_summary(candidate: dict, job_title: str, skills: list) -> str:
    """A summary built only from what the candidate gave us, plus the target role."""
    existing = str(candidate.get('summary') or '').strip()
    source = f"{json.dumps(candidate, default=str)} {job_title} {' '.join(skills)}"
    fallback = existing or (
        f"Candidate targeting {job_title or 'software'} roles, with skills in {', '.join(skills[:5])}."
        if skills else ''
    )
    if not skills and not existing:
        return ''

    from .resume_generation_service import sanitize_rewrite

    messages = [
        {
            "role": "system",
            "content": (
                "Write a 2 sentence resume summary for the target role using only the supplied facts. "
                "Do not say the candidate is experienced. Do not add years of experience, numbers, employers, results or tools. Do not use hype "
                "words such as robust, scalable, enterprise, results-driven or passionate. "
                'Return JSON: {"summary": "..."}'
            ),
        },
        {
            "role": "user",
            "content": json.dumps({
                "target_role": job_title,
                "skills": skills[:12],
                "current_summary": existing,
                "projects": [p.get('title') for p in candidate.get('projects') or [] if isinstance(p, dict)][:4],
            }),
        },
    ]
    try:
        data = json.loads(call_groq_chat(messages, temperature=0.3, json_mode=True, timeout=10))
        summary = sanitize_rewrite(data.get('summary') if isinstance(data, dict) else '', source)
        claims_experience = re.search(r'\bexperienced?\b|\byears?\b', summary, re.I)
        if summary and not claims_experience and not _adds_unlisted_tech(summary, source):
            return summary
    except Exception as e:
        logger.warning(f"Groq job summary fallback: {e}")
    return fallback


def build_resume_for_job(
    job_description: str,
    job_title: str = "",
    candidate_info: dict = None,
    confirmed_skills: list = None,
    practice_projects: list = None,
) -> dict:
    """
    Arrange the candidate's own resume for one job.

    Skills the job asks for are moved to the front, and skills the candidate
    ticked as true are added. Experience, education and certifications are only
    ever copied from the candidate, so a blank field stays blank. Practice
    projects appear only when the candidate picked them, and are labelled.
    """
    from .resume_engine import inject_missing_ats_skills
    from .resume_parser import evaluate_uploaded_resume_ats

    candidate = dict(candidate_info or {})
    analysis = analyse_job_for_candidate(job_description, candidate)
    job_title = (job_title or detect_job_title(job_description)).strip()

    confirmed = [skill for skill in (confirmed_skills or []) if skill]
    groups = _candidate_skill_groups(candidate)
    if confirmed:
        from .resume_engine import inject_missing_ats_skills
        groups = inject_missing_ats_skills(groups, confirmed)

    priority = {skill.lower() for skill in analysis['required']}
    skills = {}
    for name, items in groups.items():
        if isinstance(items, list):
            sorted_items = sorted(items, key=lambda item: item.lower() not in priority)
            skills[name] = ', '.join(sorted_items)
        else:
            skills[name] = str(items)

    projects = [p for p in candidate.get('projects') or [] if isinstance(p, dict)]
    def relevance(project):
        text = json.dumps(project, default=str).lower()
        return -sum(1 for skill in analysis['required'] if _mentions_skill(skill, text))
    projects = sorted(projects, key=relevance) + list(practice_projects or [])

    listed_skills = [item for items in groups.values() for item in items]
    resume = dict(candidate)
    resume.update({
        'name': candidate.get('name') or '',
        'contact': candidate.get('contact') or {},
        'skills': skills,
        'projects': projects,
        'education': candidate.get('education') or {},
        'certifications': candidate.get('certifications') or [],
    })
    resume['summary'] = _job_summary(resume, job_title, listed_skills)

    final = analyse_job_for_candidate(job_description, resume)
    ats_eval = evaluate_uploaded_resume_ats(resume, analysis['required'])
    return {
        'resume': resume,
        'job_title': job_title,
        'target_skills': analysis['required'],
        'matched_skills': final['matched'],
        'missing_skills': final['missing'],
        'ats_score': ats_eval.get('overall_score', ats_eval.get('score', 0)),
        'ats_eval': ats_eval,
    }



# ---------------------------------------------------------------------------
# Resume fitting: reverse engineer the posting, then fit the candidate to it.
# The prompts live in resume_prompts.py; everything below is what makes their
# rules hold even when the model ignores them.
# ---------------------------------------------------------------------------

BLUEPRINT_CACHE_SECONDS = 24 * 60 * 60
# The whole fitting request has to answer well inside the web server's 60s limit.
FIT_TIME_BUDGET = 40
_FIT_CANDIDATE_FIELDS = (
    'summary', 'skills', 'experience', 'projects', 'education', 'certifications', 'achievements',
)
_BLUEPRINT_LISTS = ('must_have', 'good_to_have', 'implied', 'soft_skills', 'duties')
_SENIORITY_LEVELS = ('intern', 'fresher', 'junior', 'mid', 'senior', 'lead')
_SECTION_NAMES = ('Summary', 'Skills', 'Experience', 'Projects', 'Education', 'Certifications', 'Achievements')


def _clean_terms(value, limit: int = 25, max_len: int = 80) -> list:
    """A list of short non-empty strings, without repeats."""
    if isinstance(value, str):
        value = value.split(',')
    seen, kept = set(), []
    for item in value if isinstance(value, (list, tuple)) else []:
        text = ' '.join(str(item or '').split())
        if text and len(text) <= max_len and text.lower() not in seen:
            seen.add(text.lower())
            kept.append(text)
    return kept[:limit]


def _fallback_blueprint(job_description: str, job_title: str, job_skills) -> dict:
    """What we can say about a posting without a model: its listed and recognised skills."""
    must = _clean_terms(job_skills) or extract_jd_skills(job_description)
    return {
        'ai': False,
        'target_title': (job_title or detect_job_title(job_description)).strip(),
        'seniority': '', 'domain': '',
        'must_have': must, 'good_to_have': [], 'implied': [], 'soft_skills': [], 'duties': [],
    }


def reverse_engineer_job(
    job_description: str, job_title: str = "", company: str = "", job_skills="", posting=None,
) -> dict:
    """
    The posting as a blueprint of what its ATS search looks for.

    Depends only on the posting, so it is worked out once: kept on the
    JobPosting when there is one (so every visitor sees the same keyword list,
    across restarts), and in the cache for pasted job descriptions.
    """
    import hashlib
    from django.core.cache import cache
    from .resume_prompts import build_blueprint_messages

    skills_text = ', '.join(_clean_terms(job_skills))
    digest = hashlib.sha256(
        '\x1f'.join([job_title or '', company or '', skills_text, job_description or '']).encode('utf-8')
    ).hexdigest()
    cache_key = f'jd-blueprint:v1:{digest}'
    stored = getattr(posting, 'ats_blueprint', None) or {}
    if stored.get('digest') == digest and stored.get('must_have'):
        return stored
    cached = cache.get(cache_key)
    if cached:
        return cached

    fallback = _fallback_blueprint(job_description, job_title, job_skills)
    if not (job_description or '').strip():
        return fallback
    try:
        messages = build_blueprint_messages(job_description, job_title, company, skills_text)
        data = json.loads(call_groq_chat(
            messages, temperature=0.1, max_tokens=900, json_mode=True, timeout=10, max_retries=2, budget=14))
    except Exception as e:
        logger.warning(f"Job blueprint unavailable, using listed skills: {e}")
        return fallback
    if not isinstance(data, dict):
        return fallback

    blueprint = {name: _clean_terms(data.get(name)) for name in _BLUEPRINT_LISTS}
    blueprint['implied'] = blueprint['implied'][:4]
    # A term the posting never contains was invented by the model, not found in it.
    posting_text = f"{job_title} {skills_text} {job_description}"
    for name in ('must_have', 'good_to_have'):
        blueprint[name] = [t for t in blueprint[name] if _term_in_text(t, posting_text)]
    # Skills the employer listed on the posting are required whatever the model says.
    for skill in _clean_terms(job_skills):
        if not any(skill.lower() == t.lower() for t in blueprint['must_have']):
            blueprint['must_have'].append(skill)
    must_lower = {t.lower() for t in blueprint['must_have']}
    blueprint['good_to_have'] = [t for t in blueprint['good_to_have'] if t.lower() not in must_lower]

    seniority = str(data.get('seniority') or '').strip().lower()
    blueprint.update({
        'ai': True,
        'target_title': (job_title or str(data.get('target_title') or '')).strip() or fallback['target_title'],
        'seniority': seniority if seniority in _SENIORITY_LEVELS else '',
        'domain': ' '.join(str(data.get('domain') or '').split())[:80],
    })
    if not blueprint['must_have']:
        return fallback
    blueprint['digest'] = digest
    cache.set(cache_key, blueprint, BLUEPRINT_CACHE_SECONDS)
    if posting is not None and getattr(posting, 'pk', None):
        try:
            type(posting).objects.filter(pk=posting.pk).update(ats_blueprint=blueprint)
        except Exception as e:
            logger.warning(f"Could not store the job blueprint: {e}")
    return blueprint


def _term_forms(term: str) -> list:
    from .resume_engine import term_forms
    return term_forms(term)


def _term_in_text(term: str, text: str) -> bool:
    from .resume_engine import has_term
    return has_term(term, text)


def blueprint_coverage(blueprint: dict, text: str) -> dict:
    """
    How much of what the job searches for is literally in `text`.

    This is the product's match figure: must-haves weigh three times a
    good-to-have, and nothing is rounded up. It measures keyword coverage, which
    is what we can know; it is not any employer's ATS score.
    """
    def split(terms):
        found = [t for t in terms if _term_in_text(t, text)]
        return found, [t for t in terms if t not in found]

    must_found, must_missing = split(blueprint.get('must_have') or [])
    good_found, good_missing = split(blueprint.get('good_to_have') or [])
    total = 3 * (len(must_found) + len(must_missing)) + len(good_found) + len(good_missing)
    score = round(100 * (3 * len(must_found) + len(good_found)) / total) if total else None
    return {
        'score': score,
        'must_have_found': must_found, 'must_have_missing': must_missing,
        'good_to_have_found': good_found, 'good_to_have_missing': good_missing,
    }


def _same_skill(model_skill: str, listed: set) -> bool:
    """The model may respell a skill the blueprint's way, but not add one."""
    return any(
        form.lower() in listed or any(_term_in_text(form, known) and _term_in_text(known, form) for known in listed)
        for form in _term_forms(model_skill)
    )


def _fit_skills(altered, original: dict, confirmed: list) -> dict:
    """The model's grouping and order, holding only skills the candidate has."""
    from .resume_engine import inject_missing_ats_skills

    def split(value):
        parts = value if isinstance(value, (list, tuple)) else str(value or '').split(',')
        return [str(part).strip() for part in parts if str(part).strip()]

    own = [part for value in (original or {}).values() for part in split(value)]
    listed = {part.lower() for part in own + list(confirmed)}
    kept, used = {}, []
    for group, value in altered.items() if isinstance(altered, dict) else []:
        parts = [part for part in split(value) if _same_skill(part, listed)]
        if parts:
            kept[str(group)] = ', '.join(parts)
            used.extend(parts)
    if not kept:
        return inject_missing_ats_skills(dict(original or {}), confirmed)
    # Nothing the candidate listed may vanish because the model forgot it.
    used_text = ', '.join(used)
    dropped = [skill for skill in own + list(confirmed) if not _term_in_text(skill, used_text)]
    return inject_missing_ats_skills(kept, dropped) if dropped else kept


_TARGETING_WORDS = r'(?:targeting|seeking|pursuing|aspiring|applying for|interested in|aiming for|for|as)'


def _claims_unheld_title(summary: str, title: str, source: str) -> bool:
    """
    True when the summary calls the candidate by a job title they have never held.

    "Graduate targeting a Business Analyst role" is an aim. "Business Analyst
    skilled in..." is a claim, and a recruiter will ask where they were one.
    """
    title = ' '.join((title or '').split())
    if not title or not summary or title.lower() in (source or '').lower():
        return False
    name = re.escape(title)
    for match in re.finditer(name, summary, re.I):
        before = summary[max(0, match.start() - 40):match.start()]
        after = summary[match.end():match.end() + 20]
        aimed = re.search(rf'{_TARGETING_WORDS}\s+(?:an?\s+|the\s+)?(?:[\w-]+\s+)?$', before, re.I)
        named_as_role = re.match(r'\s+(?:role|position|opening|job|internship)s?\b', after, re.I)
        if not aimed and not named_as_role:
            return True
    return False


def _apply_skill_evidence(candidate: dict, skill_evidence, confirmed: list) -> dict:
    """Record where the candidate says they used a confirmed skill, on that entry."""
    if not isinstance(skill_evidence, dict) or not skill_evidence:
        return candidate
    allowed = {skill.lower(): skill for skill in confirmed}
    candidate = dict(candidate)
    projects = [dict(p) for p in candidate.get('projects') or [] if isinstance(p, dict)]
    experience = [dict(e) for e in candidate.get('experience') or [] if isinstance(e, dict)]

    def label(text):
        return ' '.join(str(text or '').lower().split())

    for raw_skill, where in skill_evidence.items():
        skill = allowed.get(label(raw_skill))
        if not skill or not label(where):
            continue
        for project in projects:
            if label(project.get('title')) == label(where):
                stack = project.get('tech_stack') or ''
                stack = ', '.join(stack) if isinstance(stack, (list, tuple)) else str(stack)
                if not _term_in_text(skill, stack):
                    project['tech_stack'] = f"{stack}, {skill}" if stack.strip() else skill
        for entry in experience:
            if label(f"{entry.get('role') or ''} at {entry.get('company') or ''}") == label(where):
                tools = str(entry.get('tools_used') or '')
                if not _term_in_text(skill, tools):
                    entry['tools_used'] = f"{tools}, {skill}" if tools.strip() else skill
    if projects:
        candidate['projects'] = projects
    if experience:
        candidate['experience'] = experience
    return candidate


def _fit_bullets(bullets, source: str, guarded_terms: list) -> list:
    """Bullets that say nothing the candidate's own facts do not."""
    from .resume_generation_service import sanitize_rewrite

    if isinstance(bullets, str):
        bullets = [part for part in re.split(r"(?<=[.!?])\s+|\n+", bullets) if part.strip()]
    kept = []
    for bullet in bullets if isinstance(bullets, list) else []:
        text = sanitize_rewrite(bullet, source)
        if len(text) < 20 or _adds_unlisted_tech(text, source):
            continue
        if any(_term_in_text(term, text) and not _term_in_text(term, source) for term in guarded_terms):
            continue
        if any(claim.lower() not in source.lower() for claim in _UNEARNED_CLAIMS.findall(text)):
            continue
        kept.append(text)
    return kept


def _fit_entries(altered, originals: list, keys: tuple, source: str, guarded_terms: list) -> list:
    """
    The candidate's entries in the model's order, with only the bullets reworded.

    Titles, employers, roles, dates and tech stacks are copied from the candidate,
    never from the model. An entry the model left out or emptied keeps its own text.
    """
    def identity(entry):
        return tuple(' '.join(str(entry.get(k) or '').lower().split()) for k in keys)

    originals = [entry for entry in originals or [] if isinstance(entry, dict)]
    remaining = list(originals)
    result = []
    for entry in altered if isinstance(altered, list) else []:
        if not isinstance(entry, dict):
            continue
        match = next((o for o in remaining if identity(o) == identity(entry)), None)
        if match is None:
            continue
        remaining.remove(match)
        fitted = dict(match)
        # Checked against this entry alone: a number or tool from another project
        # is still a false claim about this one.
        bullets = _fit_bullets(entry.get('bullets'), json.dumps(match, default=str), guarded_terms)
        if bullets:
            fitted['bullets'] = bullets
        result.append(fitted)
    return result + remaining


def fit_resume_to_job(
    job_description: str,
    candidate: dict,
    job_title: str = "",
    company: str = "",
    job_skills="",
    confirmed_skills: list = None,
    experience_level: str = "",
    posting=None,
    skill_evidence: dict = None,
) -> dict:
    """
    Fit a candidate's resume to one job without adding a single fact.

    `skill_evidence` maps a confirmed skill to the project title or
    "Role at Company" where the candidate says they used it. That is the
    candidate's own statement, so the skill joins that entry's tech stack and
    may then be written into its bullets.

    The posting is reverse engineered into a blueprint, the model rewrites the
    candidate's own facts in the blueprint's words, and then every line is
    checked against what the candidate supplied. Requirements the candidate
    does not show come back in `skills_to_confirm` instead of in the resume.
    The match figure is keyword coverage measured here, before and after.
    """
    from .resume_generation_service import sanitize_rewrite
    from .resume_prompts import build_fit_messages

    import time

    started = time.monotonic()
    # Only resume content goes to the model. Name, email, phone and links are
    # never needed to reword a bullet, so they never leave the server.
    candidate = {
        key: value for key, value in (candidate or {}).items()
        if key in _FIT_CANDIDATE_FIELDS and value
    }
    confirmed = _clean_terms(confirmed_skills)
    candidate = _apply_skill_evidence(candidate, skill_evidence, confirmed)
    summary = str(candidate.get('summary') or '').strip()
    skills = _candidate_skill_groups(candidate)
    skills = {group: ', '.join(items) for group, items in skills.items()}
    projects = [p for p in candidate.get('projects') or [] if isinstance(p, dict)]
    experience = [e for e in candidate.get('experience') or [] if isinstance(e, dict)]

    blueprint = reverse_engineer_job(job_description, job_title, company, job_skills, posting=posting)
    source = f"{json.dumps(candidate, default=str)} {' '.join(confirmed)}"
    guarded_terms = blueprint['must_have'] + blueprint['good_to_have']

    def text_of(summary_, skills_, experience_, projects_):
        return json.dumps([summary_, skills_, experience_, projects_], default=str)

    before = blueprint_coverage(blueprint, text_of(summary, skills, experience, projects))
    result = {
        'ai': False,
        'blueprint': blueprint,
        'altered_summary': summary,
        'altered_skills': _fit_skills({}, skills, confirmed),
        'altered_experience': experience,
        'altered_projects': projects,
        'section_order': [],
        'evidence_map': [],
        'key_alterations': [],
    }

    data = None
    remaining = FIT_TIME_BUDGET - (time.monotonic() - started)
    has_content = bool(summary or projects or experience)
    if has_content and remaining >= 10:
        try:
            messages = build_fit_messages(blueprint, candidate, confirmed, company, experience_level)
            data = json.loads(call_groq_chat(
                messages, temperature=0.2, max_tokens=4000, json_mode=True,
                timeout=18, max_retries=2, budget=min(24, remaining),
            ))
        except Exception as e:
            logger.warning(f"Resume fitting unavailable, leaving the resume as supplied: {e}")
    elif has_content:
        logger.warning("Resume fitting skipped: the job blueprint used up the time budget.")

    # A reply with none of the expected keys is a broken generation, not a rewrite.
    if isinstance(data, dict) and any(
        data.get(key) for key in ('altered_summary', 'altered_skills', 'altered_experience', 'altered_projects')
    ):
        result['ai'] = True
        # The target role and company are the job's words, so the summary may use them.
        summary_source = f"{source} {blueprint['target_title']} {company}"
        new_summary = sanitize_rewrite(data.get('altered_summary'), summary_source)
        adds_claim = any(c.lower() not in source.lower() for c in _UNEARNED_CLAIMS.findall(new_summary))
        adds_skill = any(_term_in_text(t, new_summary) and not _term_in_text(t, summary_source) for t in guarded_terms)
        claims_title = _claims_unheld_title(new_summary, blueprint['target_title'], source)
        if (new_summary and not adds_claim and not adds_skill and not claims_title
                and not _adds_unlisted_tech(new_summary, summary_source)):
            result['altered_summary'] = new_summary
        elif blueprint['target_title'] and FIT_TIME_BUDGET - (time.monotonic() - started) >= 8:
            # The long prompt overreached, so ask the short strict one for just this.
            proven = [t for t in blueprint['must_have'] if _term_in_text(t, source)]
            retry = write_tailored_summary(
                summary, blueprint['target_title'], company, ', '.join(proven[:6]),
                ', '.join(str(p.get('title') or '') for p in projects[:3]),
                budget=FIT_TIME_BUDGET - (time.monotonic() - started),
            )
            if retry and not _claims_unheld_title(retry, blueprint['target_title'], source):
                result['altered_summary'] = retry

        result['altered_skills'] = _fit_skills(data.get('altered_skills'), skills, confirmed)
        result['altered_experience'] = _fit_entries(
            data.get('altered_experience'), experience, ('company', 'role'), source, guarded_terms)
        result['altered_projects'] = _fit_entries(
            data.get('altered_projects'), projects, ('title',), source, guarded_terms)
        result['section_order'] = [
            name for name in _clean_terms(data.get('section_order')) if name in _SECTION_NAMES
        ]
        result['key_alterations'] = _clean_terms(data.get('key_alterations'), limit=5, max_len=300)
        result['evidence_map'] = [
            {
                'requirement': str(row.get('requirement') or '').strip(),
                'priority': row.get('priority'),
                'status': row.get('status'),
                'evidence': str(row.get('evidence') or '').strip(),
            }
            for row in data.get('evidence_map') or []
            if isinstance(row, dict) and row.get('status') in ('proven', 'adjacent', 'missing')
            and str(row.get('requirement') or '').strip()
        ]

    after = blueprint_coverage(blueprint, text_of(
        result['altered_summary'], result['altered_skills'],
        result['altered_experience'], result['altered_projects'],
    ))

    # What to ask the candidate is decided by what is really absent, not by the model's list.
    asked = {}
    for row in (data.get('skills_to_confirm') or []) if isinstance(data, dict) else []:
        if isinstance(row, dict) and str(row.get('skill') or '').strip():
            asked[str(row['skill']).strip().lower()] = row
    to_confirm = []
    for priority, terms in (('must_have', after['must_have_missing']), ('good_to_have', after['good_to_have_missing'])):
        for term in terms:
            row = asked.get(term.lower(), {})
            to_confirm.append({
                'skill': term,
                'priority': priority,
                'closest_evidence': str(row.get('closest_evidence') or '').strip(),
                'question': str(row.get('question') or '').strip() or f"Have you worked with {term}?",
            })

    # `tools_used` only told the model where a confirmed skill belongs.
    result['altered_experience'] = [
        {k: v for k, v in entry.items() if k != 'tools_used'} for entry in result['altered_experience']
    ]
    # Older copies of the page read the skills block from these names.
    result['suggested_skills'] = result['reordered_skills'] = result['altered_skills']
    # Whether any wording really changed, so the page never announces a rewrite
    # that every check rejected.
    result['changed'] = (
        result['altered_summary'] != summary
        or result['altered_projects'] != projects
        or result['altered_experience'] != [
            {k: v for k, v in entry.items() if k != 'tools_used'} for entry in experience
        ]
    )
    result.update({
        'match_score': after['score'],
        'match_score_before': before['score'],
        'matching_keywords': after['must_have_found'] + after['good_to_have_found'],
        'missing_keywords': after['must_have_missing'] + after['good_to_have_missing'],
        'coverage': after,
        'skills_to_confirm': to_confirm,
    })
    return result
