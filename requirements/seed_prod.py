import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reqpulse.settings')
django.setup()

from django.contrib.auth.models import User
from requirements.models import Category, JobPosting, GuideArticle

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

JobPosting.objects.all().update(category=sw_cat)
Category.objects.exclude(id=sw_cat.id).delete()

# 3. Comprehensive High-Value Guide Library with Downloadable PDFs from User Drive
PYTHON_DRIVE_FOLDER = "https://drive.google.com/drive/folders/1tULDwty-7eXsHh2jAAKCM2OK7YxYSuyp?usp=drive_link"
JAVA_DRIVE_FOLDER = "https://drive.google.com/drive/folders/1khZVS3OSY3EyVVOrRZi33QGchWI9ntM2?usp=drive_link"

guides_seeds = [
    {
        'title': 'Advanced Python Handbook by Kashinath: Internals, Concurrency & Meta-Programming',
        'slug': 'advanced-python-handbook-by-kashinath',
        'topic': 'PYTHON',
        'read_time': '15 min read',
        'summary': 'A masterclass in advanced Python architecture: deep dive into generator pipelines, custom context managers, metaclasses, descriptors, asyncio event loops, and memory profiling.',
        'tags': 'Python, Advanced Python, Generators, Metaclasses, Concurrency, PDF Notes',
        'pdf_download_url': PYTHON_DRIVE_FOLDER,
        'pdf_file_name': 'ADVANCED PYTHON BY KASHINATH.pdf',
        'content': '''<h2>Introduction to Advanced Python Architecture</h2>
<p>Modern backend systems require a deep understanding of Python beyond basic scripting syntax. This guide, compiled from <strong>Advanced Python by Kashinath</strong>, explores how CPython executes bytecode, optimizes memory allocation, and provides high-performance metaprogramming hooks.</p>

<hr/>

<h3>1. Custom Context Managers with Protocols</h3>
<p>While the <code>with</code> statement is commonly used for file handling, creating robust context managers via <code>__enter__</code> and <code>__exit__</code> allows developers to manage database transactions, lock acquisitions, and profiling scopes cleanly.</p>

<pre><code class="language-python">import time

class PerformanceTimer:
    def __init__(self, label: str):
        self.label = label
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        print(f"[{self.label}] Elapsed Execution Time: {elapsed:.6f}s")
        # Returning True suppresses any exception raised inside with block
        return False

# Usage:
with PerformanceTimer("Batch Query Processor"):
    total = sum(x ** 2 for x in range(500_000))
</code></pre>

<hr/>

<h3>2. Python Metaclasses: Controlling Class Creation</h3>
<p>In Python, classes are themselves objects of type <code>type</code>. A metaclass allows you to intercept class definition, enforce coding standards, register plugins dynamically, or validate class attributes at import time.</p>

<pre><code class="language-python">class InterfaceEnforcer(type):
    def __new__(mcs, name, bases, namespace):
        if name != "BaseRepository" and "save" not in namespace:
            raise TypeError(f"Class '{name}' must implement a 'save()' method.")
        return super().__new__(mcs, name, bases, namespace)

class BaseRepository(metaclass=InterfaceEnforcer):
    pass

class UserRepository(BaseRepository):
    def save(self, user):
        return f"Saved user {user}"
</code></pre>

<hr/>

<h3>3. Generator Pipelines & Memory Efficiency</h3>
<p>When processing multi-gigabyte log streams or high-volume API feeds, list comprehensions cause Out-Of-Memory (OOM) fatal crashes. Generator pipelines stream data lazily in constant <code>O(1)</code> space.</p>

<pre><code class="language-python">def stream_numbers(limit: int):
    for i in range(limit):
        yield i

def filter_evens(numbers):
    for n in numbers:
        if n % 2 == 0:
            yield n

def multiply_ten(numbers):
    for n in numbers:
        yield n * 10

# Chained generator pipeline: zero RAM allocation overhead
pipeline = multiply_ten(filter_evens(stream_numbers(1_000_000)))
print("First 3 items:", [next(pipeline), next(pipeline), next(pipeline)])
</code></pre>

<hr/>

<div class="note-box" style="background:#eff6ff; border-left:4px solid #3b82f6; padding:16px; border-radius:8px; margin:24px 0;">
  <strong>📥 Download the Full PDF Notes:</strong> You can download the complete <em>ADVANCED PYTHON BY KASHINATH.pdf</em> study material directly from the link at the top or bottom of this page.
</div>
'''
    },
    {
        'title': 'Python Practice Programs & Logic Building: 100+ Essential Coding Exercises',
        'slug': 'python-practice-programs-logic-building-guide',
        'topic': 'DSA',
        'read_time': '14 min read',
        'summary': 'Master coding round interviews with 100+ solved logic problems: Palindromes, Fibonacci series, Matrix transformations, Armstrong numbers, and recursive tree traversals.',
        'tags': 'Python, Coding Practice, DSA, Logic Building, Freshers, PDF Programs',
        'pdf_download_url': PYTHON_DRIVE_FOLDER,
        'pdf_file_name': 'BASIC PROGRAMS & Programs-1-3.pdf',
        'content': '''<h2>Logic Building & Problem Solving in Python</h2>
<p>Coding test rounds at IT service companies and product startups evaluate algorithmic reasoning, corner case handling, and space-time efficiency. Below are core coding patterns extracted from our <strong>Basic Programs & Logic Handbook</strong>.</p>

<hr/>

<h3>1. Prime Number Checking with Optimized Square-Root Bound</h3>
<p>Checking divisibility up to $\sqrt{N}$ reduces time complexity from $O(N)$ to $O(\sqrt{N})$.</p>

<pre><code class="language-python">import math

def is_prime(n: int) -> bool:
    if n <= 1:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    
    # Check 6k +/- 1 primes
    for i in range(5, int(math.isqrt(n)) + 1, 6):
        if n % i == 0 or n % (i + 2) == 0:
            return False
    return True

print("Is 97 prime?", is_prime(97)) # True
print("Is 100 prime?", is_prime(100)) # False
</code></pre>

<hr/>

<h3>2. String Anagram Detection (Hash Map vs Sorting)</h3>
<pre><code class="language-python">from collections import Counter

def are_anagrams(s1: str, s2: str) -> bool:
    # Clean whitespace and case
    clean_s1 = s1.replace(" ", "").lower()
    clean_s2 = s2.replace(" ", "").lower()
    return Counter(clean_s1) == Counter(clean_s2)

print("Listen & Silent:", are_anagrams("Listen", "Silent")) # True
</code></pre>

<hr/>

<h3>3. Flattening Nested Arrays Recursively</h3>
<pre><code class="language-python">def flatten(nested_list: list) -> list:
    flat = []
    for item in nested_list:
        if isinstance(item, list):
            flat.extend(flatten(item))
        else:
            flat.append(item)
    return flat

sample = [1, [2, [3, 4], 5], 6, [7, 8]]
print("Flattened:", flatten(sample)) # [1, 2, 3, 4, 5, 6, 7, 8]
</code></pre>
'''
    },
    {
        'title': 'Mastering Pytest: Automated Testing, Fixtures & Parametrization for Python',
        'slug': 'mastering-pytest-testing-fixtures-guide',
        'topic': 'PYTHON',
        'read_time': '11 min read',
        'summary': 'Learn professional unit testing with Pytest: test fixtures, dependency injection, parametrization, mocking external APIs, and test coverage reporting.',
        'tags': 'Pytest, Python Testing, QA, Unit Testing, PDF Notes',
        'pdf_download_url': PYTHON_DRIVE_FOLDER,
        'pdf_file_name': 'Pytest Notes & Guides.pdf',
        'content': '''<h2>Why Pytest is the Industry Standard Testing Framework</h2>
<p>Modern Python engineering teams use <strong>Pytest</strong> for its concise syntax, powerful fixture dependency injection system, and rich plugin ecosystem. Unlike standard <code>unittest</code>, Pytest avoids boilerplate class hierarchies.</p>

<hr/>

<h3>1. Pytest Fixtures with Yield Teardown</h3>
<pre><code class="language-python">import pytest

@pytest.fixture
def sample_database():
    # Setup connection
    db = {"users": [], "connected": True}
    print("\n[Setup] Connected to mock DB")
    yield db
    # Teardown
    db["connected"] = False
    print("[Teardown] Closed mock DB connection")

def test_insert_user(sample_database):
    sample_database["users"].append("Kashinath")
    assert len(sample_database["users"]) == 1
    assert "Kashinath" in sample_database["users"]
</code></pre>

<hr/>

<h3>2. Test Parametrization (`@pytest.mark.parametrize`)</h3>
<pre><code class="language-python">import pytest

def calculate_discount(price: float, is_student: bool) -> float:
    return price * 0.8 if is_student else price

@pytest.mark.parametrize("price, is_student, expected", [
    (100.0, True, 80.0),
    (100.0, False, 100.0),
    (50.0, True, 40.0),
    (0.0, True, 0.0),
])
def test_discounts(price, is_student, expected):
    assert calculate_discount(price, is_student) == expected
</code></pre>
'''
    },
    {
        'title': 'Java Multi-Threading & Concurrency Deep Dive: Thread Lifecycle & Synchronization',
        'slug': 'java-multithreading-concurrency-deep-dive',
        'topic': 'DSA',
        'read_time': '13 min read',
        'summary': 'Master Java concurrency: Thread states, Runnable vs Callable, synchronized blocks, volatile keywords, deadlock prevention, and ExecutorService thread pools.',
        'tags': 'Java, Multi-Threading, Concurrency, JVM, OCJP Notes',
        'pdf_download_url': JAVA_DRIVE_FOLDER,
        'pdf_file_name': '1.1 MultiThreading.pdf',
        'content': '''<h2>Java Multi-Threading & Concurrent Architecture</h2>
<p>In enterprise backend applications (Spring Boot, Kafka consumers, trading systems), concurrency allows maximizing multi-core CPU throughput. This guide explores Java multi-threading principles from our <strong>Core Java & SCJP/OCJP Notes</strong>.</p>

<hr/>

<h3>1. Creating Threads: `Thread` vs `Runnable` vs `Callable`</h3>
<ul>
  <li><strong>Runnable Interface:</strong> Preferred over extending <code>Thread</code> because Java allows single class inheritance but multiple interface implementation.</li>
  <li><strong>Callable&lt;V&gt; Interface:</strong> Used when thread execution needs to return a computed value or throw checked exceptions.</li>
</ul>

<pre><code class="language-java">// Runnable with Java Lambda
Runnable task = () -> {
    System.out.println("Executing thread: " + Thread.currentThread().getName());
};
Thread t1 = new Thread(task, "Worker-1");
t1.start();
</code></pre>

<hr/>

<h3>2. Synchronization & Atomic Memory Guarantees</h3>
<p>When multiple threads mutate shared state without synchronization, race conditions cause memory inconsistency. Use synchronized methods or Java's <code>java.util.concurrent.atomic</code> classes.</p>

<pre><code class="language-java">import java.util.concurrent.atomic.AtomicInteger;

public class ThreadSafeCounter {
    private final AtomicInteger count = new AtomicInteger(0);

    public void increment() {
        count.incrementAndGet(); // Lock-free atomic operation
    }

    public int getCount() {
        return count.get();
    }
}
</code></pre>

<hr/>

<h3>3. ExecutorService Thread Pools</h3>
<p>Spawning raw <code>new Thread()</code> instances on every incoming request is expensive. Use thread pools to reuse worker threads efficiently.</p>

<pre><code class="language-java">import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

ExecutorService executor = Executors.newFixedThreadPool(4);
for (int i = 0; i < 10; i++) {
    final int taskId = i;
    executor.submit(() -> System.out.println("Processing task " + taskId + " on " + Thread.currentThread().getName()));
}
executor.shutdown();
</code></pre>
'''
    },
    {
        'title': 'Java Collections Framework Mastery: ArrayList, HashMap & Queue Implementations',
        'slug': 'java-collections-framework-internal-architecture',
        'topic': 'DSA',
        'read_time': '12 min read',
        'summary': 'Under the hood of the Java Collections Framework: HashMap collision handling with red-black trees, ArrayList dynamic capacity doubling, and ConcurrentHashMap locks.',
        'tags': 'Java, Collections, HashMap, ArrayList, Data Structures, PDF Notes',
        'pdf_download_url': JAVA_DRIVE_FOLDER,
        'pdf_file_name': 'Java Collections Framework.pdf',
        'content': '''<h2>Java Collections Architecture Under the Hood</h2>
<p>The Java Collections Framework (JCF) provides unified data structures for storing and manipulating groups of objects. Understanding the internal implementation of each collection is essential for writing high-performance enterprise applications.</p>

<hr/>

<h3>1. How HashMap Works Internally in Java 8+</h3>
<p>Java HashMap operates on hashing principles with an array of Node buckets:</p>
<ol>
  <li><strong>Hash Calculation:</strong> Computes <code>hash(key)</code> and determines bucket index via <code>(n - 1) & hash</code>.</li>
  <li><strong>Collision Resolution:</strong> Handled using a singly linked list.</li>
  <li><strong>Treeification (Java 8):</strong> When bucket elements exceed <code>TREEIFY_THRESHOLD = 8</code> and total map capacity $\ge 64$, the bucket linked list converts into a <strong>Red-Black Balanced Binary Search Tree</strong>, improving lookup from $O(N)$ to $O(\log N)$.</li>
</ol>

<hr/>

<h3>2. ArrayList vs LinkedList Performance Comparison</h3>
<table style="width:100%; border-collapse:collapse; margin:20px 0; font-size:14px;">
  <thead>
    <tr style="background:#f1f5f9; text-align:left;">
      <th style="padding:10px; border:1px solid #cbd5e1;">Operation</th>
      <th style="padding:10px; border:1px solid #cbd5e1;">ArrayList</th>
      <th style="padding:10px; border:1px solid #cbd5e1;">LinkedList</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding:10px; border:1px solid #cbd5e1;">Index Access (`get(i)`)</td>
      <td style="padding:10px; border:1px solid #cbd5e1; color:#16a34a; font-weight:700;">O(1)</td>
      <td style="padding:10px; border:1px solid #cbd5e1; color:#dc2626; font-weight:700;">O(N)</td>
    </tr>
    <tr>
      <td style="padding:10px; border:1px solid #cbd5e1;">Append (`add()`)</td>
      <td style="padding:10px; border:1px solid #cbd5e1; color:#16a34a; font-weight:700;">O(1) amortized</td>
      <td style="padding:10px; border:1px solid #cbd5e1; color:#16a34a; font-weight:700;">O(1)</td>
    </tr>
    <tr>
      <td style="padding:10px; border:1px solid #cbd5e1;">Insert at Beginning</td>
      <td style="padding:10px; border:1px solid #cbd5e1; color:#dc2626; font-weight:700;">O(N) (shifting)</td>
      <td style="padding:10px; border:1px solid #cbd5e1; color:#16a34a; font-weight:700;">O(1) (pointer adjustment)</td>
    </tr>
  </tbody>
</table>
'''
    },
    {
        'title': 'Core Java & JVM Memory Architecture: Static, Final, Heap & Stack Models',
        'slug': 'core-java-jvm-memory-static-final-guide',
        'topic': 'INTERVIEW',
        'read_time': '10 min read',
        'summary': 'Understand JVM internal runtime data areas: ClassLoader subsystem, Heap memory generations, Stack frames, Method Area, and exact Static vs Final behavior.',
        'tags': 'Java, JVM, Memory Model, Garbage Collection, SCJP Notes',
        'pdf_download_url': JAVA_DRIVE_FOLDER,
        'pdf_file_name': '1.1 Static Final & Core Java Notes.pdf',
        'content': '''<h2>JVM Memory Architecture Explained</h2>
<p>When a Java application starts, the Java Virtual Machine allocates runtime memory divided into five primary data areas:</p>

<ol>
  <li><strong>Classloader Subsystem:</strong> Loads, links, and initializes <code>.class</code> bytecode files.</li>
  <li><strong>Method Area (Metaspace):</strong> Stores class-level structure, static variables, and runtime constant pool.</li>
  <li><strong>Heap Memory:</strong> Stores all instantiated objects. Divided into Young Generation (Eden, S0, S1) and Old (Tenured) Generation.</li>
  <li><strong>JVM Stack:</strong> Stores stack frames for active method invocations containing local primitive variables and object references.</li>
  <li><strong>PC Registers & Native Method Stacks:</strong> Track instruction execution addresses for each thread.</li>
</ol>

<hr/>

<h3>Static vs Final Keywords in Java</h3>
<ul>
  <li><strong>`static`:</strong> Associates variable or method with the Class rather than individual instances. Allocated once in Method Area.</li>
  <li><strong>`final`:</strong> Prevents mutation. When applied to variables, value cannot be reassigned; applied to methods, prevents overriding; applied to classes, prevents inheritance (e.g. <code>java.lang.String</code>).</li>
</ul>
'''
    },
    {
        'title': 'Top 30 Python Interview Questions & In-Depth Code Solutions (2026 Edition)',
        'slug': 'top-30-python-interview-questions-answers',
        'topic': 'INTERVIEW',
        'read_time': '12 min read',
        'summary': 'Master the most frequently asked Python technical interview questions for junior to mid-level software engineering roles with executable code examples, memory models, and interviewer expectations.',
        'tags': 'Python, Interview Prep, Freshers, OOP, GIL, Memory Management',
        'pdf_download_url': PYTHON_DRIVE_FOLDER,
        'pdf_file_name': 'ADVANCED PYTHON BY KASHINATH.pdf',
        'content': '''<h2>Introduction: Cracking the Modern Python Technical Interview</h2><p>Python remains one of the world's most popular programming languages for backend engineering, data science, automation, and cloud infrastructure. When interviewing for fresher and junior developer roles, hiring managers look beyond basic syntax; they evaluate your grasp of Python's memory management, data model, performance characteristics, and object-oriented architecture.</p><hr/><h3>1. How Does Python Handle Memory Management & Garbage Collection?</h3><p>Python uses Reference Counting and a Generational Cyclic Garbage Collector.</p><pre><code class="language-python">import sys\ndata = ["Django", "Python", "SQLite"]\nprint(f"Reference Count: {sys.getrefcount(data) - 1}")</code></pre><hr/><h3>2. What is the Global Interpreter Lock (GIL)?</h3><p>The GIL is a mutex in CPython that prevents multiple native threads from executing Python bytecode simultaneously, avoiding race conditions in reference counting.</p><hr/><h3>3. Mutable vs Immutable Default Argument Gotcha</h3><pre><code class="language-python">def append_student_safe(name, student_list=None):\n    if student_list is None:\n        student_list = []\n    student_list.append(name)\n    return student_list</code></pre>'''
    },
    {
        'title': 'Complete Python & Django Full-Stack Developer Roadmap for Freshers (2026)',
        'slug': 'python-django-full-stack-developer-roadmap',
        'topic': 'CAREER',
        'read_time': '10 min read',
        'summary': 'A comprehensive step-by-step career guide for college students and fresh graduates to transition from zero coding knowledge to a hired Full-Stack Python Django Software Engineer.',
        'tags': 'Django, Python, Career Roadmap, Freshers, Web Development',
        'pdf_download_url': PYTHON_DRIVE_FOLDER,
        'pdf_file_name': 'Py Notes By kashi.pdf',
        'content': '''<h2>Why Choose Python & Django in 2026?</h2><p>Django is the industry standard high-level Python web framework powering Instagram, Spotify, and Pinterest with built-in ORM, Auth, Admin, and CSRF protection.</p><hr/><h3>Phase 1: Core Python Fundamentals</h3><p>Master control flow, lists, dicts, tuples, sets, functions, OOP, and exception handling.</p><hr/><h3>Phase 2: Database Design & Relational Modeling</h3><p>Learn SQL, schema normalization (1NF, 2NF, 3NF), and PostgreSQL.</p><hr/><h3>Phase 3: Django Web Architecture & MVT</h3><p>Models, Views, Templates, ModelForms, and Middleware.</p><hr/><h3>Phase 4: Django REST Framework & APIs</h3><p>Serializers, ViewSets, SimpleJWT authentication, and pagination.</p>'''
    },
    {
        'title': 'Mastering Python Object-Oriented Programming (OOP) with Practical Examples',
        'slug': 'mastering-python-oop-concepts-practical-guide',
        'topic': 'PYTHON',
        'read_time': '9 min read',
        'summary': 'Deep dive into OOP in Python: understand classes, inheritance, encapsulation, polymorphism, abstract base classes, and dunder methods with clean production code.',
        'tags': 'Python, OOP, Software Engineering, Best Practices',
        'pdf_download_url': PYTHON_DRIVE_FOLDER,
        'pdf_file_name': 'ADVANCED PYTHON BY KASHINATH.pdf',
        'content': '''<h2>Core Pillars of OOP in Python</h2><hr/><h3>1. Encapsulation</h3><pre><code class="language-python">class BankAccount:\n    def __init__(self, owner: str, initial_balance: float = 0.0):\n        self.owner = owner\n        self._balance = initial_balance\n    @property\n    def balance(self):\n        return self._balance</code></pre><hr/><h3>2. Inheritance & Polymorphism</h3><pre><code class="language-python">class BaseTracer:\n    def trace(self):\n        pass</code></pre>'''
    },
    {
        'title': 'How to Crack Off-Campus IT & Software Engineering Placement Drives (2026)',
        'slug': 'crack-off-campus-software-engineering-placements',
        'topic': 'CAREER',
        'read_time': '11 min read',
        'summary': 'Proven strategies for college students and fresh graduates to secure high-paying tech jobs through off-campus recruitment drives, cold outreach, ATS resume design, and technical preparation.',
        'tags': 'Jobs, Career Advice, Placements, Resume, Off-Campus',
        'pdf_download_url': PYTHON_DRIVE_FOLDER,
        'pdf_file_name': 'Python Notes & Resume Guide.pdf',
        'content': '''<h2>Strategies for Off-Campus Success</h2><hr/><h3>1. ATS-Optimized Single Page Resume</h3><p>Use clean single-column formatting and highlight Python, Django, PostgreSQL, and Git.</p><hr/><h3>2. Impactful GitHub Portfolios</h3><p>Build 2-3 production-grade projects with clean commit histories and unit test coverage.</p><hr/><h3>3. Strategic Cold Outreach</h3><p>Connect with Engineering Managers and Tech Leads directly on LinkedIn.</p>'''
    },
    {
        'title': 'Django REST Framework (DRF) & API Architecture: Complete Beginner Guide',
        'slug': 'django-rest-framework-drf-api-complete-guide',
        'topic': 'DJANGO',
        'read_time': '10 min read',
        'summary': 'Learn how to architect, serialize, secure, and document scalable RESTful APIs with Django REST Framework, SimpleJWT authentication, and pagination.',
        'tags': 'Django, DRF, REST API, Web Development, Backend',
        'pdf_download_url': PYTHON_DRIVE_FOLDER,
        'pdf_file_name': 'Py Notes By kashi.pdf',
        'content': '''<h2>REST API Architecture in Django</h2><hr/><h3>1. Serializers</h3><p>Transforming complex querysets to native JSON representations.</p><hr/><h3>2. ModelViewSets</h3><p>Standardized CRUD operations with clean routing.</p><hr/><h3>3. JWT Authentication</h3><p>Stateless user authentication using SimpleJWT.</p>'''
    },
    {
        'title': 'Essential Data Structures in Python: Complexity, Use Cases & Code Patterns',
        'slug': 'essential-data-structures-in-python-guide',
        'topic': 'DSA',
        'read_time': '9 min read',
        'summary': 'Master the core data structures in Python with time complexity breakdowns (Big-O), memory footprints, and practical coding patterns for technical interviews.',
        'tags': 'Python, Data Structures, Algorithms, Big-O, Coding',
        'pdf_download_url': PYTHON_DRIVE_FOLDER,
        'pdf_file_name': 'BASIC PROGRAMS.pdf',
        'content': '''<h2>Core Python Data Structures & Complexity</h2><hr/><h3>1. Lists (Dynamic Arrays)</h3><p>Index lookup O(1), Append O(1), Search O(N).</p><hr/><h3>2. Dictionaries (Hash Tables)</h3><p>Key lookup O(1) average case.</p><hr/><h3>3. Sets (Hash Sets)</h3><p>Membership test O(1) with set union and intersection operations.</p>'''
    },
    {
        'title': 'Visual Code Debugging: How AST Tracing & Memory Diagrams Help Master Algorithms',
        'slug': 'visual-code-debugging-ast-tracing-memory-guide',
        'topic': 'DEBUGGER',
        'read_time': '8 min read',
        'summary': 'Discover how interactive visual debuggers, Abstract Syntax Tree (AST) instrumentation, call stack inspection, and heap memory diagrams accelerate programming mastery.',
        'tags': 'Debugger, Algorithms, Python, Computer Science, AST',
        'pdf_download_url': PYTHON_DRIVE_FOLDER,
        'pdf_file_name': 'Python Expert Colaboratory Guide.pdf',
        'content': '''<h2>Why Step-by-Step Visual Tracing Matters</h2><p>Step through execution frames, watch memory heaps mutate in real-time, and visualize recursion trees.</p>'''
    },
    {
        'title': 'Git & GitHub Complete Learning Path: Zero to Production Masterclass (2026)',
        'slug': 'git-github-complete-learning-path',
        'topic': 'CAREER',
        'read_time': '14 min read',
        'summary': 'A complete, step-by-step masterclass on Git version control and GitHub collaboration: working tree vs staging area, branching workflows, merge vs rebase, conflict resolution, cherry-pick, stashing, pull requests, and CI/CD pipelines.',
        'tags': 'Git, GitHub, Version Control, Open Source, DevOps, CI/CD, Notion Guide',
        'pdf_download_url': 'https://app.notion.com/p/Git-GitHub-Complete-Learning-Path-2d8e0960b8f88031b77ef78eadb1afbe?source=copy_link',
        'pdf_file_name': 'Official Notion Learning Path & Masterclass Workspace (Click to Open)',
        'content': '''<h2>1. Introduction: Why Git & GitHub Rule Modern Software Engineering</h2>
<p>In modern software engineering, writing code is only half the battle. Teams distributed across time zones build, test, and deploy complex systems consisting of hundreds of microservices. <strong>Git</strong> is the decentralized version control system created by Linus Torvalds in 2005 to manage the Linux kernel codebase, and <strong>GitHub</strong> is the global collaboration platform built on top of Git.</p>
<p>Whether you are a college student building your first portfolio or a staff engineer managing enterprise Kubernetes deployments, mastering Git's internal architecture, branching workflows, and conflict resolution is non-negotiable.</p>

<div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: 1px solid rgba(56,189,248,0.3); border-radius: 14px; padding: 18px 22px; margin: 24px 0; color: #e2e8f0;">
  <div style="font-size: 11px; font-weight: 800; color: #38bdf8; font-family: monospace; letter-spacing: 0.5px; margin-bottom: 6px;">📌 OFFICIAL NOTION WORKSPACE</div>
  <p style="margin: 0 0 10px; font-size: 14px; color: #cbd5e1;">Access the interactive Notion checklist, command cheatsheets, and animated mental models on the official workspace:</p>
  <a href="https://app.notion.com/p/Git-GitHub-Complete-Learning-Path-2d8e0960b8f88031b77ef78eadb1afbe?source=copy_link" target="_blank" rel="noopener" style="display: inline-flex; align-items: center; gap: 8px; background: #2563eb; color: #fff; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 700; text-decoration: none;">
    📓 Open Official Notion Learning Path ↗
  </a>
</div>

<hr/>

<h2>2. Git's Internal Mental Model: The 3 Local Zones</h2>
<p>Git does not track files as diffs or delta patches like older centralized systems (SVN or CVS). Instead, Git thinks of its data more like a series of <strong>snapshots</strong> of a miniature filesystem.</p>

<pre><code class="language-bash">┌──────────────────────┐      git add       ┌──────────────────────┐     git commit     ┌──────────────────────┐
│   Working Directory  │ ─────────────────> │  Staging Area (Index)│ ─────────────────> │ Local Git Repository │
│  (Untracked/Modified)│                    │  (Ready for Snapshot)│                    │     (.git / HEAD)    │
└──────────────────────┘ <───────────────── └──────────────────────┘ <───────────────── └──────────────────────┘
                              git restore                           git reset / revert</code></pre>

<ul>
  <li><strong>Working Directory:</strong> The actual sandbox directory on your computer where you create, edit, and delete source files.</li>
  <li><strong>Staging Area (Index):</strong> A binary index file located inside <code>.git/index</code> that pre-formats and organizes the precise changes destined for the next commit snapshot.</li>
  <li><strong>Local Repository (.git folder):</strong> The permanent object store (Blobs, Trees, Commits, Annotated Tags) where Git permanently saves SHA-1 hashed immutable snapshots.</li>
</ul>

<hr/>

<h2>3. Initial Configuration & First-Time Setup</h2>
<p>Before making any commits, configure your global developer identity and preferred default branch:</p>

<pre><code class="language-bash"># 1. Set your global commit author name & email
git config --global user.name "Kashinath Chavan"
git config --global user.email "kashichavan7777@gmail.com"

# 2. Set default branch to main (standard across modern GitHub)
git config --global init.defaultBranch main

# 3. Configure auto-correct and sensible line-ending handling
git config --global core.autocrlf input
git config --global help.autocorrect 20

# 4. Verify your active configurations
git config --list --show-origin</code></pre>

<hr/>

<h2>4. Daily Core Workflow Commands</h2>
<p>The core daily cycle of a software developer involves checking status, staging modified chunks, and creating meaningful atomic commit snapshots:</p>

<pre><code class="language-bash"># Initialize a new local repository
git init

# Check the state of working directory and staging area
git status

# Stage specific files or all modified files
git add app.py requirements.txt
git add .

# Record a snapshot with a clean conventional commit message
git commit -m "feat(auth): implement JWT token verification middleware"

# Inspect detailed line-by-line diffs
git diff              # Unstaged changes vs Staging area
git diff --staged     # Staged changes vs Last commit (HEAD)

# View concise chronological commit history
git log --oneline --graph --decorate --all</code></pre>

<hr/>

<h2>5. Branching & Team Git Flow Strategies</h2>
<p>In Git, a branch is simply a lightweight, movable 41-byte pointer to a commit hash. Creating a branch is virtually instantaneous and costs zero disk overhead.</p>

<pre><code class="language-bash"># List all local and remote branches
git branch -a

# Create and switch to a new feature branch
git switch -c feature/payment-gateway-stripe
# (Legacy alternative: git checkout -b feature/payment-gateway-stripe)

# Switch back to the main branch
git switch main

# Rename a branch
git branch -m old-name new-name

# Delete a merged feature branch
git branch -d feature/payment-gateway-stripe</code></pre>

<hr/>

<h2>6. Merge vs. Rebase: The Architectural Debate</h2>
<p>When integrating feature branch code back into the main branch, developers choose between two strategies:</p>

<table style="width:100%; border-collapse: collapse; margin: 20px 0;">
  <thead>
    <tr style="background: #f8fafc; border-bottom: 2px solid #e2e8f0; text-align: left;">
      <th style="padding: 10px; border: 1px solid #e2e8f0;">Feature</th>
      <th style="padding: 10px; border: 1px solid #e2e8f0;"><code>git merge</code></th>
      <th style="padding: 10px; border: 1px solid #e2e8f0;"><code>git rebase</code></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>History Style</strong></td>
      <td style="padding: 10px; border: 1px solid #e2e8f0;">Preserves true historical timeline with explicit 2-parent merge commits</td>
      <td style="padding: 10px; border: 1px solid #e2e8f0;">Creates a perfectly linear, clean single-line commit history</td>
    </tr>
    <tr>
      <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>Commit Hashes</strong></td>
      <td style="padding: 10px; border: 1px solid #e2e8f0;">Preserves original commit SHAs</td>
      <td style="padding: 10px; border: 1px solid #e2e8f0;">Re-writes new commit hashes by replaying commits onto target HEAD</td>
    </tr>
    <tr>
      <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>Golden Rule</strong></td>
      <td style="padding: 10px; border: 1px solid #e2e8f0;">Safe for shared public branches (main, develop)</td>
      <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>NEVER</strong> rebase a shared/public branch already pushed to remotes!</td>
    </tr>
  </tbody>
</table>

<pre><code class="language-bash"># Standard Merge (from main)
git switch main
git merge feature/payment-gateway-stripe

# Interactive Rebase (squashing messy commits before submitting PR)
git rebase -i HEAD~3</code></pre>

<hr/>

<h2>7. Resolving Merge Conflicts Step-by-Step</h2>
<p>Conflicts occur when two developers alter the exact same line of code in different branches. Git halts the merge and injects conflict markers into the source file:</p>

<pre><code class="language-python">&lt;&lt;&lt;&lt;&lt;&lt;&lt; HEAD (Current branch: main)
PAYMENT_GATEWAY = "STRIPE_ENTERPRISE_V2"
=======
PAYMENT_GATEWAY = "PAYPAL_PRO_SANDBOX"
>>>>>>> feature/payment-gateway-paypal (Incoming branch)</code></pre>

<p><strong>To resolve:</strong></p>
<ol>
  <li>Open the file, delete the conflict markers (<code>&lt;&lt;&lt;&lt;&lt;&lt;&lt;</code>, <code>=======</code>, <code>&gt;&gt;&gt;&gt;&gt;&gt;&gt;</code>), and keep the desired production code.</li>
  <li>Stage the resolved file: <code>git add payment_settings.py</code></li>
  <li>Complete the commit: <code>git commit -m "fix(merge): resolve payment gateway conflict between Stripe and PayPal"</code></li>
</ol>

<hr/>

<h2>8. Undoing Changes & Safety Nets</h2>

<pre><code class="language-bash"># 1. Discard uncommitted changes in a specific file
git restore filename.py

# 2. Unstage a file without losing local edits
git restore --staged filename.py

# 3. Temporarily stash uncommitted work to switch branches quickly
git stash save "WIP: half-finished login refactor"
git stash list
git stash pop

# 4. Safely undo a pushed commit by creating a new inverse commit
git revert &lt;commit-hash&gt;

# 5. Reset HEAD (Soft = keep in staging, Hard = permanently discard)
git reset --soft HEAD~1   # Undo commit, keep changes staged
git reset --hard HEAD~1   # ⚠️ Danger: completely destroy last commit and working files

# 6. The Ultimate Git Safety Net: REFLOG
# Recovers "lost" or deleted commits and branches!
git reflog
git checkout -b recovered-branch HEAD@{3}</code></pre>

<hr/>

<h2>9. Remote Collaboration on GitHub</h2>

<pre><code class="language-bash"># Link a local repository to GitHub
git remote add origin https://github.com/kashichavan/updatezbykashi.git

# Push local main branch and set upstream tracking
git push -u origin main

# Fetch changes from remote without merging
git fetch origin

# Fetch and immediately merge remote changes into current branch
git pull origin main

# Clean up stale local references to remote deleted branches
git fetch --prune</code></pre>

<hr/>

<h2>10. Professional Pull Request (PR) & Open Source Etiquette</h2>
<ul>
  <li><strong>Keep PRs Small & Focused:</strong> A PR with 150 lines of code across 3 files is reviewed in 10 minutes. A PR with 2,500 lines across 80 files is delayed for weeks.</li>
  <li><strong>Write Descriptive PR Descriptions:</strong> Mention <em>Why</em> this change is made, <em>What</em> approaches were tested, and link the related issue ticket.</li>
  <li><strong>Run Linting & Unit Tests Locally:</strong> Ensure <code>python manage.py test</code> passes and code formatting adheres to PEP 8 / Prettier before opening the PR.</li>
  <li><strong>Squash Work-in-Progress Commits:</strong> Turn 15 messy "fix typo", "test again" commits into 1 clean logical commit before merge.</li>
</ul>

<div style="text-align: center; margin-top: 36px; padding: 24px; background: #f8fafc; border-radius: 16px; border: 1px solid #e2e8f0;">
  <h3 style="margin-top: 0;">Ready for the Full Interactive Learning Path?</h3>
  <p style="color: #64748b; font-size: 14px;">Explore the full Notion workspace with copy-paste workflows, interactive flashcards, and advanced Git architecture diagrams.</p>
  <a href="https://app.notion.com/p/Git-GitHub-Complete-Learning-Path-2d8e0960b8f88031b77ef78eadb1afbe?source=copy_link" target="_blank" rel="noopener" style="display: inline-flex; align-items: center; gap: 8px; background: #0f172a; color: #fff; padding: 12px 24px; border-radius: 10px; font-size: 14px; font-weight: 800; text-decoration: none; box-shadow: 0 4px 12px rgba(15,23,42,0.25);">
    🚀 Open Git &amp; GitHub Complete Learning Path on Notion ↗
  </a>
</div>'''
    }
]

for g in guides_seeds:
    obj, _ = GuideArticle.objects.update_or_create(slug=g['slug'], defaults=g)
    print(f"[Seeded Guide] {obj.title}")

print(f"\nProduction seeding completed successfully. Total Guides in DB: {GuideArticle.objects.count()}")
