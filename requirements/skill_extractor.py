"""
Skill Extraction, Taxonomy Mapping, and Normalization Engine.
Extracts real, industry-standard technical skills from job titles, raw skill strings,
and job descriptions. Eliminates generic placeholders (e.g. 'Technical, Problem Solving')
and formats clean, high-precision skill sets for Indian tech hiring (Naukri, LinkedIn, Jobdexo, etc.).
"""

import re
import html
import logging
from typing import List, Set, Optional

logger = logging.getLogger(__name__)


# Blacklist of filler / generic non-technical words that should never appear as standalone skills
JUNK_SKILLS: Set[str] = {
    'technical',
    'technicle',
    'problem solving',
    'problem-solving',
    'problem‑solving',
    'problem solving skills',
    'soft skills',
    'communication',
    'communication skills',
    'verbal communication',
    'written communication',
    'interpersonal communication',
    'tools',
    'engineering',
    'engineer',
    'non_technical',
    'non-technical',
    'non technical',
    'senior',
    'junior',
    'lead',
    'fresher',
    'freshers',
    'intern',
    'trainee',
    'experience',
    'responsible',
    'responsibilities',
    'skills',
    'generation',
    'teamwork',
    'team player',
    'analytical thinking',
    'critical thinking',
    'willingness to learn',
    'work ethic',
    'self starter',
    'attention to detail',
    'good knowledge',
    'basic knowledge',
    'strong knowledge',
    'etc',
    # Fluff or generic fragment tags scraped from job boards
    'software',
    'hardware',
    'development',
    'developer',
    'develop',
    'software development',
    'software engineering',
    'application',
    'applications',
    'application development',
    'end',
    'front',
    'front end',
    'front-end',
    'frontend development',
    'back',
    'back end',
    'back-end',
    'backend development',
    'backend',
    'frontend',
    'core',
    'entity',
    'intelligence',
    'artificial',
    'saas',
    'modeling',
    'predictive',
    'routing',
    'serv',
    'cs',
    'bi',
    'dot',
    'id',
    'ping',
    'javas',
    'it',
    'information technology',
    'coding',
    'programming',
    'requirement',
    'requirements',
    'process',
    'management',
    'fullstack development',
    'full stack development',
    'platform',
    'system',
    'systems',
}

# Canonical capitalization map for tech skills
CANONICAL_SKILL_NAMES = {
    # Languages
    'python': 'Python',
    'java': 'Java',
    'javascript': 'JavaScript',
    'js': 'JavaScript',
    'typescript': 'TypeScript',
    'ts': 'TypeScript',
    'c++': 'C++',
    'cpp': 'C++',
    'c#': 'C#',
    'csharp': 'C#',
    'golang': 'Go',
    'go': 'Go',
    'rust': 'Rust',
    'ruby': 'Ruby',
    'php': 'PHP',
    'kotlin': 'Kotlin',
    'swift': 'Swift',
    'dart': 'Dart',
    'scala': 'Scala',
    'r': 'R',
    'sql': 'SQL',
    'shell': 'Shell Scripting',
    'bash': 'Bash',

    # Web & Frontend
    'react': 'React',
    'reactjs': 'React',
    'react.js': 'React',
    'react native': 'React Native',
    'nextjs': 'Next.js',
    'next.js': 'Next.js',
    'angular': 'Angular',
    'angularjs': 'Angular',
    'vue': 'Vue.js',
    'vuejs': 'Vue.js',
    'vue.js': 'Vue.js',
    'svelte': 'Svelte',
    'redux': 'Redux',
    'tailwind': 'Tailwind CSS',
    'tailwindcss': 'Tailwind CSS',
    'bootstrap': 'Bootstrap',
    'html': 'HTML5',
    'html5': 'HTML5',
    'css': 'CSS3',
    'css3': 'CSS3',

    # Backend & Frameworks
    'node': 'Node.js',
    'nodejs': 'Node.js',
    'node.js': 'Node.js',
    'express': 'Express.js',
    'expressjs': 'Express.js',
    'spring': 'Spring Boot',
    'spring boot': 'Spring Boot',
    'springboot': 'Spring Boot',
    'django': 'Django',
    'fastapi': 'FastAPI',
    'flask': 'Flask',
    'asp.net': 'ASP.NET Core',
    'asp.net core': 'ASP.NET Core',
    '.net': '.NET Core',
    'net': '.NET Core',
    'dotnet': '.NET Core',
    'dot net': '.NET Core',
    '.net core': '.NET Core',
    '.net 8': '.NET Core',
    'entity framework': 'Entity Framework Core',
    'entity framework core': 'Entity Framework Core',
    'ef core': 'Entity Framework Core',
    'ruby on rails': 'Ruby on Rails',
    'rails': 'Ruby on Rails',
    'nestjs': 'NestJS',
    'api': 'REST APIs',
    'apis': 'REST APIs',
    'web api': 'REST APIs',
    'web apis': 'REST APIs',
    'rest': 'REST APIs',
    'rest api': 'REST APIs',
    'rest apis': 'REST APIs',
    'restful': 'REST APIs',
    'restful api': 'REST APIs',
    'restful apis': 'REST APIs',
    'graphql': 'GraphQL',
    'grpc': 'gRPC',
    'microservices': 'Microservices',
    'hibernate': 'Hibernate',
    'jpa': 'JPA',
    'j2ee': 'Java EE',
    'java ee': 'Java EE',

    # Databases & Caches
    'postgresql': 'PostgreSQL',
    'postgres': 'PostgreSQL',
    'mysql': 'MySQL',
    'mongodb': 'MongoDB',
    'mongo': 'MongoDB',
    'redis': 'Redis',
    'oracle': 'Oracle DB',
    'sql server': 'SQL Server',
    'mssql': 'SQL Server',
    'cassandra': 'Cassandra',
    'dynamodb': 'DynamoDB',
    'elasticsearch': 'Elasticsearch',
    'sqlite': 'SQLite',
    'firebase': 'Firebase',
    'supabase': 'Supabase',

    # Cloud, DevOps & Infrastructure
    'aws': 'AWS',
    'azure': 'Azure',
    'gcp': 'GCP',
    'google cloud': 'GCP',
    'docker': 'Docker',
    'kubernetes': 'Kubernetes',
    'k8s': 'Kubernetes',
    'terraform': 'Terraform',
    'ansible': 'Ansible',
    'ci': 'CI/CD',
    'cd': 'CI/CD',
    'continuous integration': 'CI/CD',
    'continuous deployment': 'CI/CD',
    'continuous delivery': 'CI/CD',
    'ci/cd': 'CI/CD',
    'cicd': 'CI/CD',
    'jenkins': 'Jenkins',
    'git': 'Git',
    'github': 'GitHub',
    'gitlab': 'GitLab',
    'linux': 'Linux',
    'kafka': 'Apache Kafka',
    'apache kafka': 'Apache Kafka',
    'rabbitmq': 'RabbitMQ',
    'voip': 'VoIP',
    'sip': 'SIP',
    'webrtc': 'WebRTC',
    'freeswitch': 'FreeSWITCH',
    'asterisk': 'Asterisk',
    'cuda': 'CUDA',

    # Data, AI & Analytics
    'machine learning': 'Machine Learning',
    'ml': 'Machine Learning',
    'deep learning': 'Deep Learning',
    'dl': 'Deep Learning',
    'generative ai': 'Generative AI',
    'genai': 'Generative AI',
    'llm': 'LLMs',
    'llms': 'LLMs',
    'nlp': 'NLP',
    'computer vision': 'Computer Vision',
    'cv': 'Computer Vision',
    'pytorch': 'PyTorch',
    'tensorflow': 'TensorFlow',
    'scikit-learn': 'Scikit-Learn',
    'pandas': 'Pandas',
    'numpy': 'NumPy',
    'power bi': 'Power BI',
    'powerbi': 'Power BI',
    'tableau': 'Tableau',
    'excel': 'Advanced Excel',
    'data analytics': 'Data Analytics',
    'data science': 'Data Science',
    'data engineering': 'Data Engineering',
    'spark': 'Apache Spark',
    'apache spark': 'Apache Spark',
    'hadoop': 'Hadoop',
    'snowflake': 'Snowflake',
    'databricks': 'Databricks',

    # QA & Testing
    'selenium': 'Selenium',
    'cypress': 'Cypress',
    'playwright': 'Playwright',
    'junit': 'JUnit',
    'pytest': 'PyTest',
    'test automation': 'Test Automation',
    'manual testing': 'Manual Testing',
    'api testing': 'API Testing',
    'postman': 'Postman',
    'jira': 'JIRA',
    'sdet': 'SDET',
    'load testing': 'Load Testing',
    'performance testing': 'Performance Testing',

    # Mobile
    'android': 'Android',
    'ios': 'iOS',
    'flutter': 'Flutter',

    # Core Engineering
    'dsa': 'Data Structures & Algorithms',
    'data structures': 'Data Structures & Algorithms',
    'algorithms': 'Algorithms',
    'oop': 'OOP',
    'oops': 'OOP',
    'system design': 'System Design',
    'distributed systems': 'Distributed Systems',
    'clean code': 'Clean Code',
    'agile': 'Agile/Scrum',
    'scrum': 'Scrum',
}

# Regex mapping for scanning text with strict boundary protection
TECHNICAL_REGEX_CATALOG = [
    # Languages
    (r'\bpython(?:3)?\b', 'Python'),
    (r'\bjava\b(?!script)', 'Java'),
    (r'\bjavascript\b|\bjs\b', 'JavaScript'),
    (r'\btypescript\b|\bts\b', 'TypeScript'),
    (r'\bc\+\+\b', 'C++'),
    (r'\bc#\b|\bcsharp\b', 'C#'),
    (r'\bgolang\b|\bgo\s+language\b', 'Go'),
    (r'\brust\b', 'Rust'),
    (r'\bruby\b(?!(\s+on\s+rails))', 'Ruby'),
    (r'\bphp\b', 'PHP'),
    (r'\bkotlin\b', 'Kotlin'),
    (r'\bswift\b', 'Swift'),
    (r'\bdart\b', 'Dart'),
    (r'\bscala\b', 'Scala'),
    (r'\bsql\b', 'SQL'),

    # Frontend
    (r'\breact(?:\.js|js)?\b', 'React'),
    (r'\bnext(?:\.js|js)?\b', 'Next.js'),
    (r'\bangular(?:\.js|js)?\b', 'Angular'),
    (r'\bvue(?:\.js|js)?\b', 'Vue.js'),
    (r'\bredux\b', 'Redux'),
    (r'\btailwind(?:\s*css)?\b', 'Tailwind CSS'),
    (r'\bhtml(?:5)?\b', 'HTML5'),
    (r'\bcss(?:3)?\b', 'CSS3'),
    (r'\bbootstrap\b', 'Bootstrap'),

    # Backend
    (r'\bnode(?:\.js|js)?\b', 'Node.js'),
    (r'\bexpress(?:\.js|js)?\b', 'Express.js'),
    (r'\bspring\s*boot\b|\bspringboot\b', 'Spring Boot'),
    (r'\bdjango\b', 'Django'),
    (r'\bfastapi\b', 'FastAPI'),
    (r'\bflask\b', 'Flask'),
    (r'\basp\.net\b|\b\.net\s*core\b|\bdotnet\b|\b\.net\b', '.NET Core'),
    (r'\bruby\s*on\s*rails\b|\brails\b', 'Ruby on Rails'),
    (r'\bnest(?:\.js|js)?\b', 'NestJS'),
    (r'\brest(?:\s*apis?|\s*ful)?\b', 'REST APIs'),
    (r'\bmicroservices?\b', 'Microservices'),
    (r'\bgraphql\b', 'GraphQL'),
    (r'\bgrpc\b', 'gRPC'),
    (r'\bhibernate\b', 'Hibernate'),

    # Databases
    (r'\bpostgres(?:ql)?\b', 'PostgreSQL'),
    (r'\bmysql\b', 'MySQL'),
    (r'\bmongo(?:db)?\b', 'MongoDB'),
    (r'\bredis\b', 'Redis'),
    (r'\boracle(?:\s*db)?\b', 'Oracle DB'),
    (r'\bsql\s*server\b|\bmssql\b', 'SQL Server'),
    (r'\bdynamodb\b', 'DynamoDB'),
    (r'\belasticsearch\b', 'Elasticsearch'),

    # Cloud & DevOps
    (r'\baws\b|\bamazon\s+web\s+services\b', 'AWS'),
    (r'\bazure\b', 'Azure'),
    (r'\bgcp\b|\bgoogle\s+cloud\b', 'GCP'),
    (r'\bdocker\b', 'Docker'),
    (r'\bkubernetes\b|\bk8s\b', 'Kubernetes'),
    (r'\bci\s*/\s*cd\b|\bcicd\b', 'CI/CD'),
    (r'\bterraform\b', 'Terraform'),
    (r'\bgit\b|\bgithub\b|\bgitlab\b', 'Git'),
    (r'\blinux\b', 'Linux'),
    (r'\bkafka\b|\bapache\s*kafka\b', 'Apache Kafka'),
    (r'\brabbitmq\b', 'RabbitMQ'),

    # AI, Data & Analytics
    (r'\bmachine\s*learning\b|\bml\b', 'Machine Learning'),
    (r'\bdeep\s*learning\b', 'Deep Learning'),
    (r'\bgenerative\s*ai\b|\bgenai\b|\bllms?\b', 'Generative AI / LLMs'),
    (r'\bpytorch\b', 'PyTorch'),
    (r'\btensorflow\b', 'TensorFlow'),
    (r'\bpower\s*bi\b|\bpowerbi\b', 'Power BI'),
    (r'\btableau\b', 'Tableau'),
    (r'\b(?:advanced\s+)?excel\b', 'Advanced Excel'),
    (r'\bdata\s*analytics\b', 'Data Analytics'),
    (r'\bspark\b|\bapache\s*spark\b', 'Apache Spark'),
    (r'\bsnowflake\b', 'Snowflake'),
    (r'\bdatabricks\b', 'Databricks'),

    # QA & Testing
    (r'\bselenium\b', 'Selenium'),
    (r'\bcypress\b', 'Cypress'),
    (r'\bplaywright\b', 'Playwright'),
    (r'\btest\s*automation\b|\bautomation\s*testing\b', 'Test Automation'),
    (r'\bmanual\s*testing\b', 'Manual Testing'),
    (r'\bapi\s*testing\b|\bpostman\b', 'API Testing (Postman)'),
    (r'\bsdet\b', 'SDET'),
    (r'\bjira\b', 'JIRA'),

    # Mobile
    (r'\bflutter\b', 'Flutter'),
    (r'\breact\s*native\b', 'React Native'),
    (r'\bandroid\b', 'Android'),
    (r'\bios\b', 'iOS'),

    # Core CS
    (r'\bdsa\b|\bdata\s*structures\b', 'Data Structures & Algorithms'),
    (r'\bsystem\s*design\b', 'System Design'),
    (r'\bdistributed\s*systems?\b', 'Distributed Systems'),
    (r'\boop[s]?\b|\bobject\s*oriented\b', 'OOP'),
]

# Archetype and companion skills for tech roles
ROLE_ARCHETYPES = [
    # Senior Python Developer / Lead Python / Python Backend
    (
        r'senior\s+python|python.*senior|lead\s+python|python\s+lead|principal\s+python',
        ['Python', 'Django', 'FastAPI', 'Docker', 'REST APIs', 'SQL', 'PostgreSQL', 'Redis', 'Kubernetes']
    ),
    # Python Developer / General Python
    (
        r'python|django|fastapi',
        ['Python', 'Django', 'FastAPI', 'Docker', 'REST APIs', 'SQL', 'PostgreSQL', 'Redis']
    ),
    # Senior Java / Backend Lead
    (
        r'senior\s+java|java.*senior|lead\s+java|principal\s+java',
        ['Java', 'Spring Boot', 'Microservices', 'Kubernetes', 'Docker', 'REST APIs', 'SQL', 'PostgreSQL', 'Apache Kafka']
    ),
    # Java Developer
    (
        r'java\b|spring\s*boot|j2ee',
        ['Java', 'Spring Boot', 'Microservices', 'REST APIs', 'Docker', 'SQL', 'PostgreSQL', 'Git']
    ),
    # DotNet / C#
    (
        r'dot\s*net|\.net|dotnet|c#|csharp|asp\.net',
        ['C#', '.NET Core', 'ASP.NET Core', 'Entity Framework Core', 'SQL Server', 'REST APIs', 'Azure', 'Docker']
    ),
    # Frontend / React / Angular / Vue
    (
        r'front[\s\-]*end|react|angular|vue|ui[\s\/]*developer',
        ['React', 'TypeScript', 'JavaScript', 'Next.js', 'HTML5', 'CSS3', 'Tailwind CSS', 'Redux', 'Git']
    ),
    # Full Stack
    (
        r'full[\s\-]*stack|fsd|mean\s*stack|mern\s*stack',
        ['React', 'Node.js', 'TypeScript', 'JavaScript', 'REST APIs', 'SQL', 'Docker', 'Git']
    ),
    # VoIP / SIP / FreeSWITCH / WebRTC
    (
        r'voip|sip|webrtc|freeswitch|asterisk',
        ['VoIP', 'SIP', 'WebRTC', 'FreeSWITCH', 'Linux', 'C++', 'Python', 'Docker']
    ),
    # Mobile
    (
        r'mobile|android|ios|flutter|react\s*native|app\s*developer',
        ['Flutter', 'React Native', 'Android', 'iOS', 'Kotlin', 'Swift', 'REST APIs', 'Git']
    ),
    # QA / Automation / Testing / SDET
    (
        r'qa\b|sdet|test|quality\s*assurance|automation\s*engineer',
        ['Selenium', 'Test Automation', 'API Testing (Postman)', 'Java/Python', 'JIRA', 'CI/CD', 'Docker', 'Git']
    ),
    # DevOps / Cloud / SRE
    (
        r'devops|cloud|sre|site\s*reliability|infrastructure|kubernetes|aws',
        ['AWS', 'Docker', 'Kubernetes', 'CI/CD', 'Terraform', 'Linux', 'Python', 'Git']
    ),
    # Data Analyst / Business Intelligence
    (
        r'data\s*analyst|bi\s*developer|business\s*intelligence|analytics\s*engineer',
        ['SQL', 'Python', 'Power BI', 'Tableau', 'Advanced Excel', 'Data Analytics', 'Statistics']
    ),
    # Data Engineer / Big Data
    (
        r'data\s*engineer|big\s*data|etl|spark',
        ['Python', 'SQL', 'Apache Spark', 'Apache Kafka', 'AWS', 'Docker', 'PostgreSQL', 'Snowflake']
    ),
    # AI / Machine Learning / Data Science
    (
        r'ai\b|ml\b|machine\s*learning|deep\s*learning|data\s*scientist|llm|generative\s*ai',
        ['Python', 'Machine Learning', 'PyTorch', 'TensorFlow', 'LLMs', 'SQL', 'FastAPI', 'Docker']
    ),
    # General SDE / Software Engineer / Programmer
    (
        r'sde|software\s*engineer|software\s*dev|developer|programmer|engineer\b',
        ['Data Structures & Algorithms', 'Python/Java', 'System Design', 'SQL', 'REST APIs', 'Docker', 'Git']
    ),
    # Business Analyst / Product
    (
        r'business\s*analyst|product\s*manager|management\s*trainee',
        ['Business Analysis', 'SQL', 'Advanced Excel', 'Agile/Scrum', 'JIRA', 'Stakeholder Management']
    ),
    # Non-technical / Operations / HR
    (
        r'hr\b|recruiter|operations|sales|marketing|customer\s*service',
        ['Operations Management', 'Advanced Excel', 'Written Communication', 'Team Coordination', 'Reporting']
    ),
]


def clean_skill_token(token: str) -> Optional[str]:
    """Cleans, normalizes, and filters a single skill token."""
    if not token or not isinstance(token, str):
        return None

    cleaned = html.unescape(token).strip()
    cleaned = re.sub(r'[\'\"\[\]\{\}]', '', cleaned).strip()
    cleaned = re.sub(r'^(?:skills?|tech\s*stack|technologies|requirements?)\s*[:\-–]\s*', '', cleaned, flags=re.I).strip()
    cleaned = re.sub(r'\s*\((?:basic|basics|core|intermediate|advanced|hands-on|proficient)\)', '', cleaned, flags=re.I).strip()
    cleaned = re.sub(r'\s+(?:basics?|fundamentals?)$', '', cleaned, flags=re.I).strip()
    if not cleaned.lower().startswith('.net'):
        cleaned = re.sub(r'^[•\-\*·\d\.\)]+\s*', '', cleaned).strip()

    if not cleaned or len(cleaned) < 2 or len(cleaned) > 40:
        return None

    lower = cleaned.lower()
    if lower in JUNK_SKILLS:
        return None

    # Check direct canonical mapping
    if lower in CANONICAL_SKILL_NAMES:
        return CANONICAL_SKILL_NAMES[lower]

    # Preserve well-formed multi-word skills if capital (e.g. 'REST APIs', 'Spring Boot')
    if cleaned.isupper() and len(cleaned) <= 6:
        return cleaned

    # Capitalize title words cleanly
    return cleaned.title()


def generate_skills_with_ai(
    title: str,
    raw_skills: str = "",
    description: str = "",
    category_slug: str = "",
    max_skills: int = 8,
) -> List[str]:
    """
    Leverages Groq AI (qwen/qwen3.8-27b) to generate real, modern, industry-standard technical skills.
    Ensures all tokens are passed through clean_skill_token and deduplicated.
    """
    try:
        from requirements.ai_engine import call_groq_chat, get_groq_api_key
        if not get_groq_api_key():
            return []

        prompt = f"""You are an elite Tech Recruiter and Principal Software Architect.
Given this job posting, generate exactly 6 to {max_skills} industry-standard, high-demand modern technical skills that a top company hires for this specific role.

Job Title: {title}
Category: {category_slug or 'Software Engineering'}
Existing Tags / Text: {raw_skills}
Description Snippet: {description[:400] if description else 'N/A'}

STRICT RULES:
1. Return ONLY pure technical skills: programming languages, frameworks, databases, cloud, DevOps, and core software engineering tools.
2. For Python roles (e.g. Senior Python Developer, Python Developer): always include Python, Django, FastAPI, Docker, REST APIs, SQL, PostgreSQL, Redis.
3. For Java roles: Java, Spring Boot, Microservices, REST APIs, Docker, SQL, PostgreSQL, Kafka.
4. For Frontend roles: React, TypeScript, JavaScript, Next.js, Tailwind CSS, Redux, Git.
5. For Full Stack roles: React, Node.js, TypeScript, REST APIs, SQL, Docker, Git.
6. For DevOps roles: AWS, Docker, Kubernetes, CI/CD, Terraform, Linux, Git.
7. Return ONLY a single comma-separated list of skill names on ONE line.
8. NO bullets, no markdown, no numbering, no preamble, and absolutely NO soft skills (no 'problem solving', 'communication', 'teamwork').
"""
        response_text = call_groq_chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=120,
            timeout=6
        )

        tokens = re.split(r'[,|;\n/]+', response_text)
        cleaned_skills = []
        seen = set()
        for t in tokens:
            c = clean_skill_token(t)
            if c and c.lower() not in seen:
                seen.add(c.lower())
                cleaned_skills.append(c)
            if len(cleaned_skills) >= max_skills:
                break
        return cleaned_skills
    except Exception as e:
        logger.warning(f"AI skill generation error: {e}")
        return []


def extract_technical_skills(
    title: str = "",
    raw_skills: str = "",
    description: str = "",
    category_slug: str = "",
    max_skills: int = 8,
    use_ai: bool = False,
) -> str:
    """
    Standard skill extraction and enrichment engine.
    
    1. If use_ai=True, queries Groq AI to infer the modern role tech stack.
    2. Inspects explicit raw_skills tags if present, filtering out non-technical junk.
    3. Scans full job description and title with the technical regex catalog.
    4. Enriches skills with role companions (e.g. for Senior Python Developer -> Python, Django, FastAPI, Docker, REST APIs, SQL, PostgreSQL, Redis).
    5. Guarantees clean, deduplicated, comma-separated technical skills.
       NEVER returns 'Technical, Problem Solving' or generic filler.
    """
    extracted_skills: List[str] = []
    seen_canonical_lower: Set[str] = set()

    def _add_skill(skill_name: Optional[str]):
        if not skill_name:
            return
        lower_name = skill_name.lower().strip()
        if lower_name in seen_canonical_lower or lower_name in JUNK_SKILLS:
            return
        # Prevent slight redundancies like 'React' and 'React.js'
        if lower_name.endswith('.js') and lower_name[:-3] in seen_canonical_lower:
            return
        if f"{lower_name}.js" in seen_canonical_lower:
            return
        # Prevent root collisions like 'Python' vs 'Python (Basic)'
        base_clean = re.sub(r'[\(\)\s]+', '', lower_name)
        for existing in list(seen_canonical_lower):
            existing_clean = re.sub(r'[\(\)\s]+', '', existing)
            if base_clean == existing_clean:
                return
        seen_canonical_lower.add(lower_name)
        extracted_skills.append(skill_name)

    # 1. AI-driven extraction if requested
    if use_ai:
        ai_skills = generate_skills_with_ai(
            title=title,
            raw_skills=raw_skills,
            description=description,
            category_slug=category_slug,
            max_skills=max_skills
        )
        if len(ai_skills) >= 4:
            for s in ai_skills:
                _add_skill(s)
            return ", ".join(extracted_skills[:max_skills])

    # 2. Parse raw_skills if available (from Naukri tags, Jobdexo jd-skill tags, etc.)
    if raw_skills and isinstance(raw_skills, str):
        # Split on commas, bullets, pipes, or semicolons
        tokens = re.split(r'[,|;\n/]+', raw_skills)
        for t in tokens:
            c = clean_skill_token(t)
            if c:
                _add_skill(c)
            if len(extracted_skills) >= max_skills:
                break

    # 3. Scan title and description text using technical regex catalog
    combined_text = f"{title}\n{description}"
    for pattern, canonical in TECHNICAL_REGEX_CATALOG:
        if re.search(pattern, combined_text, re.IGNORECASE):
            _add_skill(canonical)
        if len(extracted_skills) >= max_skills + 2:
            break

    # 4. Companion enrichment for tech roles (e.g. Python Developer gets Django, FastAPI, Docker, REST APIs, SQL)
    title_lower = (title or '').lower()
    is_technical = (
        category_slug in ['software-engineering', 'software-tech', 'technical', 'data-ai', 'internships'] or
        any(k in title_lower for k in [
            'developer', 'engineer', 'sde', 'programmer', 'software', 'full stack', 'frontend',
            'backend', 'data', 'analyst', 'qa', 'sdet', 'cloud', 'devops', 'architect', 'coder', 'python', 'java'
        ])
    )

    if is_technical:
        for pattern, archetype_skills in ROLE_ARCHETYPES:
            if re.search(pattern, title_lower):
                for s in archetype_skills:
                    _add_skill(s)
                    if len(extracted_skills) >= max_skills:
                        break
                break

    # 5. Final safety guard: if still completely empty or sparse (< 3 skills)
    if len(extracted_skills) < 3:
        if is_technical:
            for s in ['Data Structures & Algorithms', 'Python/Java', 'OOP', 'SQL', 'REST APIs', 'Git', 'Docker']:
                _add_skill(s)
                if len(extracted_skills) >= max_skills:
                    break
        else:
            for s in ['Operations Management', 'Advanced Excel', 'Project Coordination', 'Reporting']:
                _add_skill(s)

    # Return top max_skills
    final_skills = extracted_skills[:max_skills]
    return ", ".join(final_skills)
