from django.core.management.base import BaseCommand
from blog.models import Category, Tag, BlogPost
from django.utils import timezone
from datetime import timedelta
import re

CATEGORY_CONFIG = {
    'PYTHON': {
        'name': 'Python & Backend',
        'icon': '🐍',
        'color': '#3b82f6',
        'description': 'Advanced Python architecture, memory models, asyncio concurrency, pytest, and OOP design patterns.',
        'order': 1,
    },
    'DJANGO': {
        'name': 'Django & Web Architecture',
        'icon': '🚀',
        'color': '#10b981',
        'description': 'Django MVT, Django REST Framework, Django Ninja type-safe APIs, and scalable full-stack SaaS backends.',
        'order': 2,
    },
    'DSA': {
        'name': 'Data Structures & Algorithms',
        'icon': '🧩',
        'color': '#f97316',
        'description': 'Core data structures, Java Collections internals, time complexity, and practical programming problems.',
        'order': 3,
    },
    'INTERVIEW': {
        'name': 'Interview Prep & Database',
        'icon': '🎯',
        'color': '#a855f7',
        'description': 'High-frequency technical interview questions, FAANG SQL handbooks, JVM memory internals, and system design.',
        'order': 4,
    },
    'CAREER': {
        'name': 'Career & Git Roadmaps',
        'icon': '💼',
        'color': '#ec4899',
        'description': 'Career roadmaps for freshers, Git & GitHub production workflows, and placement drive strategies.',
        'order': 5,
    },
    'JAVASCRIPT': {
        'name': 'JavaScript & Engines',
        'icon': '⚡',
        'color': '#f59e0b',
        'description': 'Deep dives into V8 bytecode, JIT optimization, Event Loop mechanics, and ECMAScript specifications.',
        'order': 6,
    },
    'FRONTEND': {
        'name': 'Frontend & Next.js',
        'icon': '⚛️',
        'color': '#38bdf8',
        'description': 'Next.js 15 App Router, React 19 Server Components, Tailwind CSS, and edge rendering patterns.',
        'order': 7,
    },
    'DEBUGGER': {
        'name': 'Developer Tooling & Compilers',
        'icon': '🛠️',
        'color': '#14b8a6',
        'description': 'AST tracing, visual step debuggers, memory diagrams, and compiler engineering.',
        'order': 8,
    }
}

COVER_IMAGES = {
    'PYTHON': 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1200',
    'DJANGO': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200',
    'DSA': 'https://images.unsplash.com/photo-1509228468518-180dd4864904?w=1200',
    'INTERVIEW': 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200',
    'CAREER': 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1200',
    'JAVASCRIPT': 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1200',
    'FRONTEND': 'https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=1200',
    'DEBUGGER': 'https://images.unsplash.com/photo-1542831371-29b0f74f9713?w=1200',
}

MODERN_POSTS = [
    {
        "topic": "JAVASCRIPT",
        "tags": "javascript, v8, performance, nodejs, compilers",
        "title": "Deep Dive into V8 Engine: How Ignition and TurboFan Execute JavaScript at Light Speed",
        "slug": "deep-dive-v8-engine-ignition-turbofan-javascript",
        "summary": "Explore the inner workings of Google Chrome's V8 engine: Abstract Syntax Trees (AST), Ignition bytecode generation, hidden classes, and TurboFan JIT machine code compilation.",
        "cover_image_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1200",
        "is_featured": True,
        "content": """<h2>1. The Anatomy of Modern JavaScript Execution</h2>
<p>When your browser loads a <code>.js</code> bundle, JavaScript does not execute as simple interpreted text. Under the hood, Google's <strong>V8 engine</strong> (which powers Chrome, Node.js, Electron, and Bun/Deno) executes a sophisticated multi-tier pipeline:</p>

<pre><code class="language-text">[ JavaScript Source Code ]
           │
           ▼
[ Scanner & Tokenizer ] ───▶ [ Abstract Syntax Tree (AST) ]
                                       │
                                       ▼
                         [ Ignition Bytecode Interpreter ]
                                       │
                        ┌──────────────┴──────────────┐
                        │ Dynamic Profiler (Type Feedback) │
                        └──────────────┬──────────────┘
                                       ▼
                         [ TurboFan Optimizing Compiler ]
                                       │
                                       ▼
                            [ Highly Optimized Machine Code ]</code></pre>

<hr/>

<h2>2. Parsing and AST Generation</h2>
<p>The Scanner breaks raw source code into atomic tokens (<code>let</code>, <code>identifier</code>, <code>operator</code>, <code>literal</code>). The Parser turns these tokens into an <strong>Abstract Syntax Tree (AST)</strong>.</p>
<p>During this phase, Scope Analysis occurs where variable declarations (<code>let</code>, <code>const</code>, <code>var</code>) are registered in Lexical Environment records.</p>

<hr/>

<h2>3. Ignition Bytecode & TurboFan JIT Optimization</h2>
<p>Ignition compiles AST into compact bytecode. As functions run hot, TurboFan generates high-speed machine code directly for CPU execution with monomorphic inline caching.</p>"""
    },
    {
        "topic": "DJANGO",
        "tags": "django, python, ninja, api, saas",
        "title": "Django Ninja vs FastAPI: Building Type-Safe High-Concurrency APIs in Python",
        "slug": "django-ninja-vs-fastapi-high-concurrency-python-apis",
        "summary": "A hands-on architectural comparison between Django Ninja and FastAPI for modern SaaS backends. Learn how Pydantic v2 and async ORM enable blazing-fast API development.",
        "cover_image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200",
        "is_featured": True,
        "content": """<h2>Why Django Ninja is Revolutionizing Python SaaS</h2>
<p>Django Ninja combines the speed and ergonomics of FastAPI with the battle-tested ORM, admin portal, and authentication of Django.</p>

<hr/>

<h3>Defining High-Performance Endpoints with Django Ninja</h3>
<pre><code class="language-python">from ninja import NinjaAPI, Schema
from typing import List

api = NinjaAPI(title="SaaS Core API", version="1.0.0")

class ProductOut(Schema):
    id: int
    name: str
    price: float

@api.get("/products", response=List[ProductOut])
def list_products(request):
    return list(Product.objects.filter(is_active=True)[:50])
</code></pre>"""
    },
    {
        "topic": "FRONTEND",
        "tags": "react, nextjs, typescript, tailwind, frontend",
        "title": "Mastering Next.js 15 App Router & React 19 Server Components: The Complete Guide",
        "slug": "mastering-nextjs-15-app-router-react-19-server-components",
        "summary": "Learn how to architect lightning-fast full-stack web applications using Next.js 15 App Router, Server Actions, streaming SSR with Suspense, and Tailwind CSS.",
        "cover_image_url": "https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=1200",
        "is_featured": True,
        "content": """<h2>The Shift from Client-Side SPA to Hybrid Streaming</h2>
<p>Modern React with Next.js 15 enables zero-client-bundle React Server Components (RSC), instant streaming HTML under 50ms, and type-safe server actions.</p>"""
    }
]

class Command(BaseCommand):
    help = "Migrate and seed all guides and technical articles into BlogPost database"

    def handle(self, *args, **options):
        self.stdout.write("🌱 Migrating and seeding all Guides & Articles into Tech Blog...")
        
        # 1. Create categories
        category_map = {}
        for code, conf in CATEGORY_CONFIG.items():
            cat, _ = Category.objects.get_or_create(
                name=conf['name'],
                defaults={
                    'slug': code.lower().replace('&', '-'),
                    'icon': conf['icon'],
                    'color': conf['color'],
                    'description': conf['description'],
                    'order': conf['order'],
                }
            )
            cat.icon = conf['icon']
            cat.color = conf['color']
            cat.description = conf['description']
            cat.order = conf['order']
            cat.save()
            category_map[code] = cat

        # 2. Import existing guides from requirements.seed_prod
        from requirements.seed_prod import guides_seeds
        all_articles = list(guides_seeds) + MODERN_POSTS

        seeded_count = 0
        for idx, item in enumerate(all_articles):
            topic_key = item.get('topic', 'PYTHON').upper()
            cat = category_map.get(topic_key, category_map['PYTHON'])
            
            slug = item['slug']
            title = item['title']
            summary = item.get('summary', title)
            content = item.get('content', '')
            is_featured = item.get('is_featured', False) or idx in (0, 1, 6)
            cover_img = item.get('cover_image_url') or COVER_IMAGES.get(topic_key, COVER_IMAGES['PYTHON'])

            # Calculate read time in minutes
            read_time_str = item.get('read_time', '')
            match = re.search(r'(\d+)', read_time_str)
            read_mins = int(match.group(1)) if match else 7

            post, created = BlogPost.objects.get_or_create(
                slug=slug,
                defaults={
                    'title': title,
                    'excerpt': summary,
                    'content': content,
                    'category': cat,
                    'cover_image_url': cover_img,
                    'author_name': 'Kashinath Chavan',
                    'author_title': 'Founder & Software Architect',
                    'author_avatar_url': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
                    'read_time_minutes': read_mins,
                    'views_count': 180 + (idx * 37),
                    'likes_count': 42 + (idx * 8),
                    'is_published': True,
                    'is_featured': is_featured,
                    'published_at': timezone.now() - timedelta(days=idx)
                }
            )

            # Update content in case it changed
            post.title = title
            post.excerpt = summary
            post.content = content
            post.category = cat
            post.cover_image_url = cover_img
            post.is_published = True
            post.is_featured = is_featured
            post.read_time_minutes = read_mins
            post.save()

            # Process tags
            from django.utils.text import slugify
            tags_raw = item.get('tags', '')
            if tags_raw:
                for t_name in [t.strip().lstrip('#') for t in tags_raw.split(',') if t.strip()]:
                    t_slug = slugify(t_name)
                    if t_slug:
                        tag_obj, _ = Tag.objects.get_or_create(slug=t_slug, defaults={'name': t_name.title()})
                        post.tags.add(tag_obj)

            seeded_count += 1
            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"  ✓ {status}: [{cat.name}] {post.title[:55]}..."))

        self.stdout.write(self.style.SUCCESS(f"\n✨ Successfully seeded all {seeded_count} articles into Tech Blog!"))
