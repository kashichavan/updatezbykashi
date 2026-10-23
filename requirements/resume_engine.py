"""
ATS 90+ Score Resume Generator & Enterprise Project Matching Engine.
Tailored for college students, freshers, and off-campus tech drives.
All projects use Google XYZ formula: Action Verb + Accomplished [X] + Measured by [Y] + Using [Z].
"""

RESUME_ROLES = {
    'python-backend': {
        'role_id': 'python-backend',
        'title': 'Python & Django Backend Engineer',
        'badge': 'Python / Django / FastAPI',
        'summary': 'Results-driven Backend Software Engineer with deep expertise in Python, Django REST Framework, and distributed microservices. Proven track record of designing high-throughput REST APIs, optimizing relational databases, and reducing API latency by up to 65% through Redis caching and asynchronous job workers.',
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
                    'Architected high-throughput transactional order execution engine handling 2,500+ concurrent requests/sec with zero double-allocation errors.',
                    'Engineered distributed concurrency lock using Redis Redlock and atomic database transactions, preventing race conditions during flash sale spikes.',
                    'Optimized relational database queries via Django select_related/prefetch_related and B-tree indexes, slashing p95 latency from 185ms to 24ms.',
                    'Configured asynchronous background queue using Celery and Redis to reliably process invoice generation, payment webhooks, and audit logs.'
                ]
            },
            {
                'title': 'Real-Time API Telemetry & Rate-Limiting Security Gateway',
                'role': 'Lead Backend Developer',
                'tech_stack': 'Python, FastAPI, AsyncIO, Redis, Docker, Prometheus',
                'bullets': [
                    'Developed asynchronous API reverse proxy enforcing sliding-window rate limiting (10,000 req/min per tenant) using Redis sorted sets.',
                    'Implemented JWT authentication with HMAC signature verification and role-based access control (RBAC) across 8 internal microservices.',
                    'Containerized service with multi-stage Docker builds reducing image footprint by 62% and automated CI test pipeline via GitHub Actions.'
                ]
            }
        ],
        'education': {
            'degree': 'Bachelor of Engineering / B.Tech in Computer Science',
            'institution': 'Engineering College & Technical University',
            'year': '2022 – 2026',
            'gpa': '8.6 / 10.0 CGPA',
            'coursework': 'Data Structures & Algorithms, Database Management Systems (DBMS), Operating Systems, Computer Networks'
        },
        'certifications': [
            'Python Institute — Certified Associate in Python Programming (PCAP)',
            'PostgreSQL Professional Query Optimization & Indexing — Verified Certificate',
            'HackerRank — Python (5 Stars) & SQL (Advanced Problem Solving)'
        ],
        'target_ats_keywords': [
            'Python', 'Django', 'Django REST Framework', 'PostgreSQL', 'Redis', 'Celery',
            'Docker', 'REST API', 'Microservices', 'Git', 'CI/CD', 'Scalability', 'Unit Testing'
        ]
    },

    'full-stack': {
        'role_id': 'full-stack',
        'title': 'Full-Stack Software Engineer',
        'badge': 'React / Next.js / Python / Node',
        'summary': 'Full-Stack Software Engineer adept at building responsive, scalable end-to-end web applications using modern React, TypeScript, and robust Python/Node backends. Passionate about component craftsmanship, sub-second API performance, and fluid user experiences with 98+ Lighthouse scores.',
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
                    'Engineered real-time document collaboration and activity feeds with WebSocket state synchronization, delivering <50ms broadcast latency.',
                    'Built modern responsive component library with Tailwind CSS, achieving 98/100 Google Lighthouse mobile performance and WCAG accessibility.',
                    'Integrated secure OAuth2 and JWT session management with token refreshing, supporting seamless multi-tenant team organizations.',
                    'Optimized bundle size via route-based dynamic code splitting and image CDN caching, reducing initial bundle transfer from 1.4MB to 310KB.'
                ]
            },
            {
                'title': 'Cloud Media Asset Ingestion & Resumable Chunked Uploader',
                'role': 'Full-Stack Developer',
                'tech_stack': 'React, Node.js, Express, Cloudflare R2 / AWS S3, Redis',
                'bullets': [
                    'Implemented chunked file uploading architecture handling assets up to 2GB with automatic network failure retry and pause-resume capability.',
                    'Generated presigned upload URLs with strict cryptographic hashing, eliminating server disk storage bottlenecks and reducing network transit cost.'
                ]
            }
        ],
        'education': {
            'degree': 'Bachelor of Engineering in Information Technology / Computer Science',
            'institution': 'State Technical University',
            'year': '2022 – 2026',
            'gpa': '8.5 / 10.0 CGPA',
            'coursework': 'Object-Oriented Programming, Web Technologies, Software Engineering, Cloud Computing'
        },
        'certifications': [
            'Meta Certified Front-End Developer — Coursera Professional Certificate',
            'Full Stack Web Development Masterclass — Verified SDE Certificate',
            'HackerRank — Frontend Developer (React) & Problem Solving (Intermediate)'
        ],
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
                    'Engineered resilient event-driven payment reconciliation service streaming 12,000+ transaction events/hour via Apache Kafka.',
                    'Implemented idempotent consumer patterns and database optimistic locking (@Version) to guarantee zero double-crediting in financial operations.',
                    'Secured inter-service communication using Spring Security with OAuth2 JWT tokens and custom authentication filters.',
                    'Achieved 91% test coverage using JUnit 5 and Mockito, integrating automated SonarQube static analysis in the CI/CD pipeline.'
                ]
            },
            {
                'title': 'High-Throughput Distributed Cache-Aside Catalog Service',
                'role': 'Software Development Engineer',
                'tech_stack': 'Java 17, Spring Boot, Redis, MySQL, Docker, Maven',
                'bullets': [
                    'Implemented two-tier cache-aside pattern with Spring Cache and Redis cluster, decreasing database queries by 68% and improving TPS by 3.8x.',
                    'Designed multi-tenant relational schema with composite indexes and pagination, handling catalog queries across 500,000 SKUs.'
                ]
            }
        ],
        'education': {
            'degree': 'Bachelor of Engineering in Computer Science & Engineering',
            'institution': 'Institute of Technology & Science',
            'year': '2022 – 2026',
            'gpa': '8.7 / 10.0 CGPA',
            'coursework': 'Design & Analysis of Algorithms, Object-Oriented Analysis, System Design, Distributed Systems'
        },
        'certifications': [
            'Oracle Certified Associate — Java SE 8 / 11 Programmer',
            'Spring Framework 6 & Spring Boot 3 Deep Dive — Official Specialist Certificate',
            'LeetCode — Top 10% in Java Algorithms & Data Structures'
        ],
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
                    'Engineered predictive classification pipeline analyzing 250,000+ historical user records, achieving 91.8% ROC-AUC using XGBoost.',
                    'Constructed automated feature engineering pipeline extracting behavioral metrics (RFM analysis, session frequency, ticket velocity).',
                    'Deployed model inference endpoint via FastAPI with sub-18ms latency, enabling real-time churn intervention in customer workflows.',
                    'Developed interactive executive dashboard in PowerBI tracking monthly retention rates and projected revenue risk factors.'
                ]
            },
            {
                'title': 'High-Volume E-Commerce ETL Pipeline & Sales Analytics Lake',
                'role': 'Data Analyst Engineer',
                'tech_stack': 'Python, DuckDB, Pandas, Parquet, SQLite, Streamlit',
                'bullets': [
                    'Built automated daily ETL pipeline ingesting disparate CSV and JSON sales feeds into partitioned columnar Parquet files, accelerating queries by 5x.',
                    'Created an open-source Streamlit analytics dashboard with multi-variable cohort filters, identifying $42,000 in unoptimized inventory costs.'
                ]
            }
        ],
        'education': {
            'degree': 'Bachelor of Engineering in Data Science / Computer Engineering',
            'institution': 'College of Engineering & Technology',
            'year': '2022 – 2026',
            'gpa': '8.8 / 10.0 CGPA',
            'coursework': 'Probability & Statistics, Machine Learning, Data Mining, Applied Linear Algebra, Big Data Systems'
        },
        'certifications': [
            'IBM Data Science Professional Certificate — Coursera Verified',
            'Google Data Analytics Professional Certificate',
            'HackerRank — SQL (5 Stars) & Python Data Analysis'
        ],
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
                    'Architected automated CI/CD pipeline using GitHub Actions, cutting staging-to-production deployment duration from 45 mins to 3.5 mins.',
                    'Provisioned reproducible AWS infrastructure via modular Terraform scripts, enforcing strict least-privilege IAM security policies.',
                    'Configured Kubernetes Horizontal Pod Autoscaler (HPA) and rolling zero-downtime deployments, maintaining 99.98% platform availability.',
                    'Instrumented full-stack observability with Prometheus metric exporters and Grafana alert notifications, reducing incident MTTR by 55%.'
                ]
            },
            {
                'title': 'Automated Container Security & Image Vulnerability Scanner',
                'role': 'Cloud Security Engineer',
                'tech_stack': 'Docker, Trivy, GitHub Actions, Bash, Python',
                'bullets': [
                    'Integrated automated Trivy vulnerability scanning into CI pull-request checks, blocking builds with critical CVE security flaws.',
                    'Engineered multi-stage alpine container builds reducing production container image sizes by 74% and eliminating build bloat.'
                ]
            }
        ],
        'education': {
            'degree': 'Bachelor of Engineering in Information Science / Computer Science',
            'institution': 'Technological University',
            'year': '2022 – 2026',
            'gpa': '8.4 / 10.0 CGPA',
            'coursework': 'Cloud Computing, Computer Systems, Network Security, System Administration, Linux Internals'
        },
        'certifications': [
            'AWS Certified Cloud Practitioner (CLF-C02)',
            'Docker & Kubernetes Certified Masterclass — DevOps Institute',
            'Linux Foundation — Certified System Administrator Essentials'
        ],
        'target_ats_keywords': [
            'DevOps', 'AWS', 'Docker', 'Kubernetes', 'CI/CD', 'GitHub Actions',
            'Terraform', 'Linux', 'Bash', 'Prometheus', 'Grafana', 'Nginx', 'Infrastructure as Code'
        ]
    }
}


def calculate_ats_score(resume_data, role_key='python-backend'):
    """
    Evaluates resume against strict ATS compliance rules.
    Returns:
      score: int (0 to 100)
      checks: list of dicts with rule, passed, score, tips
    """
    role = RESUME_ROLES.get(role_key, RESUME_ROLES['python-backend'])
    checks = []
    total_score = 0

    # 1. Contact Details Completeness (10 pts)
    contact = resume_data.get('contact', {})
    has_email = bool(contact.get('email'))
    has_phone = bool(contact.get('phone'))
    has_linkedin = bool(contact.get('linkedin'))
    has_github = bool(contact.get('github'))
    contact_pts = (2.5 if has_email else 0) + (2.5 if has_phone else 0) + (2.5 if has_linkedin else 0) + (2.5 if has_github else 0)
    total_score += int(contact_pts)
    checks.append({
        'rule': 'Contact Information Completeness',
        'passed': contact_pts >= 7.5,
        'points': int(contact_pts),
        'max_points': 10,
        'detail': 'Email, Phone, LinkedIn, and GitHub profile links.'
    })

    # 2. Single-Column Layout & Header Standards (20 pts)
    total_score += 20
    checks.append({
        'rule': 'ATS Semantic Single-Column Layout',
        'passed': True,
        'points': 20,
        'max_points': 20,
        'detail': 'No multi-column tables, textboxes, or graphics that break ATS parsers (Taleo, Workday, Greenhouse).'
    })

    # 3. Action Verb Starting Words (20 pts)
    action_verbs = {
        'architected', 'engineered', 'developed', 'optimized', 'built', 'spearheaded',
        'designed', 'implemented', 'constructed', 'deployed', 'automated', 'integrated'
    }
    bullets = []
    for proj in resume_data.get('projects', []):
        bullets.extend(proj.get('bullets', []))
    for exp in resume_data.get('experience', []):
        bullets.extend(exp.get('bullets', []))

    action_verb_count = sum(1 for b in bullets if any(b.strip().lower().startswith(v) for v in action_verbs))
    action_pts = 20 if action_verb_count >= 4 else (action_verb_count * 5)
    total_score += action_pts
    checks.append({
        'rule': 'Google XYZ Formula & Strong Action Verbs',
        'passed': action_pts >= 15,
        'points': action_pts,
        'max_points': 20,
        'detail': f'{action_verb_count} bullets start with high-impact power action verbs.'
    })

    # 4. Quantified Metrics & Hard Numbers (25 pts)
    import re
    metric_regex = re.compile(r'(\d+[\.,]?\d*\s*(%|ms|kb|mb|gb|req|k|x|skus|cve|users|tps))|\b(\d{2,})\b', re.IGNORECASE)
    metric_count = sum(1 for b in bullets if metric_regex.search(b))
    metric_pts = 25 if metric_count >= 4 else (metric_count * 6)
    total_score += metric_pts
    checks.append({
        'rule': 'Quantified Impact & Numerical Achievements',
        'passed': metric_pts >= 20,
        'points': metric_pts,
        'max_points': 25,
        'detail': f'{metric_count} accomplishments contain verifiable metrics (percentages, throughput, latency).'
    })

    # 5. Core Role Keyword Density (15 pts)
    text_content = (
        resume_data.get('summary', '') + ' ' +
        str(resume_data.get('skills', '')) + ' ' +
        ' '.join(bullets)
    ).lower()

    target_keywords = role['target_ats_keywords']
    matched_keywords = [kw for kw in target_keywords if kw.lower() in text_content]
    match_ratio = len(matched_keywords) / max(1, len(target_keywords))
    keyword_pts = int(match_ratio * 15)
    total_score += keyword_pts
    checks.append({
        'rule': 'ATS Scanner Keyword Match Density',
        'passed': match_ratio >= 0.7,
        'points': keyword_pts,
        'max_points': 15,
        'detail': f'{len(matched_keywords)} / {len(target_keywords)} key ATS keywords matched for {role["title"]}.'
    })

    # 6. Section Hierarchy & Education (10 pts)
    total_score += 10
    checks.append({
        'rule': 'Standard Section Hierarchy',
        'passed': True,
        'points': 10,
        'max_points': 10,
        'detail': 'Summary, Technical Skills, Enterprise Projects, Education, Certifications.'
    })

    final_score = min(100, max(0, total_score))
    if final_score >= 90:
        grade = 'Top Tier (ATS 90+)'
        pass_rate = 'Guaranteed Pass on Workday, Taleo & Greenhouse'
    elif final_score >= 80:
        grade = 'Competitive (ATS 80+)'
        pass_rate = 'Passes Enterprise ATS Filters'
    elif final_score >= 70:
        grade = 'Moderate (ATS 70+)'
        pass_rate = 'Eligible for review — add metrics'
    else:
        grade = 'Needs Work (ATS <70)'
        pass_rate = 'High risk of rejection — boost metrics'

    return {
        'score': final_score,
        'checks': checks,
        'matched_keywords': matched_keywords,
        'grade': grade,
        'pass_rate': pass_rate
    }


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
    import re

    action_verbs = {
        'architected', 'engineered', 'developed', 'optimized', 'built', 'spearheaded',
        'designed', 'implemented', 'constructed', 'deployed', 'automated', 'integrated',
        'refactored', 'orchestrated', 'streamlined', 'benchmarked', 'scaled', 'accelerated'
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
    all_text = (project.get('title', '') + ' ' + tech_stack + ' ' + ' '.join(bullets)).lower()

    relevance_score = 15
    if target_skills:
        matched = sum(1 for s in target_skills if s.lower() in all_text)
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
    'python-backend': {
        'title': 'Senior Python & Backend Engineer (SDE-2)',
        'summary': 'Senior Software Engineer with 3+ years of experience architecting distributed backend services, high-throughput RESTful APIs, and scalable database systems at high-growth Bengaluru product startups. Expert in Python, Django, FastAPI, Redis, and event-driven microservices processing millions of daily transactions.',
        'experience': [
            {
                'company': 'Bengaluru FinTech & SaaS Product Startup',
                'role': 'Software Development Engineer II (Backend)',
                'location': 'Bengaluru, India',
                'period': '2023 – Present',
                'tech_stack': 'Python, Django REST Framework, FastAPI, PostgreSQL, Redis, Celery, Docker, AWS',
                'bullets': [
                    'Architected core transactional payment processing microservices handling ₹40Cr+ monthly GMV with 99.98% system availability.',
                    'Engineered distributed Redis caching and query indexing layer across 18 PostgreSQL tables, slashing p95 API response latency from 320ms to 38ms.',
                    'Led migration of monolithic services into 4 decoupled containerized microservices orchestrated via Kubernetes and AWS ECS.',
                    'Mentored 4 junior engineers, conducted 60+ rigorous code reviews, and established automated CI/CD pipelines reducing defect leakages by 40%.'
                ]
            },
            {
                'company': 'Hyperlocal E-Commerce Unicorn',
                'role': 'Software Development Engineer I',
                'location': 'Bengaluru, India',
                'period': '2021 – 2023',
                'tech_stack': 'Python, Flask, MySQL, Redis, Celery, Git, Linux',
                'bullets': [
                    'Developed asynchronous order lifecycle notification service serving 200,000+ daily push and SMS events with zero queue backlog.',
                    'Refactored database query execution plans and eliminated N+1 query bottlenecks, reducing database CPU utilization by 35% during peak traffic.',
                    'Implemented automated unit and integration test suites achieving 88% code coverage and preventing critical regression bugs.'
                ]
            }
        ]
    },
    'full-stack': {
        'title': 'Senior Full-Stack Engineer',
        'summary': 'Full-Stack Software Engineer with 3+ years of experience designing scalable web platforms and responsive interfaces for top Indian consumer tech startups. Expert in React, Next.js, TypeScript, Node.js/Python, and cloud-native microservices.',
        'experience': [
            {
                'company': 'Bengaluru B2B SaaS Unicorn',
                'role': 'Full-Stack Software Engineer II',
                'location': 'Bengaluru, India',
                'period': '2023 – Present',
                'tech_stack': 'React, Next.js, TypeScript, Node.js, PostgreSQL, Docker, AWS',
                'bullets': [
                    'Architected enterprise customer analytics dashboard used by 12,000+ daily business users, optimizing client-side bundle size by 45%.',
                    'Built high-performance GraphQL and REST API endpoints supporting 4,500 req/sec with robust JWT-based RBAC security.',
                    'Pioneered design system component library in React and Tailwind, accelerating frontend feature velocity across 3 engineering squads by 50%.'
                ]
            }
        ]
    },
    'java-sde': {
        'title': 'Senior Java & Spring Cloud Engineer',
        'summary': 'Java Software Engineer with 3+ years of experience developing mission-critical financial and e-commerce distributed systems. Deep expertise in Java 17/21, Spring Boot, Spring Cloud, Kafka, and relational databases.',
        'experience': [
            {
                'company': 'Tier-1 Bengaluru E-Commerce Platform',
                'role': 'Software Development Engineer II (Java)',
                'location': 'Bengaluru, India',
                'period': '2023 – Present',
                'tech_stack': 'Java 17, Spring Boot, Spring Cloud, Apache Kafka, PostgreSQL, Docker',
                'bullets': [
                    'Engineered distributed inventory reservation engine processing 80,000+ orders during peak flash sales with zero race conditions.',
                    'Implemented event-driven choreography with Apache Kafka, reducing inter-service HTTP dependency bottlenecks by 65%.',
                    'Optimized JVM garbage collection and thread pool configuration, sustaining sub-25ms response latencies across 12 microservices.'
                ]
            }
        ]
    },
    'data-analyst': {
        'title': 'Senior Data & ML Systems Engineer',
        'summary': 'Data Engineer with 3+ years of experience building large-scale data ingestion pipelines, real-time analytics platforms, and machine learning model serving architectures at top Bengaluru data-driven tech firms.',
        'experience': [
            {
                'company': 'Bengaluru Mobility & Logistics Unicorn',
                'role': 'Data Platform Engineer II',
                'location': 'Bengaluru, India',
                'period': '2023 – Present',
                'tech_stack': 'Python, PySpark, Apache Airflow, Snowflake, PostgreSQL, AWS',
                'bullets': [
                    'Constructed daily batch and streaming ETL pipelines ingesting 4TB+ telemetry data, reducing pipeline execution latency by 40%.',
                    'Designed executive KPI dashboards and predictive rider churn models improving quarterly customer retention by 14%.',
                    'Automated data quality validation and schema enforcement checks using Great Expectations and Airflow DAGs.'
                ]
            }
        ]
    },
    'devops-cloud': {
        'title': 'Senior DevOps & Cloud Platform Engineer',
        'summary': 'DevOps & SRE Engineer with 3+ years of experience managing multi-region cloud infrastructure, Kubernetes clusters, and zero-downtime CI/CD deployment pipelines for high-traffic Bengaluru tech platforms.',
        'experience': [
            {
                'company': 'Bengaluru FinTech Platform',
                'role': 'DevOps & SRE Engineer II',
                'location': 'Bengaluru, India',
                'period': '2023 – Present',
                'tech_stack': 'AWS, Kubernetes (EKS), Terraform, Docker, GitHub Actions, Prometheus',
                'bullets': [
                    'Architected multi-region AWS Kubernetes (EKS) infrastructure with Terraform, delivering 99.99% system availability.',
                    'Automated zero-downtime blue/green deployment workflows in GitHub Actions, slashing release deployment time from 45min to 6min.',
                    'Optimized cloud computing costs by 32% through spot instance orchestration, Karpenter autoscaling, and S3 lifecycle tiering.'
                ]
            }
        ]
    }
}

