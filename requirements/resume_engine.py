"""
ATS 90+ Score Resume Generator & Enterprise Project Matching Engine.
Tailored for college students, freshers, and off-campus tech drives.
All projects use Google XYZ formula: Action Verb + Accomplished [X] + Measured by [Y] + Using [Z].
"""

import re

RESUME_ROLES = {
    'python-backend': {
        'role_id': 'python-backend',
        'title': 'Python & Django Backend Engineer',
        'badge': 'Python / Django / FastAPI',
        'summary': 'Results-driven Backend Software Engineer with deep expertise in Python, Django REST Framework, and distributed microservices. Proven track record of designing high-throughput REST APIs, optimizing relational databases, and using Redis caching and asynchronous job workers.',
        'technical_skills': {
            'Languages': 'Python, SQL, JavaScript, Bash',
            'Frameworks': 'Django, Django REST Framework (DRF), FastAPI, Flask',
            'Databases': 'PostgreSQL, SQLite, Redis, MySQL',
            'Cloud & DevOps': 'Docker, AWS (S3, EC2), GitHub Actions, Linux, Nginx',
            'Architecture & Tools': 'RESTful APIs, Celery, Git, JWT Auth, Postman, Pytest'
        },
        'enterprise_projects': [
            {
                'title': 'Distributed Order Processing & Inventory Locking Microservice',
                'role': 'Backend Systems Architect',
                'tech_stack': 'Python, Django REST Framework, PostgreSQL, Redis, Celery, Docker',
                'bullets': [
                    'Built a transactional order execution engine that reserves inventory before payment confirmation.',
                    'Used a Redis lock with atomic database transactions so two orders cannot claim the same SKU.',
                    'Tuned relational queries with select_related/prefetch_related and B-tree indexes after profiling slow endpoints.',
                    'Moved invoice generation, payment webhooks and audit logging onto a Celery queue backed by Redis.',
                ]
            },
            {
                'title': 'Real-Time API Telemetry & Rate-Limiting Security Gateway',
                'role': 'Lead Backend Developer',
                'tech_stack': 'Python, FastAPI, AsyncIO, Redis, Docker, Prometheus',
                'bullets': [
                    'Built an asynchronous API reverse proxy that enforces sliding-window rate limits per tenant with Redis sorted sets.',
                    'Implemented JWT authentication with HMAC signature verification and role-based access control.',
                    'Wrote multi-stage Docker builds for the service and ran the test suite in GitHub Actions.',
                ]
            }
        ],
        'education': {
            'degree': 'Bachelor of Engineering / B.Tech in Computer Science',
            'institution': 'Engineering College & Technical University',
            'year': '2022 – 2026',
            'gpa': '',
            'coursework': 'Data Structures & Algorithms, Database Management Systems (DBMS), Operating Systems, Computer Networks'
        },
        'certifications': [],
        'target_ats_keywords': [
            'Python', 'Django', 'Django REST Framework', 'PostgreSQL', 'Redis', 'Celery',
            'Docker', 'REST API', 'Microservices', 'Git', 'CI/CD', 'Scalability', 'Unit Testing'
        ]
    },

    'full-stack': {
        'role_id': 'full-stack',
        'title': 'Full-Stack Software Engineer',
        'badge': 'React / Next.js / Python / Node',
        'summary': 'Full-Stack Software Engineer adept at building responsive, scalable end-to-end web applications using modern React, TypeScript, and robust Python/Node backends. Focused on component structure, API performance and accessible, responsive interfaces.',
        'technical_skills': {
            'Languages': 'JavaScript (ES6+), TypeScript, Python, HTML5, CSS3, SQL',
            'Frontend': 'React.js, Next.js, Tailwind CSS, Redux Toolkit, Lucide Icons',
            'Backend': 'Node.js, Express, Django REST Framework, RESTful APIs, WebSockets',
            'Databases': 'PostgreSQL, MongoDB, SQLite, Redis',
            'Tools & Platforms': 'Docker, Git/GitHub, Vercel, Postman, Vite, Webpack'
        },
        'enterprise_projects': [
            {
                'title': 'Enterprise Collaborative Workspace & Workflow Telemetry Platform',
                'role': 'Full-Stack Lead Engineer',
                'tech_stack': 'React.js, TypeScript, Next.js 14, Tailwind CSS, Django REST, WebSockets',
                'bullets': [
                    'Built real-time document collaboration and activity feeds with WebSocket state synchronization.',
                    'Built a responsive component library with Tailwind CSS, checked for WCAG contrast and keyboard navigation.',
                    'Integrated OAuth2 and JWT session management with token refresh for multi-tenant teams.',
                    'Split the bundle by route and cached images on a CDN to shorten the first load.',
                ]
            },
            {
                'title': 'Cloud Media Asset Ingestion & Resumable Chunked Uploader',
                'role': 'Full-Stack Developer',
                'tech_stack': 'React, Node.js, Express, Cloudflare R2 / AWS S3, Redis',
                'bullets': [
                    'Implemented chunked uploads with automatic retry and pause/resume, so a dropped connection does not restart the transfer.',
                    'Generated presigned upload URLs so files go straight to object storage instead of through the app server.',
                ]
            }
        ],
        'education': {
            'degree': 'Bachelor of Engineering in Information Technology / Computer Science',
            'institution': 'State Technical University',
            'year': '2022 – 2026',
            'gpa': '',
            'coursework': 'Object-Oriented Programming, Web Technologies, Software Engineering, Cloud Computing'
        },
        'certifications': [],
        'target_ats_keywords': [
            'Full Stack', 'React', 'Next.js', 'TypeScript', 'JavaScript', 'Python',
            'Node.js', 'PostgreSQL', 'Tailwind CSS', 'WebSockets', 'REST APIs', 'Git', 'Agile'
        ]
    },

    'java-sde': {
        'role_id': 'java-sde',
        'title': 'Java & Spring Boot SDE-1',
        'badge': 'Java 17 / Spring Boot / Kafka',
        'summary': 'Software Development Engineer with deep foundation in Java 17, Spring Boot, and enterprise microservices architecture. Experienced in event-driven systems with Apache Kafka, robust database design with Spring Data JPA/Hibernate, and writing comprehensive test suites with JUnit 5 & Mockito.',
        'technical_skills': {
            'Languages': 'Java (11/17/21), SQL, Python, Bash',
            'Frameworks': 'Spring Boot, Spring Data JPA, Hibernate, Spring Security, Spring Cloud',
            'Messaging & Microservices': 'Apache Kafka, RabbitMQ, REST APIs, Microservices, Eureka',
            'Databases': 'MySQL, PostgreSQL, Oracle, Redis',
            'Tools & DevOps': 'Maven, Gradle, Docker, Git, JUnit 5, Mockito, SonarQube'
        },
        'enterprise_projects': [
            {
                'title': 'Distributed Payment Reconciliation & Transaction Ledger Engine',
                'role': 'Backend Java Developer',
                'tech_stack': 'Java 17, Spring Boot, Spring Data JPA, Apache Kafka, PostgreSQL, Docker',
                'bullets': [
                    'Built an event-driven payment reconciliation service that consumes transaction events from Apache Kafka.',
                    'Used idempotent consumers and JPA optimistic locking (@Version) so a retried event cannot double-credit an account.',
                    'Secured inter-service calls with Spring Security, OAuth2 JWT tokens and custom authentication filters.',
                    'Wrote JUnit 5 and Mockito tests for the reconciliation rules and ran SonarQube analysis in CI.',
                ]
            },
            {
                'title': 'High-Throughput Distributed Cache-Aside Catalog Service',
                'role': 'Software Development Engineer',
                'tech_stack': 'Java 17, Spring Boot, Redis, MySQL, Docker, Maven',
                'bullets': [
                    'Implemented a two-tier cache-aside pattern with Spring Cache and a Redis cluster in front of the catalog database.',
                    'Designed a multi-tenant schema with composite indexes and pagination for catalog queries.',
                ]
            }
        ],
        'education': {
            'degree': 'Bachelor of Engineering in Computer Science & Engineering',
            'institution': 'Institute of Technology & Science',
            'year': '2022 – 2026',
            'gpa': '',
            'coursework': 'Design & Analysis of Algorithms, Object-Oriented Analysis, System Design, Distributed Systems'
        },
        'certifications': [],
        'target_ats_keywords': [
            'Java', 'Spring Boot', 'Spring Data JPA', 'Microservices', 'Apache Kafka',
            'Hibernate', 'REST API', 'MySQL', 'PostgreSQL', 'Docker', 'JUnit', 'Maven', 'Git'
        ]
    },

    'data-analyst': {
        'role_id': 'data-analyst',
        'title': 'Data Analyst & Machine Learning Engineer',
        'badge': 'Python / Pandas / ML / SQL',
        'summary': 'Analytical and detail-oriented Data Professional with proven skills in exploratory data analysis (EDA), predictive machine learning modeling, and automated ETL data pipelines. Adept at translating complex datasets into actionable business intelligence using Python, SQL, and interactive dashboards.',
        'technical_skills': {
            'Languages': 'Python, SQL (PostgreSQL, MySQL), R',
            'Data Science & ML': 'Pandas, NumPy, Scikit-Learn, XGBoost, Matplotlib, Seaborn',
            'Data Engineering & ETL': 'DuckDB, Apache Airflow, REST APIs, JSON/Parquet',
            'BI & Visualization': 'PowerBI, Tableau, Streamlit, Excel (Advanced VLOOKUP & Pivots)',
            'Tools': 'Jupyter Notebooks, Git, Docker, Google Colab'
        },
        'enterprise_projects': [
            {
                'title': 'Automated Customer Churn Prediction & Retention Analytics Engine',
                'role': 'Lead Data Scientist',
                'tech_stack': 'Python, Scikit-Learn, XGBoost, Pandas, FastAPI, PostgreSQL, PowerBI',
                'bullets': [
                    'Built a churn classification pipeline on historical user records, evaluated with ROC-AUC on a held-out split.',
                    'Built a feature engineering pipeline covering RFM, session frequency and ticket velocity.',
                    'Served the model through a FastAPI inference endpoint so churn scores are available inside customer workflows.',
                    'Built an executive PowerBI dashboard tracking monthly retention and revenue risk.',
                ]
            },
            {
                'title': 'High-Volume E-Commerce ETL Pipeline & Sales Analytics Lake',
                'role': 'Data Analyst Engineer',
                'tech_stack': 'Python, DuckDB, Pandas, Parquet, SQLite, Streamlit',
                'bullets': [
                    'Built a daily ETL pipeline that lands CSV and JSON sales feeds as partitioned Parquet files.',
                    'Built a Streamlit dashboard with cohort filters to surface inventory costs that were not being tracked.',
                ]
            }
        ],
        'education': {
            'degree': 'Bachelor of Engineering in Data Science / Computer Engineering',
            'institution': 'College of Engineering & Technology',
            'year': '2022 – 2026',
            'gpa': '',
            'coursework': 'Probability & Statistics, Machine Learning, Data Mining, Applied Linear Algebra, Big Data Systems'
        },
        'certifications': [],
        'target_ats_keywords': [
            'Data Analysis', 'Python', 'SQL', 'Pandas', 'NumPy', 'Machine Learning',
            'Scikit-Learn', 'XGBoost', 'PowerBI', 'Tableau', 'ETL', 'Data Visualization', 'Statistics'
        ]
    },

    'devops-cloud': {
        'role_id': 'devops-cloud',
        'title': 'Cloud & DevOps SDE',
        'badge': 'Docker / K8s / CI-CD / AWS',
        'summary': 'Cloud & DevOps Engineer committed to infrastructure automation, continuous integration, and high-availability distributed systems. Experienced in writing Infrastructure-as-Code with Terraform, container orchestration using Kubernetes, and crafting zero-downtime CI/CD deployment pipelines.',
        'technical_skills': {
            'Cloud Providers': 'AWS (EC2, S3, RDS, IAM, EKS, CloudWatch), Cloudflare',
            'Containers & K8s': 'Docker, Docker Compose, Kubernetes, Helm, Ingress',
            'CI/CD & GitOps': 'GitHub Actions, GitLab CI, ArgoCD, Jenkins',
            'IaC & Config': 'Terraform, Ansible, Bash Scripting, Python Automation',
            'Observability': 'Prometheus, Grafana, ELK Stack, Nginx'
        },
        'enterprise_projects': [
            {
                'title': 'Zero-Downtime Multi-Stage GitOps Pipeline & Kubernetes Cluster',
                'role': 'DevOps & Infrastructure Engineer',
                'tech_stack': 'Docker, Kubernetes, GitHub Actions, Terraform, AWS, Helm, Prometheus',
                'bullets': [
                    'Built a CI/CD pipeline in GitHub Actions that promotes builds from staging to production.',
                    'Provisioned AWS infrastructure with modular Terraform and least-privilege IAM policies.',
                    'Configured the Kubernetes Horizontal Pod Autoscaler and rolling deployments to keep releases zero-downtime.',
                    'Instrumented services with Prometheus exporters and Grafana alerts to shorten incident response.',
                ]
            },
            {
                'title': 'Automated Container Security & Image Vulnerability Scanner',
                'role': 'Cloud Security Engineer',
                'tech_stack': 'Docker, Trivy, GitHub Actions, Bash, Python',
                'bullets': [
                    'Added Trivy vulnerability scanning to pull-request checks so builds with critical CVEs fail.',
                    'Wrote multi-stage Alpine container builds to keep production images small.',
                ]
            }
        ],
        'education': {
            'degree': 'Bachelor of Engineering in Information Science / Computer Science',
            'institution': 'Technological University',
            'year': '2022 – 2026',
            'gpa': '',
            'coursework': 'Cloud Computing, Computer Systems, Network Security, System Administration, Linux Internals'
        },
        'certifications': [],
        'target_ats_keywords': [
            'DevOps', 'AWS', 'Docker', 'Kubernetes', 'CI/CD', 'GitHub Actions',
            'Terraform', 'Linux', 'Bash', 'Prometheus', 'Grafana', 'Nginx', 'Infrastructure as Code'
        ]
    }
}


# Tokens containing a slash that are one skill. Anything else with a slash, such
# as "Python/Java", means either one.
_ONE_SKILL_WITH_SLASH = {'ci/cd', 'tcp/ip', 'ui/ux', 'a/b testing', 'pl/sql', 'i/o'}
_SKILL_ALIASES = {
    'javascript': ('js',), 'typescript': ('ts',), 'kubernetes': ('k8s',),
    'postgresql': ('postgres',), 'postgres': ('postgresql',),
    'node.js': ('node', 'nodejs'), 'nodejs': ('node.js', 'node'), 'node': ('node.js', 'nodejs'),
    'react': ('react.js', 'reactjs'), 'react.js': ('react', 'reactjs'), 'reactjs': ('react', 'react.js'),
    'next.js': ('nextjs',), 'nextjs': ('next.js',), 'vue': ('vue.js', 'vuejs'), 'vue.js': ('vue', 'vuejs'),
    'golang': ('go',), 'rest api': ('restful', 'rest apis'), 'restful api': ('rest api', 'restful'),
    'ci/cd': ('continuous integration',), 'machine learning': ('ml',), 'artificial intelligence': ('ai',),
    'dsa': ('data structures',), 'data structures & algorithms': ('dsa', 'data structures'),
}
# Ordinary English words, so they only count in the capitalisation a skill uses.
_CASE_SENSITIVE_SKILLS = {'go', 'c', 'r', 'd', 'j', 'ai', 'ml', 'ts', 'js'}
_SKILL_PREFIXES = ('core ', 'advanced ', 'basic ', 'strong ', 'modern ')


def _skill_variants(skill: str) -> set:
    name = ' '.join(str(skill or '').lower().split())
    for prefix in _SKILL_PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix):]
    parts = [name] if name in _ONE_SKILL_WITH_SLASH or '/' not in name else [p.strip() for p in name.split('/')]
    variants = set()
    for part in parts:
        if part:
            variants.add(part)
            variants.update(_SKILL_ALIASES.get(part, ()))
            variants.update(_SKILL_ALIASES.get(part.rstrip('s'), ()))
    return variants


def has_keyword(skill: str, text: str) -> bool:
    """
    True when `text` really names the skill.

    A plain substring test said a JavaScript resume knows Java and that a resume
    with "experience" in it knows R. Skills match as whole words instead, in the
    forms people actually write them.
    """
    if not text:
        return False
    lowered = text.lower()
    for variant in _skill_variants(skill):
        haystack, needle = (text, variant.upper() if len(variant) < 3 and variant != 'go' else variant.capitalize()) \
            if variant in _CASE_SENSITIVE_SKILLS else (lowered, variant)
        stem = needle[:-1] if needle.endswith('s') and len(needle) > 3 else needle
        if re.search(rf'(?<![A-Za-z0-9+#.]){re.escape(stem)}s?(?![A-Za-z0-9+#])', haystack):
            return True
    return False


# Parts of a resume the candidate did not write as a claim about themselves.
_NOT_RESUME_CONTENT = {
    'contact', 'github', 'github_url', 'url', 'candidate_relationship', 'profile_level',
    'ats_score', 'ats_badge', 'ats_grade', 'breakdown',
}


def resume_text(resume) -> str:
    """The words on the resume, without JSON keys, profile links or score fields."""
    if isinstance(resume, str):
        return resume
    if isinstance(resume, dict):
        return ' '.join(
            resume_text(value) if key not in ('skills',) else skills_text(value)
            for key, value in resume.items() if key not in _NOT_RESUME_CONTENT
        )
    if isinstance(resume, (list, tuple)):
        return ' '.join(resume_text(item) for item in resume)
    return ''


def skills_text(skills) -> str:
    """Group names like "Languages" are headings, so only the skills themselves count."""
    if isinstance(skills, dict):
        return ' , '.join(resume_text(value) for value in skills.values())
    return resume_text(skills)


def job_match_limit(job_match: int) -> int:
    """Polish cannot make up for missing skills: 0% match tops out at 40, 100% at 100."""
    return 40 + round(job_match * 0.6)


def pick_role_for_skills(skills) -> str:
    """The role template closest to a job's skills, or '' if none shares any."""
    best, best_hits = '', 0
    for role_id, role in RESUME_ROLES.items():
        text = ' '.join([' '.join(role['target_ats_keywords']), skills_text(role['technical_skills'])])
        hits = sum(1 for skill in skills or [] if has_keyword(skill, text))
        if hits > best_hits:
            best, best_hits = role_id, hits
    return best


ATS_SKILL_CATEGORIES = {
    'Languages': [
        'Python', 'JavaScript', 'TypeScript', 'Java', 'Golang', 'Go', 'C++', 'C#', 'Rust', 'SQL',
        'PHP', 'Ruby', 'Swift', 'Kotlin', 'Scala', 'Bash', 'Shell', 'HTML', 'CSS', 'HTML/CSS',
    ],
    'Frameworks & Libraries': [
        'Django', 'Django REST Framework', 'DRF', 'FastAPI', 'Flask', 'React', 'Next.js', 'Node.js',
        'Express', 'Express.js', 'Spring Boot', 'Spring', 'Angular', 'Vue.js', 'Vue', 'Redux',
        'Tailwind CSS', 'Tailwind', 'GraphQL', 'gRPC', 'PyTorch', 'TensorFlow', 'Pandas', 'NumPy',
        'Scikit-Learn', 'Selenium', 'Playwright', 'Flutter', 'React Native',
    ],
    'Databases & Caching': [
        'PostgreSQL', 'Postgres', 'MySQL', 'MongoDB', 'Redis', 'Cassandra', 'Elasticsearch',
        'DynamoDB', 'SQLite', 'Oracle', 'Snowflake', 'BigQuery', 'Firebase',
    ],
    'Cloud & DevOps': [
        'Docker', 'Kubernetes', 'AWS', 'GCP', 'Azure', 'CI/CD', 'GitHub Actions', 'Jenkins',
        'Terraform', 'Linux', 'Nginx', 'Kafka', 'Celery', 'RabbitMQ', 'Prometheus', 'Grafana', 'Git',
    ],
    'Architecture & Tools': [
        'REST API', 'RESTful APIs', 'Microservices', 'Distributed Systems', 'System Design', 'JWT',
        'Unit Testing', 'Pytest', 'Postman', 'Agile', 'Scrum', 'Machine Learning', 'AI', 'OOP',
    ],
}


def categorize_skill(skill: str) -> str:
    """Map a skill or technology keyword to its standard ATS category."""
    s_clean = skill.strip()
    s_lower = s_clean.lower()
    for cat, items in ATS_SKILL_CATEGORIES.items():
        for item in items:
            if item.lower() == s_lower:
                return cat
    for cat, items in ATS_SKILL_CATEGORIES.items():
        for item in items:
            if s_lower in item.lower() or item.lower() in s_lower:
                return cat
    return 'Architecture & Tools'


def inject_missing_ats_skills(current_skills, missing_skills):
    """
    Intelligently injects missing ATS keywords and skills into the resume's skills data.
    Preserves existing candidate skills and organizes new skills under appropriate standard categories.
    """
    if not missing_skills:
        return current_skills

    if isinstance(missing_skills, str):
        missing_list = [s.strip() for s in missing_skills.split(',') if s.strip()]
    elif isinstance(missing_skills, (list, tuple, set)):
        missing_list = [str(s).strip() for s in missing_skills if str(s).strip()]
    else:
        missing_list = []

    if not missing_list:
        return current_skills

    if isinstance(current_skills, dict):
        result = {k: v for k, v in current_skills.items()}
        existing = set()
        for v in result.values():
            if isinstance(v, list):
                existing.update(str(x).strip().lower() for x in v)
            elif isinstance(v, str):
                existing.update(str(x).strip().lower() for x in v.split(','))

        to_add = [s for s in missing_list if s.lower() not in existing]
        if not to_add:
            return result

        for skill in to_add:
            cat = categorize_skill(skill)
            matched_cat = None
            for existing_cat in result.keys():
                if existing_cat.lower() in cat.lower() or cat.lower() in existing_cat.lower():
                    matched_cat = existing_cat
                    break
            if not matched_cat:
                if 'Technical Skills' in result:
                    matched_cat = 'Technical Skills'
                elif 'Skills' in result:
                    matched_cat = 'Skills'
                elif len(result) == 1:
                    matched_cat = next(iter(result.keys()))
                else:
                    matched_cat = cat
                    result[matched_cat] = ''

            curr_val = result.get(matched_cat, '')
            if isinstance(curr_val, list):
                result[matched_cat] = curr_val + [skill]
            else:
                items = [x.strip() for x in str(curr_val).split(',') if x.strip()]
                if skill not in items:
                    items.append(skill)
                result[matched_cat] = ', '.join(items)
        return result
    elif isinstance(current_skills, list):
        existing = {str(x).strip().lower() for x in current_skills}
        new_items = list(current_skills)
        for s in missing_list:
            if s.lower() not in existing:
                new_items.append(s)
                existing.add(s.lower())
        return new_items
    elif isinstance(current_skills, str):
        existing = {x.strip().lower() for x in current_skills.split(',') if x.strip()}
        items = [x.strip() for x in current_skills.split(',') if x.strip()]
        for s in missing_list:
            if s.lower() not in existing:
                items.append(s)
                existing.add(s.lower())
        return ', '.join(items)
    return current_skills


def calculate_ats_score(resume_data, role_key='python-backend'):
    """Score a resume against a role, using the same evaluator as every other page."""
    from .resume_parser import evaluate_uploaded_resume_ats

    role = RESUME_ROLES.get(role_key, RESUME_ROLES['python-backend'])
    result = evaluate_uploaded_resume_ats(resume_data, role['target_ats_keywords'])
    result['matched_keywords'] = result['matched_skills']
    return result


def score_project_ats(project: dict, target_skills: list = None) -> dict:
    """
    Reverse-engineered ATS Project Scoring Engine (inspired by Resume Worded & Jobscan).
    Evaluates individual projects across 5 key dimensions:
    1. Strong Action Verbs (25 pts)
    2. Google XYZ Formula (25 pts)
    3. Quantified Numerical Metrics (20 pts)
    4. Target Tech Stack Relevance (20 pts)
    5. Architecture & System Depth (10 pts)
    """
    action_verbs = {
        'architected', 'engineered', 'developed', 'optimized', 'built', 'spearheaded',
        'designed', 'implemented', 'constructed', 'deployed', 'automated', 'integrated',
        'refactored', 'orchestrated', 'streamlined', 'benchmarked', 'scaled', 'accelerated',
        'authored', 'pioneered', 'established', 'executed', 'created', 'standardized', 'accomplished', 'modernized'
    }

    weak_verbs = {'helped', 'worked on', 'assisted', 'handled', 'was responsible for', 'tried', 'participated in'}

    bullets = project.get('bullets', [])
    if not bullets:
        return {
            'score': 20,
            'grade': 'Needs Bullets',
            'badge': '🔴 20/100',
            'feedback': 'Add at least 3 accomplishment bullets to pass ATS parsing.'
        }

    # 1. Action Verbs (25 pts)
    verb_score = 0
    strong_count = 0
    weak_count = 0
    for b in bullets:
        first_word = b.strip().lower().split(' ')[0] if b.strip() else ''
        if first_word in action_verbs:
            strong_count += 1
        elif any(b.strip().lower().startswith(wv) for wv in weak_verbs):
            weak_count += 1

    verb_score = min(25, int((strong_count / max(1, len(bullets))) * 25))
    if weak_count > 0:
        verb_score = max(5, verb_score - (weak_count * 5))

    # 2. Google XYZ Formula (Accomplished [X] by doing [Z], measured by [Y]) (25 pts)
    xyz_count = 0
    outcome_indicators = ['reducing', 'slashing', 'increasing', 'improving', 'cutting', 'preventing', 'delivering', 'achieving', 'generating', 'saving', 'by', 'utilizing', 'via', 'through']
    for b in bullets:
        b_lower = b.lower()
        has_action = any(b_lower.startswith(v) for v in action_verbs)
        has_outcome = any(ind in b_lower for ind in outcome_indicators)
        has_measure = bool(re.search(r'\d+', b))
        if has_action and (has_outcome or has_measure):
            xyz_count += 1

    xyz_score = min(25, int((xyz_count / max(1, len(bullets))) * 25))

    # 3. Quantified Numerical Metrics (20 pts)
    metric_regex = re.compile(r'(\d+[\.,]?\d*\s*(%|ms|kb|mb|gb|tb|req|k|x|skus|cve|users|tps|sec|min|hr|lpa|cr))|\b(\d{2,})\b|[₹$]\d+', re.IGNORECASE)
    bullets_with_metrics = sum(1 for b in bullets if metric_regex.search(b))
    metric_score = min(20, int((bullets_with_metrics / max(1, len(bullets))) * 20))

    # 4. Target Tech Stack Relevance (20 pts)
    tech_stack = project.get('tech_stack', '').lower()
    all_text_raw = ' '.join([project.get('title', ''), project.get('tech_stack', ''), ' '.join(bullets)])
    all_text = all_text_raw.lower()

    relevance_score = 15
    if target_skills:
        matched = sum(1 for s in target_skills if has_keyword(s, all_text_raw))
        relevance_score = min(20, int((matched / max(1, len(target_skills))) * 20) + 5)
    elif len(tech_stack) > 10:
        relevance_score = 20

    # 5. Architecture & System Depth (10 pts)
    arch_keywords = [
        'concurrency', 'distributed', 'redis', 'cache', 'queue', 'kafka', 'lock', 'index',
        'async', 'celery', 'docker', 'ci/cd', 'jwt', 'rbac', 'microservice', 'query',
        'latency', 'throughput', 'sharding', 'replica', 'api', 'postgres', 'nosql', 'load'
    ]
    arch_matches = sum(1 for kw in arch_keywords if kw in all_text)
    arch_score = min(10, arch_matches * 3)

    total = verb_score + xyz_score + metric_score + relevance_score + arch_score
    final_score = min(100, max(20, total))

    if final_score >= 85:
        grade = "Strong ATS Pass"
        badge = f"🟢 {final_score}/100"
    elif final_score >= 65:
        grade = "Moderate ATS Pass"
        badge = f"🟡 {final_score}/100"
    else:
        grade = "Needs Quantified Metrics"
        badge = f"🔴 {final_score}/100"

    return {
        'score': final_score,
        'grade': grade,
        'badge': badge,
        'breakdown': {
            'action_verbs': {'score': verb_score, 'max': 25, 'strong_count': strong_count},
            'google_xyz': {'score': xyz_score, 'max': 25, 'compliant_count': xyz_count},
            'metrics': {'score': metric_score, 'max': 20, 'bullets_with_metrics': bullets_with_metrics},
            'tech_relevance': {'score': relevance_score, 'max': 20},
            'system_depth': {'score': arch_score, 'max': 10}
        },
        'suggestions': [s for s in [
            "Add verifiable metrics (% latency reduction, req/sec throughput, scale)" if metric_score < 15 else None,
            "Start every bullet with strong action verbs (Architected, Engineered, Optimized)" if verb_score < 20 else None,
            "Apply Google XYZ: 'Accomplished [X] measured by [Y] by doing [Z]'" if xyz_score < 20 else None
        ] if s is not None]
    }



# ==============================================================================
# BENGALURU STARTUP PROJECTS CATALOG
# Real-world Indian tech startup company architectures with Google XYZ metrics
# ==============================================================================

BENGALURU_STARTUP_PROJECTS = [
    {
        'id': 'razorpay-upi-gateway',
        'company': 'Razorpay / CRED Style (Bengaluru FinTech)',
        'domain': 'FinTech & Payments Infrastructure',
        'title': 'High-Throughput UPI Webhook Ingestion & Idempotent Ledger Gateway',
        'role': 'Backend Systems Engineer',
        'tech_stack': 'Python, FastAPI, Redis Redlock, PostgreSQL, Docker, AWS SQS',
        'bullets': [
            'Architected asynchronous webhook ingestion engine processing ₹25Cr+ simulated daily UPI transaction notifications with 99.99% availability.',
            'Engineered strict idempotency layer using Redis Redlock distributed locking and PostgreSQL serializable transactions, preventing duplicate debit reconciliations.',
            'Reduced p99 webhook acknowledgement latency from 420ms to 28ms by decoupling ledger writes via asynchronous Celery/SQS worker pipelines.',
            'Implemented automated SHA-256 HMAC signature verification and merchant API key rotation defending against replay attacks.'
        ]
    },
    {
        'id': 'swiggy-hyperlocal-dispatch',
        'company': 'Swiggy / Zomato Style (Bengaluru Hyperlocal)',
        'domain': 'Hyperlocal Logistics & Real-Time Telemetry',
        'title': 'Distributed Real-Time Delivery Partner Dispatcher & Geo-spatial Route Optimizer',
        'role': 'Full Stack / Systems Engineer',
        'tech_stack': 'Node.js, TypeScript, Python, Redis GEORADIUS, Apache Kafka, WebSockets',
        'bullets': [
            'Engineered real-time geospatial dispatch engine streaming GPS telemetry for 8,000+ active delivery partners with < 35ms WebSocket latency.',
            'Implemented dynamic batching algorithm utilizing Redis GEORADIUS and Haversine distance heuristics, cutting fleet dead-mileage by 23%.',
            'Integrated Apache Kafka topic partitioning to handle burst order surges during peak Indian dinner hours (7 PM – 10 PM) with zero message loss.',
            'Constructed live operations dashboard in React and Tailwind displaying driver density heatmaps and SLA breach predictions.'
        ]
    },
    {
        'id': 'zerodha-kite-tick-streamer',
        'company': 'Zerodha / Groww Style (Bengaluru WealthTech)',
        'domain': 'High-Frequency Financial Data & Trading Systems',
        'title': 'High-Frequency Stock Market Tick Ingestion & Real-Time Portfolio Ledger',
        'role': 'Systems Software Engineer',
        'tech_stack': 'Go (Golang), Python, TimescaleDB, WebSockets, Redis Pub/Sub, Docker',
        'bullets': [
            'Built high-performance market feed distributor ingesting 75,000+ NSE/BSE stock ticks/sec via binary WebSockets with sub-10ms broadcast latency.',
            'Aggregated raw tick data into 1-minute and 5-minute OHLCV candles utilizing TimescaleDB continuous aggregates and compression policies.',
            'Slashing memory footprint by 58% by implementing Protobuf binary serialization over standard JSON payloads.',
            'Engineered real-time P&L valuation engine computing portfolio risk exposure across 50,000+ simultaneous simulated trader accounts.'
        ]
    },
    {
        'id': 'zepto-darkstore-inventory',
        'company': 'Zepto / Blinkit Style (Bengaluru Quick-Commerce)',
        'domain': '10-Minute Dark Store & Supply Chain Systems',
        'title': '10-Minute Dark Store Micro-Fulfillment & Concurrency Inventory Lock Engine',
        'role': 'Backend / Platform Engineer',
        'tech_stack': 'Python, Django REST Framework, Redis, MySQL, Celery, Docker',
        'bullets': [
            'Engineered dark store warehouse routing algorithm optimizing picker traversal path, reducing item pick times from 180s to 55s per basket.',
            'Implemented optimistic database locking and two-phase stock reservation eliminating phantom inventory out-of-stock cancellations by 98%.',
            'Orchestrated multi-store inventory sync processing 15,000+ SKU updates every 30 seconds across 40 simulated Bangalore micro-fulfillment centers.',
            'Designed automated restocking prediction model utilizing exponential moving averages based on hourly localized consumption velocity.'
        ]
    },
    {
        'id': 'flipkart-flash-sale-queue',
        'company': 'Flipkart / Meesho Style (Bengaluru E-Commerce)',
        'domain': 'E-Commerce Infrastructure & High-Concurrency Sales',
        'title': 'Flash Sale High-Concurrency Checkout Queue & Anti-Bot Protection Service',
        'role': 'Distributed Systems Engineer',
        'tech_stack': 'Java 17, Spring Boot, Apache Kafka, Redis Cluster, PostgreSQL',
        'bullets': [
            'Architected distributed token bucket queue managing 120,000+ simultaneous checkout requests during Big Billion Day flash sale simulations.',
            'Implemented sliding-window rate limiting and device fingerprint validation dropping 94% of malicious bot scalper checkout attempts.',
            'Maintained strictly ordered cart state checkouts using Kafka partition keys with zero inventory desynchronization across database replicas.',
            'Benchmarked sustained throughput of 9,200 requests/sec with p95 response time under 45ms using Gatling load testing suites.'
        ]
    },
    {
        'id': 'sarvam-indic-rag-pipeline',
        'company': 'Sarvam AI / Krutrim Style (Bengaluru GenAI)',
        'domain': 'Generative AI & Indian Language Technologies',
        'title': 'Multilingual Indic Document Semantic Search & RAG Chat Intelligence Engine',
        'role': 'AI / Machine Learning Engineer',
        'tech_stack': 'Python, LangChain, Llama-3, ChromaDB / Qdrant, FastAPI, PyTorch',
        'bullets': [
            'Engineered retrieval-augmented generation (RAG) system ingesting Hindi, Kannada, Tamil, and English tax invoices and GST compliance filings.',
            'Achieved 91% factual accuracy by implementing hybrid search combining dense BGE-M3 vector embeddings with BM25 lexical keyword matching.',
            'Optimized model inference latency by 65% via 4-bit quantization (GGUF/AWQ) on local hardware, maintaining sub-800ms generation response.',
            'Constructed evaluation test harness with automated hallucination scoring and ground truth verification across 1,000+ test queries.'
        ]
    }
]


# ==============================================================================
# EXPERIENCED PROFILES (1-5+ YOE) DEFAULTS
# Production Work Experience at Top Indian Bengaluru Startups & Tech Unicorns
# ==============================================================================

EXPERIENCED_ROLE_DEFAULTS = {
    # Experienced mode starts with the same rule as fresher mode: the tool may
    # suggest a tone, never a job history. Employers, dates, teams and metrics
    # belong to the candidate, so experience starts empty and the editor asks
    # them to add a real role.
    'python-backend': {
        'title': 'Python & Backend Engineer',
        'summary': 'Backend engineer working with Python, Django REST Framework and relational databases. Comfortable owning a service end to end: schema, API, background jobs and the deployment that runs them.',
        'experience': []
    },
    'full-stack': {
        'title': 'Full-Stack Engineer',
        'summary': 'Full-stack engineer building web applications with React, TypeScript and Python or Node backends. Works across the interface, the API and the database behind it.',
        'experience': []
    },
    'java-sde': {
        'title': 'Java & Spring Engineer',
        'summary': 'Java engineer building Spring Boot services with Spring Data JPA and Kafka. Focused on clear domain models, testable business rules and safe deployments.',
        'experience': []
    },
    'data-analyst': {
        'title': 'Data & Analytics Engineer',
        'summary': 'Data professional working with Python, SQL and dashboards. Turns operational data into reports and models the business can act on.',
        'experience': []
    },
    'devops-cloud': {
        'title': 'DevOps & Cloud Engineer',
        'summary': 'Cloud and DevOps engineer working with Terraform, Kubernetes, GitHub Actions and observability tooling. Automates the path from commit to production.',
        'experience': []
    }
}


def basic_project_score(project: dict, target_skills: list = None) -> dict:
    """Rule-based project score in the shape the resume builder shows."""
    result = score_project_ats(project, target_skills)
    parts = result.get('breakdown') or {}

    def points(key):
        value = parts.get(key)
        return value.get('score', 0) if isinstance(value, dict) else 0

    return {
        'score': result.get('score', 0),
        'breakdown': {
            'action_verbs': points('action_verbs'),
            'google_xyz': points('google_xyz'),
            'quantified_metrics': points('metrics'),
            'tech_relevance': points('tech_relevance'),
            'architecture_scale': points('system_depth'),
        },
    }
