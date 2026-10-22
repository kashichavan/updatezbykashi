"""
GitHub Project Discovery Engine for Kashii Updatez.
Discovers and ranks public GitHub repositories matching target job descriptions
using official GitHub REST API with 5-factor relevance scoring.
"""

import os
import re
import json
import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com/search/repositories"
DEFAULT_TIMEOUT = 6  # seconds
CACHE_TTL = 3600 * 6  # 6 hours cache for search results


def get_github_headers() -> Dict[str, str]:
    """Build GitHub API headers with optional token for high rate limits."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "KashiiUpdatez-ResumeBuilder/2.0",
    }
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token.strip()}"
    return headers


COMPANY_AND_NOISE_TERMS = {
    'google', 'amazon', 'microsoft', 'apple', 'meta', 'netflix', 'uber',
    'tcs', 'infosys', 'wipro', 'hcl', 'cognizant', 'accenture', 'swiggy',
    'zomato', 'razorpay', 'phonepe', 'paytm', 'flipkart', 'jobdexo', 'naukri',
    'linkedin', 'bengaluru', 'bangalore', 'hyderabad', 'pune', 'chennai',
    'mumbai', 'delhi', 'noida', 'gurugram', 'remote', 'india', 'fresher',
    'internship', 'hiring', 'drive', 'urgent', 'experience', 'years', 'lpa',
    'salary', 'stipend', 'immediate', 'opening', 'walkin', 'technologies',
    'solutions', 'pvt', 'ltd', 'limited', 'inc', 'corp', 'corporation',
    'company', 'leading', 'client', 'confidential', 'software', 'engineer',
    'developer', 'analyst', 'associate', 'trainee', 'senior', 'junior', 'lead'
}


def extract_keywords_from_job(job_title: str = "", job_skills: str = "", job_description: str = "") -> List[str]:
    """
    Extract normalized technology keywords and frameworks from job metadata.
    Excludes hiring companies, recruiter noise, and non-technical stopwords.
    """
    raw_text = f"{job_title} {job_skills} {job_description}".lower()
    
    # Common tech stack vocabulary
    known_tech = [
        "python", "django", "fastapi", "flask", "javascript", "typescript", "react", "nextjs", "vue",
        "angular", "node", "nodejs", "express", "java", "spring", "springboot", "c++", "c#", ".net",
        "golang", "go", "rust", "postgresql", "postgres", "mysql", "mongodb", "redis", "docker",
        "kubernetes", "aws", "gcp", "azure", "graphql", "rest", "api", "tailwind", "redux", "kafka",
        "rabbitmq", "celery", "elasticsearch", "pytorch", "tensorflow", "pandas", "numpy", "scikit-learn",
        "flutter", "dart", "android", "ios", "swift", "kotlin", "ci/cd", "devops", "linux", "sql"
    ]
    
    found_tech = []
    # If explicit skills were provided, parse them first
    if job_skills:
        for s in re.split(r'[,|/\n]', job_skills):
            cleaned = s.strip().lower()
            if cleaned and cleaned not in COMPANY_AND_NOISE_TERMS and len(cleaned) >= 2:
                if cleaned not in found_tech:
                    found_tech.append(cleaned)
                    
    # Search for known technologies in the text
    for tech in known_tech:
        pattern = r'\b' + re.escape(tech) + r'\b'
        if re.search(pattern, raw_text) and tech not in found_tech:
            found_tech.append(tech)

    return found_tech[:10]


def build_search_queries(job_title: str, detected_tech: List[str]) -> List[str]:
    """
    Generate 2-3 focused search queries for GitHub repository discovery.
    Strictly focuses on programming languages, frameworks, and engineering concepts.
    """
    queries = []
    
    # Query 1: Top 2 technologies
    if len(detected_tech) >= 2:
        queries.append(f"{detected_tech[0]} {detected_tech[1]} stars:>10")
    elif detected_tech:
        queries.append(f"{detected_tech[0]} stars:>10")
        
    # Query 2: Technology + engineering component
    arch_terms = ["backend", "frontend", "fullstack", "microservice", "api", "dashboard", "pipeline"]
    matched_arch = next((t for t in arch_terms if t in job_title.lower()), "application")
    
    if detected_tech:
        queries.append(f"{detected_tech[0]} {matched_arch} stars:>15")
    else:
        queries.append("fullstack web application stars:>50")
            
    return queries[:2]


def calculate_relevance_score(
    repo: Dict[str, Any],
    job_skills: List[str],
    job_description: str = "",
    job_title: str = ""
) -> Dict[str, Any]:
    """
    5-Factor Transparent Relevance Scoring (0-100 scale):
    - 1. Technology overlap (35%)
    - 2. Job responsibility / role overlap (25%)
    - 3. Implementation structure & code completeness (20%)
    - 4. Documentation & reproducibility (10%)
    - 5. Maintenance & recency (10%)
    """
    repo_name = (repo.get("name") or "").lower()
    description = (repo.get("description") or "").lower()
    topics = [t.lower() for t in repo.get("topics", [])]
    language = (repo.get("language") or "").lower()
    full_searchable = f"{repo_name} {description} {' '.join(topics)} {language}"

    # 1. Technology Overlap (Max 35 pts)
    matched_skills = []
    if job_skills:
        for skill in job_skills:
            skill_lower = skill.lower()
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, full_searchable) or skill_lower in language:
                matched_skills.append(skill)
        tech_ratio = len(matched_skills) / max(len(job_skills), 1)
        tech_score = min(tech_ratio * 35.0, 35.0)
    else:
        tech_score = 20.0  # baseline if no target skills specified

    # 2. Job Responsibility / Role Overlap (Max 25 pts)
    responsibility_terms = [
        "api", "database", "crud", "auth", "authentication", "dashboard", "rest", "backend",
        "frontend", "fullstack", "microservice", "docker", "pipeline", "etl", "machine learning",
        "realtime", "websocket", "cache", "redis", "postgresql", "production"
    ]
    job_desc_lower = f"{job_title} {job_description}".lower()
    target_resp_terms = [t for t in responsibility_terms if t in job_desc_lower]
    if not target_resp_terms:
        target_resp_terms = ["api", "backend", "crud", "dashboard"]
    
    matched_resp = [t for t in target_resp_terms if t in full_searchable]
    resp_ratio = len(matched_resp) / max(len(target_resp_terms), 1)
    responsibility_score = min(resp_ratio * 25.0, 25.0)

    # 3. Implementation Evidence & Code Structure (Max 20 pts)
    structure_score = 0.0
    if language:
        structure_score += 7.0  # Has clear primary language
    if topics:
        structure_score += min(len(topics) * 2.0, 8.0)  # Tagged with topics
    if repo.get("size", 0) > 50:  # Non-empty codebase
        structure_score += 5.0

    # 4. Documentation & Reproducibility (Max 10 pts)
    doc_score = 0.0
    if repo.get("description") and len(repo.get("description", "")) > 25:
        doc_score += 5.0
    if repo.get("homepage"):
        doc_score += 3.0  # Live deployment / documentation link
    if repo.get("license"):
        doc_score += 2.0  # Open-source licensed

    # 5. Maintenance & Recency Signals (Max 10 pts)
    recency_score = 0.0
    pushed_at_str = repo.get("pushed_at") or repo.get("updated_at")
    if pushed_at_str:
        try:
            pushed_year = int(pushed_at_str[:4])
            current_year = datetime.now().year
            diff_years = max(current_year - pushed_year, 0)
            if diff_years <= 1:
                recency_score += 6.0
            elif diff_years <= 2:
                recency_score += 4.0
            else:
                recency_score += 2.0
        except Exception:
            recency_score += 3.0

    stars = repo.get("stargazers_count", 0)
    if stars >= 50:
        recency_score += 4.0
    elif stars >= 10:
        recency_score += 2.5
    elif stars >= 3:
        recency_score += 1.0

    total_score = round(min(tech_score + responsibility_score + structure_score + doc_score + recency_score, 100.0), 1)

    evidence_summary = (
        f"Matches {len(matched_skills)} target technologies ({', '.join(matched_skills[:3]) if matched_skills else 'core stack'}). "
        f"Implements {len(matched_resp)} key architecture components ({', '.join(matched_resp[:2]) if matched_resp else 'production design'})."
    )

    return {
        "relevance_score": total_score,
        "score_breakdown": {
            "technology_overlap": round(tech_score, 1),
            "responsibility_overlap": round(responsibility_score, 1),
            "code_structure": round(structure_score, 1),
            "documentation": round(doc_score, 1),
            "maintenance_recency": round(recency_score, 1),
        },
        "matched_skills": matched_skills,
        "evidence_summary": evidence_summary,
    }


NON_PROJECT_INDICATORS = {
    'interview', 'interviews', 'exercise', 'exercises', 'question', 'questions',
    'cheat-sheet', 'cheatsheet', 'awesome', 'roadmap', 'curated-list',
    'study-plan', 'handbook', 'leetcode', 'qa', 'quiz', 'quizzes', 'prep-guide',
    'interview-questions', 'interview-prep'
}


def is_interview_or_qa_repo(repo: Dict[str, Any]) -> bool:
    """Check if repository is an interview question collection rather than a real software project."""
    name_str = (repo.get("repo_name") or repo.get("name") or repo.get("full_name") or "").lower()
    desc_lower = (repo.get("description") or "").lower()

    if not name_str:
        return False

    name_words = set(re.split(r'[-_/\s.]', name_str))
    if name_words.intersection(NON_PROJECT_INDICATORS):
        return True

    for ind in NON_PROJECT_INDICATORS:
        if ind in name_str:
            return True

    indicators_in_desc = [
        'interview question', 'interview questions', 'interview prep',
        'cheatsheet', 'cheat sheet', 'devops interview', 'python interview',
        'java interview', 'coding interview', 'leetcode solutions', 'exercise questions'
    ]
    if any(q in desc_lower for q in indicators_in_desc):
        return True

    return False


def search_github_repositories(
    job_title: str = "",
    job_skills: str = "",
    job_description: str = "",
    limit: int = 8
) -> List[Dict[str, Any]]:
    """
    Search GitHub public repositories matching target job parameters with caching and rate-limit safety.
    Filters out interview cheat sheets and QA lists to return real software engineering projects.
    """
    detected_tech = extract_keywords_from_job(job_title, job_skills, job_description)
    queries = build_search_queries(job_title, detected_tech)
    
    cache_key = f"gh_disc_v3_{hashlib.md5(f'{job_title}_{job_skills}_{limit}'.encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    headers = get_github_headers()
    collected_repos = {}

    # Check if user specified a direct repository path e.g. "jhipster/generator-jhipster"
    clean_target = (job_skills or '').strip()
    if '/' in clean_target and len(clean_target.split()) == 1 and not clean_target.startswith(('http://', 'https://')):
        try:
            r_single = requests.get(f"https://api.github.com/repos/{clean_target}", headers=headers, timeout=DEFAULT_TIMEOUT)
            if r_single.status_code == 200:
                item = r_single.json()
                collected_repos[item.get("id")] = item
        except Exception as e:
            logger.warning(f"Error fetching specific repo {clean_target}: {e}")

    for query in queries:
        try:
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": 12,
            }
            res = requests.get(GITHUB_API_URL, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
            
            # Check rate limiting
            if res.status_code == 403:
                logger.warning("GitHub API rate limit exceeded in repository search.")
                break
                
            if res.status_code == 200:
                data = res.json()
                for item in data.get("items", []):
                    repo_id = item.get("id")
                    if repo_id and repo_id not in collected_repos:
                        collected_repos[repo_id] = item
                        
        except Exception as e:
            logger.warning(f"Error querying GitHub API for '{query}': {e}")
            continue

    # Score and rank all collected repositories, filtering out interview QA repos
    scored_list = []
    for repo in collected_repos.values():
        if is_interview_or_qa_repo(repo):
            # Skip interview question banks — candidates need real codebases on their resume
            continue

        scoring = calculate_relevance_score(
            repo=repo,
            job_skills=detected_tech,
            job_description=job_description,
            job_title=job_title
        )
        
        # Build tech stack tag list from language + topics
        tech_tags = [repo.get("language")] if repo.get("language") else []
        for top in repo.get("topics", [])[:4]:
            if top and top.lower() not in [t.lower() for t in tech_tags]:
                tech_tags.append(top)

        scored_list.append({
            "repo_name": repo.get("full_name") or repo.get("name"),
            "repo_url": repo.get("html_url"),
            "description": repo.get("description") or "Open-source software application.",
            "stars": repo.get("stargazers_count", 0),
            "language": repo.get("language") or "Python / JavaScript",
            "tech_stack": tech_tags,
            "relevance_score": scoring["relevance_score"],
            "score_breakdown": scoring["score_breakdown"],
            "evidence_summary": scoring["evidence_summary"],
            "candidate_relationship": "RECOMMENDED",
            "is_selected": False,
        })

    # If no results collected (e.g. rate limit or offline), fall back to curated startup/enterprise projects
    if not scored_list:
        results = get_fallback_curated_projects(detected_tech)
        cache.set(cache_key, results, 3600)  # cache 1 hour
        return results

    # Sort descending by relevance score
    scored_list.sort(key=lambda x: (x["relevance_score"], x["stars"]), reverse=True)
    final_results = scored_list[:limit]
    
    cache.set(cache_key, final_results, CACHE_TTL)
    return final_results


def get_fallback_curated_projects(detected_tech: List[str]) -> List[Dict[str, Any]]:
    """
    Domain-aware curated open-source projects for fallback when rate-limited.
    Matches the candidate's exact tech stack (Java, Python, React, Cloud, Mobile, AI/ML).
    """
    curated_pool = [
        # 1. Python & FastAPI / Microservices
        {
            "repo_name": "tiangolo/fastapi",
            "repo_url": "https://github.com/tiangolo/fastapi",
            "description": "FastAPI framework, high performance, easy to learn, fast to code, ready for production.",
            "stars": 75000,
            "language": "Python",
            "tech_stack": ["Python", "FastAPI", "AsyncIO", "Pydantic", "Starlette"],
            "relevance_score": 92.0,
            "score_breakdown": {
                "technology_overlap": 32.0,
                "responsibility_overlap": 23.0,
                "code_structure": 19.0,
                "documentation": 9.5,
                "maintenance_recency": 8.5
            },
            "evidence_summary": "Production ASGI REST API architecture with type validation, automated OpenAPI docs, and asynchronous database connection pools.",
            "candidate_relationship": "RECOMMENDED",
            "is_selected": False,
        },
        # 2. Python & Django REST Framework
        {
            "repo_name": "encode/django-rest-framework",
            "repo_url": "https://github.com/encode/django-rest-framework",
            "description": "Web APIs for Django. Powerful and flexible toolkit for building Web APIs.",
            "stars": 28000,
            "language": "Python",
            "tech_stack": ["Python", "Django", "DRF", "PostgreSQL", "REST"],
            "relevance_score": 90.0,
            "score_breakdown": {
                "technology_overlap": 31.0,
                "responsibility_overlap": 22.5,
                "code_structure": 18.0,
                "documentation": 9.0,
                "maintenance_recency": 9.0
            },
            "evidence_summary": "Enterprise RESTful API pattern with ModelSerializers, JWT authentication, pagination, and relational query optimization.",
            "candidate_relationship": "RECOMMENDED",
            "is_selected": False,
        },
        # 3. Java & Spring Boot / Microservices
        {
            "repo_name": "macrozheng/mall-swarm",
            "repo_url": "https://github.com/macrozheng/mall-swarm",
            "description": "Enterprise microservices system built on Spring Cloud & Spring Boot with Docker, MyBatis, Redis, and Elasticsearch.",
            "stars": 38000,
            "language": "Java",
            "tech_stack": ["Java", "Spring Boot", "Spring Cloud", "Docker", "Elasticsearch", "MySQL"],
            "relevance_score": 91.5,
            "score_breakdown": {
                "technology_overlap": 32.0,
                "responsibility_overlap": 23.5,
                "code_structure": 18.5,
                "documentation": 9.0,
                "maintenance_recency": 8.5
            },
            "evidence_summary": "Enterprise microservices architecture utilizing Spring Cloud Gateway, JWT authentication, and distributed Redis caching.",
            "candidate_relationship": "RECOMMENDED",
            "is_selected": False,
        },
        # 4. Java PetClinic Reference Implementation
        {
            "repo_name": "spring-projects/spring-petclinic",
            "repo_url": "https://github.com/spring-projects/spring-petclinic",
            "description": "A Spring Boot sample application showcasing JPA, validation, database integration, and MVC patterns.",
            "stars": 8200,
            "language": "Java",
            "tech_stack": ["Java", "Spring Boot", "Spring Data JPA", "PostgreSQL", "Maven"],
            "relevance_score": 88.0,
            "score_breakdown": {
                "technology_overlap": 30.0,
                "responsibility_overlap": 22.0,
                "code_structure": 18.0,
                "documentation": 9.0,
                "maintenance_recency": 9.0
            },
            "evidence_summary": "Canonical Spring Boot application demonstrating Repository design patterns, Hibernate ORM mappings, and JUnit integration test suites.",
            "candidate_relationship": "RECOMMENDED",
            "is_selected": False,
        },
        # 5. JavaScript / TypeScript & React / Next.js
        {
            "repo_name": "vercel/next.js",
            "repo_url": "https://github.com/vercel/next.js",
            "description": "The React Framework for the Web. Hybrid static & server rendering, TypeScript support, smart bundling.",
            "stars": 125000,
            "language": "TypeScript",
            "tech_stack": ["React", "Next.js", "TypeScript", "Node.js", "Tailwind"],
            "relevance_score": 91.0,
            "score_breakdown": {
                "technology_overlap": 31.0,
                "responsibility_overlap": 23.0,
                "code_structure": 19.0,
                "documentation": 9.0,
                "maintenance_recency": 9.0
            },
            "evidence_summary": "Server-side rendering (SSR), dynamic App Router, edge runtime deployment, and responsive UI components.",
            "candidate_relationship": "RECOMMENDED",
            "is_selected": False,
        },
        # 6. React Core Component Architecture
        {
            "repo_name": "facebook/react",
            "repo_url": "https://github.com/facebook/react",
            "description": "The library for web and native user interfaces.",
            "stars": 225000,
            "language": "JavaScript",
            "tech_stack": ["JavaScript", "TypeScript", "React", "Frontend", "UI"],
            "relevance_score": 88.0,
            "score_breakdown": {
                "technology_overlap": 30.0,
                "responsibility_overlap": 21.0,
                "code_structure": 18.0,
                "documentation": 8.5,
                "maintenance_recency": 8.5
            },
            "evidence_summary": "Modern component-driven UI architecture, state synchronization, virtual DOM reconciliation, and responsive accessibility.",
            "candidate_relationship": "RECOMMENDED",
            "is_selected": False,
        },
        # 7. Data Science & Machine Learning / AI
        {
            "repo_name": "langchain-ai/langchain",
            "repo_url": "https://github.com/langchain-ai/langchain",
            "description": "Building applications with LLMs through composability and retrieval-augmented generation (RAG).",
            "stars": 95000,
            "language": "Python",
            "tech_stack": ["Python", "Machine Learning", "LLMs", "Vector DB", "RAG"],
            "relevance_score": 90.5,
            "score_breakdown": {
                "technology_overlap": 31.0,
                "responsibility_overlap": 23.0,
                "code_structure": 18.5,
                "documentation": 9.0,
                "maintenance_recency": 9.0
            },
            "evidence_summary": "RAG architecture with vector embedding storage, semantic retrieval pipelines, and streaming LLM token generation.",
            "candidate_relationship": "RECOMMENDED",
            "is_selected": False,
        },
        # 8. Cloud / DevOps & Docker / Kubernetes
        {
            "repo_name": "moby/moby",
            "repo_url": "https://github.com/moby/moby",
            "description": "Moby Project - a collaborative project for the container ecosystem to assemble container-based systems.",
            "stars": 68000,
            "language": "Go",
            "tech_stack": ["Docker", "Kubernetes", "DevOps", "Linux", "Cloud", "Go"],
            "relevance_score": 87.5,
            "score_breakdown": {
                "technology_overlap": 29.0,
                "responsibility_overlap": 22.0,
                "code_structure": 18.0,
                "documentation": 9.0,
                "maintenance_recency": 9.5
            },
            "evidence_summary": "Containerization runtime engine, automated image layer caching, networking bridges, and daemon process management.",
            "candidate_relationship": "RECOMMENDED",
            "is_selected": False,
        },
        # 9. Mobile / Flutter / Android
        {
            "repo_name": "flutter/flutter",
            "repo_url": "https://github.com/flutter/flutter",
            "description": "Flutter makes it easy and fast to build beautiful apps for mobile and beyond.",
            "stars": 165000,
            "language": "Dart",
            "tech_stack": ["Flutter", "Dart", "Android", "iOS", "Mobile"],
            "relevance_score": 89.0,
            "score_breakdown": {
                "technology_overlap": 30.0,
                "responsibility_overlap": 22.5,
                "code_structure": 18.5,
                "documentation": 9.0,
                "maintenance_recency": 9.0
            },
            "evidence_summary": "Cross-platform mobile UI framework with declarative widgets, native platform channels, and high-performance skia canvas rendering.",
            "candidate_relationship": "RECOMMENDED",
            "is_selected": False,
        },
        # 10. DevOps / Cloud & Microservices Platform (JHipster)
        {
            "repo_name": "jhipster/generator-jhipster",
            "repo_url": "https://github.com/jhipster/generator-jhipster",
            "description": "Enterprise microservice platform generating production-ready fullstack architectures with Spring Boot, Angular/React, Docker, and Kubernetes.",
            "stars": 22500,
            "language": "TypeScript",
            "tech_stack": ["Spring Boot", "Kubernetes", "Docker", "DevOps", "Microservices", "Java"],
            "relevance_score": 93.0,
            "score_breakdown": {
                "technology_overlap": 33.0,
                "responsibility_overlap": 23.5,
                "code_structure": 19.0,
                "documentation": 9.0,
                "maintenance_recency": 8.5
            },
            "evidence_summary": "Enterprise microservices and cloud deployment framework with Kubernetes manifests, Docker containerization, and automated CI/CD pipelines.",
            "candidate_relationship": "RECOMMENDED",
            "is_selected": False,
        },
        # 11. GitOps & Cloud Continuous Delivery (ArgoCD)
        {
            "repo_name": "argoproj/argo-cd",
            "repo_url": "https://github.com/argoproj/argo-cd",
            "description": "Declarative, GitOps continuous delivery tool for Kubernetes, managing automated deployments and cluster state synchronization.",
            "stars": 19500,
            "language": "Go",
            "tech_stack": ["Kubernetes", "GitOps", "Docker", "CI/CD", "DevOps", "Go"],
            "relevance_score": 92.0,
            "score_breakdown": {
                "technology_overlap": 32.0,
                "responsibility_overlap": 23.0,
                "code_structure": 19.0,
                "documentation": 9.0,
                "maintenance_recency": 9.0
            },
            "evidence_summary": "Kubernetes-native declarative GitOps controller automating progressive syncs, rollback validation, and multi-cluster deployments.",
            "candidate_relationship": "RECOMMENDED",
            "is_selected": False,
        }
    ]

    # Rank pool by matching detected technologies
    tech_set = {t.lower() for t in detected_tech} if detected_tech else set()
    if tech_set:
        def match_score(p):
            p_stack = {s.lower() for s in p.get("tech_stack", [])} | {p.get("language", "").lower()}
            common = tech_set.intersection(p_stack)
            return len(common) * 10.0 + p.get("relevance_score", 80)
        curated_pool.sort(key=match_score, reverse=True)

    return curated_pool[:6]
