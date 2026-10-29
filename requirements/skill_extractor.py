"""
Skill Extraction, Taxonomy Mapping, and Normalization Engine.
Extracts real, industry-standard technical skills from job titles, raw skill strings,
and job descriptions. Eliminates generic placeholders (e.g. 'Technical, Problem Solving')
and formats clean, high-precision skill sets for Indian tech hiring (Naukri, LinkedIn, Jobdexo, etc.).
"""

import re
import html
from typing import List, Set, Optional


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
    'non_technical',
    'non-technical',
    'non technical',
    'senior',
    'junior',
    'lead',
    'fresher',
    'freshers',
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
    'asp.net': 'ASP.NET',
    '.net': '.NET Core',
    'dotnet': '.NET Core',
    '.net core': '.NET Core',
    'ruby on rails': 'Ruby on Rails',
    'rails': 'Ruby on Rails',
    'nestjs': 'NestJS',
    'rest': 'REST APIs',
    'rest api': 'REST APIs',
    'rest apis': 'REST APIs',
    'restful apis': 'REST APIs',
    'graphql': 'GraphQL',
    'grpc': 'gRPC',
    'microservices': 'Microservices',
    'hibernate': 'Hibernate',
    'jpa': 'JPA',

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

# Archetype fallbacks for software roles when explicit mentions in title/desc are sparse
ROLE_ARCHETYPES = [
    # Full Stack
    (
        r'full[\s\-]*stack|fsd|mean\s*stack|mern\s*stack',
        ['React', 'Node.js', 'JavaScript', 'TypeScript', 'REST APIs', 'SQL', 'Git']
    ),
    # Frontend
    (
        r'front[\s\-]*end|ui[\s\/]*ux\s*developer|web\s*developer|react|angular|vue',
        ['React', 'JavaScript', 'TypeScript', 'HTML5', 'CSS3', 'Tailwind CSS', 'Redux', 'Git']
    ),
    # Backend
    (
        r'back[\s\-]*end|server\s*side|api\s*developer',
        ['Java', 'Spring Boot', 'Microservices', 'REST APIs', 'SQL', 'Docker', 'Git']
    ),
    # Python
    (
        r'python|django|fastapi',
        ['Python', 'Django', 'FastAPI', 'PostgreSQL', 'REST APIs', 'Docker', 'Git']
    ),
    # Java
    (
        r'java\b|spring\s*boot|j2ee',
        ['Java', 'Spring Boot', 'Microservices', 'REST APIs', 'MySQL', 'Hibernate', 'Git']
    ),
    # DotNet / C#
    (
        r'\.net|dotnet|c#|csharp|asp\.net',
        ['C#', '.NET Core', 'ASP.NET', 'SQL Server', 'REST APIs', 'Azure', 'Git']
    ),
    # Mobile
    (
        r'mobile|android|ios|flutter|react\s*native|app\s*developer',
        ['Flutter', 'React Native', 'Android', 'iOS', 'Kotlin', 'Swift', 'REST APIs']
    ),
    # QA / Automation / Testing / SDET
    (
        r'qa\b|sdet|test|quality\s*assurance|automation\s*engineer',
        ['Selenium', 'Test Automation', 'Java/Python', 'API Testing (Postman)', 'JIRA', 'CI/CD', 'Git']
    ),
    # DevOps / Cloud / SRE
    (
        r'devops|cloud|sre|site\s*reliability|infrastructure|kubernetes|aws',
        ['AWS', 'Docker', 'Kubernetes', 'CI/CD', 'Terraform', 'Linux', 'Git', 'Python']
    ),
    # Data Analyst / Business Analyst
    (
        r'data\s*analyst|bi\s*developer|business\s*intelligence|analytics\s*engineer',
        ['SQL', 'Python', 'Power BI', 'Advanced Excel', 'Data Analytics', 'Tableau', 'Statistics']
    ),
    # Data Engineer / Big Data
    (
        r'data\s*engineer|big\s*data|etl|spark',
        ['Python', 'SQL', 'Apache Spark', 'Apache Kafka', 'AWS', 'Data Pipelines', 'Snowflake']
    ),
    # AI / Machine Learning / Data Science
    (
        r'ai\b|ml\b|machine\s*learning|deep\s*learning|data\s*scientist|llm',
        ['Python', 'Machine Learning', 'PyTorch', 'TensorFlow', 'NLP', 'SQL', 'Scikit-Learn']
    ),
    # General SDE / Software Engineer / Programmer
    (
        r'sde|software\s*engineer|software\s*dev|developer|programmer|engineer\b',
        ['Data Structures & Algorithms', 'Java/Python', 'OOP', 'SQL', 'REST APIs', 'Git', 'System Design']
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


def extract_technical_skills(
    title: str = "",
    raw_skills: str = "",
    description: str = "",
    category_slug: str = "",
    max_skills: int = 7
) -> str:
    """
    Standard skill extraction engine.
    
    1. Inspects explicit raw_skills tags if present, filtering out non-technical junk.
    2. Scans full job description and title with the technical regex catalog.
    3. If fewer than 3 high-quality technical skills are identified, infers modern,
       role-specific technical skills from the job title and category.
    4. Guarantees clean, deduplicated, comma-separated technical skills.
       NEVER returns 'Technical, Problem Solving' or generic filler.
    """
    extracted_skills: List[str] = []
    seen_canonical_lower: Set[str] = set()

    def _add_skill(skill_name: Optional[str]):
        if not skill_name:
            return
        lower_name = skill_name.lower()
        if lower_name in seen_canonical_lower or lower_name in JUNK_SKILLS:
            return
        # Prevent slight redundancies like 'React' and 'React.js'
        if lower_name.endswith('.js') and lower_name[:-3] in seen_canonical_lower:
            return
        if f"{lower_name}.js" in seen_canonical_lower:
            return
        seen_canonical_lower.add(lower_name)
        extracted_skills.append(skill_name)

    # 1. Parse raw_skills if available (from Naukri tags, Jobdexo jd-skill tags, etc.)
    if raw_skills and isinstance(raw_skills, str):
        # Split on commas, bullets, pipes, or semicolons
        tokens = re.split(r'[,|;\n/]+', raw_skills)
        for t in tokens:
            c = clean_skill_token(t)
            if c:
                _add_skill(c)
            if len(extracted_skills) >= max_skills:
                break

    # 2. Scan title and description text using technical regex catalog
    combined_text = f"{title}\n{description}"
    for pattern, canonical in TECHNICAL_REGEX_CATALOG:
        if re.search(pattern, combined_text, re.IGNORECASE):
            _add_skill(canonical)
        if len(extracted_skills) >= max_skills + 2:
            break

    # 3. If still sparse (< 3 skills) and the role is technical / software, apply smart archetype fallback
    title_lower = (title or '').lower()
    is_technical = (
        category_slug in ['software-engineering', 'software-tech', 'technical', 'data-ai', 'internships'] or
        any(k in title_lower for k in [
            'developer', 'engineer', 'sde', 'programmer', 'software', 'full stack', 'frontend',
            'backend', 'data', 'analyst', 'qa', 'sdet', 'cloud', 'devops', 'architect', 'coder'
        ])
    )

    if len(extracted_skills) < 3 and is_technical:
        for pattern, archetype_skills in ROLE_ARCHETYPES:
            if re.search(pattern, title_lower):
                for s in archetype_skills:
                    _add_skill(s)
                    if len(extracted_skills) >= max_skills:
                        break
                break

    # 4. Final safety guard: if still completely empty, supply software engineering fundamentals
    if not extracted_skills:
        if is_technical:
            extracted_skills = ['Data Structures & Algorithms', 'Java/Python', 'OOP', 'SQL', 'REST APIs', 'Git']
        else:
            extracted_skills = ['Business Operations', 'Advanced Excel', 'Project Coordination', 'Reporting']

    # Return top max_skills
    final_skills = extracted_skills[:max_skills]
    return ", ".join(final_skills)
