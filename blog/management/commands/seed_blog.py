from django.core.management.base import BaseCommand
from blog.models import Category, Tag, BlogPost
from django.utils import timezone
from datetime import timedelta

SAMPLE_POSTS = [
    {
        "category": "JavaScript & Engines",
        "category_icon": "⚡",
        "category_color": "#f59e0b",
        "category_desc": "Deep dives into V8 bytecode, JIT optimization, Event Loop mechanics, and ECMAScript specifications.",
        "tags": ["javascript", "v8", "performance", "nodejs", "webdev"],
        "title": "Deep Dive into V8 Engine: How Ignition and TurboFan Execute JavaScript at Light Speed",
        "slug": "deep-dive-v8-engine-ignition-turbofan-javascript",
        "excerpt": "Explore the inner workings of Google Chrome's V8 engine: Abstract Syntax Trees (AST), Ignition bytecode generation, hidden classes, and TurboFan JIT machine code compilation.",
        "cover_image_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Compiler Enthusiast",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "is_featured": True,
        "content": """## 1. The Anatomy of Modern JavaScript Execution

When your browser loads a `.js` bundle, JavaScript does not execute as simple interpreted text. Under the hood, Google's **V8 engine** (which powers Chrome, Node.js, Electron, and Bun/Deno) executes a sophisticated multi-tier pipeline:

```text
[ JavaScript Source Code ]
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
                            [ Highly Optimized Machine Code ]
```

---

## 2. Parsing and AST Generation

The Scanner breaks raw source code into atomic tokens (`let`, `identifier`, `operator`, `literal`). The Parser turns these tokens into an **Abstract Syntax Tree (AST)**. 

During this phase:
- **Scope Analysis** occurs: variable declarations (`let`, `const`, `var`) are registered in Lexical Environment records.
- **Syntax validation** is enforced: unbalanced brackets, illegal returns, and lexical errors are surfaced before execution.

---

## 3. Ignition: High-Efficiency Bytecode Interpreter

Instead of compiling directly to machine code (which consumed massive memory in early V8 versions), V8 compiles the AST into compact **Ignition Bytecode**.

Ignition executes in an accumulator-based register machine model:
```text
LdaNamedProperty a0, [0]   ; Load property into accumulator register
Star r1                    ; Store accumulator in local register r1
Add r1, [1]                ; Add constant operand to register
Return                     ; Return top of stack value
```

---

## 4. TurboFan JIT Compiler & Speculative Optimization

As bytecode executes, the runtime collects **Type Feedback Vectors**. If a function is called thousands of times with predictable object shapes (monomorphic types), TurboFan compiles that function into raw x86/ARM assembly with direct memory offset lookups.

> **Key Takeaway:** Always maintain consistent object shapes (order of keys initialized in constructor) to prevent TurboFan **De-optimizations (Deopt)**.
"""
    },
    {
        "category": "Backend & SaaS",
        "category_icon": "🚀",
        "category_color": "#10b981",
        "category_desc": "High-performance Python APIs, Django Ninja, PostgreSQL query optimization, and SaaS architecture.",
        "tags": ["django", "python", "api", "saas", "postgresql"],
        "title": "Django Ninja vs FastAPI: Building Type-Safe High-Concurrency APIs in Python",
        "slug": "django-ninja-vs-fastapi-high-concurrency-python-apis",
        "excerpt": "A hands-on architectural comparison between Django Ninja and FastAPI for modern SaaS backends. Learn how Pydantic v2 and async ORM enable blazing-fast API development.",
        "cover_image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Full-Stack SaaS Architect",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "is_featured": True,
        "content": """## Why Django Ninja is Revolutionizing Python SaaS

For years, Python developers were caught in a trade-off:
1. **Django REST Framework (DRF):** Robust ORM, batteries-included admin, auth, and ecosystem — but verbose serializers and higher latency.
2. **FastAPI:** Lightning fast, Pydantic type-hints, auto OpenAPI docs — but lacks built-in ORM, admin portal, user migrations, and auth tooling.

Enter **Django Ninja**: the perfect blend of FastAPI's modern developer ergonomics and Django's enterprise foundation.

---

## Defining a High-Performance Endpoint with Django Ninja

```python
from ninja import NinjaAPI, Schema
from typing import List
from .models import Product

api = NinjaAPI(title="SaaS Core API", version="1.0.0")

class ProductOutSchema(Schema):
    id: int
    name: str
    price: float
    is_in_stock: bool

@api.get("/products", response=List[ProductOutSchema])
def list_products(request, category: str = None):
    qs = Product.objects.filter(is_active=True)
    if category:
        qs = qs.filter(category__slug=category)
    return list(qs.select_related("category")[:50])
```

---

## 3 Reasons Why Django Ninja Wins for SaaS

1. **Pydantic v2 Core Performance:** Serializing 10,000 ORM objects takes ~8ms instead of 180ms with classic serializers.
2. **Instant OpenAPI & Swagger Docs:** Interactive testing UI mounted automatically at `/api/docs`.
3. **Seamless Django Ecosystem:** Zero migration overhead; access Django ORM, signals, auth, and Celery tasks directly.
"""
    },
    {
        "category": "Frontend & Next.js",
        "category_icon": "⚛️",
        "category_color": "#38bdf8",
        "category_desc": "Next.js 14/15 App Router, React 19 Server Components, Tailwind CSS, and edge rendering patterns.",
        "tags": ["react", "nextjs", "typescript", "tailwind", "frontend"],
        "title": "Mastering Next.js 15 App Router & React 19 Server Components: The Complete Guide",
        "slug": "mastering-nextjs-15-app-router-react-19-server-components",
        "excerpt": "Learn how to architect lightning-fast full-stack web applications using Next.js 15 App Router, Server Actions, streaming SSR with Suspense, and Tailwind CSS.",
        "cover_image_url": "https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Frontend Architect",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "is_featured": True,
        "content": """## The Shift from Client-Side SPA to Hybrid Streaming

Modern React with Next.js 15 has redefined how web applications fetch and render data:

```text
User Request
     │
     ▼
[ Next.js Edge / Node.js Server ]
     │
     ├─▶ [ React Server Component (RSC) ] (Direct Database / API Access, Zero Client JS)
     │
     ├─▶ [ Streaming SSR Chunk 1 ] ───▶ Browser displays initial HTML instantly (<50ms)
     │
     └─▶ [ Suspense Fallback ] ───▶ Streams dynamic data chunks asynchronously
```

---

## Type-Safe Data Fetching Pattern in Next.js Server Components

```tsx
// app/learn/javascript/[slug]/page.tsx
import { notFound } from 'next/navigation';
import { getChapterDetail } from '@/lib/api';
import { CodeEditor } from '@/components/ui/CodeEditor';
import { TableOfContents } from '@/components/ui/TableOfContents';

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default async function ChapterPage({ params }: PageProps) {
  const { slug } = await params;
  const chapter = await getChapterDetail(slug);

  if (!chapter) {
    notFound();
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-4 gap-8">
      <main className="lg:col-span-3 space-y-8">
        <h1 className="text-3xl font-extrabold text-white">{chapter.title}</h1>
        <div className="prose prose-invert max-w-none" dangerouslySetInnerHTML={{ __html: chapter.introduction }} />
        <CodeEditor starterCode={chapter.starter_code} />
      </main>
      <aside className="hidden lg:block">
        <TableOfContents />
      </aside>
    </div>
  );
}
```
"""
    },
    {
        "category": "Database & SQL",
        "category_icon": "🗄️",
        "category_color": "#a855f7",
        "category_desc": "Relational databases, indexing strategies, EXPLAIN plan analyzers, and transaction isolation.",
        "tags": ["sql", "postgresql", "database", "performance", "indexing"],
        "title": "PostgreSQL Query Optimization: Understanding B-Tree Indexes, EXPLAIN ANALYZE & Buffer Hits",
        "slug": "postgresql-query-optimization-explain-analyze-indexing",
        "excerpt": "Demystify query performance in PostgreSQL. Learn how sequential scans, index scans, bitmap heap scans, and memory work behind every high-speed SQL query.",
        "cover_image_url": "https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Database Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "is_featured": False,
        "content": """## Why Your Queries Are Slow: Index Scans vs Seq Scans

When you execute `SELECT * FROM orders WHERE customer_id = 4521`, PostgreSQL's query planner evaluates multiple candidate execution paths:

1. **Sequential Scan (Seq Scan):** Reads every single 8KB disk page on the table sequentially. O(N) complexity.
2. **Index Scan:** Traverses the balanced tree (B-Tree) in O(log N) steps to fetch exact row pointers (TIDs).
3. **Bitmap Index Scan:** Constructs an in-memory bitmask of matching disk pages when returning multiple matches.

---

## Visualizing EXPLAIN (ANALYZE, BUFFERS)

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    e.ename,
    d.dname,
    e.sal
FROM emp e
INNER JOIN dept d ON e.deptno = d.deptno
WHERE e.sal >= 2000
ORDER BY e.sal DESC;
```

Look for **`Buffers: shared hit=4`** — when shared hits equal total blocks, your data is served 100% from PostgreSQL RAM cache without touching slow NVMe storage.
"""
    },
    {
        "category": "JavaScript & Engines",
        "category_icon": "⚡",
        "category_color": "#f59e0b",
        "category_desc": "Deep dives into V8 bytecode, JIT optimization, Event Loop mechanics, and ECMAScript specifications.",
        "tags": ["javascript", "async", "eventloop", "promises", "concurrency"],
        "title": "The JavaScript Event Loop Explained: Microtasks, Macrotasks and Execution Contexts",
        "slug": "javascript-event-loop-microtasks-macrotasks-explained",
        "excerpt": "A visual step-by-step breakdown of how single-threaded JavaScript handles asynchronous operations, Promise microtask queues, setTimeout timers, and UI render ticks.",
        "cover_image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "JavaScript Architect",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "is_featured": False,
        "content": """## Single-Threaded Non-Blocking Concurrency

JavaScript is single-threaded: it has exactly **one Call Stack** and executes one statement at a time. Yet, web applications handle thousands of concurrent network requests, UI clicks, and animations seamlessly.

This magic is powered by the **Event Loop** operating in coordination with browser Web APIs / Node.js libuv:

```text
[ Synchronous Call Stack ] ────▶ (Runs statements to completion)
            │
            ▼ (Stack Empty)
[ Microtask Queue ] ───────────▶ (Promise.then, queueMicrotask, MutationObserver)
            │                    * Drained COMPLETELY before moving on!
            ▼
[ Animation Frame Queue ] ─────▶ (requestAnimationFrame, UI Layout Repaint)
            │
            ▼
[ Macrotask Queue (Task) ] ────▶ (setTimeout, setInterval, I/O, setImmediate)
                                 * Executes ONE single macrotask per tick!
```
"""
    },
    {
        "category": "UI & Design Systems",
        "category_icon": "🎨",
        "category_color": "#ec4899",
        "category_desc": "Modern UI engineering, dark mode design systems, micro-animations, and fluid web experiences.",
        "tags": ["ui", "design", "css", "tailwind", "ux"],
        "title": "Engineering High-Converting SaaS Dashboards: Modern Dark Mode, Micro-Interactions & Glassmorphism",
        "slug": "engineering-high-converting-saas-dashboards-dark-mode-design",
        "excerpt": "Master the principles of elite developer tooling UI: semantic color palettes, subtle glowing borders, interactive code playground ergonomics, and accessible typography.",
        "cover_image_url": "https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Design Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "is_featured": False,
        "content": """## The 4 Laws of Premium Developer Tooling UI

Developers have high aesthetic standards. Cluttered, bright, low-contrast interfaces increase cognitive fatigue. Elite software like Linear, Supabase, and Vercel follow 4 core principles:

1. **Deep Slate/Zinc Backgrounds (`#070b14`):** Avoid pure `#000000` to maintain perceptual depth and soft contrast.
2. **Subtle Cyan/Blue Accent Glows (`rgba(56, 189, 248, 0.18)`):** Direct focus to primary actions without visual noise.
3. **Monospace Code Legibility:** JetBrains Mono or Fira Code with tabular figures and clear distinction between `0`, `O`, `l`, and `1`.
4. **Instant Keyboard Navigation:** Power users expect `Cmd+K`, `Ctrl+Enter`, and instant feedback loops.
"""
    }
]

class Command(BaseCommand):
    help = "Seed technical blog posts and categories"

    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding technical blog posts and categories...")
        
        for idx, item in enumerate(SAMPLE_POSTS):
            cat, _ = Category.objects.get_or_create(
                name=item["category"],
                defaults={
                    "icon": item["category_icon"],
                    "color": item["category_color"],
                    "description": item["category_desc"],
                    "order": idx
                }
            )

            post, created = BlogPost.objects.get_or_create(
                slug=item["slug"],
                defaults={
                    "title": item["title"],
                    "excerpt": item["excerpt"],
                    "content": item["content"],
                    "category": cat,
                    "cover_image_url": item["cover_image_url"],
                    "author_name": item["author_name"],
                    "author_title": item["author_title"],
                    "author_avatar_url": item["author_avatar_url"],
                    "is_featured": item["is_featured"],
                    "is_published": True,
                    "views_count": 120 + (idx * 45),
                    "likes_count": 28 + (idx * 12),
                    "published_at": timezone.now() - timedelta(days=idx * 2)
                }
            )

            for tag_name in item["tags"]:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                post.tags.add(tag)

            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"  ✓ {status}: {post.title}"))

        self.stdout.write(self.style.SUCCESS("✨ Successfully seeded blog articles!"))
