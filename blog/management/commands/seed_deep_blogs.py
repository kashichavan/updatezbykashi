from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
from blog.models import BlogPost, Category, Tag

DEEP_POSTS = [
    {
        "slug": "typescript-5-deep-dive",
        "title": "TypeScript 5.x Deep Dive: Satisfies Operator, Const Type Params, Variadic Tuple Types",
        "excerpt": "A deep dive into TypeScript 5.x advanced features including the satisfies operator, const type parameters, and variadic tuple types. Learn how to write highly robust and type-safe enterprise applications.",
        "content": """
<h2>Understanding TypeScript 5.x</h2>
<p>TypeScript continues to evolve, bringing more powerful type inference and advanced tools for developers. The 5.x releases introduced game-changing features.</p>
<h3>The Satisfies Operator</h3>
<p>The <code>satisfies</code> operator allows you to validate that an expression matches a type, without widening the type of the expression itself.</p>
<pre><code class='language-typescript'>
type Colors = "red" | "green" | "blue";
type RGB = [number, number, number];
const palette = {
    red: [255, 0, 0],
    green: "#00ff00",
    blue: [0, 0, 255]
} satisfies Record<Colors, string | RGB>;
// We still know that palette.red is an array and palette.green is a string
palette.red.map(x => x * 2); 
</code></pre>
<blockquote>
  <p><strong>Gotcha:</strong> Don't confuse <code>satisfies</code> with type assertions (<code>as</code>). Assertions can be unsafe, whereas <code>satisfies</code> is strictly checked.</p>
</blockquote>
<h2>Const Type Parameters</h2>
<p>Const type parameters allow inference of literal types by default, rather than their widened versions, when using generic functions.</p>
<pre><code class='language-typescript'>
function getRoute&lt;const T extends string&gt;(route: T): T {
    return route;
}
const myRoute = getRoute("/home"); // Inferred as "/home" instead of string
</code></pre>
<h2>Variadic Tuple Types</h2>
<p>This feature allows you to extract and spread tuples with unknown length, enabling complex concatenation operations at the type level.</p>
<pre><code class='language-typescript'>
type Concat&lt;T extends unknown[], U extends unknown[]&gt; = [...T, ...U];
type Result = Concat&lt;[1, 2], [3, 4]&gt;; // [1, 2, 3, 4]
</code></pre>
<h2>Comparison: TypeScript 4 vs 5</h2>
<table>
  <tr><th>Feature</th><th>TS 4.x</th><th>TS 5.x</th></tr>
  <tr><td>Performance</td><td>Standard</td><td>20% faster compile times</td></tr>
  <tr><td>Decorators</td><td>Experimental</td><td>Standard ECMAScript Decorators</td></tr>
  <tr><td>Module Resolution</td><td>node</td><td>bundler</td></tr>
</table>
<h2>Building a Type-Safe API Client</h2>
<p>Let's combine these features to build a fully type-safe API client.</p>
<pre><code class='language-typescript'>
type Endpoints = {
    "/users": { response: { id: number; name: string }[] };
    "/posts": { response: { title: string; content: string }[] };
};

async function fetchApi&lt;const T extends keyof Endpoints&gt;(path: T): Promise&lt;Endpoints[T]["response"]&gt; {
    const res = await fetch(path);
    return res.json();
}
// Fully typed!
const users = await fetchApi("/users");
</code></pre>
        """,
        "category_name": "JavaScript & Engines",
        "tags": "TypeScript, JavaScript, Frontend, Compilers",
        "cover_image_url": "https://images.unsplash.com/photo-1593720213428-28a5b9e94613?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 8,
        "is_featured": True,
        "views_count": 4200,
        "likes_count": 550,
        "published_days_ago": 2,
    },
    {
        "slug": "docker-compose-multi-stage-deep-dive",
        "title": "Docker & Docker Compose Deep Dive: Multi-Stage Builds, Layer Caching & Production Optimization",
        "excerpt": "Master Docker for production with multi-stage builds, aggressive layer caching, and optimized Compose configurations. Reduce your image sizes by 90% and speed up deployments.",
        "content": """
<h2>The Need for Multi-Stage Builds</h2>
<p>When containerizing applications, image size and security are paramount. Including build tools in your final production image increases the attack surface and wastes bandwidth.</p>
<h3>A Standard Django Dockerfile (Bad)</h3>
<pre><code class='language-dockerfile'>
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi"]
</code></pre>
<h3>Multi-Stage Build (Good)</h3>
<pre><code class='language-dockerfile'>
# Build Stage
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update &amp;&amp; apt-get install -y gcc
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Production Stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*
COPY . .
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "config.asgi:application"]
</code></pre>
<blockquote>
  <p><strong>Tip:</strong> Always order your COPY instructions from least frequently changed to most frequently changed to maximize layer caching.</p>
</blockquote>
<h2>Docker Compose for Local vs Production</h2>
<p>Your local compose should mount volumes for hot reloading, while production should use the baked images.</p>
<h3>Production docker-compose.yml</h3>
<pre><code class='language-yaml'>
version: '3.8'
services:
  web:
    image: myapp:v1
    command: gunicorn config.wsgi:application
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/db
    depends_on:
      db:
        condition: service_healthy
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 5s
      timeout: 5s
      retries: 5
volumes:
  postgres_data:
</code></pre>
<h2>Benchmarking Image Sizes</h2>
<table>
  <tr><th>Framework</th><th>Single Stage</th><th>Multi-Stage</th><th>Savings</th></tr>
  <tr><td>Django (Python)</td><td>1.2 GB</td><td>180 MB</td><td>85%</td></tr>
  <tr><td>Next.js (Node)</td><td>1.8 GB</td><td>250 MB</td><td>86%</td></tr>
  <tr><td>Go API</td><td>800 MB</td><td>25 MB</td><td>97%</td></tr>
</table>
<h2>Layer Caching Strategy</h2>
<p>To optimize layer caching, always copy dependency files (like package.json or requirements.txt) and install them BEFORE copying the rest of your source code. This ensures that changes to your source code don't bust the cache for your dependencies.</p>
        """,
        "category_name": "Developer Tooling & Compilers",
        "tags": "Docker, DevOps, Docker Compose, Deployment",
        "cover_image_url": "https://images.unsplash.com/photo-1648134859182-58553cb2ab37?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 10,
        "is_featured": True,
        "views_count": 3500,
        "likes_count": 480,
        "published_days_ago": 5,
    },
    {
        "slug": "system-design-twitter-whatsapp-youtube",
        "title": "System Design Interview: How to Design Twitter's Feed, WhatsApp, and YouTube in 45 Minutes",
        "excerpt": "A masterclass in tackling FAANG system design interviews. We break down the architectures of Twitter, WhatsApp, and YouTube, covering load balancing, sharding, and CDNs.",
        "content": """
<h2>Approaching System Design</h2>
<p>System design interviews are not about getting the exact architecture the company uses. They are about demonstrating your ability to trade-off consistency, availability, latency, and throughput.</p>
<h3>The CAP Theorem</h3>
<p>You can only have two: Consistency, Availability, and Partition Tolerance. In modern distributed systems, Partition Tolerance is a given, so the real choice is between Consistency and Availability.</p>
<h2>Designing Twitter's Feed</h2>
<p>Twitter is a heavily read-heavy system (100:1 read-to-write ratio). A standard pull-based approach (querying the DB for all followers' tweets on every page load) will collapse under load.</p>
<h3>Fan-out on Write (Push Model)</h3>
<pre><code class='language-python'>
# Simplified Fan-out Logic
def publish_tweet(user_id, tweet):
    save_to_db(tweet)
    followers = get_followers(user_id)
    
    # Push to Redis queues of active followers
    for follower in followers:
        if is_active(follower):
            redis_client.lpush(f"feed:{follower}", tweet.id)
            redis_client.ltrim(f"feed:{follower}", 0, 800) # Keep only latest 800
</code></pre>
<blockquote>
  <p><strong>Gotcha:</strong> The push model fails for celebrities with millions of followers. For them, use a hybrid approach (pull for celebs, push for regular users).</p>
</blockquote>
<h2>Designing WhatsApp</h2>
<p>WhatsApp requires real-time messaging, low latency, and end-to-end encryption. The core is the chat server, which maintains persistent WebSocket connections with clients.</p>
<h3>Chat Server Architecture</h3>
<pre><code class='language-bash'>
# Nginx load balancer to chat servers
upstream websocket_cluster {
    hash $remote_addr consistent;
    server chat1.example.com:8080;
    server chat2.example.com:8080;
}
</code></pre>
<p>Messages are temporarily stored in a distributed key-value store (like Cassandra) until they are delivered, after which they can be deleted from the server (if using strict E2E without cloud backup).</p>
<h2>Designing YouTube</h2>
<p>YouTube is a video streaming platform. It requires massive storage, efficient encoding, and a global CDN.</p>
<h3>Video Upload Flow</h3>
<p>Uploads go directly to a cloud blob storage (S3) using multi-part uploads. Then, an event triggers an encoding pipeline (RabbitMQ + worker nodes) to convert the video into multiple resolutions (1080p, 720p, etc.) and formats (HLS, DASH).</p>
<h2>Database Selection: SQL vs NoSQL</h2>
<table>
  <tr><th>Aspect</th><th>SQL (PostgreSQL)</th><th>NoSQL (Cassandra/MongoDB)</th></tr>
  <tr><td>Schema</td><td>Rigid, tabular</td><td>Flexible, document/columnar</td></tr>
  <tr><td>Scaling</td><td>Vertical (mostly)</td><td>Horizontal (native)</td></tr>
  <tr><td>Transactions</td><td>ACID compliant</td><td>BASE (Eventually consistent)</td></tr>
</table>
        """,
        "category_name": "Interview Prep & Database",
        "tags": "System Design, Architecture, Interview, Scalability",
        "cover_image_url": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 12,
        "is_featured": True,
        "views_count": 4500,
        "likes_count": 650,
        "published_days_ago": 1,
    },
    {
        "slug": "python-asyncio-masterclass",
        "title": "Python Asyncio Masterclass: Building a High-Concurrency Web Scraper with aiohttp",
        "excerpt": "Stop using thread pools for I/O bound tasks. Learn how Python's event loop works under the hood and build a blisteringly fast web scraper using asyncio and aiohttp.",
        "content": """
<h2>Understanding the Python Event Loop</h2>
<p>Python's <code>asyncio</code> module provides a single-threaded, single-process concurrent code execution model using coroutines. It's perfect for I/O-bound tasks like network requests.</p>
<h3>Coroutines vs Threads vs Processes</h3>
<table>
  <tr><th>Model</th><th>Memory Footprint</th><th>Context Switch Overhead</th><th>Best For</th></tr>
  <tr><td>Asyncio (Coroutines)</td><td>Very Low (~1-2KB)</td><td>Almost Zero</td><td>High I/O, Web Servers</td></tr>
  <tr><td>Threading</td><td>Medium (~8MB)</td><td>High (OS level)</td><td>Blocking I/O (files)</td></tr>
  <tr><td>Multiprocessing</td><td>High (Full interpreter)</td><td>Very High</td><td>CPU Bound (math)</td></tr>
</table>
<h2>Building the Scraper</h2>
<p>Let's build a scraper that can fetch thousands of pages concurrently, but safely, using Semaphores to avoid DDoSing the target server.</p>
<h3>The Code</h3>
<pre><code class='language-python'>
import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def fetch_page(session, url, semaphore):
    async with semaphore:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    return soup.title.string if soup.title else "No title"
        except Exception as e:
            return f"Error: {e}"
        return f"Status: {response.status}"

async def main(urls):
    # Limit to 50 concurrent requests
    semaphore = asyncio.Semaphore(50)
    
    # Use a single session for connection pooling
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_page(session, url, semaphore) for url in urls]
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        for url, res in zip(urls, results):
            print(f"{url}: {res}")

if __name__ == "__main__":
    urls_to_scrape = [f"https://example.com/page/{i}" for i in range(1000)]
    asyncio.run(main(urls_to_scrape))
</code></pre>
<blockquote>
  <p><strong>Gotcha:</strong> Never use blocking functions like <code>requests.get()</code> or <code>time.sleep()</code> inside an async function. It will block the entire event loop for all coroutines. Always use <code>aiohttp</code> and <code>asyncio.sleep()</code>.</p>
</blockquote>
<h2>Performance Tuning</h2>
<p>To go even faster, you can swap the default asyncio event loop with <code>uvloop</code>, which is written in Cython and based on libuv (the same engine powering Node.js).</p>
<pre><code class='language-python'>
import asyncio
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
# Now your asyncio code runs 2-4x faster
</code></pre>
        """,
        "category_name": "Python & Backend",
        "tags": "Python, Asyncio, Scraping, Concurrency",
        "cover_image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 9,
        "is_featured": False,
        "views_count": 2800,
        "likes_count": 310,
        "published_days_ago": 10,
    },
    {
        "slug": "react-19-deep-dive-actions",
        "title": "React 19 Deep Dive: Actions, useOptimistic, useFormStatus, and Concurrent Rendering",
        "excerpt": "React 19 changes everything. Bid farewell to complex state management for forms and mutations. Embrace Server Actions and native optimistic UI updates.",
        "content": """
<h2>The Era of Server Actions</h2>
<p>React 19 formalizes Actions. An action is an asynchronous function that handles data mutations. It integrates deeply with React's transitions, forms, and error boundaries.</p>
<h3>Forms the React 19 Way</h3>
<p>No more <code>e.preventDefault()</code> and complex state mapping for inputs.</p>
<pre><code class='language-javascript'>
// actions.js
'use server'

export async function createPost(formData) {
    const title = formData.get('title');
    const content = formData.get('content');
    
    await db.post.create({ data: { title, content } });
    revalidatePath('/posts');
}
</code></pre>
<pre><code class='language-javascript'>
// PostForm.jsx
import { createPost } from './actions';
import { useFormStatus } from 'react-dom';

function SubmitButton() {
    const { pending } = useFormStatus();
    return &lt;button disabled={pending}&gt;
        {pending ? 'Saving...' : 'Publish'}
    &lt;/button&gt;;
}

export default function PostForm() {
    return (
        &lt;form action={createPost}&gt;
            &lt;input name="title" required /&gt;
            &lt;textarea name="content" required /&gt;
            &lt;SubmitButton /&gt;
        &lt;/form&gt;
    );
}
</code></pre>
<h2>Optimistic UI Updates</h2>
<p>The new <code>useOptimistic</code> hook allows you to show immediate visual feedback while the server action is processing in the background.</p>
<pre><code class='language-javascript'>
import { useOptimistic } from 'react';
import { addMessage } from './actions';

export function Chat({ messages }) {
    const [optimisticMessages, addOptimisticMessage] = useOptimistic(
        messages,
        (state, newMessage) => [...state, { text: newMessage, sending: true }]
    );

    async function formAction(formData) {
        const text = formData.get('message');
        addOptimisticMessage(text);
        await addMessage(text);
    }

    return (
        &lt;div&gt;
            {optimisticMessages.map((m, i) => (
                &lt;div key={i} style={{ opacity: m.sending ? 0.5 : 1 }}&gt;
                    {m.text}
                &lt;/div&gt;
            ))}
            &lt;form action={formAction}&gt;
                &lt;input name="message" /&gt;
                &lt;button&gt;Send&lt;/button&gt;
            &lt;/form&gt;
        &lt;/div&gt;
    );
}
</code></pre>
<h2>React 18 vs React 19 Forms</h2>
<table>
  <tr><th>Feature</th><th>React 18</th><th>React 19</th></tr>
  <tr><td>Form Submission</td><td>onSubmit + e.preventDefault()</td><td>action={myAction}</td></tr>
  <tr><td>Pending State</td><td>useState(false)</td><td>useFormStatus()</td></tr>
  <tr><td>Optimistic UI</td><td>Manual state rollbacks</td><td>useOptimistic()</td></tr>
</table>
<blockquote>
  <p><strong>Note:</strong> Server actions can be passed as props to Client Components, allowing you to trigger server-side code directly from client interactions without setting up API routes manually.</p>
</blockquote>
        """,
        "category_name": "Frontend & Next.js",
        "tags": "React, Next.js, Frontend, UI",
        "cover_image_url": "https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 7,
        "is_featured": False,
        "views_count": 3100,
        "likes_count": 420,
        "published_days_ago": 15,
    },
    {
        "slug": "postgresql-advanced-patterns-jsonb",
        "title": "PostgreSQL Advanced Patterns: JSONB Queries, Partial Indexes, and Full-Text Search",
        "excerpt": "Unlock the true power of PostgreSQL. Learn how to ditch Elasticsearch for Postgres' built-in full-text search, and how to effectively index and query nested JSONB data.",
        "content": """
<h2>Why Postgres is the Only DB You Need (Usually)</h2>
<p>Modern PostgreSQL is incredibly versatile. It can handle relational data perfectly, but it also has robust features for NoSQL-style JSON document storage and full-text search capabilities.</p>
<h3>JSONB Operations</h3>
<p>Unlike standard <code>JSON</code> columns, <code>JSONB</code> stores data in a binary format, allowing for fast indexing and querying.</p>
<pre><code class='language-sql'>
-- Create a table with a JSONB column
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    profile JSONB
);

-- Insert nested data
INSERT INTO users (profile) VALUES 
('{"name": "Alice", "skills": ["python", "sql"], "address": {"city": "NY"}}');

-- Querying nested keys (->> returns text)
SELECT profile->>'name' FROM users WHERE profile->'address'->>'city' = 'NY';

-- Checking if a JSON array contains an element
SELECT * FROM users WHERE profile->'skills' ? 'sql';
</code></pre>
<h2>Indexing JSONB with GIN</h2>
<p>To make the above queries fast on millions of rows, we need a Generalized Inverted Index (GIN).</p>
<pre><code class='language-sql'>
CREATE INDEX idx_users_profile_skills ON users USING GIN ((profile->'skills'));
</code></pre>
<h2>Partial Indexes</h2>
<p>If you only query a subset of your data frequently, a partial index saves massive amounts of memory and disk space.</p>
<pre><code class='language-sql'>
-- Only index active users
CREATE INDEX idx_active_users_email ON users(email) WHERE is_active = true;
</code></pre>
<h2>Full-Text Search</h2>
<p>You might not need Elasticsearch. Postgres has powerful full-text search built-in.</p>
<pre><code class='language-sql'>
-- Add a tsvector column for fast searching
ALTER TABLE articles ADD COLUMN tsv tsvector;

-- Update the column combining title (weight A) and content (weight B)
UPDATE articles SET tsv =
    setweight(to_tsvector('english', coalesce(title,'')), 'A') ||
    setweight(to_tsvector('english', coalesce(content,'')), 'B');

-- Create a GIN index on the tsvector
CREATE INDEX idx_articles_tsv ON articles USING GIN(tsv);

-- Query the text
SELECT title FROM articles 
WHERE tsv @@ to_tsquery('english', 'postgres & index');
</code></pre>
<table>
  <tr><th>Search Tool</th><th>Complexity</th><th>Best For</th></tr>
  <tr><td>PostgreSQL ILIKE</td><td>Low</td><td>Simple substrings, small tables</td></tr>
  <tr><td>PostgreSQL tsvector</td><td>Medium</td><td>Word stems, rankings, medium tables</td></tr>
  <tr><td>Elasticsearch</td><td>High</td><td>Typo tolerance, massive scale analytics</td></tr>
</table>
<blockquote>
  <p><strong>Gotcha:</strong> Remember to use triggers to automatically update the <code>tsvector</code> column whenever the source columns (like title or content) are updated.</p>
</blockquote>
        """,
        "category_name": "Database & SQL",
        "tags": "PostgreSQL, SQL, Database, Performance",
        "cover_image_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 11,
        "is_featured": False,
        "views_count": 2950,
        "likes_count": 380,
        "published_days_ago": 18,
    },
    {
        "slug": "kubernetes-for-developers-explained",
        "title": "Kubernetes for Developers: Pods, Services, Deployments and Helm Charts Explained",
        "excerpt": "Demystifying Kubernetes for software engineers. Learn the core primitives (Pods, Deployments, Services) and how to package your apps with Helm.",
        "content": """
<h2>Why Kubernetes?</h2>
<p>Kubernetes (K8s) is an open-source container orchestration platform. It handles scaling, failover, deployment, and networking for your Docker containers automatically.</p>
<h3>Core Primitives</h3>
<ul>
  <li><strong>Pod:</strong> The smallest deployable unit. Usually contains one container (e.g., a Django app container).</li>
  <li><strong>Deployment:</strong> Manages a set of identical Pods, ensuring a specific number are always running (ReplicaSet) and handling zero-downtime rolling updates.</li>
  <li><strong>Service:</strong> Provides a stable IP address and DNS name to a set of Pods, acting as a load balancer.</li>
</ul>
<h2>A Basic Deployment YAML</h2>
<p>Here is how you define a Deployment for a web application.</p>
<pre><code class='language-yaml'>
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web-container
        image: myregistry/myapp:v1.0.0
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: app-secrets
</code></pre>
<h2>Exposing the App with a Service</h2>
<p>Pods are ephemeral; their IPs change. We use a Service to point traffic to them.</p>
<pre><code class='language-yaml'>
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP
</code></pre>
<h2>Helm Charts: The Package Manager for K8s</h2>
<p>Writing YAML by hand for every environment (dev, staging, prod) is tedious. Helm allows you to template your YAML files.</p>
<pre><code class='language-bash'>
# Install a helm chart
helm install my-release bitnami/postgresql

# Upgrade a release
helm upgrade my-release my-chart/ -f values-prod.yaml
</code></pre>
<table>
  <tr><th>Object</th><th>Analogy</th><th>Purpose</th></tr>
  <tr><td>Pod</td><td>Server Instance</td><td>Runs your code</td></tr>
  <tr><td>Deployment</td><td>Auto-scaling Group</td><td>Keeps Pods alive and updates them</td></tr>
  <tr><td>Service</td><td>Load Balancer</td><td>Routes traffic to Pods</td></tr>
  <tr><td>Ingress</td><td>Reverse Proxy (Nginx)</td><td>Routes external HTTP traffic to Services</td></tr>
</table>
<blockquote>
  <p><strong>Gotcha:</strong> Avoid storing raw passwords in ConfigMaps or directly in Deployment YAML. Always use Kubernetes <code>Secrets</code>, and consider integrating a tool like ExternalSecrets to fetch them from AWS Secrets Manager or HashiCorp Vault.</p>
</blockquote>
        """,
        "category_name": "Developer Tooling & Compilers",
        "tags": "Kubernetes, DevOps, Docker, Helm",
        "cover_image_url": "https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 14,
        "is_featured": False,
        "views_count": 2100,
        "likes_count": 250,
        "published_days_ago": 22,
    },
    {
        "slug": "leetcode-75-patterns-two-pointers",
        "title": "LeetCode 75: Solving Two Pointers, Sliding Window & Binary Search with Pattern Recognition",
        "excerpt": "Stop memorizing solutions and start recognizing patterns. Master the core algorithmic patterns needed to ace coding interviews at top tech companies.",
        "content": """
<h2>Pattern Recognition is Key</h2>
<p>Grinding hundreds of LeetCode problems blindly is inefficient. The secret is recognizing that most problems fall into a handful of distinct patterns.</p>
<h3>Pattern 1: Two Pointers</h3>
<p>Used primarily when dealing with sorted arrays or linked lists where you need to find a set of elements that fulfill certain constraints.</p>
<p><strong>Classic Problem: Valid Palindrome</strong></p>
<pre><code class='language-python'>
def isPalindrome(s: str) -> bool:
    left, right = 0, len(s) - 1
    
    while left < right:
        while left < right and not s[left].isalnum():
            left += 1
        while left < right and not s[right].isalnum():
            right -= 1
            
        if s[left].lower() != s[right].lower():
            return False
            
        left += 1
        right -= 1
        
    return True
</code></pre>
<p><em>Complexity: O(N) Time, O(1) Space.</em></p>
<h3>Pattern 2: Sliding Window</h3>
<p>Used to perform operations on a specific window size of a given array or string, such as finding the longest substring or maximum sum subarray.</p>
<p><strong>Classic Problem: Longest Substring Without Repeating Characters</strong></p>
<pre><code class='language-python'>
def lengthOfLongestSubstring(s: str) -> int:
    char_set = set()
    left = 0
    max_length = 0
    
    for right in range(len(s)):
        while s[right] in char_set:
            char_set.remove(s[left])
            left += 1
        char_set.add(s[right])
        max_length = max(max_length, right - left + 1)
        
    return max_length
</code></pre>
<h3>Pattern 3: Binary Search</h3>
<p>Used to search in a sorted array, but also applicable to problems where you are searching for an optimal solution within a range (e.g., Koko Eating Bananas).</p>
<pre><code class='language-python'>
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
</code></pre>
<h2>Time/Space Complexity Cheat Sheet</h2>
<table>
  <tr><th>Pattern</th><th>Data Structure</th><th>Time Complexity</th><th>Space Complexity</th></tr>
  <tr><td>Two Pointers</td><td>Array, String, List</td><td>O(N)</td><td>O(1)</td></tr>
  <tr><td>Sliding Window</td><td>Array, String</td><td>O(N)</td><td>O(K) or O(1)</td></tr>
  <tr><td>Binary Search</td><td>Sorted Array</td><td>O(log N)</td><td>O(1)</td></tr>
</table>
<blockquote>
  <p><strong>Tip:</strong> If the problem asks for permutations or combinations, think Backtracking. If it asks for the shortest path in an unweighted graph, think BFS.</p>
</blockquote>
        """,
        "category_name": "Data Structures & Algorithms",
        "tags": "Algorithms, Python, Interview Prep, LeetCode",
        "cover_image_url": "https://images.unsplash.com/photo-1516116216624-53e697fedbea?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 15,
        "is_featured": False,
        "views_count": 4100,
        "likes_count": 620,
        "published_days_ago": 25,
    },
    {
        "slug": "saas-stripe-django-subscriptions",
        "title": "Building a SaaS Stripe Payment Integration: Subscriptions, Webhooks & Proration in Django",
        "excerpt": "A complete guide to integrating Stripe Subscriptions in a Django SaaS. Handle checkout sessions, secure webhooks, customer portals, and seamless plan upgrades.",
        "content": """
<h2>The Architecture of Stripe Subscriptions</h2>
<p>Integrating Stripe isn't just about calling an API; it requires a robust state machine in your database synchronized via webhooks.</p>
<h3>Creating a Checkout Session</h3>
<p>Never process credit cards directly on your server. Use Stripe Checkout.</p>
<pre><code class='language-python'>
import stripe
from django.conf import settings
from django.shortcuts import redirect

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(request, price_id):
    domain_url = 'https://mysaas.com/'
    
    try:
        checkout_session = stripe.checkout.Session.create(
            customer=request.user.stripe_customer_id,
            success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + 'canceled/',
            payment_method_types=['card'],
            mode='subscription',
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                }
            ],
            client_reference_id=request.user.id,
        )
        return redirect(checkout_session.url)
    except Exception as e:
        return JsonResponse({'error': str(e)})
</code></pre>
<h2>Handling Stripe Webhooks securely</h2>
<p>Webhooks are critical. If a user's payment fails next month, Stripe tells your server via a webhook, and you must revoke access.</p>
<pre><code class='language-python'>
import stripe
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        revoke_user_access(subscription)

    return HttpResponse(status=200)
</code></pre>
<h2>Managing Proration and Upgrades</h2>
<p>When a user upgrades from a $10 plan to a $20 plan mid-month, Stripe handles proration automatically. Your database needs to reflect the new state based on the <code>customer.subscription.updated</code> event.</p>
<table>
  <tr><th>Event Type</th><th>Action Required in DB</th></tr>
  <tr><td>checkout.session.completed</td><td>Activate subscription, store sub_id</td></tr>
  <tr><td>invoice.payment_failed</td><td>Mark as past_due, notify user</td></tr>
  <tr><td>customer.subscription.deleted</td><td>Revoke premium features</td></tr>
</table>
<blockquote>
  <p><strong>Gotcha:</strong> Always verify webhook signatures! Without it, anyone can send a POST request to your endpoint pretending to be Stripe and grant themselves free premium access.</p>
</blockquote>
        """,
        "category_name": "Django & Web Architecture",
        "tags": "Django, Stripe, Payments, SaaS",
        "cover_image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 12,
        "is_featured": False,
        "views_count": 3200,
        "likes_count": 450,
        "published_days_ago": 28,
    },
    {
        "slug": "git-advanced-workflows-rebase",
        "title": "Git Advanced Workflows: Rebase vs Merge, Interactive Rebase, Cherry-Pick & Bisect",
        "excerpt": "Move beyond git pull and git push. Master Git internals, clean up messy histories with interactive rebase, and hunt down bugs efficiently using git bisect.",
        "content": """
<h2>Understanding Git Internals</h2>
<p>Git is fundamentally a Directed Acyclic Graph (DAG) of commits. Branches are merely lightweight pointers to specific commits. Understanding this makes advanced commands intuitive.</p>
<h3>Merge vs. Rebase</h3>
<p>Both integrate changes, but they do it differently.</p>
<ul>
  <li><strong>Merge:</strong> Creates a new "merge commit", preserving the exact history of when things happened. Can lead to a messy, non-linear history.</li>
  <li><strong>Rebase:</strong> Rewrites history by moving the base of your feature branch to the tip of main. Creates a clean, linear history.</li>
</ul>
<pre><code class='language-bash'>
# To rebase your current branch onto main
git fetch origin
git rebase origin/main

# If conflicts occur, resolve them, then:
git add .
git rebase --continue
</code></pre>
<h2>Interactive Rebase (Rewriting History)</h2>
<p>Did you make 5 tiny "WIP" commits? Squash them into one clean commit before opening a PR using interactive rebase.</p>
<pre><code class='language-bash'>
# Interactively rebase the last 5 commits
git rebase -i HEAD~5
</code></pre>
<p>An editor will open. Change <code>pick</code> to <code>squash</code> (or <code>s</code>) for the commits you want to meld into the previous one.</p>
<h2>Cherry-Picking</h2>
<p>Need a specific bugfix from another branch but don't want to merge the whole branch? Cherry-pick the commit.</p>
<pre><code class='language-bash'>
git cherry-pick &lt;commit-hash&gt;
</code></pre>
<h2>Hunting Bugs with Git Bisect</h2>
<p>If a bug was introduced somewhere in the last 100 commits, <code>git bisect</code> uses binary search to find the exact commit that broke the code in log2(100) ≈ 7 steps.</p>
<pre><code class='language-bash'>
git bisect start
git bisect bad                 # Current commit is bad
git bisect good v2.0           # Tag v2.0 was good

# Git checks out a commit halfway. Test the code.
# If it's broken, type: git bisect bad
# If it works, type: git bisect good

# Repeat until Git tells you the exact bad commit!
git bisect reset               # End the session
</code></pre>
<table>
  <tr><th>Command</th><th>Use Case</th><th>Warning</th></tr>
  <tr><td>git rebase</td><td>Keeping a linear history</td><td>Never rebase public, shared branches!</td></tr>
  <tr><td>git revert</td><td>Undoing a pushed commit safely</td><td>Adds a new commit, doesn't erase history</td></tr>
  <tr><td>git push -f</td><td>Pushing rebased history</td><td>Can overwrite coworkers' work if not careful</td></tr>
</table>
<blockquote>
  <p><strong>Gotcha:</strong> The golden rule of Git: <strong>Do not rewrite public history.</strong> Only rebase branches that you are working on locally before they are merged into shared branches like <code>main</code>.</p>
</blockquote>
        """,
        "category_name": "Career & Git Roadmaps",
        "tags": "Git, Developer Tools, Version Control, Career",
        "cover_image_url": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 8,
        "is_featured": False,
        "views_count": 2200,
        "likes_count": 300,
        "published_days_ago": 29,
    },
]

class Command(BaseCommand):
    help = 'Seeds the database with 10 deep, high-quality technical blog posts'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting database seed...")
        
        for post_data in DEEP_POSTS:
            # 1. Look up or create Category by name
            category_name = post_data.pop('category_name')
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={'slug': slugify(category_name)}
            )
            
            # 2. Extract tags and published date
            tags_str = post_data.pop('tags')
            published_days_ago = post_data.pop('published_days_ago')
            
            # Set published_at dynamically
            published_at = timezone.now() - timedelta(days=published_days_ago)
            
            slug = post_data.get('slug')
            
            # Prepare defaults
            defaults = {
                'title': post_data['title'],
                'excerpt': post_data['excerpt'],
                'content': post_data['content'],
                'cover_image_url': post_data['cover_image_url'],
                'author_name': post_data['author_name'],
                'author_title': post_data['author_title'],
                'author_avatar_url': post_data['author_avatar_url'],
                'read_time_minutes': post_data['read_time_minutes'],
                'is_featured': post_data['is_featured'],
                'views_count': post_data['views_count'],
                'likes_count': post_data['likes_count'],
                'published_at': published_at,
                'category': category,
                'is_published': True,
            }
            
            # 3. Create or update BlogPost
            post, created = BlogPost.objects.update_or_create(
                slug=slug,
                defaults=defaults
            )
            
            # 4. Process tags
            if tags_str:
                tag_names = [t.strip().title() for t in tags_str.split(',')]
                for tag_name in tag_names:
                    tag_slug = slugify(tag_name)
                    tag, _ = Tag.objects.get_or_create(
                        slug=tag_slug,
                        defaults={'name': tag_name}
                    )
                    post.tags.add(tag)
                    
            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{status}: {post.title}"))

        self.stdout.write(self.style.SUCCESS("Successfully seeded 10 blog posts!"))
