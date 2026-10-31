from datetime import datetime, timedelta
from ninja import Router, Query, Schema
from typing import List, Optional, Dict, Any
from api.auth import OwnerAuthBearer
from ninja.errors import HttpError
from django.db.models import Count # For potential future use with real models
import random # For simulating job/group data
import time

# Assuming these schemas exist from api/schemas.py (need to ensure they are available)
# from api.schemas import OwnerJobsResponse, OwnerGroupsResponse, OwnerJob, OwnerGroup

# Placeholder schemas for now, until full integration
class OwnerJobSchema(Schema):
    id: int
    title: str
    company_name: str
    company_logo: Optional[str] = None
    location: str
    domain: str
    source: str
    job_type: str
    experience_tier: str
    category: str
    status: str
    posted_date: str
    deadline: str
    description: Optional[str] = None
    requirements: List[str] = []
    skills: List[str] = []

class OwnerJobsResponseSchema(Schema):
    jobs: List[OwnerJobSchema]
    total: int
    page: int
    page_size: int
    total_pages: int

class OwnerGroupSchema(Schema):
    id: int
    name: str
    slug: str
    banner_tag: str
    description: str
    tier_type: str
    jobs: List[OwnerJobSchema] = []

class OwnerGroupsResponseSchema(Schema):
    groups: List[OwnerGroupSchema]
    total: int
    page: int
    page_size: int
    total_pages: int

class AutoOrganizeResponseSchema(Schema):
    status: str
    message: str
    groups_created: int
    jobs_organized: int

router = Router(tags=["Owner Dashboard"])

# --- Mock Data Generation ---
def generate_mock_job(job_id: int) -> OwnerJobSchema:
    companies = ["Tech Solutions", "Innovate Corp", "Future Systems", "Global Dynamics"]
    titles = ["Software Engineer", "Data Scientist", "DevOps Engineer", "Product Manager"]
    locations = ["Remote", "New York", "San Francisco", "London"]
    job_types = ["Full-Time", "Contract", "Internship"]
    experience_tiers = ["FRESHER", "EXPERIENCED", "INTERNSHIP"]
    categories = ["Web Dev", "Data", "Cloud"]
    statuses = ["ACTIVE", "CLOSED", "PENDING"]
    skills = {
        "Web Dev": ["React", "Node.js", "Django", "TypeScript"],
        "Data": ["Python", "SQL", "Machine Learning"],
        "Cloud": ["AWS", "Docker", "Kubernetes"]
    }

    company = random.choice(companies)
    title = random.choice(titles)
    location = random.choice(locations)
    job_type = random.choice(job_types)
    exp_tier = random.choice(experience_tiers)
    category = random.choice(categories)
    status = random.choice(statuses)
    post_date = (datetime.now() - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d")
    deadline = (datetime.now() + timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d")

    return OwnerJobSchema(
        id=job_id,
        title=f"[{company}] {title}",
        company_name=company,
        company_logo=f"https://picsum.photos/seed/{company}/50/50",
        location=location,
        domain=f"www.{company.lower().replace(" ", "")}.com",
        source="LinkedIn",
        job_type=job_type,
        experience_tier=exp_tier,
        category=category,
        status=status,
        posted_date=post_date,
        deadline=deadline,
        description=f"Exciting opportunity for a {exp_tier.lower()} {title} at {company}.",
        requirements=[f"Proficiency in {s}" for s in random.sample(skills.get(category, []), k=random.randint(1,3))],
        skills=random.sample(skills.get(category, []), k=random.randint(1,3)),
    )

def get_mock_jobs(count: int = 10) -> List[OwnerJobSchema]:
    return [generate_mock_job(i) for i in range(1, count + 1)]

def get_mock_groups(jobs: List[OwnerJobSchema]) -> List[OwnerGroupSchema]:
    # Simple grouping by experience tier for demonstration
    grouped: Dict[str, List[OwnerJobSchema]] = {"FRESHER": [], "EXPERIENCED": [], "INTERNSHIP": [], "GENERAL": []}
    for job in jobs:
        if job.experience_tier in grouped: 
            grouped[job.experience_tier].append(job)
        else: 
            grouped["GENERAL"].append(job)

    mock_groups = []
    for tier, jobs_list in grouped.items():
        if jobs_list:
            mock_groups.append(
                OwnerGroupSchema(
                    id=random.randint(100, 999),
                    name=f"{tier.title()} Jobs",
                    slug=f"{tier.lower()}-jobs",
                    banner_tag=f"#{tier.title()}",
                    description=f"Jobs for {tier.lower()} candidates.",
                    tier_type=tier,
                    jobs=jobs_list
                )
            )
    return mock_groups

# --- API Endpoints ---

@router.get("/jobs", response=OwnerJobsResponseSchema, auth=OwnerAuthBearer(), summary="List owner jobs")
def get_owner_jobs(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    experience: Optional[str] = None,
    status: Optional[str] = None,
    sort: Optional[str] = None,
):
    """
    Fetch a paginated and filterable list of job postings for the owner dashboard.
    Requires JWT authentication.
    """
    if not request.auth: 
        raise HttpError(401, "Unauthorized: Valid JWT token required.")

    # Simulate fetching and filtering jobs
    all_jobs = get_mock_jobs(50) # Generate more mock data
    filtered_jobs = all_jobs

    if search:
        search_lower = search.lower()
        filtered_jobs = [j for j in filtered_jobs if 
            search_lower in j.title.lower() or 
            search_lower in j.company_name.lower() or 
            search_lower in j.location.lower()
        ]
    if category:
        filtered_jobs = [j for j in filtered_jobs if j.category.lower() == category.lower()]
    if experience and experience != "ALL":
        filtered_jobs = [j for j in filtered_jobs if j.experience_tier == experience]
    if status:
        filtered_jobs = [j for j in filtered_jobs if j.status.lower() == status.lower()]

    # Sort (simple simulation)
    if sort == "date_desc":
        filtered_jobs.sort(key=lambda j: j.posted_date, reverse=True)
    elif sort == "title_asc":
        filtered_jobs.sort(key=lambda j: j.title)

    total = len(filtered_jobs)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_jobs = filtered_jobs[start_idx:end_idx]

    return OwnerJobsResponseSchema(
        jobs=paginated_jobs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )

@router.get("/groups", response=OwnerGroupsResponseSchema, auth=OwnerAuthBearer(), summary="List owner job groups")
def get_owner_groups(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    tier_type: Optional[str] = None,
):
    """
    Fetch a paginated list of job groups (e.g., by experience tier) for the owner dashboard.
    Requires JWT authentication.
    """
    if not request.auth: 
        raise HttpError(401, "Unauthorized: Valid JWT token required.")

    all_jobs = get_mock_jobs(50) # Get consistent job set
    all_groups = get_mock_groups(all_jobs) # Generate groups from them

    filtered_groups = all_groups
    if tier_type and tier_type != "ALL":
        filtered_groups = [g for g in filtered_groups if g.tier_type.lower() == tier_type.lower()]
    
    total = len(filtered_groups)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_groups = filtered_groups[start_idx:end_idx]

    return OwnerGroupsResponseSchema(
        groups=paginated_groups,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )

@router.post("/groups/auto-organize", response=AutoOrganizeResponseSchema, auth=OwnerAuthBearer(), summary="Auto-organize jobs into groups")
def auto_organize_groups(request):
    """
    Trigger an automated process to organize unassigned jobs into predefined groups based on criteria.
    Requires JWT authentication.
    """
    if not request.auth: 
        raise HttpError(401, "Unauthorized: Valid JWT token required.")

    # Simulate organization logic
    time.sleep(1) # Simulate work
    jobs_processed = random.randint(5, 20)
    groups_created = random.randint(1, 3)

    return AutoOrganizeResponseSchema(
        status="success",
        message="Jobs successfully auto-organized.",
        groups_created=groups_created,
        jobs_organized=jobs_processed
    )

