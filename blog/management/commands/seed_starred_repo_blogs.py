from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
from blog.models import BlogPost, Category, Tag

STARRED_REPO_POSTS = [
    {
        "slug": "inside-fastapi-asgi-architecture-pydantic-v2",
        "title": "Inside tiangolo/fastapi: ASGI Architecture, Pydantic v2 Core & Dependency Injection Mastery",
        "excerpt": "Analyzing the 82,000+ star repository: How FastAPI leverages Starlette ASGI event loops, Rust-compiled Pydantic v2 validation, and dependency injection graphs to handle 40,000+ req/sec in production.",
        "cover_image_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1200",
        "category_name": "Python & Backend",
        "tags": "fastapi,pydantic,asgi,asyncio,python,github-repo,architecture",
        "read_time_minutes": 16,
        "is_featured": True,
        "views_count": 6420,
        "likes_count": 890,
        "content": """## The Architecture Behind 82,000+ GitHub Stars

When Sebastián Ramírez released **[`tiangolo/fastapi`](https://github.com/tiangolo/fastapi)**, it revolutionized Python backend engineering. Prior to FastAPI, developers had to choose between the batteries-included but synchronous nature of Django, or lightweight Flask without built-in schema validation or type safety.

FastAPI achieved exponential adoption because it fused three distinct architectural primitives into one developer experience:
1. **Starlette's Async Event Loop:** Direct ASGI specification support with non-blocking I/O.
2. **Pydantic v2:** Rust-backed data validation compiling Python type hints into machine-speed type validators.
3. **DAG Dependency Injection:** An explicit, reusable dependency graph evaluated per-request.

---

## 1. How FastAPI Solves the GIL Bottleneck with ASGI

Traditional WSGI servers (Django WSGI, Flask) allocate one synchronous operating system thread or process per concurrent HTTP request. If a database query or external API call takes 200ms, that worker thread is completely blocked from processing any other incoming socket connection.

FastAPI runs on the **ASGI (Asynchronous Server Gateway Interface)** standard via Uvicorn:

```python
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
import asyncio

app = FastAPI(title="Kashii Verified Opportunities Engine")

class JobFilterSchema(BaseModel):
    category: str = Field(default="software-tech", max_length=50)
    max_days: int = Field(default=7, ge=1, le=30)
    remote_only: bool = False

# Non-blocking async route handler
@app.post("/api/v1/jobs/query")
async def query_student_jobs(payload: JobFilterSchema):
    # Non-blocking I/O: Yields control back to the event loop!
    # While awaiting, Uvicorn serves 5,000 other requests on the SAME thread
    results = await asyncio.sleep(0.05, result=[{"id": 1, "company": "Google"}])
    return {"status": "success", "data": results}
```

---

## 2. Pydantic v2: Rust Core Serialization Speedup

In FastAPI 0.100+, Pydantic v2 moved its entire validation engine (`pydantic-core`) to **Rust**.
- **Validation Speed:** Up to 17x faster than Pydantic v1.
- **JSON Serialization:** Direct SIMD-accelerated serialization without intermediate Python dictionary allocation.
- **Strict Mode:** Prevents type coercion bugs (e.g. string `"123"` will not silently turn into integer `123` if `strict=True`).

```python
class StrictRequirement(BaseModel):
    id: int
    salary_usd: float
    is_active: bool

    model_config = {
        "strict": True,
        "frozen": True, # Immutable memory layout
    }
```

---

## 3. Dependency Injection as an Inversion-of-Control Graph

FastAPI's `Depends` system creates an in-memory Directed Acyclic Graph (DAG) for every request. Dependencies can be nested, cached within the request scope, and execute cleanup routines using `yield`:

```python
async def get_db_session():
    db = await DatabasePool.acquire()
    try:
        yield db  # Injected into route handler
    finally:
        await DatabasePool.release(db) # Guaranteed cleanup even on exceptions!

async def get_current_owner(db = Depends(get_db_session)):
    user = await db.fetch_user()
    if not user.is_staff:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user

@app.get("/owner/stats")
async def get_stats(owner = Depends(get_current_owner)):
    return {"owner": owner.name, "status": "authorized"}
```

---

## 4. Key Takeaways from `tiangolo/fastapi`

1. **Leverage Type Hints as Single Source of Truth:** OpenAPI documentation, request validation, and editor auto-completion all flow from Python type annotations.
2. **Embrace Async I/O for Network-Bound Workloads:** When querying databases or microservices, `async def` maximizes single-core concurrency.
3. **Check the GitHub Repository:** [github.com/tiangolo/fastapi](https://github.com/tiangolo/fastapi)
"""
    },
    {
        "slug": "shadcn-ui-architecture-revolution",
        "title": "The shadcn/ui Architecture Revolution: Why Copy-Paste Components Defeated Monolithic NPM UI Kits",
        "excerpt": "Analyzing the 85,000+ star repository: How shadcn/ui revolutionized frontend design systems by rejecting npm packaging in favor of Radix primitives, Tailwind CSS, and copy-paste component ownership.",
        "cover_image_url": "https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?w=1200",
        "category_name": "Frontend & Next.js",
        "tags": "shadcn,tailwind,react,nextjs,ui-ux,github-repo,design-systems",
        "read_time_minutes": 15,
        "is_featured": True,
        "views_count": 7120,
        "likes_count": 940,
        "content": """## The NPM Package Dilemma in UI Development

For over a decade, frontend engineering followed an unquestioned paradigm: install UI component libraries as external NPM packages (`npm install @material-ui/core`, `npm install antd`, `npm install chakra-ui`).

Yet every team eventually hit the **Customization Wall**:
- Upstream styling overrides required clumsy `!important` CSS rules or vendor-specific theme tokens.
- Breaking major version updates created weeks of migration churn.
- Bundle sizes ballooned because unused components remained packaged in node_modules.

Then **[`shadcn/ui`](https://github.com/shadcn-ui/ui)** appeared, rapidly surpassing **85,000+ GitHub stars** by turning the traditional NPM model upside down: **Do not install it as a dependency. Copy the source code directly into your repository.**

---

## 1. The Anatomy of an Open-Code Component

In shadcn/ui, components reside directly in your project under `@/components/ui/button.tsx`. You own every line of code, every accessibility attribute, and every Tailwind class:

```tsx
// components/ui/button.tsx
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-xl text-sm font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-blue-600 text-white shadow-sm hover:bg-blue-700 active:scale-[0.98]",
        destructive: "bg-red-600 text-white hover:bg-red-700",
        outline: "border border-slate-200 bg-white hover:bg-slate-100 text-slate-900",
        ghost: "hover:bg-slate-100 hover:text-slate-900",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 rounded-lg px-3 text-xs",
        lg: "h-12 rounded-xl px-8 text-base",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
```

---

## 2. Why the `asChild` Pattern (Radix Slot) is a Superpower

Have you ever tried styling a Next.js `<Link>` component inside a button library? Monolithic libraries forced awkward props like `<Button component={Link} to="/home">` with broken TypeScript inference.

The `asChild` pattern from Radix UI merges props onto its direct child element without adding an extra DOM wrapper:

```tsx
import Link from "next/link"
import { Button } from "@/components/ui/button"

// Renders a single <a> tag with all Button styles, accessibility, and hover physics!
<Button asChild variant="outline">
  <Link href="/blog">Browse Engineering Articles &rarr;</Link>
</Button>
```

---

## 3. Summary & Takeaways from `shadcn-ui/ui`

1. **Own Your Design System:** When UI code is in your git tree, customizing an animation or padding takes 5 seconds instead of hacking theme providers.
2. **Zero Runtime Overhead:** No CSS-in-JS style injection runtime; Tailwind compiles down to pure atomic CSS at build time.
3. **Uncompromising Accessibility:** Built on Radix primitives, ensuring complete WAI-ARIA keyboard navigation, screen reader announcements, and focus rings.
4. **Explore the Repo:** [github.com/shadcn-ui/ui](https://github.com/shadcn-ui/ui)
"""
    },
    {
        "slug": "vllm-pagedattention-architecture-deep-dive",
        "title": "vLLM & PagedAttention: How OS Virtual Memory Concepts Slashed GPU KV Cache Waste by 96%",
        "excerpt": "Analyzing the 40,000+ star repository: How UC Berkeley's vllm-project/vllm solved GPU memory fragmentation during LLM inference by translating operating system paging algorithms into PagedAttention.",
        "cover_image_url": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=1200",
        "category_name": "Backend & SaaS",
        "tags": "vllm,ai,llm,cuda,python,pagedattention,github-repo",
        "read_time_minutes": 17,
        "is_featured": False,
        "views_count": 5890,
        "likes_count": 810,
        "content": """## The Memory Crisis in High-Concurrency LLM Serving

When serving Large Language Models (LLMs) like LLaMA-3, Mistral, or DeepSeek, the primary performance bottleneck is not raw FLOPS compute—it is **GPU High Bandwidth Memory (HBM) capacity**.

During token generation, the model saves Key and Value tensors for all previous tokens in what is called the **KV Cache**. Prior to vLLM, standard serving systems (like HuggingFace Transformers) suffered from **60% to 80% wasted GPU memory**:
- **Internal Fragmentation:** Memory was reserved upfront for a request's maximum output length (e.g. 2,048 tokens), even if the model finished in 50 tokens.
- **External Fragmentation:** Memory allocations had to be contiguous, leaving small unusable gaps between allocations.

Then researchers at UC Berkeley released **[`vllm-project/vllm`](https://github.com/vllm-project/vllm)** (40,000+ ⭐), demonstrating that this is the exact problem operating system architects solved in the 1960s with **Virtual Memory and Paging**.

---

## 1. How PagedAttention Works

PagedAttention divides the continuous KV cache of a request into fixed-size **KV Blocks** (typically 16 or 32 tokens).
- Tensors are stored in non-contiguous physical GPU memory pages.
- A **Block Table** maps logical token sequences to physical GPU memory addresses, identical to an OS Page Table.
- As new tokens generate, vLLM allocates new physical blocks on demand without pre-reserving maximum lengths!

```text
Logical Token Stream:  [Token 0 ... 15]  -> Block Table -> Physical GPU Block #42
                       [Token 16 ... 31] -> Block Table -> Physical GPU Block #108
                       [Token 32 ... 47] -> Block Table -> Physical GPU Block #12
```

Because memory is allocated in discrete block chunks, wasted memory drops to **less than 4%** (only the unused slots in the final block of a sequence).

---

## 2. Serving 24x Higher Throughput with vLLM in Python

```python
from vllm import LLM, SamplingParams

# Configure model with PagedAttention engine
llm = LLM(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    gpu_memory_utilization=0.90,
    max_model_len=4096,
    tensor_parallel_size=1
)

sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.95,
    max_tokens=256
)

prompts = [
    "Explain monotonic clock vs wall clock in Python.",
    "Why does shadcn/ui avoid npm package publishing?",
    "How does vLLM optimize GPU KV cache allocation?"
]

# Continuous batching processes all prompts concurrently with zero wasted memory
outputs = llm.generate(prompts, sampling_params)

for output in outputs:
    prompt = output.prompt
    generated_text = output.outputs[0].text
    print(f"Generated {len(output.outputs[0].token_ids)} tokens.")
```

---

## 3. Copy-on-Write for Parallel Sampling and Beam Search

When generating multiple candidate responses for the same prompt, traditional systems duplicated the prompt's KV cache multiple times.

PagedAttention enables **Copy-on-Write**: Multiple output streams share the exact same prompt KV blocks in GPU memory. Only when their generated tokens diverge does vLLM allocate new physical blocks, slashing memory requirements for beam search by up to 55%.

---

## 4. Key Takeaways from `vllm-project/vllm`

1. **Classic Computer Science Principles Endure:** When facing modern AI scaling challenges, OS fundamentals (virtual memory, page tables, continuous batching) often hold the optimal solution.
2. **Eliminate Contiguous Memory Requirements:** Non-contiguous block allocation eliminates memory fragmentation.
3. **Explore the Repository:** [github.com/vllm-project/vllm](https://github.com/vllm-project/vllm)
"""
    },
    {
        "slug": "textual-rich-terminal-ui-architecture",
        "title": "Textualize/rich & Textual Architecture: Building Terminal TUIs with Python CSS Engines",
        "excerpt": "Analyzing the 51,000+ star repository: How Will McGugan built Rich and Textual to bring full-stack web concepts—box model, CSS layout engines, and async event dispatchers—to the terminal.",
        "cover_image_url": "https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=1200",
        "category_name": "Python & Backend",
        "tags": "rich,textual,cli,tui,python,github-repo,developer-tooling",
        "read_time_minutes": 14,
        "is_featured": False,
        "views_count": 4820,
        "likes_count": 690,
        "content": """## The Terminal as a Modern Graphical Canvas

Command-line interfaces were traditionally limited to scrolling lines of monochrome ASCII text. When developers needed interactive dashboards or multi-column layouts, they had to struggle with ancient C libraries like `curses`.

Then Will McGugan created **[`Textualize/rich`](https://github.com/Textualize/rich)** (51,000+ ⭐) followed by **`Textual`**, proving that the modern terminal terminal emulator supports 24-bit TrueColor, Unicode glyphs, mouse tracking, and full CSS layouts.

---

## 1. How Rich Renders Tables, Markdown, and Progress Bars

Rich operates on a simple functional concept: **Renderables**. Any object that implements a `__rich_console__` generator method can yield segments of styled text to the terminal canvas:

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
import time

console = Console()

# Display styled banner panel
console.print(Panel.fit(
    "[bold cyan]⚡ Kashii Updatez[/bold cyan] & [bold green]DevCodex Labs[/bold green]\n"
    "[dim]Real-time Student Opportunities & Open Source Analytics[/dim]",
    border_style="blue"
))

# Rich Table with auto-sizing and column styling
table = Table(title="Top Open Source Repositories 2026", show_header=True, header_style="bold magenta")
table.add_column("Repository", style="cyan", no_wrap=True)
table.add_column("Stars", justify="right", style="green")
table.add_column("Primary Language", style="yellow")
table.add_column("Architecture Core", style="white")

table.add_row("tiangolo/fastapi", "82.0k", "Python / Rust", "Starlette ASGI + Pydantic v2")
table.add_row("shadcn-ui/ui", "85.2k", "TypeScript", "Radix Primitives + Tailwind CVA")
table.add_row("vllm-project/vllm", "40.1k", "Python / C++", "PagedAttention Virtual Memory")
table.add_row("kdeldycke/awesome-falsehood", "31.4k", "Markdown", "Distributed Systems & Time Fallacies")

console.print(table)
```

---

## 2. Textual: Web Architecture in the Terminal

While Rich excels at formatted output, **Textual** is a full Application Framework featuring:
- **CSS-like Styling:** A dedicated CSS dialect (`TCSS`) supporting flexbox, grid, padding, margin, dock, and hover pseudo-classes.
- **Async Event Loop:** Complete keyboard navigation and mouse click dispatch.
- **Diff-Based Terminal Screen Updates:** Only changed cells are repainted, eliminating terminal flicker.

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button

class DashboardCard(Static):
    \"\"\"A reactive widget that responds to mouse clicks.\"\"\"
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.notify("Executing git clone in background sandbox...")

class KashiiCodexApp(App):
    CSS = \"\"\"
    Screen {
        background: #0f172a;
    }
    #welcome-box {
        border: solid #3b82f6;
        padding: 1 2;
        margin: 1;
        background: #1e293b;
    }
    Button {
        background: #2563eb;
        color: white;
    }
    \"\"\"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Welcome to the Terminal Codex", id="welcome-box")
        yield Button("Clone Curated Repositories", variant="primary")
        yield Footer()

if __name__ == "__main__":
    KashiiCodexApp().run()
```

---

## 3. Summary & Takeaways from `Textualize/rich`

1. **User Experience Matters Everywhere:** Whether building web apps or developer CLI tools, clear visual hierarchy, tables, and progress bars dramatically improve adoption.
2. **Terminal Capabilities Are Expanding:** Modern terminals support TrueColor, emojis, and mouse events.
3. **Explore the Repository:** [github.com/Textualize/rich](https://github.com/Textualize/rich)
"""
    },
    {
        "slug": "sqlfluff-ast-parser-architecture",
        "title": "sqlfluff/sqlfluff Architecture: AST Parsing, Lexer State Machines & Dialect Normalization",
        "excerpt": "Analyzing the 10,000+ star repository: How sqlfluff solves the notoriously difficult challenge of tokenizing, parsing, and linting multi-dialect SQL statements through recursive AST state machines.",
        "cover_image_url": "https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=1200",
        "category_name": "Database & SQL",
        "tags": "sql,sqlfluff,compilers,ast,databases,github-repo",
        "read_time_minutes": 15,
        "is_featured": False,
        "views_count": 3980,
        "likes_count": 520,
        "content": """## Why SQL Is the Hardest Language to Parse

Parsing general-purpose programming languages like Python or Go is relatively straightforward: they have formal context-free grammars, strict token definitions, and a single reference compiler.

SQL, in contrast, is an anarchic collection of dozens of conflicting dialects:
- PostgreSQL supports dollar-quoted strings (`$$body$$`) and custom operator definitions.
- Snowflake and BigQuery introduce bespoke syntax for semi-structured JSON traversing (`col:field.subfield`).
- MySQL allows backtick identifiers (`SELECT `col` FROM `table``), while ANSI SQL reserves backticks.
- In production, SQL is often wrapped in Jinja template tags (`{% if is_prod %} ... {% endif %}`).

This is the monumental challenge solved by **[`sqlfluff/sqlfluff`](https://github.com/sqlfluff/sqlfluff)** (10,000+ ⭐)—the open-source dialect-flexible SQL linter and auto-formatter.

---

## 1. The 4-Stage SQLFluff Parser Pipeline

SQLFluff transforms raw SQL string buffers into formatted code through four decoupled stages:

1. **Templating (Jinja/dbt):** Slices out Jinja macros and tracks string position maps so errors in compiled SQL map back to original source template lines.
2. **Lexing:** Converts raw character streams into continuous segments (`WhitespaceSegment`, `KeywordSegment`, `IdentifierSegment`).
3. **Grammar Parsing:** Uses recursive grammar matchers (`Sequence`, `OneOf`, `AnyNumberOf`, `Ref`) to construct a concrete Syntax Tree (CST).
4. **Rule Linting & Auto-Fixing:** Crawls the syntax tree, checks style/correctness rules (e.g. indentation, column quoting, reserved keyword capitalization), and applies atomic tree transformations.

```python
import sqlfluff

query = \"\"\"
select
    id,
    company_name,
    salary_usd,
    posted_date
from public.job_postings
where is_active = true and deadline > now()
order by posted_date desc
limit 10
\"\"\"

# Lint SQL query against ANSI dialect rules
lint_errors = sqlfluff.lint(query, dialect="postgres")
for err in lint_errors:
    print(f"Line {err['line_no']}: [{err['code']}] {err['description']}")

# Auto-format and fix keywords to standard uppercase
fixed_sql = sqlfluff.fix(query, dialect="postgres")
print("=== Formatted SQL ===")
print(fixed_sql)
```

---

## 2. Dialect Inheritance Hierarchy

Rather than rewriting grammar definitions for every database vendor from scratch, SQLFluff employs an **Object-Oriented Dialect Inheritance Tree**:

- The **`ansi`** dialect defines baseline SQL-92 / SQL-99 grammar.
- The **`postgres`** dialect inherits from `ansi`, overriding specific rules (e.g. adding `ILIKE`, `ON CONFLICT DO NOTHING`, and JSONB operator grammars).
- The **`redshift`** dialect inherits from `postgres`, modifying syntax rules specific to AWS data warehouses.

This inheritance architecture allows SQLFluff to support 25+ dialects with minimal code duplication.

---

## 3. Key Takeaways from `sqlfluff/sqlfluff`

1. **Maintain Position Mapping Across Preprocessors:** When compiling or linting templated code, always preserve byte offset mappings back to the user's source file.
2. **Inheritance for Dialect Trees:** Base grammar plus override leaves creates scalable multi-dialect compilers.
3. **Explore the Repository:** [github.com/sqlfluff/sqlfluff](https://github.com/sqlfluff/sqlfluff)
"""
    }
]


class Command(BaseCommand):
    help = "Seeds in-depth engineering masterclasses analyzing top-starred GitHub repositories"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🚀 Seeding Top-Starred GitHub Repository Masterclasses..."))

        created_count = 0
        updated_count = 0

        for post_data in STARRED_REPO_POSTS:
            cat_name = post_data["category_name"]
            category, _ = Category.objects.get_or_create(
                name=cat_name,
                defaults={
                    "slug": slugify(cat_name),
                    "description": f"Curated masterclasses on {cat_name}.",
                    "icon": "⭐",
                    "color": "#2563eb",
                    "order": 1,
                }
            )

            post, created = BlogPost.objects.update_or_create(
                slug=post_data["slug"],
                defaults={
                    "title": post_data["title"],
                    "excerpt": post_data["excerpt"],
                    "content": post_data["content"].strip(),
                    "cover_image_url": post_data["cover_image_url"],
                    "category": category,
                    "author_name": "Kashinath Chavan",
                    "author_title": "Founder & Software Architect",
                    "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
                    "read_time_minutes": post_data["read_time_minutes"],
                    "is_featured": post_data.get("is_featured", False),
                    "is_published": True,
                    "views_count": post_data.get("views_count", 1500),
                    "likes_count": post_data.get("likes_count", 200),
                    "published_at": timezone.now() - timedelta(days=2),
                }
            )

            # Safely add tags with slug and name uniqueness handling
            tags_list = [t.strip().title() for t in post_data["tags"].split(",") if t.strip()]
            for t_name in tags_list:
                s_val = slugify(t_name)
                tag = Tag.objects.filter(slug=s_val).first() or Tag.objects.filter(name__iexact=t_name).first()
                if not tag:
                    tag = Tag.objects.create(name=t_name, slug=s_val)
                post.tags.add(tag)

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Seeding complete! {created_count} created, {updated_count} updated."
        ))
