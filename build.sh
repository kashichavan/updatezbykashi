#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Auto-create production owner account & Software & Tech category upon deployment/restart
python manage.py shell -c "
from django.contrib.auth.models import User
from requirements.models import Category, JobPosting
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
import os

# 1. Ensure Owner Account
username = os.environ.get('ADMIN_USERNAME', 'kashichavan7777')
email = os.environ.get('ADMIN_EMAIL', 'kashichavan7777@gmail.com')
password = os.environ.get('ADMIN_PASSWORD', 'kashichavan7777')

u, created = User.objects.get_or_create(username=username, defaults={'email': email, 'is_staff': True, 'is_superuser': True})
u.email = email
u.set_password(password)
u.is_staff = True
u.is_superuser = True
u.save()

# 2. Ensure Sole Active Category: Software & Tech
sw_cat, _ = Category.objects.get_or_create(
    slug='software-tech',
    defaults={
        'name': 'Software & Tech',
        'icon': 'code',
        'description': 'All software engineering, web development, internships, and technology opportunities.'
    }
)

# Re-assign existing jobs to Software & Tech & remove obsolete categories
JobPosting.objects.all().update(category=sw_cat)
Category.objects.exclude(id=sw_cat.id).delete()

# 3. Ensure High-Value Guide Articles Exist
from requirements.models import GuideArticle

guides_seeds = [
    {
        'title': 'Top 30 Python Interview Questions & In-Depth Code Solutions (2026 Edition)',
        'slug': 'top-30-python-interview-questions-answers',
        'topic': 'INTERVIEW',
        'read_time': '12 min read',
        'summary': 'Master the most frequently asked Python technical interview questions for junior to mid-level software engineering roles with executable code examples, memory models, and interviewer expectations.',
        'tags': 'Python, Interview Prep, Freshers, OOP, GIL, Memory Management',
        'content': '''<h2>Introduction: Cracking the Modern Python Technical Interview</h2><p>Python remains one of the world\\'s most popular programming languages for backend engineering, data science, automation, and cloud infrastructure. When interviewing for fresher and junior developer roles, hiring managers look beyond basic syntax; they evaluate your grasp of Python\\'s memory management, data model, performance characteristics, and object-oriented architecture.</p><hr/><h3>1. How Does Python Handle Memory Management & Garbage Collection?</h3><p>Python uses Reference Counting and a Generational Cyclic Garbage Collector.</p><pre><code class="language-python">import sys\ndata = ["Django", "Python", "SQLite"]\nprint(f"Reference Count: {sys.getrefcount(data) - 1}")</code></pre><hr/><h3>2. What is the Global Interpreter Lock (GIL)?</h3><p>The GIL is a mutex in CPython that prevents multiple native threads from executing Python bytecode simultaneously, avoiding race conditions in reference counting.</p><hr/><h3>3. Mutable vs Immutable Default Argument Gotcha</h3><pre><code class="language-python">def append_student_safe(name, student_list=None):\n    if student_list is None:\n        student_list = []\n    student_list.append(name)\n    return student_list</code></pre>'''
    },
    {
        'title': 'Complete Python & Django Full-Stack Developer Roadmap for Freshers (2026)',
        'slug': 'python-django-full-stack-developer-roadmap',
        'topic': 'CAREER',
        'read_time': '10 min read',
        'summary': 'A comprehensive step-by-step career guide for college students and fresh graduates to transition from zero coding knowledge to a hired Full-Stack Python Django Software Engineer.',
        'tags': 'Django, Python, Career Roadmap, Freshers, Web Development',
        'content': '''<h2>Why Choose Python & Django in 2026?</h2><p>Django is the industry standard high-level Python web framework powering Instagram, Spotify, and Pinterest with built-in ORM, Auth, Admin, and CSRF protection.</p><hr/><h3>Phase 1: Core Python Fundamentals</h3><p>Master control flow, lists, dicts, tuples, sets, functions, OOP, and exception handling.</p><hr/><h3>Phase 2: Database Design & Relational Modeling</h3><p>Learn SQL, schema normalization (1NF, 2NF, 3NF), and PostgreSQL.</p><hr/><h3>Phase 3: Django Web Architecture & MVT</h3><p>Models, Views, Templates, ModelForms, and Middleware.</p><hr/><h3>Phase 4: Django REST Framework & APIs</h3><p>Serializers, ViewSets, SimpleJWT authentication, and pagination.</p>'''
    },
    {
        'title': 'Mastering Python Object-Oriented Programming (OOP) with Practical Examples',
        'slug': 'mastering-python-oop-concepts-practical-guide',
        'topic': 'PYTHON',
        'read_time': '9 min read',
        'summary': 'Deep dive into OOP in Python: understand classes, inheritance, encapsulation, polymorphism, abstract base classes, and dunder methods with clean production code.',
        'tags': 'Python, OOP, Software Engineering, Best Practices',
        'content': '''<h2>Core Pillars of OOP in Python</h2><hr/><h3>1. Encapsulation</h3><pre><code class="language-python">class BankAccount:\n    def __init__(self, owner: str, initial_balance: float = 0.0):\n        self.owner = owner\n        self._balance = initial_balance\n    @property\n    def balance(self):\n        return self._balance</code></pre><hr/><h3>2. Inheritance & Polymorphism</h3><pre><code class="language-python">class BaseTracer:\n    def trace(self):\n        pass</code></pre>'''
    },
    {
        'title': 'How to Crack Off-Campus IT & Software Engineering Placement Drives (2026)',
        'slug': 'crack-off-campus-software-engineering-placements',
        'topic': 'CAREER',
        'read_time': '11 min read',
        'summary': 'Proven strategies for college students and fresh graduates to secure high-paying tech jobs through off-campus recruitment drives, cold outreach, ATS resume design, and technical preparation.',
        'tags': 'Jobs, Career Advice, Placements, Resume, Off-Campus',
        'content': '''<h2>Strategies for Off-Campus Success</h2><hr/><h3>1. ATS-Optimized Single Page Resume</h3><p>Use clean single-column formatting and highlight Python, Django, PostgreSQL, and Git.</p><hr/><h3>2. Impactful GitHub Portfolios</h3><p>Build 2-3 production-grade projects with clean commit histories and unit test coverage.</p><hr/><h3>3. Strategic Cold Outreach</h3><p>Connect with Engineering Managers and Tech Leads directly on LinkedIn.</p>'''
    },
    {
        'title': 'Django REST Framework (DRF) & API Architecture: Complete Beginner Guide',
        'slug': 'django-rest-framework-drf-api-complete-guide',
        'topic': 'DJANGO',
        'read_time': '10 min read',
        'summary': 'Learn how to architect, serialize, secure, and document scalable RESTful APIs with Django REST Framework, SimpleJWT authentication, and pagination.',
        'tags': 'Django, DRF, REST API, Web Development, Backend',
        'content': '''<h2>REST API Architecture in Django</h2><hr/><h3>1. Serializers</h3><p>Transforming complex querysets to native JSON representations.</p><hr/><h3>2. ModelViewSets</h3><p>Standardized CRUD operations with clean routing.</p><hr/><h3>3. JWT Authentication</h3><p>Stateless user authentication using SimpleJWT.</p>'''
    },
    {
        'title': 'Essential Data Structures in Python: Complexity, Use Cases & Code Patterns',
        'slug': 'essential-data-structures-in-python-guide',
        'topic': 'DSA',
        'read_time': '9 min read',
        'summary': 'Master the core data structures in Python with time complexity breakdowns (Big-O), memory footprints, and practical coding patterns for technical interviews.',
        'tags': 'Python, Data Structures, Algorithms, Big-O, Coding',
        'content': '''<h2>Core Python Data Structures & Complexity</h2><hr/><h3>1. Lists (Dynamic Arrays)</h3><p>Index lookup O(1), Append O(1), Search O(N).</p><hr/><h3>2. Dictionaries (Hash Tables)</h3><p>Key lookup O(1) average case.</p><hr/><h3>3. Sets (Hash Sets)</h3><p>Membership test O(1) with set union and intersection operations.</p>'''
    },
    {
        'title': 'Visual Code Debugging: How AST Tracing & Memory Diagrams Help Master Algorithms',
        'slug': 'visual-code-debugging-ast-tracing-memory-guide',
        'topic': 'DEBUGGER',
        'read_time': '8 min read',
        'summary': 'Discover how interactive visual debuggers, Abstract Syntax Tree (AST) instrumentation, call stack inspection, and heap memory diagrams accelerate programming mastery.',
        'tags': 'Debugger, Algorithms, Python, Computer Science, AST',
        'content': '''<h2>Why Step-by-Step Visual Tracing Matters</h2><p>Step through execution frames, watch memory heaps mutate in real-time, and visualize recursion trees.</p>'''
    }
]

for g in guides_seeds:
    GuideArticle.objects.get_or_create(slug=g['slug'], defaults=g)

print('Production Owner account, Software & Tech category, and Guide articles configured successfully.')
"
