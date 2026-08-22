from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
from blog.models import BlogPost, Category, Tag


DEEP_POSTS = [
    {
        "slug": "typescript-5-deep-dive",
        "title": "TypeScript 5.x Deep Dive: Satisfies Operator, Const Type Params & Branded Types",
        "excerpt": "TypeScript 5.x brings game-changing features that reshape how enterprise applications are built. Master the satisfies operator, const type parameters, decorators, and branded types with real-world production code examples.",
        "cover_image_url": "https://images.unsplash.com/photo-1516116216624-53e697fedbea?w=1200",
        "category_name": "JavaScript",
        "tags": "typescript,javascript,type-safety,enterprise,advanced",
        "read_time_minutes": 14,
        "is_featured": True,
        "views_count": 3840,
        "likes_count": 512,
    },
    {
        "slug": "docker-compose-multi-stage-deep-dive",
        "title": "Docker & Docker Compose Deep Dive: Multi-Stage Builds, Layer Caching & Production Optimization",
        "excerpt": "Docker multi-stage builds cut production image sizes from 1.2GB to under 80MB. Learn layer caching strategies, BuildKit secrets, health checks, and production-grade docker-compose patterns for Django, Node, and Next.js apps.",
        "cover_image_url": "https://images.unsplash.com/photo-1648134859182-58553cb2ab37?w=1200",
        "category_name": "Developer",
        "tags": "docker,devops,containers,deployment,backend",
        "read_time_minutes": 15,
        "is_featured": True,
        "views_count": 4120,
        "likes_count": 487,
    },
    {
        "slug": "system-design-twitter-whatsapp-youtube",
        "title": "System Design Interview: Designing Twitter Feed, WhatsApp & YouTube Architecture",
        "excerpt": "Step-by-step system design walkthroughs for FAANG interviews. Learn how to design scalable distributed systems for Twitter's news feed, WhatsApp's messaging, and YouTube's video pipeline with CAP theorem, consistent hashing, and sharding explained.",
        "cover_image_url": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=1200",
        "category_name": "Interview",
        "tags": "system-design,distributed-systems,faang,interview,architecture",
        "read_time_minutes": 18,
        "is_featured": True,
        "views_count": 5210,
        "likes_count": 693,
    },
    {
        "slug": "python-asyncio-masterclass",
        "title": "Python Asyncio Masterclass: Building a High-Concurrency Web Scraper with aiohttp",
        "excerpt": "Python's asyncio event loop can handle 10,000+ concurrent connections on a single thread. Learn coroutines, tasks, semaphores, and build a real production async web scraper with aiohttp that is 40x faster than the requests equivalent.",
        "cover_image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1200",
        "category_name": "Python",
        "tags": "python,asyncio,aiohttp,concurrency,performance,scraping",
        "read_time_minutes": 16,
        "is_featured": False,
        "views_count": 2980,
        "likes_count": 398,
    },
    {
        "slug": "react-19-deep-dive-actions",
        "title": "React 19 Deep Dive: Actions, useOptimistic, useFormStatus & Concurrent Rendering",
        "excerpt": "React 19 is the biggest release since React 16 hooks. Actions replace useEffect form submissions, useOptimistic enables instant UI feedback, and React Compiler eliminates manual memoization. Complete guide with working code examples.",
        "cover_image_url": "https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=1200",
        "category_name": "Frontend",
        "tags": "react,react-19,typescript,frontend,hooks,nextjs",
        "read_time_minutes": 14,
        "is_featured": False,
        "views_count": 3650,
        "likes_count": 445,
    },
    {
        "slug": "postgresql-advanced-patterns-jsonb",
        "title": "PostgreSQL Advanced Patterns: JSONB Queries, Partial Indexes & Full-Text Search",
        "excerpt": "PostgreSQL JSONB with GIN indexes delivers MongoDB-level document flexibility inside a relational database. Learn partial indexes, expression indexes, covering indexes, and full-text search with tsvector — the patterns used by Shopify and GitLab at scale.",
        "cover_image_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200",
        "category_name": "Database",
        "tags": "postgresql,sql,database,indexing,performance,jsonb",
        "read_time_minutes": 15,
        "is_featured": False,
        "views_count": 2890,
        "likes_count": 362,
    },
    {
        "slug": "kubernetes-for-developers-explained",
        "title": "Kubernetes for Developers: Pods, Services, Deployments and Helm Charts Explained",
        "excerpt": "Kubernetes does not have to be intimidating. Learn the core objects — Pods, Deployments, Services, Ingress, ConfigMaps, Secrets — with real YAML manifests for a Django + Next.js app, then package it all with a Helm chart.",
        "cover_image_url": "https://images.unsplash.com/photo-1648134859182-58553cb2ab37?w=1200",
        "category_name": "Developer",
        "tags": "kubernetes,k8s,devops,docker,deployment,helm",
        "read_time_minutes": 16,
        "is_featured": False,
        "views_count": 3120,
        "likes_count": 408,
    },
    {
        "slug": "leetcode-75-patterns-two-pointers",
        "title": "LeetCode 75: Two Pointers, Sliding Window & Binary Search with Pattern Recognition",
        "excerpt": "Stop memorising solutions. Learn the 5 core algorithmic patterns that solve 80% of LeetCode problems. Two Pointers, Sliding Window, Binary Search, and more with 15 solved problems, Big-O analysis, and interview strategy.",
        "cover_image_url": "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=1200",
        "category_name": "Data Structures",
        "tags": "dsa,leetcode,algorithms,interview,python,problem-solving",
        "read_time_minutes": 17,
        "is_featured": False,
        "views_count": 4780,
        "likes_count": 621,
    },
    {
        "slug": "saas-stripe-django-subscriptions",
        "title": "Building SaaS Stripe Payment Integration: Subscriptions, Webhooks & Proration in Django",
        "excerpt": "Build a production-ready Stripe subscription system in Django with webhook handling, subscription lifecycle management, proration for plan upgrades, and the Customer Portal.",
        "cover_image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200",
        "category_name": "Django",
        "tags": "django,stripe,saas,payments,webhooks,subscriptions",
        "read_time_minutes": 17,
        "is_featured": False,
        "views_count": 3210,
        "likes_count": 438,
    },
    {
        "slug": "git-advanced-workflows-rebase",
        "title": "Git Advanced Workflows: Interactive Rebase, Cherry-Pick, Bisect & Worktrees",
        "excerpt": "Git power users know commands that make time travel possible. Learn interactive rebase to sculpt perfect commit histories, git bisect to find the exact commit that introduced a bug in 12 steps, cherry-pick for surgical code transplants, and worktrees for parallel feature development.",
        "cover_image_url": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1200",
        "category_name": "Career",
        "tags": "git,github,version-control,devops,workflow,productivity",
        "read_time_minutes": 13,
        "is_featured": False,
        "views_count": 2650,
        "likes_count": 347,
    },
]


DEEP_CONTENT = {

"typescript-5-deep-dive": """<h2>Why TypeScript 5.x Changes Everything</h2>
<p>TypeScript 5.0 shipped with over 50% faster build times, a complete rewrite of the decorator system, and a collection of type-level features so expressive they eliminate entire categories of runtime bugs. If you are still writing TypeScript the same way you did in 4.x, you are leaving correctness and developer productivity on the table.</p>
<p>This article breaks down each major TypeScript 5.x feature with real production code, explains the underlying type theory, and shows you exactly where these features matter in enterprise-scale codebases at companies like Airbnb, Stripe, and Microsoft.</p>
<hr/>
<h2>1. The satisfies Operator — Validate Without Widening</h2>
<p>Before <code>satisfies</code>, you had two unsatisfying options. You could use a type annotation and lose narrow inference, or use <code>as const</code> and lose type validation. The <code>satisfies</code> operator gives you both simultaneously.</p>
<h3>The Classic Problem</h3>
<pre><code class="language-typescript">// Old approach — annotation widens the type
type Colors = "red" | "green" | "blue";
type RGB   = [number, number, number];

const palette: Record&lt;Colors, string | RGB&gt; = {
  red:   [255, 0, 0],
  green: "#00ff00",
  blue:  [0, 0, 255],
};

// palette.red is now string | RGB — TypeScript lost the tuple info!
// Error: Property 'map' does not exist on type 'string | RGB'
palette.red.map(x => x * 2);</code></pre>
<h3>The satisfies Solution</h3>
<pre><code class="language-typescript">const palette = {
  red:   [255, 0, 0],
  green: "#00ff00",
  blue:  [0, 0, 255],
} satisfies Record&lt;Colors, string | RGB&gt;;

// TypeScript KNOWS palette.red is [number,number,number]
palette.red.map(x => x * 2); // Works perfectly
palette.green.toUpperCase();  // Works — still a string

// Misspellings caught at compile time:
const bad = { red: [255,0,0], purpl: "#ff00ff" } satisfies Record&lt;Colors, string | RGB&gt;;
// Error: Object literal may only specify known properties</code></pre>
<h3>Real-World: Type-Safe Route Config</h3>
<pre><code class="language-typescript">type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";
type RouteConfig = { method: HttpMethod; path: string; auth: boolean };

const routes = {
  listUsers:   { method: "GET",    path: "/users",       auth: true  },
  createUser:  { method: "POST",   path: "/users",       auth: true  },
  healthCheck: { method: "GET",    path: "/health",      auth: false },
  deleteUser:  { method: "DELETE", path: "/users/:id",   auth: true  },
} satisfies Record&lt;string, RouteConfig&gt;;

// TypeScript infers literal types
type ListUsersMethod = typeof routes.listUsers.method; // "GET"</code></pre>
<hr/>
<h2>2. Const Type Parameters — Infer Literal Types in Generics</h2>
<p>TypeScript normally widens generic type inference. Pass <code>"hello"</code> to <code>T extends string</code> and T becomes <code>string</code>, not <code>"hello"</code>. Const type parameters fix this at the call site.</p>
<pre><code class="language-typescript">// Without const — T widens to string
function identity&lt;T extends string&gt;(val: T): T { return val; }
const x = identity("hello"); // type is string

// With const — T stays literal
function identityConst&lt;const T extends string&gt;(val: T): T { return val; }
const y = identityConst("hello"); // type is "hello"</code></pre>
<h3>Practical: Type-Safe Event Emitter</h3>
<pre><code class="language-typescript">type EventMap = { click: MouseEvent; keydown: KeyboardEvent; load: Event };

function on&lt;const K extends keyof EventMap&gt;(
  event: K,
  handler: (e: EventMap[K]) => void
): void {
  document.addEventListener(event, handler as EventListener);
}

on("click", (e) => {
  console.log(e.clientX, e.clientY); // TypeScript knows this is MouseEvent
});</code></pre>
<hr/>
<h2>3. Decorator Standard — ECMAScript Stage 3</h2>
<p>TypeScript 5.0 implements the finalized ECMAScript decorator proposal. The old experimental decorators are incompatible with the new standard.</p>
<table>
  <thead><tr><th>Feature</th><th>TypeScript 4.x</th><th>TypeScript 5.x</th></tr></thead>
  <tbody>
    <tr><td>Stage</td><td>Stage 2 (experimental)</td><td>Stage 3 (standard)</td></tr>
    <tr><td>Parameter Decorators</td><td>Supported</td><td>Removed</td></tr>
    <tr><td>Metadata API</td><td>reflect-metadata</td><td>TC39 decorator metadata</td></tr>
    <tr><td>Return value</td><td>Ignored for classes</td><td>Replaces decorated value</td></tr>
  </tbody>
</table>
<pre><code class="language-typescript">function logged(target: Function, context: ClassMethodDecoratorContext) {
  const methodName = String(context.name);
  return function (this: unknown, ...args: unknown[]) {
    console.log(`[${methodName}] called with:`, args);
    const result = target.apply(this, args);
    console.log(`[${methodName}] returned:`, result);
    return result;
  };
}

class UserService {
  @logged
  findById(id: string): { id: string; name: string } {
    return { id, name: "Kashinath" };
  }
}

const svc = new UserService();
svc.findById("u-123");
// [findById] called with: ["u-123"]
// [findById] returned: { id: "u-123", name: "Kashinath" }</code></pre>
<hr/>
<h2>4. Branded Types — Zero-Cost Runtime Validation</h2>
<p>Primitive types like <code>string</code> are structurally equivalent in TypeScript. A <code>UserId</code> and an <code>OrderId</code> are both strings. Branded types add a nominal tag to prevent accidental misuse at zero runtime cost.</p>
<pre><code class="language-typescript">type Brand&lt;T, B&gt; = T & { readonly __brand: B };

type UserId  = Brand&lt;string, "UserId"&gt;;
type OrderId = Brand&lt;string, "OrderId"&gt;;

const UserId  = (id: string): UserId  => id as UserId;
const OrderId = (id: string): OrderId => id as OrderId;

function getUser(id: UserId): { id: UserId; name: string } {
  return { id, name: "Kashinath" };
}

const uid = UserId("u-123");
const oid = OrderId("o-456");

getUser(uid); // Correct
getUser(oid); // Compile error: 'OrderId' not assignable to 'UserId'
getUser("u-raw"); // Compile error: 'string' not assignable to 'UserId'</code></pre>
<hr/>
<h2>5. Template Literal Types</h2>
<pre><code class="language-typescript">type EventName = "click" | "focus" | "blur";
type ListenerName = `on${Capitalize&lt;EventName&gt;}`;
// Result: "onClick" | "onFocus" | "onBlur"

type HttpVerb = "GET" | "POST" | "PUT" | "DELETE";
type Resource = "User" | "Post" | "Comment";
type ApiRoute = `${Lowercase&lt;HttpVerb&gt;}${Resource}`;
// 12 variants: "getUser" | "getPost" | ... | "deleteComment"</code></pre>
<hr/>
<h2>6. Performance Comparison</h2>
<table>
  <thead><tr><th>Project Size</th><th>TS 4.9 Build</th><th>TS 5.0 Build</th><th>Speedup</th></tr></thead>
  <tbody>
    <tr><td>Small (~1k files)</td><td>12s</td><td>9s</td><td>25%</td></tr>
    <tr><td>Medium (~10k files)</td><td>95s</td><td>68s</td><td>28%</td></tr>
    <tr><td>Large (~50k files)</td><td>480s</td><td>310s</td><td>35%</td></tr>
  </tbody>
</table>
<pre><code class="language-json">{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "verbatimModuleSyntax": true,
    "strict": true,
    "exactOptionalPropertyTypes": true,
    "noUncheckedIndexedAccess": true,
    "skipLibCheck": true
  }
}</code></pre>
<blockquote><strong>Pro tip:</strong> Enable one strict flag at a time and fix the errors before moving to the next. This keeps PRs reviewable and avoids a 300-error sea of red.</blockquote>""",

"docker-compose-multi-stage-deep-dive": """<h2>Why Docker Image Size Matters in Production</h2>
<p>A naive Django Docker image built from <code>python:3.12</code> with all build tools included weighs around 1.2 GB. A properly optimised multi-stage image serving the exact same application weighs 78 MB — a 15x reduction meaning 15x faster deploys, 15x less storage on your container registry, and dramatically reduced attack surface.</p>
<p>This guide walks through the complete Docker production playbook: multi-stage builds, BuildKit layer caching, secrets management, health checks, and a production-grade docker-compose.yml that mirrors real industry setups.</p>
<hr/>
<h2>1. Multi-Stage Builds — The Foundation</h2>
<p>Multi-stage builds allow multiple FROM statements in a single Dockerfile. Only the final stage ends up in your shipped image — previous stages are discarded after the build completes.</p>
<pre><code class="language-dockerfile"># BAD — everything in one stage, 1.2GB image
FROM python:3.12
RUN apt-get update &amp;&amp; apt-get install -y gcc libpq-dev build-essential
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "reqpulse.wsgi:application", "--bind", "0.0.0.0:8000"]</code></pre>

<pre><code class="language-dockerfile"># GOOD — multi-stage, 78MB final image
FROM python:3.12-slim AS builder
RUN apt-get update &amp;&amp; apt-get install -y gcc libpq-dev &amp;&amp; rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip &amp;&amp; \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS runtime
RUN apt-get update &amp;&amp; apt-get install -y libpq5 &amp;&amp; rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*.whl
COPY . .
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "reqpulse.wsgi:application", \
     "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]</code></pre>

<h3>Size Comparison</h3>
<table>
  <thead><tr><th>Approach</th><th>Image Size</th><th>Rebuild (code only)</th></tr></thead>
  <tbody>
    <tr><td>Single stage (python:3.12)</td><td>1.21 GB</td><td>82s</td></tr>
    <tr><td>Single stage (slim)</td><td>520 MB</td><td>54s</td></tr>
    <tr><td>Multi-stage (slim)</td><td>78 MB</td><td>8s</td></tr>
    <tr><td>Multi-stage (alpine)</td><td>62 MB</td><td>8s</td></tr>
  </tbody>
</table>
<hr/>
<h2>2. Layer Caching — Maximising Rebuild Speed</h2>
<p>Docker builds each instruction as an immutable layer. The golden rule: put things that change rarely at the top, things that change often at the bottom.</p>
<pre><code class="language-dockerfile"># BAD cache ordering
COPY . .                           # Cache busted every code change
RUN pip install -r requirements.txt   # Re-installs everything each time

# GOOD cache ordering
COPY requirements.txt .            # Only bust cache when requirements change
RUN pip install -r requirements.txt
COPY . .                           # Source change doesn't re-install deps</code></pre>

<h3>BuildKit Cache Mounts (Docker 18.09+)</h3>
<pre><code class="language-dockerfile"># syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --wheel-dir /wheels -r requirements.txt</code></pre>

<pre><code class="language-bash">export DOCKER_BUILDKIT=1</code></pre>
<hr/>
<h2>3. Secrets Management — Never Bake Credentials Into Images</h2>
<blockquote><strong>Security rule:</strong> If your secret ever appears in a Docker layer — even if deleted in the next RUN instruction — it is permanently embedded in the image history and can be extracted with <code>docker image history</code>.</blockquote>
<pre><code class="language-dockerfile"># syntax=docker/dockerfile:1
FROM python:3.12-slim
RUN --mount=type=secret,id=pip_token \
    pip install private-package \
    --extra-index-url "https://token:$(cat /run/secrets/pip_token)@pypi.company.com"</code></pre>

<pre><code class="language-bash">echo "$PYPI_TOKEN" | docker build \
  --secret id=pip_token,src=/dev/stdin \
  -t myapp:latest .</code></pre>
<hr/>
<h2>4. Production docker-compose.yml</h2>
<pre><code class="language-yaml">version: "3.9"

x-django-env: &amp;django-env
  DATABASE_URL: postgres://postgres:secret@db:5432/mydb
  REDIS_URL: redis://redis:6379/0
  SECRET_KEY: ${SECRET_KEY}
  DEBUG: "False"

services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru

  web:
    build:
      context: .
      target: runtime
    restart: unless-stopped
    environment:
      &lt;&lt;: *django-env
    depends_on:
      db:
        condition: service_healthy
    expose:
      - "8000"

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro

volumes:
  postgres_data:</code></pre>
<hr/>
<h2>5. .dockerignore — Critical for Fast Builds</h2>
<pre><code class="language-text">.git/
*.pyc
__pycache__/
.pytest_cache/
.venv/
env/
node_modules/
.env
.env.*
*.log
*.sqlite3
README.md
docs/
.agents/</code></pre>
<p>Without .dockerignore, every <code>COPY . .</code> sends your entire project including .git and node_modules to the Docker daemon — drastically slowing build context transfer on large repositories.</p>
<hr/>
<h2>6. Health Checks and Graceful Shutdown</h2>
<pre><code class="language-python"># health/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    status = 200 if db_ok else 503
    return JsonResponse({"status": "ok" if db_ok else "degraded", "db": db_ok}, status=status)</code></pre>

<blockquote><strong>Key insight:</strong> Always add <code>STOPSIGNAL SIGTERM</code> to your Dockerfile and handle SIGTERM in your application. Kubernetes sends SIGTERM before SIGKILL, giving your app 30 seconds to finish in-flight requests.</blockquote>""",

"system-design-twitter-whatsapp-youtube": """<h2>The System Design Interview Framework</h2>
<p>System design interviews test your ability to break down ambiguous requirements, identify bottlenecks, and make justified trade-offs. Every strong answer follows this structure: <strong>Clarify &rarr; Estimate &rarr; Design &rarr; Deep Dive &rarr; Trade-offs</strong>.</p>
<table>
  <thead><tr><th>Phase</th><th>Duration</th><th>Goal</th></tr></thead>
  <tbody>
    <tr><td>1. Clarify Requirements</td><td>5 min</td><td>Scope the problem: DAU, QPS, features in/out</td></tr>
    <tr><td>2. Capacity Estimation</td><td>5 min</td><td>Storage, bandwidth, read/write ratio</td></tr>
    <tr><td>3. High-Level Design</td><td>10 min</td><td>Components, APIs, data flow</td></tr>
    <tr><td>4. Deep Dive</td><td>15 min</td><td>Pick 2-3 hard problems and solve them</td></tr>
    <tr><td>5. Trade-offs</td><td>5 min</td><td>Justify choices, discuss alternatives</td></tr>
  </tbody>
</table>
<hr/>
<h2>1. Design Twitter's News Feed</h2>
<h3>Scale Numbers</h3>
<pre><code class="language-text">Writes: 5M tweets/day = ~60 QPS (peak 3x = 180 QPS)
Reads:  600M/day      = ~7,000 QPS (peak = 21,000 QPS)
Storage: avg tweet = 280 chars = ~1 KB
         5M * 1 KB = 5 GB/day =&gt; ~1.8 TB/year (text only)
         Images:  ~30% of tweets, avg 500 KB
                  1.5M * 500 KB = 750 GB/day =&gt; CDN required</code></pre>
<h3>Feed Generation: Pull vs Push vs Hybrid</h3>
<table>
  <thead><tr><th>Strategy</th><th>Write Cost</th><th>Read Cost</th><th>Best For</th></tr></thead>
  <tbody>
    <tr><td>Pull (fan-out on read)</td><td>Low</td><td>High — query all followees</td><td>Celebrities (millions of followers)</td></tr>
    <tr><td>Push (fan-out on write)</td><td>High — write to all followers</td><td>Low</td><td>Regular users (&lt;10K followers)</td></tr>
    <tr><td>Hybrid</td><td>Medium</td><td>Low</td><td>Twitter's actual approach</td></tr>
  </tbody>
</table>
<h3>Twitter's Hybrid Approach</h3>
<ol>
  <li>When a tweet is posted, push to all followers who have fewer than 10K followers (regular users).</li>
  <li>For celebrities (10K+ followers), do not pre-push. Fetch their latest tweets at read time and merge.</li>
  <li>Timelines stored in Redis (sorted set by timestamp), capped at 800 tweets.</li>
</ol>
<pre><code class="language-python">@celery_app.task
def fanout_tweet(tweet_id: str, author_id: str):
    tweet = Tweet.objects.get(id=tweet_id)
    followers = Follower.objects.filter(followee_id=author_id).values_list('follower_id', flat=True)

    pipe = redis.pipeline(transaction=False)
    for follower_id in followers:
        if get_follower_count(follower_id) &lt; 10_000:
            timeline_key = f"timeline:{follower_id}"
            pipe.zadd(timeline_key, {tweet_id: tweet.created_at.timestamp()})
            pipe.zremrangebyrank(timeline_key, 0, -801)  # Keep only latest 800
    pipe.execute()</code></pre>
<hr/>
<h2>2. Design WhatsApp Messaging</h2>
<h3>Core Challenges</h3>
<ul>
  <li><strong>Message ordering:</strong> Messages must arrive in order within a conversation</li>
  <li><strong>Delivery guarantees:</strong> At-least-once, exactly-once, or at-most-once?</li>
  <li><strong>Presence:</strong> Online/offline, last seen, typing indicators</li>
  <li><strong>End-to-end encryption:</strong> Server never sees plaintext</li>
</ul>
<h3>Message Delivery States</h3>
<p>WhatsApp uses a <strong>3-state model</strong>: SENT (single tick), DELIVERED (double tick), READ (blue double tick). Each state requires an ACK from the recipient back to the sender.</p>
<pre><code class="language-sql">CREATE TABLE messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id     UUID NOT NULL REFERENCES chats(id),
    sender_id   UUID NOT NULL,
    content     BYTEA NOT NULL,           -- encrypted blob
    seq_num     BIGINT NOT NULL,          -- monotonic per chat
    status      SMALLINT DEFAULT 0,       -- 0=sent, 1=delivered, 2=read
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (chat_id, seq_num)             -- ordering guarantee
);
CREATE INDEX idx_messages_chat_seq ON messages(chat_id, seq_num DESC);</code></pre>
<hr/>
<h2>3. Design YouTube's Video Pipeline</h2>
<h3>The Two Hard Problems</h3>
<ol>
  <li><strong>Upload and transcoding:</strong> A 4K 30-minute video is ~12 GB. Transcode into 8 quality levels (360p through 4K) in parallel.</li>
  <li><strong>Adaptive bitrate streaming:</strong> Serve the right quality based on bandwidth, switching seamlessly mid-stream.</li>
</ol>
<pre><code class="language-text">Client -&gt; Upload Service (resumable chunked upload)
               |
         Raw Video Storage (S3/GCS)
               |
     Transcoding Job Queue (SQS/Kafka)
               |
     Transcoding Workers (FFmpeg, GPU farm)
       /          |          \\
  360p.mp4  720p.mp4  1080p.mp4  ... (8 variants)
               |
    CDN (CloudFront/Akamai)
               |
         Client (HLS/DASH adaptive streaming)</code></pre>
<pre><code class="language-text"># master.m3u8 — tells the player which variants exist
#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
360p/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720
720p/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
1080p/playlist.m3u8</code></pre>
<hr/>
<h2>Key Distributed Systems Concepts</h2>
<table>
  <thead><tr><th>Concept</th><th>What It Solves</th><th>Key Trade-off</th></tr></thead>
  <tbody>
    <tr><td>Consistent Hashing</td><td>Distribute keys across nodes, minimise re-hashing</td><td>Slight uneven distribution without virtual nodes</td></tr>
    <tr><td>CAP Theorem</td><td>Guarantee 2 of: Consistency, Availability, Partition tolerance</td><td>Distributed systems must choose CP or AP</td></tr>
    <tr><td>Write-Ahead Log (WAL)</td><td>Durability: recover from crashes without data loss</td><td>Adds write latency</td></tr>
    <tr><td>Read Replicas</td><td>Scale reads horizontally</td><td>Replication lag, eventual consistency</td></tr>
    <tr><td>Rate Limiting</td><td>Prevent abuse</td><td>Token bucket vs leaky bucket</td></tr>
  </tbody>
</table>
<blockquote><strong>Interview tip:</strong> Don't just say "I'd use Redis for caching." Say "I'd use Redis with a TTL-based eviction policy, accepting eventual consistency in exchange for sub-millisecond read latency — the trade-off is appropriate because feed staleness of a few seconds is acceptable."</blockquote>""",

"python-asyncio-masterclass": """<h2>Why Asyncio Outperforms Threading for I/O-Bound Work</h2>
<p>Python's GIL prevents true CPU parallelism in threads. But for I/O-bound tasks like HTTP requests, database queries, and file reads, the GIL is irrelevant — threads spend most of their time waiting, not executing Python bytecode. Asyncio takes this further: instead of spinning up one thread per connection (expensive — each thread costs ~8MB of stack memory), the event loop multiplexes thousands of concurrent I/O operations on a single OS thread using non-blocking <code>epoll</code>/<code>kqueue</code> system calls.</p>
<table>
  <thead><tr><th>Approach</th><th>10 URLs</th><th>100 URLs</th><th>1,000 URLs</th><th>Memory</th></tr></thead>
  <tbody>
    <tr><td>Synchronous (requests)</td><td>12.4s</td><td>124s</td><td>1,240s</td><td>~50 MB</td></tr>
    <tr><td>Threading (ThreadPoolExecutor)</td><td>1.8s</td><td>6.2s</td><td>68s</td><td>~800 MB</td></tr>
    <tr><td>Asyncio + aiohttp</td><td>0.3s</td><td>0.8s</td><td>4.1s</td><td>~60 MB</td></tr>
  </tbody>
</table>
<hr/>
<h2>1. The Event Loop — How Asyncio Works</h2>
<p>The asyncio event loop is a single-threaded scheduler. When a coroutine hits an <code>await</code> expression on an I/O operation, it suspends and yields control back to the loop. The loop picks up another coroutine and runs it until it also awaits. No OS context switches needed — just Python frame switching.</p>
<pre><code class="language-python">import asyncio

async def fetch_data(name: str, delay: float) -> str:
    print(f"[{name}] Starting...")
    await asyncio.sleep(delay)  # Simulates I/O wait
    print(f"[{name}] Done after {delay}s")
    return f"data from {name}"

async def main():
    # Run 3 coroutines CONCURRENTLY — total time ~1s, not 2.3s
    results = await asyncio.gather(
        fetch_data("API-1", 1.0),
        fetch_data("API-2", 0.8),
        fetch_data("API-3", 0.5),
    )
    print(results)

asyncio.run(main())
# [API-3] Done after 0.5s
# [API-2] Done after 0.8s
# [API-1] Done after 1.0s</code></pre>
<hr/>
<h2>2. Coroutines vs Tasks vs Futures</h2>
<pre><code class="language-python">import asyncio

async def my_coroutine():
    return 42

# Coroutine object — NOT yet scheduled
coro = my_coroutine()

# Task — scheduled to run on the event loop immediately
task = asyncio.create_task(my_coroutine())

async def demonstrate():
    # SEQUENTIAL — each awaits before the next starts
    r1 = await my_coroutine()
    r2 = await my_coroutine()

    # CONCURRENT — both scheduled immediately
    t1 = asyncio.create_task(my_coroutine())
    t2 = asyncio.create_task(my_coroutine())
    r1, r2 = await asyncio.gather(t1, t2)</code></pre>
<hr/>
<h2>3. Production Async Web Scraper</h2>
<pre><code class="language-python">import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncScraper:
    def __init__(self, concurrency: int = 50, timeout: int = 30, max_retries: int = 3):
        self.semaphore = asyncio.Semaphore(concurrency)
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries

    async def fetch_one(
        self, session: aiohttp.ClientSession, url: str, attempt: int = 1
    ) -> Optional[dict]:
        async with self.semaphore:  # Max N concurrent requests
            try:
                async with session.get(url, timeout=self.timeout) as resp:
                    text = await resp.text()
                    return {
                        "url": url,
                        "status": resp.status,
                        "length": len(text),
                        "scraped_at": datetime.utcnow().isoformat(),
                    }
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt &lt; self.max_retries:
                    wait = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
                    logger.warning(f"Retry {attempt}/{self.max_retries} for {url}")
                    await asyncio.sleep(wait)
                    return await self.fetch_one(session, url, attempt + 1)
                return {"url": url, "status": None, "error": str(e)}

    async def scrape_all(self, urls: list[str]) -> list[dict]:
        connector = aiohttp.TCPConnector(limit=100, enable_cleanup_closed=True)
        headers = {"User-Agent": "AsyncScraper/1.0"}
        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            tasks = [self.fetch_one(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if r is not None]


async def main():
    urls = [f"https://httpbin.org/delay/1?n={i}" for i in range(100)]
    scraper = AsyncScraper(concurrency=20, timeout=15)
    results = await scraper.scrape_all(urls)
    print(f"Scraped {len(results)} URLs")
    print(f"Success: {sum(1 for r in results if r.get('status') == 200)}/{len(results)}")

asyncio.run(main())</code></pre>
<hr/>
<h2>4. Asyncio with Django — The Right Way</h2>
<pre><code class="language-python">from django.http import JsonResponse
from asgiref.sync import sync_to_async
import aiohttp, asyncio

get_active_jobs = sync_to_async(
    lambda: list(JobPosting.objects.filter(status='ACTIVE').values('id', 'title'))
)

async def fetch_external_salary(job_title: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.salaries.dev/?q={job_title}") as resp:
            return await resp.json()

async def jobs_with_salary_view(request):
    jobs, salary_data = await asyncio.gather(
        get_active_jobs(),
        fetch_external_salary("Software Engineer"),
    )
    return JsonResponse({"jobs": jobs, "market_salary": salary_data})</code></pre>
<blockquote><strong>Warning:</strong> Django's ORM is synchronous. Never call <code>QuerySet.all()</code> directly inside an <code>async def</code> view — always wrap it with <code>sync_to_async</code>. Django 5.x is adding native async ORM support.</blockquote>""",

"react-19-deep-dive-actions": """<h2>What's New in React 19</h2>
<p>React 19 (stable Q1 2026) ships the most developer-impactful features since React 16 introduced hooks. The theme is <strong>Actions</strong>: a unified pattern for handling async mutations that eliminates the verbose useState + useEffect + loading/error state boilerplate that every React developer has written hundreds of times.</p>
<table>
  <thead><tr><th>Feature</th><th>Before (React 18)</th><th>After (React 19)</th></tr></thead>
  <tbody>
    <tr><td>Form submissions</td><td>useState + useEffect + manual error handling</td><td>Actions with built-in pending/error states</td></tr>
    <tr><td>Optimistic UI</td><td>Manual state + rollback logic</td><td>useOptimistic hook</td></tr>
    <tr><td>Form status</td><td>Prop drilling or Context</td><td>useFormStatus hook</td></tr>
    <tr><td>Memoization</td><td>useMemo + useCallback everywhere</td><td>React Compiler (auto-memoization)</td></tr>
    <tr><td>Refs on function components</td><td>forwardRef wrapper</td><td>ref as regular prop</td></tr>
  </tbody>
</table>
<hr/>
<h2>1. Actions — The End of Form Boilerplate</h2>
<h3>React 18 — The Old Way</h3>
<pre><code class="language-tsx">function UpdateNameForm() {
  const [name, setName] = useState('');
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState&lt;string | null&gt;(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsPending(true);
    setError(null);
    try {
      await updateUserName(name);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsPending(false);
    }
  }

  return (
    &lt;form onSubmit={handleSubmit}&gt;
      &lt;input value={name} onChange={e =&gt; setName(e.target.value)} /&gt;
      {error &amp;&amp; &lt;p className="error"&gt;{error}&lt;/p&gt;}
      &lt;button disabled={isPending}&gt;{isPending ? 'Saving...' : 'Save'}&lt;/button&gt;
    &lt;/form&gt;
  );
}</code></pre>
<h3>React 19 — Actions</h3>
<pre><code class="language-tsx">import { useActionState } from 'react';

async function updateNameAction(prevState: unknown, formData: FormData) {
  const name = formData.get('name') as string;
  if (!name || name.length &lt; 2) {
    return { error: 'Name must be at least 2 characters' };
  }
  await updateUserName(name);
  return { success: true };
}

function UpdateNameForm() {
  const [state, submitAction, isPending] = useActionState(updateNameAction, null);

  return (
    &lt;form action={submitAction}&gt;
      &lt;input name="name" /&gt;
      {state?.error &amp;&amp; &lt;p className="error"&gt;{state.error}&lt;/p&gt;}
      {state?.success &amp;&amp; &lt;p className="success"&gt;Name updated!&lt;/p&gt;}
      &lt;SubmitButton /&gt;
    &lt;/form&gt;
  );
}</code></pre>
<hr/>
<h2>2. useFormStatus — Smart Submit Buttons</h2>
<pre><code class="language-tsx">import { useFormStatus } from 'react-dom';

function SubmitButton({ label = 'Submit' }: { label?: string }) {
  const { pending } = useFormStatus();

  return (
    &lt;button type="submit" disabled={pending} aria-busy={pending}&gt;
      {pending ? '&lt;span className="spinner" /&gt; Saving...' : label}
    &lt;/button&gt;
  );
}

// Reuse across any form — automatically picks up the right pending state
function CreatePostForm() {
  const [state, action] = useActionState(createPostAction, null);
  return (
    &lt;form action={action}&gt;
      &lt;input name="title" placeholder="Post title" /&gt;
      &lt;textarea name="body" placeholder="Content..." /&gt;
      &lt;SubmitButton label="Publish Post" /&gt;
    &lt;/form&gt;
  );
}</code></pre>
<hr/>
<h2>3. useOptimistic — Instant UI Feedback</h2>
<pre><code class="language-tsx">import { useOptimistic, useActionState } from 'react';

type Message = { id: string; text: string; status: 'sent' | 'pending' };

function ChatThread({ initialMessages }: { initialMessages: Message[] }) {
  const [optimisticMessages, addOptimisticMessage] = useOptimistic&lt;Message[], string&gt;(
    initialMessages,
    (currentMessages, newText) =&gt; [
      ...currentMessages,
      { id: Date.now().toString(), text: newText, status: 'pending' },
    ]
  );

  async function sendMessageAction(_: unknown, formData: FormData) {
    const text = formData.get('text') as string;
    addOptimisticMessage(text);  // Update UI immediately
    await sendMessage(text);     // Then actually send
  }

  const [, action] = useActionState(sendMessageAction, null);

  return (
    &lt;&gt;
      &lt;div className="messages"&gt;
        {optimisticMessages.map(msg =&gt; (
          &lt;div key={msg.id} style={{ opacity: msg.status === 'pending' ? 0.5 : 1 }}&gt;
            {msg.text}
          &lt;/div&gt;
        ))}
      &lt;/div&gt;
      &lt;form action={action}&gt;
        &lt;input name="text" autoFocus /&gt;
        &lt;SubmitButton label="Send" /&gt;
      &lt;/form&gt;
    &lt;/&gt;
  );
}</code></pre>
<hr/>
<h2>4. React Compiler — Automatic Memoization</h2>
<pre><code class="language-tsx">// Before Compiler — manual memoization
const ExpensiveList = React.memo(function ExpensiveList({ items, onSelect }) {
  const sortedItems = useMemo(
    () =&gt; [...items].sort((a, b) =&gt; a.name.localeCompare(b.name)),
    [items]
  );
  const handleSelect = useCallback((id: string) =&gt; onSelect(id), [onSelect]);
  return sortedItems.map(item =&gt; &lt;Item key={item.id} item={item} onSelect={handleSelect} /&gt;);
});

// After Compiler — write normal code
function ExpensiveList({ items, onSelect }) {
  const sortedItems = [...items].sort((a, b) =&gt; a.name.localeCompare(b.name));
  return sortedItems.map(item =&gt; (
    &lt;Item key={item.id} item={item} onSelect={() =&gt; onSelect(item.id)} /&gt;
  ));
}</code></pre>
<blockquote><strong>Important:</strong> React Compiler requires components to follow the Rules of React (pure renders, no mutation of props/state). Components that violate the rules are automatically skipped by the compiler.</blockquote>
<hr/>
<h2>5. Refs as Regular Props</h2>
<pre><code class="language-tsx">// React 18 — required forwardRef wrapper
const Input = React.forwardRef&lt;HTMLInputElement, { label: string }&gt;(
  function Input({ label }, ref) {
    return &lt;input ref={ref} aria-label={label} /&gt;;
  }
);

// React 19 — ref is just a prop
function Input({ label, ref }: { label: string; ref: React.Ref&lt;HTMLInputElement&gt; }) {
  return &lt;input ref={ref} aria-label={label} /&gt;;
}

const inputRef = useRef&lt;HTMLInputElement&gt;(null);
&lt;Input label="Username" ref={inputRef} /&gt;</code></pre>""",

"postgresql-advanced-patterns-jsonb": """<h2>PostgreSQL as Your Document Database</h2>
<p>PostgreSQL's JSONB type stores JSON as a decomposed binary format that supports fast key-value lookups, nested queries, and full index coverage. Combined with GIN indexes, JSONB queries can be faster than equivalent MongoDB queries because PostgreSQL can plan the query in context of joins and other relational operations.</p>
<p>This article covers the advanced patterns that power Shopify's product metadata system, GitLab's CI configuration storage, and Stripe's event payload indexing.</p>
<hr/>
<h2>1. JSONB Fundamentals — Operators and Functions</h2>
<pre><code class="language-sql">CREATE TABLE products (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    price       NUMERIC(10,2) NOT NULL,
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO products (name, price, metadata) VALUES
('MacBook Pro M4', 1999.00, '{"brand":"Apple","specs":{"ram":16,"storage":512},"tags":["laptop","productivity"],"in_stock":true}'),
('Dell XPS 15',    1599.00, '{"brand":"Dell","specs":{"ram":32,"storage":1024},"tags":["laptop","workstation"],"in_stock":false}');</code></pre>

<h3>JSONB Operators</h3>
<pre><code class="language-sql">-- Arrow operators
SELECT metadata -&gt; 'brand' FROM products;          -- Returns JSON: "Apple"
SELECT metadata -&gt;&gt; 'brand' FROM products;         -- Returns TEXT: Apple
SELECT metadata -&gt; 'specs' -&gt;&gt; 'ram' FROM products; -- Nested: 16

-- Containment operators (use GIN index!)
SELECT * FROM products WHERE metadata @&gt; '{"brand": "Apple"}';
SELECT * FROM products WHERE metadata @&gt; '{"tags": ["laptop"]}';
SELECT * FROM products WHERE metadata @&gt; '{"specs": {"ram": 16}}';

-- Key existence
SELECT * FROM products WHERE metadata ? 'brand';
SELECT * FROM products WHERE metadata ?| ARRAY['brand', 'sku'];  -- ANY key
SELECT * FROM products WHERE metadata ?&amp; ARRAY['brand', 'specs']; -- ALL keys</code></pre>
<hr/>
<h2>2. GIN Indexes for JSONB</h2>
<pre><code class="language-sql">-- Default GIN index — supports @&gt;, ?, ?|, ?&amp; operators
CREATE INDEX idx_products_metadata ON products USING GIN (metadata);

-- jsonb_path_ops — smaller, faster for @&gt; containment only
CREATE INDEX idx_products_meta_path ON products USING GIN (metadata jsonb_path_ops);

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM products WHERE metadata @&gt; '{"brand": "Apple"}';
-- With GIN: Index Scan, actual time=0.02ms
-- Without:  Seq Scan, actual time=120ms on 1M rows</code></pre>
<hr/>
<h2>3. Partial Indexes — Index Only What You Query</h2>
<p>A partial index only includes rows matching a WHERE clause, making it dramatically smaller and faster.</p>
<pre><code class="language-sql">-- Full index wastes space on inactive records
CREATE INDEX idx_orders_status ON orders(status);

-- Partial index — only indexes rows you actually query
CREATE INDEX idx_orders_active ON orders(created_at DESC)
    WHERE status = 'ACTIVE' AND deadline &gt; NOW();

-- Real-world size comparison (1M order table, 10% active):
-- Full index:    ~42 MB
-- Partial index: ~4.2 MB (10x smaller, faster cache utilisation)</code></pre>

<h3>Expression Indexes</h3>
<pre><code class="language-sql">-- Case-insensitive email search
CREATE INDEX idx_users_email_lower ON users(LOWER(email));
SELECT * FROM users WHERE LOWER(email) = 'user@gmail.com';  -- Uses index

-- Index on JSONB computed value
CREATE INDEX idx_products_ram ON products((CAST(metadata -&gt;&gt; 'specs' AS JSONB) -&gt;&gt; 'ram'));
SELECT * FROM products WHERE (metadata -&gt; 'specs' -&gt;&gt; 'ram')::INT &gt;= 16;</code></pre>
<hr/>
<h2>4. Full-Text Search with tsvector and tsquery</h2>
<pre><code class="language-sql">-- Generated tsvector column for full-text search
ALTER TABLE products ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
        to_tsvector('english',
            coalesce(name, '') || ' ' ||
            coalesce(metadata -&gt;&gt; 'brand', '')
        )
    ) STORED;

CREATE INDEX idx_products_fts ON products USING GIN(search_vector);

-- Full-text search with ranking and highlighting
SELECT
    name,
    price,
    ts_rank(search_vector, query) AS rank,
    ts_headline('english', name, query, 'StartSel=&lt;b&gt;, StopSel=&lt;/b&gt;') AS highlighted
FROM
    products,
    to_tsquery('english', 'MacBook &amp; Pro') query
WHERE
    search_vector @@ query
ORDER BY rank DESC;</code></pre>

<h3>Weighted Search</h3>
<pre><code class="language-sql">-- Assign weights: A (title), B (description), C (tags)
UPDATE products SET search_vector =
    setweight(to_tsvector('english', name), 'A') ||
    setweight(to_tsvector('english', coalesce(metadata -&gt;&gt; 'description', '')), 'B') ||
    setweight(to_tsvector('english', coalesce(metadata -&gt;&gt; 'tags', '')::text), 'C');</code></pre>
<hr/>
<h2>5. Covering Indexes — Eliminate Heap Fetches</h2>
<pre><code class="language-sql">-- Regular index: still needs heap fetch for SELECT columns
CREATE INDEX idx_orders_user ON orders(user_id);

-- Covering index (INCLUDE): all needed columns in the index leaf
CREATE INDEX idx_orders_user_covering ON orders(user_id)
    INCLUDE (id, status, created_at);
-- Plan: Index Only Scan (no heap fetch!) — 3-10x faster for cached data</code></pre>
<blockquote><strong>Rule of thumb:</strong> Add INCLUDE only for columns that appear in SELECT but not in WHERE/ORDER BY. Too many included columns negate the size benefits.</blockquote>""",

"kubernetes-for-developers-explained": """<h2>Kubernetes in Plain English</h2>
<p>Kubernetes (K8s) takes your Docker containers and decides where to run them, restarts them if they crash, scales them up when traffic increases, and routes traffic to the right containers.</p>
<table>
  <thead><tr><th>Object</th><th>What It Does</th><th>Analogy</th></tr></thead>
  <tbody>
    <tr><td>Pod</td><td>Runs one or more containers together</td><td>A single process group</td></tr>
    <tr><td>Deployment</td><td>Manages replicas of Pods, handles rolling updates</td><td>A supervisor managing workers</td></tr>
    <tr><td>Service</td><td>Stable network endpoint for a set of Pods</td><td>A load balancer / DNS name</td></tr>
    <tr><td>Ingress</td><td>HTTP/HTTPS routing from external traffic to Services</td><td>An Nginx reverse proxy</td></tr>
    <tr><td>ConfigMap</td><td>Non-secret configuration as key-value pairs</td><td>Environment variables file</td></tr>
    <tr><td>Secret</td><td>Sensitive data (base64-encoded)</td><td>Encrypted .env file</td></tr>
  </tbody>
</table>
<hr/>
<h2>1. Deploy Django to Kubernetes</h2>
<h3>ConfigMap — Application Settings</h3>
<pre><code class="language-yaml">apiVersion: v1
kind: ConfigMap
metadata:
  name: django-config
  namespace: production
data:
  DJANGO_SETTINGS_MODULE: "reqpulse.settings"
  ALLOWED_HOSTS: "kashiiupdatez.online"
  DEBUG: "False"
  DATABASE_HOST: "postgres-service"
  REDIS_URL: "redis://redis-service:6379/0"</code></pre>

<h3>Deployment — Django App with Rolling Updates</h3>
<pre><code class="language-yaml">apiVersion: apps/v1
kind: Deployment
metadata:
  name: django-web
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: django-web
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: django-web
    spec:
      containers:
        - name: django
          image: ghcr.io/kashichavan/kashii-updatez:latest
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: django-config
            - secretRef:
                name: django-secrets
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /health/
              port: 8000
            initialDelaySeconds: 15
          livenessProbe:
            httpGet:
              path: /health/
              port: 8000
            initialDelaySeconds: 30
      initContainers:
        - name: migrate
          image: ghcr.io/kashichavan/kashii-updatez:latest
          command: ["python", "manage.py", "migrate", "--noinput"]
          envFrom:
            - configMapRef:
                name: django-config
            - secretRef:
                name: django-secrets</code></pre>

<h3>Ingress — External HTTP Routing with TLS</h3>
<pre><code class="language-yaml">apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kashii-ingress
  namespace: production
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - kashiiupdatez.online
      secretName: kashii-tls-cert
  rules:
    - host: kashiiupdatez.online
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: django-service
                port:
                  number: 80</code></pre>
<hr/>
<h2>2. Horizontal Pod Autoscaler</h2>
<pre><code class="language-yaml">apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: django-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: django-web
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70</code></pre>
<hr/>
<h2>3. Essential kubectl Commands</h2>
<pre><code class="language-bash">kubectl apply -f k8s/                      # Apply all YAML in directory
kubectl set image deployment/django-web django=ghcr.io/kashichavan/kashii:v2.1.0

kubectl get pods -n production             # List pods
kubectl describe pod django-web-abc123     # Detailed pod info
kubectl logs django-web-abc123 --follow    # Stream logs
kubectl exec -it django-web-abc123 -- bash # Shell into pod

kubectl rollout history deployment/django-web
kubectl rollout undo deployment/django-web
kubectl scale deployment django-web --replicas=5</code></pre>
<hr/>
<h2>4. Packaging with Helm</h2>
<pre><code class="language-bash">helm create kashii-chart   # Generates scaffold</code></pre>

<pre><code class="language-yaml"># values.yaml
image:
  repository: ghcr.io/kashichavan/kashii-updatez
  tag: "latest"
replicaCount: 3
ingress:
  enabled: true
  host: kashiiupdatez.online
  tls: true
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"</code></pre>

<pre><code class="language-bash">helm upgrade --install kashii ./kashii-chart \
  --namespace production \
  --set image.tag=$(git rev-parse --short HEAD)

helm rollback kashii 2   # Roll back to revision 2</code></pre>""",

"leetcode-75-patterns-two-pointers": """<h2>The Pattern-Based Approach to LeetCode</h2>
<p>There are ~3,000 LeetCode problems. You cannot memorise them all. But there are only ~10 core patterns that power the majority of solutions. Once you internalize each pattern, you can solve novel problems you have never seen before.</p>
<hr/>
<h2>Pattern 1: Two Pointers</h2>
<p><strong>When to use:</strong> Sorted input, find a pair/triplet that satisfies a condition. Nested loops would be O(n^2) — two pointers brings it to O(n).</p>
<h3>Problem: Two Sum II (Sorted Input)</h3>
<pre><code class="language-python">def two_sum_sorted(numbers: list[int], target: int) -> list[int]:
    # Time: O(n), Space: O(1)
    left, right = 0, len(numbers) - 1

    while left &lt; right:
        current_sum = numbers[left] + numbers[right]
        if current_sum == target:
            return [left + 1, right + 1]   # 1-indexed
        elif current_sum &lt; target:
            left += 1
        else:
            right -= 1

    return []

print(two_sum_sorted([2, 7, 11, 15], 9))   # [1, 2]
print(two_sum_sorted([2, 3, 4], 6))         # [1, 3]</code></pre>

<h3>Problem: 3Sum</h3>
<pre><code class="language-python">def three_sum(nums: list[int]) -> list[list[int]]:
    # Time: O(n^2), Space: O(1) excluding output
    nums.sort()
    result = []

    for i in range(len(nums) - 2):
        if i &gt; 0 and nums[i] == nums[i - 1]:
            continue
        left, right = i + 1, len(nums) - 1
        while left &lt; right:
            total = nums[i] + nums[left] + nums[right]
            if total == 0:
                result.append([nums[i], nums[left], nums[right]])
                while left &lt; right and nums[left] == nums[left + 1]: left += 1
                while left &lt; right and nums[right] == nums[right - 1]: right -= 1
                left += 1; right -= 1
            elif total &lt; 0:
                left += 1
            else:
                right -= 1

    return result

print(three_sum([-1, 0, 1, 2, -1, -4]))  # [[-1,-1,2],[-1,0,1]]</code></pre>
<hr/>
<h2>Pattern 2: Sliding Window</h2>
<table>
  <thead><tr><th>Variant</th><th>Window Size</th><th>Expand When</th><th>Shrink When</th></tr></thead>
  <tbody>
    <tr><td>Fixed window</td><td>Exactly k</td><td>Always add right</td><td>When window &gt; k</td></tr>
    <tr><td>Variable (max)</td><td>Variable</td><td>Always add right</td><td>When constraint violated</td></tr>
    <tr><td>Variable (min)</td><td>Variable</td><td>Always add right</td><td>While constraint satisfied</td></tr>
  </tbody>
</table>

<h3>Problem: Longest Substring Without Repeating Characters</h3>
<pre><code class="language-python">def length_of_longest_substring(s: str) -> int:
    # Time: O(n), Space: O(min(m,n))
    char_index: dict[str, int] = {}
    max_length = 0
    left = 0

    for right, char in enumerate(s):
        if char in char_index and char_index[char] &gt;= left:
            left = char_index[char] + 1
        char_index[char] = right
        max_length = max(max_length, right - left + 1)

    return max_length

print(length_of_longest_substring("abcabcbb"))  # 3
print(length_of_longest_substring("pwwkew"))    # 3</code></pre>

<h3>Problem: Minimum Window Substring (Hard)</h3>
<pre><code class="language-python">from collections import Counter

def min_window(s: str, t: str) -> str:
    # Time: O(|s| + |t|), Space: O(|t|)
    if not t or not s:
        return ""

    need = Counter(t)
    missing = len(t)
    best = ""
    left = 0

    for right, char in enumerate(s):
        if need[char] &gt; 0:
            missing -= 1
        need[char] -= 1

        while missing == 0:
            window = s[left:right + 1]
            if not best or len(window) &lt; len(best):
                best = window
            left_char = s[left]
            need[left_char] += 1
            if need[left_char] &gt; 0:
                missing += 1
            left += 1

    return best

print(min_window("ADOBECODEBANC", "ABC"))  # "BANC"</code></pre>
<hr/>
<h2>Pattern 3: Binary Search on Answer</h2>
<pre><code class="language-python">import math

def min_eating_speed(piles: list[int], h: int) -> int:
    # Find minimum k bananas/hour to eat all piles within h hours. | Time: O(n log m) where m = max(piles), Space: O(1)
    def can_finish(speed: int) -> bool:
        return sum(math.ceil(p / speed) for p in piles) &lt;= h

    left, right = 1, max(piles)

    while left &lt; right:
        mid = (left + right) // 2
        if can_finish(mid):
            right = mid
        else:
            left = mid + 1

    return left

print(min_eating_speed([3, 6, 7, 11], 8))       # 4
print(min_eating_speed([30, 11, 23, 4, 20], 5)) # 30</code></pre>
<hr/>
<h2>Pattern 4: Prefix Sum</h2>
<pre><code class="language-python">def subarray_sum_equals_k(nums: list[int], k: int) -> int:
    # Count subarrays with sum = k. | Key insight: if prefix[j] - prefix[i] = k, subarray i..j sums to k | Time: O(n), Space: O(n)
    count = 0
    prefix_sum = 0
    seen: dict[int, int] = {0: 1}

    for num in nums:
        prefix_sum += num
        count += seen.get(prefix_sum - k, 0)
        seen[prefix_sum] = seen.get(prefix_sum, 0) + 1

    return count

print(subarray_sum_equals_k([1, 1, 1], 2))           # 2
print(subarray_sum_equals_k([1, 2, 3, -3, 3], 3))    # 3</code></pre>
<hr/>
<h2>Time Complexity Quick Reference</h2>
<table>
  <thead><tr><th>Pattern</th><th>Time</th><th>Space</th><th>Typical Problems</th></tr></thead>
  <tbody>
    <tr><td>Two Pointers</td><td>O(n)</td><td>O(1)</td><td>Sorted array sum, palindrome check</td></tr>
    <tr><td>Sliding Window</td><td>O(n)</td><td>O(k)</td><td>Longest substring, max sum subarray</td></tr>
    <tr><td>Binary Search</td><td>O(log n)</td><td>O(1)</td><td>Sorted search, rotated array, optimise</td></tr>
    <tr><td>Prefix Sum</td><td>O(n)</td><td>O(n)</td><td>Subarray sum, range sum query</td></tr>
  </tbody>
</table>""",

"saas-stripe-django-subscriptions": """<h2>The Stripe Subscription Lifecycle</h2>
<p>Most Stripe integration bugs come from misunderstanding the subscription lifecycle. Before writing a single line of code, understand the states a Stripe subscription moves through.</p>
<pre><code class="language-text">trialing -&gt; active -&gt; (payment fails) -&gt; past_due -&gt; (still failing) -&gt; canceled
                                               |
                                               +-- (payment recovers) -&gt; active</code></pre>
<table>
  <thead><tr><th>Status</th><th>Access Granted?</th><th>Charge Attempted?</th></tr></thead>
  <tbody>
    <tr><td>trialing</td><td>Yes</td><td>No</td></tr>
    <tr><td>active</td><td>Yes</td><td>Yes — succeeded</td></tr>
    <tr><td>past_due</td><td>Grace period</td><td>Yes — failed, retrying</td></tr>
    <tr><td>canceled</td><td>No</td><td>No</td></tr>
  </tbody>
</table>
<hr/>
<h2>1. Django Models — Tracking Subscriptions</h2>
<pre><code class="language-python">from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Plan(models.Model):
    TIER_CHOICES = [('FREE', 'Free'), ('PRO', 'Pro'), ('ENTERPRISE', 'Enterprise')]
    name             = models.CharField(max_length=50)
    tier             = models.CharField(max_length=20, choices=TIER_CHOICES)
    stripe_price_id  = models.CharField(max_length=100, unique=True)
    price_monthly    = models.DecimalField(max_digits=8, decimal_places=2)
    features         = models.JSONField(default=dict)

class Subscription(models.Model):
    STATUS_CHOICES = [
        ('trialing', 'Trialing'), ('active', 'Active'),
        ('past_due', 'Past Due'), ('canceled', 'Canceled'),
    ]
    user                   = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan                   = models.ForeignKey(Plan, on_delete=models.PROTECT)
    stripe_customer_id     = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    status                 = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trialing')
    current_period_end     = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end   = models.BooleanField(default=False)

    @property
    def is_active(self) -> bool:
        return self.status in ('active', 'trialing')</code></pre>
<hr/>
<h2>2. Creating a Stripe Checkout Session</h2>
<pre><code class="language-python">import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
@require_POST
def create_checkout_session(request):
    plan_id = request.POST.get('plan_id')
    plan = Plan.objects.get(id=plan_id, is_active=True)

    sub, _ = Subscription.objects.get_or_create(
        user=request.user,
        defaults={'plan': Plan.objects.get(tier='FREE')}
    )

    if not sub.stripe_customer_id:
        customer = stripe.Customer.create(
            email=request.user.email,
            metadata={'django_user_id': request.user.id}
        )
        sub.stripe_customer_id = customer.id
        sub.save(update_fields=['stripe_customer_id'])

    session = stripe.checkout.Session.create(
        customer=sub.stripe_customer_id,
        payment_method_types=['card'],
        line_items=[{'price': plan.stripe_price_id, 'quantity': 1}],
        mode='subscription',
        subscription_data={'trial_period_days': 14},
        success_url=settings.DOMAIN + '/billing/success/?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=settings.DOMAIN + '/pricing/',
    )

    return JsonResponse({'checkout_url': session.url})</code></pre>
<hr/>
<h2>3. Webhook Handler — The Critical Part</h2>
<blockquote><strong>Never trust frontend callbacks to update subscription status.</strong> A user could close the browser, the callback could fail, or a clever user could fake it. Always use Stripe webhooks to update your database.</blockquote>
<pre><code class="language-python">from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    event_type = event['type']
    data = event['data']['object']

    if event_type in ('customer.subscription.created', 'customer.subscription.updated'):
        _sync_subscription(data)
    elif event_type == 'customer.subscription.deleted':
        _cancel_subscription(data)

    return HttpResponse(status=200)


def _sync_subscription(stripe_sub: dict) -> None:
    from datetime import datetime
    from django.utils.timezone import make_aware

    customer_id = stripe_sub['customer']
    try:
        sub = Subscription.objects.get(stripe_customer_id=customer_id)
    except Subscription.DoesNotExist:
        logger.error(f"No subscription for customer {customer_id}")
        return

    price_id = stripe_sub['items']['data'][0]['price']['id']
    try:
        plan = Plan.objects.get(stripe_price_id=price_id)
    except Plan.DoesNotExist:
        return

    sub.stripe_subscription_id = stripe_sub['id']
    sub.plan = plan
    sub.status = stripe_sub['status']
    sub.cancel_at_period_end = stripe_sub['cancel_at_period_end']
    if stripe_sub.get('current_period_end'):
        sub.current_period_end = make_aware(
            datetime.fromtimestamp(stripe_sub['current_period_end'])
        )
    sub.save()
    logger.info(f"Synced subscription for {sub.user.email}: {sub.status}")</code></pre>
<hr/>
<h2>4. Proration — Upgrading Plans Mid-Cycle</h2>
<pre><code class="language-python">@login_required
@require_POST
def upgrade_plan(request):
    new_plan = Plan.objects.get(id=request.POST.get('plan_id'))
    sub = request.user.subscription

    stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
    current_item_id = stripe_sub['items']['data'][0]['id']

    stripe.Subscription.modify(
        sub.stripe_subscription_id,
        items=[{'id': current_item_id, 'price': new_plan.stripe_price_id}],
        proration_behavior='create_prorations',
    )

    sub.plan = new_plan
    sub.save(update_fields=['plan'])
    return JsonResponse({'success': True, 'new_plan': new_plan.name})</code></pre>
<hr/>
<h2>5. Customer Portal — Self-Service Billing</h2>
<pre><code class="language-python">@login_required
def billing_portal(request):
    sub = request.user.subscription
    portal_session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=settings.DOMAIN + '/dashboard/',
    )
    return redirect(portal_session.url)</code></pre>
<p>The Stripe Customer Portal lets users update payment methods, download invoices, upgrade/downgrade plans, and cancel subscriptions — all hosted by Stripe with PCI compliance built in.</p>""",

"git-advanced-workflows-rebase": """<h2>Git Internals — How Git Actually Stores Data</h2>
<p>Understanding Git's data model is the key to never being afraid of any Git command. Git stores everything as objects in a content-addressable store. There are 4 object types:</p>
<table>
  <thead><tr><th>Object</th><th>Content</th></tr></thead>
  <tbody>
    <tr><td>blob</td><td>File contents (no filename)</td></tr>
    <tr><td>tree</td><td>Directory listing (filenames + blob SHAs)</td></tr>
    <tr><td>commit</td><td>tree SHA + parent SHA + author + message</td></tr>
    <tr><td>tag</td><td>commit SHA + tagger + message</td></tr>
  </tbody>
</table>
<p>A branch is just a file containing a commit SHA. <code>git checkout main</code> makes HEAD point to the main branch file. Git is beautifully simple at its core.</p>
<pre><code class="language-bash">cat .git/HEAD               # ref: refs/heads/main
cat .git/refs/heads/main    # 9a1bc3d4e5f6...
git cat-file -p 9a1bc3      # content of any object by SHA</code></pre>
<hr/>
<h2>1. Interactive Rebase — Sculpting Perfect Commit Histories</h2>
<p>Interactive rebase (<code>git rebase -i</code>) lets you rewrite the commit history of your branch before merging. At companies like Google and Meta, clean commit histories are enforced — each commit should be a logical unit that passes tests.</p>
<pre><code class="language-bash">git log --oneline main..feature/payment
# f3c2a1b WIP checkpoint
# 9d8e7c6 fix typo in variable name
# 4b5a3d2 add tests
# 7e6f5a4 Add Stripe webhook handler
# 2c3d4e5 Add Subscription model
# 1a2b3c4 Add billing app scaffold

git rebase -i main   # Opens editor</code></pre>

<pre><code class="language-text"># In editor
pick 1a2b3c4 Add billing app scaffold
pick 2c3d4e5 Add Subscription model
pick 7e6f5a4 Add Stripe webhook handler
squash 4b5a3d2 add tests       # Merge into previous commit
squash 9d8e7c6 fix typo        # Merge into previous commit
drop f3c2a1b WIP checkpoint    # Discard this commit</code></pre>

<h3>Available Actions</h3>
<table>
  <thead><tr><th>Action</th><th>Short</th><th>What It Does</th></tr></thead>
  <tbody>
    <tr><td>pick</td><td>p</td><td>Keep commit as-is</td></tr>
    <tr><td>reword</td><td>r</td><td>Keep commit, edit message</td></tr>
    <tr><td>edit</td><td>e</td><td>Pause to amend commit</td></tr>
    <tr><td>squash</td><td>s</td><td>Merge into previous, edit combined message</td></tr>
    <tr><td>fixup</td><td>f</td><td>Merge into previous, discard this message</td></tr>
    <tr><td>drop</td><td>d</td><td>Delete commit entirely</td></tr>
  </tbody>
</table>
<blockquote><strong>Golden rule:</strong> Never rebase commits that have been pushed to a shared branch. Rebasing rewrites SHAs, so anyone who based work on your original commits will have diverged histories.</blockquote>
<hr/>
<h2>2. git bisect — Binary Search for Bugs</h2>
<p><code>git bisect</code> uses binary search to find the exact commit that introduced a bug. With 10,000 commits, bisect finds the culprit in at most 14 steps.</p>
<pre><code class="language-bash">git bisect start
git bisect bad                # Current commit has the bug
git bisect good v2.0.0        # This version was fine

# Git checks out midpoint — test your app, then:
git bisect bad   # Bug present
git bisect good  # Bug not present

# Repeat until Git prints: "abc1234 is the first bad commit"
git bisect reset  # End bisect</code></pre>

<h3>Automated Bisect</h3>
<pre><code class="language-bash">git bisect start
git bisect bad HEAD
git bisect good v2.0.0

# Let git run tests automatically — exit 0 = good, non-zero = bad
git bisect run python -m pytest billing/tests/test_webhook.py -x -q</code></pre>
<hr/>
<h2>3. git cherry-pick — Surgical Code Transplants</h2>
<p>Cherry-pick copies the diff from one commit and applies it to another branch. Use it to backport a bug fix to a release branch without merging the entire feature.</p>
<pre><code class="language-bash">git checkout release/2.x
git cherry-pick abc1234           # Apply single commit
git cherry-pick abc1234..def5678  # Apply range (exclusive..inclusive)
git cherry-pick -n abc1234        # Stage changes without committing
git cherry-pick --edit abc1234    # Apply and edit commit message

# Conflict resolution
git cherry-pick abc1234
# CONFLICT! Edit the files to resolve...
git add billing/views.py
git cherry-pick --continue    # Finish
# OR
git cherry-pick --abort       # Cancel</code></pre>
<hr/>
<h2>4. git worktree — Parallel Feature Development</h2>
<p>Normally, switching branches interrupts your current work. <code>git worktree</code> lets you check out multiple branches simultaneously in separate directories.</p>
<pre><code class="language-bash"># Add a second worktree for a hotfix
git worktree add ../kashii-hotfix hotfix/payment-crash
cd ../kashii-hotfix
# Fix the bug, run tests, push — without touching your feature branch

git worktree list
# /Users/kashinath/Desktop/updatezbykashi  (main)
# /Users/kashinath/Desktop/kashii-hotfix   (hotfix/payment-crash)

git worktree remove ../kashii-hotfix</code></pre>
<hr/>
<h2>5. When to Use Each Tool</h2>
<table>
  <thead><tr><th>Scenario</th><th>Tool</th></tr></thead>
  <tbody>
    <tr><td>Clean up messy commits before PR</td><td>Interactive rebase</td></tr>
    <tr><td>Combine 5 WIP commits into 1</td><td>git rebase -i + squash</td></tr>
    <tr><td>"Something broke 3 weeks ago, which commit?"</td><td>git bisect</td></tr>
    <tr><td>Backport fix to release branch</td><td>git cherry-pick</td></tr>
    <tr><td>Work on hotfix while mid-feature</td><td>git worktree</td></tr>
    <tr><td>Undo last commit (keep changes staged)</td><td>git reset --soft HEAD~1</td></tr>
    <tr><td>Undo pushed commit safely</td><td>git revert HEAD</td></tr>
  </tbody>
</table>""",
}


class Command(BaseCommand):
    help = "Seed 10 deeply detailed Medium-style blog articles"

    def handle(self, *args, **options):
        self.stdout.write("Starting deep blog seed...")

        for idx, post_data in enumerate(DEEP_POSTS):
            cat_name = post_data["category_name"]
            # Try exact match first, then partial
            category = (
                Category.objects.filter(name__icontains=cat_name).first() or
                Category.objects.first()
            )

            content = DEEP_CONTENT.get(post_data["slug"], post_data.get("content", "<p>Content coming soon.</p>"))

            post, created = BlogPost.objects.update_or_create(
                slug=post_data["slug"],
                defaults={
                    "title": post_data["title"],
                    "excerpt": post_data["excerpt"],
                    "content": content,
                    "category": category,
                    "cover_image_url": post_data["cover_image_url"],
                    "author_name": "Kashinath Chavan",
                    "author_title": "Founder & Software Engineer",
                    "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
                    "read_time_minutes": post_data.get("read_time_minutes", 12),
                    "is_published": True,
                    "is_featured": post_data.get("is_featured", False),
                    "views_count": post_data.get("views_count", 1500),
                    "likes_count": post_data.get("likes_count", 200),
                    "published_at": timezone.now() - timedelta(days=idx + 1),
                },
            )

            for t_name in [t.strip() for t in post_data.get("tags", "").split(",") if t.strip()]:
                t_slug = slugify(t_name)
                if t_slug:
                    tag_obj, _ = Tag.objects.get_or_create(slug=t_slug, defaults={"name": t_name.title()})
                    post.tags.add(tag_obj)

            action = "Created" if created else "Updated"
            words = len(content.split())
            self.stdout.write(self.style.SUCCESS(f"  {action}: {post.title[:60]} ({words} words)"))

        self.stdout.write(self.style.SUCCESS(f"\nDone! {len(DEEP_POSTS)} posts seeded."))
