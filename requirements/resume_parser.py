"""
Resume Document Parser & Reverse-Engineered ATS Evaluation Engine.
Supports PDF (.pdf) and Word (.docx, .doc) parsing with structural AI extraction,
deterministic regex fallbacks, and multi-factor ATS diagnostic scoring.
"""

import io
import re
import json
import logging
from typing import Dict, Any, List, Optional
from .ai_engine import call_groq_chat
from .resume_engine import has_keyword, has_term, job_match_limit, resume_text, score_project_ats

logger = logging.getLogger(__name__)


def extract_text_from_file_bytes(file_bytes: bytes, filename: str) -> str:
    """Extract raw text from PDF or DOCX file bytes."""
    filename_lower = filename.lower()
    text = ""

    if filename_lower.endswith('.pdf'):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            logger.warning(f"pypdf extraction error for {filename}: {e}")

    elif filename_lower.endswith('.docx'):
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            text_parts = []
            for p in doc.paragraphs:
                if p.text and p.text.strip():
                    text_parts.append(p.text.strip())
            for table in doc.tables:
                for row in table.rows:
                    row_cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if row_cells:
                        text_parts.append(" | ".join(row_cells))
            text = "\n".join(text_parts)
        except Exception as e:
            logger.warning(f"python-docx extraction error for {filename}: {e}")

    # Fallback to UTF-8 / Latin-1 decode
    if not text.strip():
        try:
            text = file_bytes.decode('utf-8', errors='ignore')
        except Exception:
            text = file_bytes.decode('latin-1', errors='ignore')

    # Clean non-printable / control chars
    clean_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    return clean_text.strip()


def parse_resume_regex_fallback(raw_text: str) -> Dict[str, Any]:
    """Deterministic regex extraction fallback when AI is unavailable."""
    # Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw_text)
    email = email_match.group(0) if email_match else ""

    # Phone
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}', raw_text)
    phone = phone_match.group(0) if phone_match else ""

    # LinkedIn / GitHub — only when the document actually contains them.
    linkedin_match = re.search(r'(linkedin\.com/in/[\w-]+)', raw_text, re.IGNORECASE)
    linkedin = linkedin_match.group(0) if linkedin_match else ""

    github_match = re.search(r'(github\.com/[\w-]+)', raw_text, re.IGNORECASE)
    github = github_match.group(0) if github_match else ""

    location_match = re.search(r'^([A-Z][a-zA-Z .]+,\s*[A-Z][a-zA-Z .]+)$', raw_text, re.MULTILINE)
    location = location_match.group(0).strip() if location_match else ""

    # Name: First non-empty line with 2-4 words
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    name = ""
    for line in lines[:5]:
        words = line.split()
        if 2 <= len(words) <= 4 and not any(char.isdigit() or char in '@:/' for char in line):
            name = line
            break

    # Extract Skills — omitted entirely when the document has no skills section.
    skills_dict = {}
    skills_match = re.search(r'(?:skills|technical skills|technologies)[:\n](.*?)(?:\n\n|\n[A-Z\s]{4,}|\Z)', raw_text, re.IGNORECASE | re.DOTALL)
    if skills_match:
        skills_text = skills_match.group(1).strip()
        skills_items = [s.strip() for s in re.split(r'[,|•\n]', skills_text) if s.strip()]
        if skills_items:
            half = max(1, len(skills_items) // 2)
            skills_dict = {
                "Languages & Frameworks": ", ".join(skills_items[:half]),
                "Tools & Technologies": ", ".join(skills_items[half:])
            }

    # Summary — only when the document supplies one.
    summary = ""
    summary_match = re.search(r'(?:summary|profile|about me|objective)[:\n](.*?)(?:\n\n|\n[A-Z\s]{4,}|\Z)', raw_text, re.IGNORECASE | re.DOTALL)
    if summary_match:
        summary_candidate = summary_match.group(1).strip()
        if len(summary_candidate) > 20:
            summary = " ".join(summary_candidate.split()[:80])

    return {
        "name": name,
        "contact": {
            "email": email,
            "phone": phone,
            "location": location,
            "linkedin": linkedin,
            "github": github,
            "portfolio": ""
        },
        "summary": summary,
        "skills": skills_dict,
        "experience": [],
        "projects": [],
        "education": [],
        "certifications": []
    }


def parse_resume_into_structured_json(raw_text: str) -> Dict[str, Any]:
    """
    Uses Groq LLM (with deterministic regex fallback) to structure the resume raw text
    into a high-fidelity JSON document suitable for ATS scoring and live interactive editing.
    """
    if not raw_text or len(raw_text.strip()) < 50:
        return parse_resume_regex_fallback(raw_text)

    # Prompt Groq with strict JSON output
    system_prompt = (
        "You are an expert resume parsing engine and ATS compiler. "
        "Extract the candidate's resume information from the provided raw text and return a valid JSON object.\n"
        "Required JSON format:\n"
        "{\n"
        '  "name": "Full Name",\n'
        '  "contact": {\n'
        '    "email": "email@example.com",\n'
        '    "phone": "+91...",\n'
        '    "location": "City, Country",\n'
        '    "linkedin": "linkedin.com/in/...",\n'
        '    "github": "github.com/...",\n'
        '    "portfolio": "url or empty"\n'
        "  },\n"
        '  "summary": "2-3 concise lines professional summary",\n'
        '  "skills": {\n'
        '    "Category Name": "comma-separated list of skills"\n'
        "  },\n"
        '  "experience": [\n'
        '    {\n'
        '      "company": "Company Name",\n'
        '      "role": "Job Title",\n'
        '      "location": "City, Country",\n'
        '      "period": "Start – End",\n'
        '      "tech_stack": "Comma-separated technologies",\n'
        '      "bullets": ["Action verb + metric accomplishment bullet 1", "bullet 2"]\n'
        "    }\n"
        "  ],\n"
        '  "projects": [\n'
        '    {\n'
        '      "title": "Project Name",\n'
        '      "role": "Role (e.g. Creator / Full Stack Developer)",\n'
        '      "tech_stack": "Tech stack used",\n'
        '      "bullets": ["Accomplished [X] measured by [Y] doing [Z]"]\n'
        "    }\n"
        "  ],\n"
        '  "education": [\n'
        '    {\n'
        '      "institution": "University / College",\n'
        '      "degree": "Degree",\n'
        '      "field": "Specialization",\n'
        '      "year": "Graduation Year",\n'
        '      "score": "CGPA / % or empty"\n'
        "    }\n"
        "  ],\n"
        '  "certifications": ["Cert 1", "Cert 2"]\n'
        "}\n"
        "Important Guidelines:\n"
        "- If experience is empty (e.g. fresher), return empty list [] for experience.\n"
        "- Ensure project bullets use strong action verbs and preserve metrics from the text.\n"
        "- Return ONLY valid JSON."
    )

    sample_slice = raw_text[:8000]
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Parse this resume:\n\n{sample_slice}"}
    ]

    try:
        response_text = call_groq_chat(messages, temperature=0.2, json_mode=True, timeout=12)
        parsed = json.loads(response_text)
        # Validate critical keys
        if "name" in parsed and ("projects" in parsed or "skills" in parsed):
            # Guarantee contact sub-dictionary
            if "contact" not in parsed or not isinstance(parsed["contact"], dict):
                parsed["contact"] = {}
            # Defaults for contact
            c = parsed["contact"]
            c.setdefault("email", "")
            c.setdefault("phone", "")
            c.setdefault("location", "Bengaluru, India")
            c.setdefault("linkedin", "")
            c.setdefault("github", "")
            c.setdefault("portfolio", "")

            # Ensure projects and experience are lists of clean dicts
            clean_projects = []
            for p in parsed.get("projects", []):
                if isinstance(p, dict):
                    # Sanitize bullets to clean strings
                    raw_b = p.get("bullets", [])
                    clean_b = []
                    for b in raw_b:
                        if isinstance(b, str) and b.strip():
                            clean_b.append(b.strip())
                        elif isinstance(b, dict):
                            clean_b.append(b.get("bullet") or b.get("text") or str(b))
                    p["bullets"] = clean_b
                    clean_projects.append(p)
            parsed["projects"] = clean_projects

            clean_exp = []
            for e in parsed.get("experience", []):
                if isinstance(e, dict):
                    raw_b = e.get("bullets", [])
                    clean_b = []
                    for b in raw_b:
                        if isinstance(b, str) and b.strip():
                            clean_b.append(b.strip())
                        elif isinstance(b, dict):
                            clean_b.append(b.get("bullet") or b.get("text") or str(b))
                    e["bullets"] = clean_b
                    clean_exp.append(e)
            parsed["experience"] = clean_exp

            if not isinstance(parsed.get("education"), list):
                parsed["education"] = []
            if not isinstance(parsed.get("certifications"), list):
                parsed["certifications"] = []

            return parsed
    except Exception as e:
        logger.warning(f"Groq parsing failed, falling back to regex: {e}")

    return parse_resume_regex_fallback(raw_text)


def _listed_skills(skills) -> List[str]:
    """The candidate's skills section as a flat list, from any of the shapes it is stored in."""
    groups = skills.values() if isinstance(skills, dict) else [skills]
    found, seen = [], set()
    for group in groups:
        parts = group if isinstance(group, (list, tuple)) else re.split(r',(?![^()]*\))', str(group or ''))
        for part in parts:
            name = re.sub(r'\s*\([^)]*\)', '', str(part)).strip()
            if name and len(name) <= 40 and name.lower() not in seen:
                seen.add(name.lower())
                found.append(name)
    return found


def evaluate_uploaded_resume_ats(parsed_resume: Dict[str, Any], target_skills_list: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Score a resume the way an ATS search and a recruiter's first read treat it.

    Six parts, and none assume the candidate is a software engineer:
    1. Contact details (15)
    2. Standard sections present (15)
    3. Bullets that open with a strong verb (20)
    4. Bullets that state a measured result (20)
    5. Job keywords on the resume (20), or the candidate's own skills when no job is given
    6. Keywords shown inside described work, not only in the skills list (10)

    With a job, the total is also capped by keyword coverage: polish cannot
    make up for missing skills. The grade never claims an ATS pass, because no
    one can know an employer's result from outside.
    """
    pillars = []
    total_score = 0
    improvements = []

    # 1. Contact & Header (15 pts)
    contact = parsed_resume.get("contact", {})
    c_score = 0
    c_feedback = []
    if contact.get("email") and "@" in contact.get("email"):
        c_score += 4
    else:
        c_feedback.append("Missing professional email address")
        improvements.append("Add a clean email address (e.g. name.dev@domain.com)")

    if contact.get("phone") and len(contact.get("phone")) >= 8:
        c_score += 4
    else:
        c_feedback.append("Missing contact phone number")
        improvements.append("Include an active phone number with country code")

    if contact.get("linkedin") and "linkedin" in contact.get("linkedin").lower():
        c_score += 4
    else:
        c_feedback.append("No LinkedIn profile link detected")
        improvements.append("Add your LinkedIn profile URL — recruiters look for it")

    if contact.get("github") and "github" in contact.get("github").lower():
        c_score += 3

    c_score = min(15, c_score)
    total_score += c_score
    pillars.append({
        "id": "contact_header",
        "name": "Contact & Header Completeness",
        "score": c_score,
        "max_score": 15,
        "status": "pass" if c_score >= 12 else "warn",
        "detail": "Email, phone, LinkedIn, and developer handles verified." if c_score >= 12 else "; ".join(c_feedback) or "Improve contact details completeness."
    })

    # 2. Section Structure & Format (15 pts)
    s_score = 0
    sections_found = 0
    if parsed_resume.get("summary") and len(parsed_resume.get("summary")) > 30:
        sections_found += 1
    if parsed_resume.get("skills"):
        sections_found += 1
    if parsed_resume.get("projects") or parsed_resume.get("experience"):
        sections_found += 2
    if parsed_resume.get("education"):
        sections_found += 1

    s_score = min(15, int((sections_found / 5) * 15))
    total_score += s_score
    pillars.append({
        "id": "format_structure",
        "name": "ATS Section Parseability",
        "score": s_score,
        "max_score": 15,
        "status": "pass" if s_score >= 12 else "warn",
        "detail": f"{min(sections_found, 5)} of 5 standard resume sections found."
    })

    # Collect all bullets across projects and experience
    all_bullets = []
    for p in parsed_resume.get("projects", []):
        all_bullets.extend(p.get("bullets", []))
    for e in parsed_resume.get("experience", []):
        all_bullets.extend(e.get("bullets", []))

    # 3. Action Verbs Power (20 pts)
    action_verbs = {
        'architected', 'engineered', 'developed', 'optimized', 'built', 'spearheaded',
        'designed', 'implemented', 'constructed', 'deployed', 'automated', 'integrated',
        'refactored', 'orchestrated', 'streamlined', 'benchmarked', 'scaled', 'accelerated',
        'reduced', 'delivered', 'formulated', 'modeled', 'directed', 'configured', 'provisioned',
        'authored', 'administered', 'secured', 'migrated', 'tuned', 'monitored', 'established', 'created',
        'wrote', 'led', 'managed', 'launched', 'grew', 'increased', 'planned', 'analyzed', 'analysed', 'organized',
        'organised', 'negotiated', 'trained', 'coordinated', 'produced', 'prepared', 'ran', 'tested', 'resolved',
        'improved', 'researched', 'presented', 'cut', 'shipped', 'drafted', 'audited', 'sold', 'taught',
    }
    weak_verbs = {'helped', 'worked on', 'assisted', 'handled', 'responsible for', 'tried', 'participated'}

    strong_count = 0
    weak_count = 0
    for b in all_bullets:
        first_word = b.strip().lower().split(' ')[0] if b.strip() else ''
        if first_word in action_verbs:
            strong_count += 1
        elif any(b.strip().lower().startswith(wv) for wv in weak_verbs):
            weak_count += 1

    verb_score = min(20, int((strong_count / max(1, len(all_bullets))) * 20))
    if weak_count > 0:
        verb_score = max(5, verb_score - (weak_count * 3))
        improvements.append("Open bullets with what you did ('Built', 'Wrote', 'Ran') instead of 'worked on' or 'helped'.")

    total_score += verb_score
    pillars.append({
        "id": "action_verbs",
        "name": "Action Verb Strength",
        "score": verb_score,
        "max_score": 20,
        "status": "pass" if verb_score >= 15 else ("warn" if verb_score >= 10 else "fail"),
        "detail": f"{strong_count} of {len(all_bullets)} bullets lead with active leadership verbs."
    })

    # 4. Quantified Metrics & Google XYZ (20 pts)
    metric_regex = re.compile(r'(\d+[\.,]?\d*\s*(%|ms|kb|mb|gb|tb|req|k|x|skus|cve|users|tps|sec|min|hr|lpa|cr))|\b(\d{2,})\b|[₹$]\d+', re.IGNORECASE)
    bullets_with_metrics = sum(1 for b in all_bullets if metric_regex.search(b))
    metric_score = min(20, int((bullets_with_metrics / max(1, len(all_bullets))) * 20))

    if metric_score < 14:
        improvements.append(
            "Quantify bullets only where you actually measured something (records processed, tests passing, "
            "build time). If you never measured it, leave the number out."
        )

    total_score += metric_score
    pillars.append({
        "id": "quantified_metrics",
        "name": "Measured Results",
        "score": metric_score,
        "max_score": 20,
        "status": "pass" if metric_score >= 14 else ("warn" if metric_score >= 8 else "fail"),
        "detail": f"{bullets_with_metrics} of {len(all_bullets)} bullets state a number."
    })

    # 5. Keywords on the resume (20 pts)
    content_text = resume_text(parsed_resume)
    own_skills = _listed_skills(parsed_resume.get("skills"))

    matched_skills = []
    missing_skills = []
    if target_skills_list:
        for s in target_skills_list:
            (matched_skills if has_term(s, content_text) else missing_skills).append(s)
        job_match = round(len(matched_skills) / len(target_skills_list) * 100)
        skills_score = int(len(matched_skills) / len(target_skills_list) * 20)
        skills_detail = f"{len(matched_skills)} of {len(target_skills_list)} skills this job asks for are on the resume."
    else:
        matched_skills = own_skills
        job_match = None
        skills_score = min(20, len(own_skills) * 2)
        skills_detail = f"{len(own_skills)} skills listed. Pick a job to see how many of its keywords you cover."
        if len(own_skills) < 8:
            improvements.append("List the tools and methods you have actually used, so searches for them can find you.")

    total_score += skills_score
    pillars.append({
        "id": "tech_skills",
        "name": "Job Keywords" if target_skills_list else "Skills Listed",
        "score": skills_score,
        "max_score": 20,
        "status": "pass" if skills_score >= 15 else "warn",
        "detail": skills_detail
    })

    # 6. Keywords shown in work (10 pts)
    # A recruiter's search counts a skill for more when it sits inside a
    # description of work, and an interviewer asks where it was used.
    work_text = " ".join(
        [str(parsed_resume.get("summary") or "")] + [str(b) for b in all_bullets]
    )
    shown_against = matched_skills if target_skills_list else own_skills
    shown = [term for term in shown_against if has_term(term, work_text)]
    if shown_against:
        shown_score = round(10 * len(shown) / len(shown_against))
        shown_detail = f"{len(shown)} of {len(shown_against)} of these skills appear in your summary or bullets, not only in the skills list."
    else:
        shown_score = 0
        shown_detail = "No skills to check yet."
    if shown_against and shown_score < 7:
        unshown = [term for term in shown_against if term not in shown][:3]
        improvements.append(
            "Mention where you used " + ", ".join(unshown) + " in a project or job bullet, if you did."
        )
    total_score += shown_score
    pillars.append({
        "id": "architecture_depth",
        "name": "Skills Shown in Work",
        "score": shown_score,
        "max_score": 10,
        "status": "pass" if shown_score >= 7 else "warn",
        "detail": shown_detail,
    })

    total_score = min(100, total_score)

    if job_match is not None:
        total_score = min(total_score, job_match_limit(job_match))

    # Grade & Rating Label
    if total_score >= 90:
        grade = "Excellent"
        pass_rate = "Strong on every check"
    elif total_score >= 75:
        grade = "Strong"
        pass_rate = "Good. A few improvements left"
    elif total_score >= 60:
        grade = "Needs polish"
        pass_rate = "Add real, measurable results to improve"
    else:
        grade = "Needs work"
        pass_rate = "Add the job's keywords you really have, and stronger action verbs"

    # Evaluate each project with reverse-engineered ATS score
    scored_projects = []
    for proj in parsed_resume.get("projects", []):
        eval_data = score_project_ats(proj, target_skills_list or [])
        proj_copy = dict(proj)
        proj_copy['ats_score'] = eval_data['score']
        proj_copy['ats_badge'] = eval_data['badge']
        proj_copy['ats_grade'] = eval_data['grade']
        proj_copy['breakdown'] = eval_data['breakdown']
        scored_projects.append(proj_copy)

    # Build checks array for backwards compatibility with all UI displays
    checks = []
    for p in pillars:
        checks.append({
            'rule': p['name'],
            'passed': (p['score'] / max(p['max_score'], 1)) >= 0.7,
            'points': p['score'],
            'max_points': p['max_score'],
            'detail': p['detail']
        })

    return {
        "score": total_score,
        "overall_score": total_score,
        "grade": grade,
        "pass_rate": pass_rate,
        "pillars": pillars,
        "checks": checks,
        "scored_projects": scored_projects,
        # Nothing to fix is a real result. The old fallback invented praise plus a
        # guaranteed "95+" score, which contradicted whatever the evaluator found.
        "improvements": improvements[:4],
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "job_match": job_match,
        "bullet_count": len(all_bullets),
        "bullets_with_metrics": bullets_with_metrics
    }


def check_ats_readability(file_bytes: bytes, filename: str, resume: Dict[str, Any], keywords: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Read an exported resume back the way an ATS does and report what survived.

    An ATS never sees the layout, only the text it can extract from the file.
    This extracts that text and checks that the candidate's name, contact
    details, section headings and keywords are all in it, so a file that looks
    fine but parses badly is caught before the candidate sends it.
    """
    from .resume_engine import has_keyword

    text = extract_text_from_file_bytes(file_bytes, filename) or ''
    flat = ' '.join(text.split()).lower()
    contact = resume.get('contact') if isinstance(resume.get('contact'), dict) else {}

    def present(value) -> bool:
        value = ' '.join(str(value or '').split()).lower()
        return bool(value) and value in flat

    checks = []
    for label, value in (
        ('Name', resume.get('name')),
        ('Email', contact.get('email') or resume.get('email')),
        ('Phone', contact.get('phone') or resume.get('phone')),
    ):
        if str(value or '').strip():
            checks.append({'check': label, 'passed': present(value)})

    sections = (
        ('Skills', resume.get('skills'), ('skills',)),
        ('Experience', resume.get('experience'), ('experience', 'employment', 'work history')),
        ('Projects', resume.get('projects'), ('projects',)),
        ('Education', resume.get('education'), ('education',)),
    )
    for label, content, headings in sections:
        if content:
            checks.append({'check': f'{label} heading', 'passed': any(h in flat for h in headings)})

    wanted = [str(k).strip() for k in (keywords or []) if str(k).strip()]
    lost = [k for k in wanted if not has_keyword(k, text)]
    return {
        'readable': bool(flat) and all(c['passed'] for c in checks) and not lost,
        'characters': len(flat),
        'checks': checks,
        'keywords_found': [k for k in wanted if k not in lost],
        'keywords_lost': lost,
    }
