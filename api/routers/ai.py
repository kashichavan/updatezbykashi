"""
⚡ Kashii DevAcademy & Career Suite — AI API Router
Powered by Groq's Low-Latency Engine.
"""

from typing import List, Optional, Dict, Any
from ninja import Router, Schema
from pydantic import Field
from requirements.ai_engine import (
    generate_job_description,
    polish_resume_bullet,
    tailor_resume_to_job,
    generate_professional_summary,
)
from api.auth import AuthBearer # Import AuthBearer
from ninja.errors import HttpError # Import HttpError

router = Router(tags=["⚡ AI Career & Job Tools"])


class JobDescriptionRequest(Schema):
    title: str = Field(..., description="Job Title, e.g. Frontend Engineer")
    company: Optional[str] = Field("", description="Company Name")
    experience: Optional[str] = Field("0-2 years", description="Experience range")
    location: Optional[str] = Field("Remote / Bangalore", description="Location & Work Mode")
    work_mode: Optional[str] = Field("Full-time", description="Employment Type")
    skills: Optional[str] = Field("", description="Core Tech Stack / Skills")
    additional_notes: Optional[str] = Field("", description="Special requirements or perks")


class BulletPolishRequest(Schema):
    bullet: str = Field(..., description="Raw resume bullet point text")
    role: Optional[str] = Field("", description="Candidate target role")
    tech_stack: Optional[str] = Field("", description="Tools/technologies used")


class ResumeTailorRequest(Schema):
    resume_summary: str = Field(..., description="Candidate summary text")
    resume_skills: List[str] = Field(..., description="List of technical skills")
    resume_projects: List[Dict[str, Any]] = Field(..., description="List of projects with bullets")
    job_description: str = Field(..., description="Target Job Description text")


class SummaryGenRequest(Schema):
    role: str = Field(..., description="Target Job Role")
    experience_level: Optional[str] = Field("fresher", description="e.g. fresher, 2 years, 5 years")
    key_skills: Optional[str] = Field("", description="Key skills and tools")
    target_company_type: Optional[str] = Field("Product Startup", description="Startup, FAANG, Service")


@router.post("/generate-jd", summary="Generate High-Converting Job Description", auth=AuthBearer())
def api_generate_jd(request, payload: JobDescriptionRequest):
    """Generate structured, ATS-compliant job description with LinkedIn and IG post formats. Requires JWT authentication."""
    if not request.auth: 
        raise HttpError(401, "Unauthorized: Valid JWT token required.")
    try:
        data = generate_job_description(
            title=payload.title,
            company=payload.company or "",
            experience=payload.experience or "0-2 years",
            location=payload.location or "Remote / Bangalore",
            work_mode=payload.work_mode or "Full-time",
            skills=payload.skills or "",
            additional_notes=payload.additional_notes or "",
        )
        return {"success": True, "data": data}
    except Exception as e:
        raise HttpError(500, f"Failed to generate job description: {e}")


@router.post("/polish-bullet", summary="Polish Resume Bullet to Google XYZ Format", auth=AuthBearer())
def api_polish_bullet(request, payload: BulletPolishRequest):
    """Transform raw bullet points into quantified Google XYZ metrics. Requires JWT authentication."""
    if not request.auth: 
        raise HttpError(401, "Unauthorized: Valid JWT token required.")
    try:
        data = polish_resume_bullet(
            bullet=payload.bullet,
            role=payload.role or "",
            tech_stack=payload.tech_stack or "",
        )
        return {"success": True, "data": data}
    except Exception as e:
        raise HttpError(500, f"Failed to polish bullet point: {e}")


@router.post("/tailor-resume", summary="Tailor Resume to Target Job Description", auth=AuthBearer())
def api_tailor_resume(request, payload: ResumeTailorRequest):
    """Compute semantic keyword gap and generate optimized resume bullets for a target JD. Requires JWT authentication."""
    if not request.auth: 
        raise HttpError(401, "Unauthorized: Valid JWT token required.")
    try:
        data = tailor_resume_to_job(
            resume_summary=payload.resume_summary,
            resume_skills=payload.resume_skills,
            resume_projects=payload.resume_projects,
            job_description=payload.job_description,
        )
        return {"success": True, "data": data}
    except Exception as e:
        raise HttpError(500, f"Failed to tailor resume: {e}")


@router.post("/generate-summary", summary="Generate Professional Resume Summary", auth=AuthBearer())
def api_generate_summary(request, payload: SummaryGenRequest):
    """Generate 3 elevator pitch options tailored to the candidate's target role. Requires JWT authentication."""
    if not request.auth: 
        raise HttpError(401, "Unauthorized: Valid JWT token required.")
    try:
        data = generate_professional_summary(
            role=payload.role,
            experience_level=payload.experience_level or "fresher",
            key_skills=payload.key_skills or "",
            target_company_type=payload.target_company_type or "Product Startup",
        )
        return {"success": True, "data": data}
    except Exception as e:
        raise HttpError(500, f"Failed to generate summary: {e}")
