from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
from blog.models import BlogPost, Category, Tag

SQL_INTERVIEW_POSTS = [
    {
        "slug": "sql-interview-powerplant-performance",
        "title": "SQL for Power Plant Performance Monitoring: Querying Time-Series Data with Window Functions",
        "excerpt": "Monitoring power plant efficiency requires analyzing time-series data from sensors. Learn how to use window functions to calculate rolling averages, detect anomalies, and optimize query performance with large datasets.",
        "content": """<h2>Power Plant Time-Series Analysis</h2>
<p>Power plants generate massive streams of sensor data every second. Tracking temperature, pressure, vibration, and efficiency metrics over time is critical for predictive maintenance and performance optimization.</p>

<h3>1. Daily Rolling Average Efficiency</h3>
<p>Calculate the 7-day rolling average efficiency across all units to smooth out daily fluctuations.</p>
<pre><code class="language-sql">SELECT
    unit_id,
    measurement_date,
    AVG(efficiency_percentage) OVER (
        PARTITION BY unit_id
        ORDER BY measurement_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7day_avg
FROM power_plant_sensor_readings
ORDER BY unit_id, measurement_date;</code></pre>

<h3>2. Detecting Anomalous Readings</h3>
<p>Identify readings that deviate more than 2 standard deviations from the 30-day rolling average — a key indicator of potential equipment failure.</p>
<pre><code class="language-sql">WITH rolling_stats AS (
    SELECT
        unit_id,
        measurement_date,
        efficiency_percentage,
        AVG(efficiency_percentage) OVER (
            PARTITION BY unit_id
            ORDER BY measurement_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS avg_30d,
        STDDEV(efficiency_percentage) OVER (
            PARTITION BY unit_id
            ORDER BY measurement_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS stddev_30d
    FROM power_plant_sensor_readings
)
SELECT
    unit_id,
    measurement_date,
    efficiency_percentage,
    avg_30d,
    efficiency_percentage - avg_30d AS deviation
FROM rolling_stats
WHERE ABS(efficiency_percentage - avg_30d) > 2 * STDDEV(stddev_30d)
ORDER BY deviation DESC;</code></pre>

<h3>3. Week-over-Week Performance Comparison</h3>
<p>Compare this week's average efficiency against the same week last year to identify seasonal trends or degradation.</p>
<pre><code class="language-sql">WITH current_week AS (
    SELECT
        unit_id,
        AVG(efficiency_percentage) AS avg_eff
    FROM power_plant_sensor_readings
    WHERE measurement_date >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY unit_id
),
previous_year_week AS (
    SELECT
        unit_id,
        AVG(efficiency_percentage) AS avg_eff
    FROM power_plant_sensor_readings
    WHERE measurement_date >= CURRENT_DATE - INTERVAL '8 days'
      AND measurement_date < CURRENT_DATE - INTERVAL '1 day'
      AND measurement_date >= CURRENT_DATE - INTERVAL '15 days'
      AND measurement_date < CURRENT_DATE - INTERVAL '7 days'
    GROUP BY unit_id
)
SELECT
    c.unit_id,
    c.avg_eff AS current_week_avg,
    p.avg_eff AS previous_year_week_avg,
    ROUND((c.avg_eff - p.avg_eff) / p.avg_eff * 100, 2) AS pct_change
FROM current_week c
JOIN previous_year_week p ON c.unit_id = p.unit_id
ORDER BY pct_change DESC;</code></pre>

<h3>4. Finding the Hottest Running Unit</h3>
<p>Identify which unit has the highest average temperature over the last 24 hours for immediate attention.</p>
<pre><code class="language-sql">SELECT
    unit_id,
    AVG(temperature_c) AS avg_temp_24h
FROM power_plant_sensor_readings
WHERE measurement_date >= CURRENT_DATE - INTERVAL '1 day'
GROUP BY unit_id
ORDER BY avg_temp_24h DESC
LIMIT 1;</code></pre>

<hr/>

<h2>Key Takeaways for Production</h2>
<ul>
  <li><strong>Window functions</strong> are essential for time-series analysis — they let you compute running totals, moving averages, and comparisons across rows without self-joins.</li>
  <li>Always <strong>index</strong> the partitioning and ordering columns (<code>unit_id</code>, <code>measurement_date</code>) for performance on billions of rows.</li>
  <li><strong>BETWEEN vs. RANGE</strong>: <code>ROWS BETWEEN</code> is physical row-offset based, while <code>RANGE BETWEEN</code> is logical value-based. Use <code>ROWS</code> for time-series with possible duplicates.</li>
  <li>Be careful with <strong>NULL handling</strong> — window functions propagate NULLs. Use <code>COALESCE</code> or <code>IGNORE NULLS</code> where needed.</li>
</ul>""",
        "category_name": "Interview Prep & Database",
        "tags": "SQL, Window Functions, Time-Series, Power Plant, PostgreSQL",
        "cover_image_url": "https://images.unsplash.com/photo-1559678218-ac2d2c4e5d5c?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 10,
        "is_featured": True,
        "views_count": 0,
        "likes_count": 0,
    },
    {
        "slug": "sql-interview-financial-transactions",
        "title": "SQL for Financial Transaction Analysis: Fraud Detection with Recursive CTEs",
        "excerpt": "Detecting fraudulent transactions in real-time requires tracing complex money flow paths. Learn how recursive CTEs can trace transaction trees, find circular patterns, and flag suspicious activity.",
        "content": """<h2>Financial Transaction Fraud Detection</h2>
<p>Banking systems process thousands of transactions per second. Detecting money laundering, circular transactions, and suspicious patterns requires powerful SQL techniques.</p>

<h3>1. Tracing Transaction Trees with Recursive CTEs</h3>
<p>Find the full origin chain of a suspicious transaction — who paid whom, and who paid them, back to the source.</p>
<pre><code class="language-sql">-- Recursive CTE to trace transaction tree up to 5 levels deep
WITH RECURSIVE transaction_tree AS (
    -- Anchor: Start with the suspicious transaction
    SELECT
        sender_id,
        receiver_id,
        amount,
        1 AS depth
    FROM transactions
    WHERE transaction_id = 'suspicious-12345'

    UNION ALL

    -- Recursive: Find who the receiver paid next
    SELECT
        t.sender_id,
        t.receiver_id,
        t.amount,
        tt.depth + 1
    FROM transactions t
    INNER JOIN transaction_tree tt ON t.sender_id = tt.receiver_id
    WHERE tt.depth < 5
)
SELECT * FROM transaction_tree ORDER BY depth, amount DESC;</code></pre>

<h3>2. Finding Circular Transaction Patterns</h3>
<p>Detounce circular money movement (A → B → C → A) which is a red flag for money laundering.</p>
<pre><code class="language-sql">WITH RECURSIVE path_cte AS (
    -- Start with any transaction
    SELECT
        t1.sender_id AS start_node,
        t1.receiver_id AS current_node,
        ARRAY[t1.sender_id, t1.receiver_id] AS path,
        2 AS depth
    FROM transactions t1

    UNION ALL

    SELECT
        p.start_node,
        t.receiver_id,
        path || t.receiver_id,
        p.depth + 1
    FROM path_cte p
    JOIN transactions t ON p.current_node = t.sender_id
    WHERE NOT t.receiver_id = ANY(path)  -- Don't close the loop yet
    AND p.depth < 6
)
SELECT DISTINCT start_node, current_node
FROM path_cte
WHERE depth >= 3
AND start_node = current_node;  -- Found a circle!</code></pre>

<h3>3. Daily Transaction Volume Spikes</h3>
<p>Detect abnormal spikes in transaction volume — could indicate card testing or fraud bursts.</p>
<pre><code class="language-sql">SELECT
    DATE(transaction_timestamp) AS txn_date,
    COUNT(*) AS txn_count,
    AVG(COUNT(*)) OVER (ORDER BY DATE(transaction_timestamp) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rolling_avg,
    CASE WHEN COUNT(*) > AVG(COUNT(*)) OVER (ORDER BY DATE(transaction_timestamp) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) * 2
         THEN 'SPIKE' ELSE 'NORMAL' END AS status
FROM transactions
WHERE transaction_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(transaction_timestamp)
ORDER BY txn_date DESC;</code></pre>

<hr/>

<h2>Key Takeaways for Production</h2>
<ul>
  <li><strong>Recursive CTEs</strong> are the go-to technique for traversing hierarchical or graph-like data in a single query — perfect for transaction trees and org charts.</li>
  <li>Use <code>ARRAY</code> to track the path taken and prevent infinite loops by checking <code>NOT ... = ANY(path)</code>.</li>
  <li><strong>Window functions</strong> with <code>ROWS BETWEEN</code> enable fast moving averages and anomaly detection without self-joins.</li>
  <li>Always <strong>index</strong> <code>sender_id</code>, <code>receiver_id</code>, and <code>transaction_timestamp</code> for performance on high-throughput tables.</li>
</ul>""",
        "category_name": "Interview Prep & Database",
        "tags": "SQL, Recursive CTEs, Fraud Detection, Finance, PostgreSQL",
        "cover_image_url": "https://images.unsplash.com/photo-1548599692-62131c1b807c?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 12,
        "is_featured": True,
        "views_count": 0,
        "likes_count": 0,
    },
    {
        "slug": "sql-interview-ecommerce-inventory",
        "title": "SQL for E-commerce Inventory: Flash Sales, Low Stock Alerts, & Stock Reconciliation",
        "excerpt": "Running a flash sale requires real-time inventory tracking. Learn how to prevent overselling, reconcile stock across warehouses, and alert on low inventory with production-ready SQL queries.",
        "content": """<h2>Flash Sale Inventory Management</h2>
<p>During a flash sale, thousands of orders hit your database in minutes. Overselling can ruin customer trust and revenue. These SQL patterns keep inventory accurate under extreme concurrency.</p>

<h3>1. Prevent Overselling with Advisory Locks</h3>
<p>Use PostgreSQL advisory locks to serialize access to limited-stock items — only one transaction can decrement stock at a time.</p>
<pre><code class="language-sql">-- Acquire advisory lock before updating stock
SELECT pg_advisory_xact_lock(12345); -- Lock persists until transaction commits

UPDATE products
SET stock = stock - 1
WHERE product_id = 123
  AND stock > 0  -- Prevent going negative
RETURNING *;</code></pre>

<h3>2. Flash Sale: Sell Remaining Stock All at Once</h3>
<p>When a flash sale ends, you need to sell whatever stock is left at a discounted price — atomically.</p>
<pre><code class="language-sql">WITH remaining AS (
    SELECT product_id, stock
    FROM products
    WHERE flash_sale_active = true
    FOR UPDATE
)
UPDATE products p
SET stock = 0,
    price = price * 0.5  -- 50% off at end
FROM remaining r
WHERE p.product_id = r.product_id
  AND r.stock > 0;
</code></pre>

<h3>3. Low Stock Alert Across Warehouses</h3>
<p>Aggregate inventory across all warehouses and flag products that fall below the reorder threshold.</p>
<pre><code class="language-sql">SELECT
    product_id,
    SUM(warehouse_stock) AS total_stock,
    MIN(reorder_threshold) AS threshold
FROM inventory
GROUP BY product_id
HAVING SUM(warehouse_stock) < MIN(reorder_threshold)
ORDER BY total_stock ASC;</code></pre>

<h3>4. Reconciling Discrepancies Between Systems</h3>
<p>Compare orders shipped vs. orders invoiced to find unshipped or unbilled orders.</p>
<pre><code class="language-sql">SELECT
    o.product_id,
    COUNT(DISTINCT o.order_id) AS orders_shipped,
    COUNT(DISTINCT i.invoice_id) AS invoiced,
    COUNT(DISTINCT o.order_id) - COUNT(DISTINCT i.invoice_id) AS uninvoiced
FROM order_items o
LEFT JOIN invoices i ON o.product_id = i.product_id
 AND o.order_id = i.order_id
GROUP BY o.product_id
HAVING COUNT(DISTINCT o.order_id) > COUNT(DISTINCT i.invoice_id)
ORDER BY uninvoiced DESC;</code></pre>

<hr/>

<h2>Key Takeaways for Production</h2>
<ul>
  <li><strong>Advisory locks</strong> (<code>pg_advisory_xact_lock</code>) are a simple way to serialize access to limited resources without full row locking.</li>
  <li><strong>LEFT JOIN … IS NULL</strong> is the classic pattern for finding records in one table with no match in another — great for reconciliation.</li>
  <li>Always use <strong>FOR UPDATE</strong> or <code>SELECT ... FOR SHARE</code> in transactions that modify shared state to avoid race conditions.</li>
  <li><strong>Materialized views</strong> can pre-compute low-stock alerts so your checkout flow doesn't have to scan the entire inventory table.</li>
</ul>""",
        "category_name": "Interview Prep & Database",
        "tags": "SQL, E-commerce, Inventory, Flash Sale, PostgreSQL",
        "cover_image_url": "https://images.unsplash.com/photo-1581090365383-6e0b8cf0f0bf?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 9,
        "is_featured": False,
        "views_count": 0,
        "likes_count": 0,
    },
    {
        "slug": "sql-interview-healthcare-patient-data",
        "title": "SQL for Healthcare Analytics: Patient Wait Times, Readmission Rates & HIPAA-Compliant Aggregations",
        "excerpt": "Healthcare data analysis requires careful handling of PHI. Learn how to compute wait times, readmission rates, and resource utilization while maintaining privacy and compliance.",
        "content": """<h2>Healthcare Analytics Without Exposing PHI</h2>
<p>Analyzing patient data while protecting privacy is a critical skill. These SQL patterns aggregate data safely and compute key metrics without exposing identifiers.</p>

<h3>1. Average Patient Wait Time by Hour</h3>
<p>Compute the average wait time across all patients per hour of the day — useful for staffing optimization.</p>
<pre><code class="language-sql">SELECT
    EXTRACT(HOUR FROM check_in_time) AS hour_of_day,
    AVG(EXTRACT(EPOCH FROM (check_out_time - check_in_time)) / 60) AS avg_wait_minutes
FROM patient_visits
GROUP BY hour_of_day
ORDER BY hour_of_day;</code></pre>

<h3>2. 30-Day Readmission Rate per Condition</h3>
<p>Find the percentage of patients readmitted within 30 days for each diagnosis, excluding the initial visit.</p>
<pre><code class="language-sql">WITH initial_visits AS (
    SELECT
        patient_id,
        diagnosis_code,
        admission_date AS first_admission
    FROM patient_admissions
    WHERE admission_rank = 1
),
readmissions AS (
    SELECT
        r.patient_id,
        r.diagnosis_code,
        r.admission_date AS readmit_date
    FROM patient_admissions r
    INNER JOIN initial_visits i
        ON r.patient_id = i.patient_id
       AND r.admission_date BETWEEN i.first_admission + INTERVAL '1 day'
                                    AND i.first_admission + INTERVAL '30 days'
)
SELECT
    diagnosis_code,
    COUNT(DISTINCT patient_id) AS readmitted_count,
    COUNT(DISTINCT i.patient_id) AS total_patients,
    ROUND(COUNT(DISTINCT r.patient_id)::numeric / COUNT(DISTINCT i.patient_id) * 100, 2) AS readmission_rate_pct
FROM readmissions r
JOIN initial_visits i ON r.patient_id = i.patient_id
GROUP BY diagnosis_code
ORDER BY readmission_rate_pct DESC;</code></pre>

<h3>3. Daily Resource Utilization Efficiency</h3>
<p>Compare occupied beds vs. total capacity by ward to identify underutilized or over capacity units.</p>
<pre><code class="language-sql">SELECT
    ward_name,
    DATE(admission_date) AS date,
    SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) AS occupied_beds,
    COUNT(*) AS total_beds,
    ROUND(100.0 * SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) / COUNT(*), 2) AS occupancy_pct
FROM bed_assignments
GROUP BY ward_name, date
ORDER BY occupancy_pct DESC;</code></pre>

<hr/>

<h2>Key Takeaways for Production</h2>
<ul>
  <li>Never expose <code>patient_id</code> or direct identifiers in analytical queries — always aggregate and anonymize.</li>
  <li><strong>CTEs</strong> make complex multi-step calculations readable and maintainable — break readmission logic into <code>initial_visits</code> and <code>readmissions</code>.</li>
  <li><strong>EXTRACT(EPOCH FROM ...)</strong> converts intervals to seconds for precise time calculations.</li>
  <li>Use <strong>materialized views</strong> for read-heavy metrics like readmission rates so OLTP tables aren't locked down by analytical queries.</li>
</ul>""",
        "category_name": "Interview Prep & Database",
        "tags": "SQL, Healthcare, Analytics, HIPAA, PostgreSQL",
        "cover_image_url": "https://images.unsplash.com/photo-1581091011143-3a7d133d7fbe?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 11,
        "is_featured": False,
        "views_count": 0,
        "likes_count": 0,
    },
    {
        "slug": "sql-interview-travel-booking",
        "title": "SQL for Travel Booking: Finding Cheapest Multi-City Itineraries with Recursive Queries",
        "excerpt": "Building a flight search engine requires finding optimal routes. Learn how to use recursive CTEs to explore city graphs, compute total prices, and find the cheapest multi-city itineraries.",
        "content": """<h2>Flight Itinerary Optimization</h2>
<p>Travel search engines must explore thousands of possible routes across a graph of cities and flights. Recursive CTEs let you traverse the graph in a single query.</p>

<h3>1. Find All Reachable Cities from a Hub</h3>
<p>Starting from a home city, find every city you can reach within 3 flight hops.</p>
<pre><code class="language-sql">WITH RECURSIVE reachable AS (
    -- Anchor: Direct flights from home city
    SELECT
        receiver_city AS destination,
        1 AS hops,
        price AS total_price
    FROM flights
    WHERE departure_city = 'SFO'

    UNION ALL

    -- Recursive: Connect to next city
    SELECT
        f.receiver_city,
        r.hops + 1,
        r.total_price + f.price
    FROM flights f
    INNER JOIN reachable r ON f.departure_city = r.destination
    WHERE r.hops < 3
)
SELECT DISTINCT destination, hops, total_price
FROM reachable
ORDER BY hops, total_price;</code></pre>

<h3>2. Find Cheapest 3-City Itinerary</h3>
<p>Search for the lowest-total-price route that visits exactly 3 distinct cities.</p>
<pre><code class="language-sql">WITH RECURSIVE itinerary AS (
    SELECT
        departure_city AS start_city,
        receiver_city AS current_city,
        ARRAY[departure_city, receiver_city] AS path,
        price AS total_price,
        2 AS city_count
    FROM flights
    WHERE departure_city = 'SFO'

    UNION ALL

    SELECT
        i.start_city,
        f.receiver_city,
        path || f.receiver_city,
        total_price + f.price,
        city_count + 1
    FROM flights f
    JOIN itinerary i ON f.departure_city = i.current_city
    WHERE NOT f.receiver_city = ANY(path)  -- Don't revisit cities
      AND city_count < 3
)
SELECT start_city, current_city, total_price, city_count
FROM itinerary
WHERE city_count = 3
ORDER BY total_price
LIMIT 1;</code></pre>

<h3>3. Detecting Routing Loops</h3>
<p>Ensure no city appears twice in a routing path — loops indicate broken graph data.</p>
<pre><code class="language-sql">WITH RECURSIVE route AS (
    SELECT
        ARRAY[departure_city] AS path,
        receiver_city AS current,
        1 AS hops
    FROM flights
    WHERE departure_city = 'SFO'

    UNION ALL

    SELECT
        path || receiver_city,
        f.receiver_city,
        hops + 1
    FROM flights f
    JOIN route r ON f.departure_city = r.current
    WHERE NOT f.receiver_ptr = ANY(path)  -- Anti-loop check
)
SELECT current, hops, path
FROM route
WHERE hops > 5  -- Flags suspicious deep paths
LIMIT 10;</code></pre>

<hr/>

<h2>Key Takeaways for Production</h2>
<ul>
  <li><strong>Recursive CTEs</strong> are your go-to for graph traversal — flight networks, org charts, recommendation engines.</li>
  <li>Use <code>ANY(path)</code> to efficiently check if a node has already been visited and avoid infinite loops.</li>
  <li>Total price computation must include <strong>all legs</strong> (taxes, fees, baggage) — the query above only sums base fares.</li>
  <li>Index <code>departure_city</code> and <code>receiver_city</code> for performance on large flight schedules.</li>
</ul>""",
        "category_name": "Interview Prep & Database",
        "tags": "SQL, Recursive CTEs, Travel, Graph, PostgreSQL",
        "cover_image_url": "https://images.unsplash.com/photo-1574662415425-4d12cd2ba6d5?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 10,
        "is_featured": False,
        "views_count": 0,
        "likes_count": 0,
    },
    {
        "slug": "sql-interview-analytics-event-funnel",
        "title": "SQL for Product Analytics: Funnel Conversion, Drop-off Points & A/B Testing Comparisons",
        "excerpt": "Understanding user funnel drop-off is key to product optimization. Learn how to compute conversion rates at each step, identify where users disappear, and compare A/B test variants with SQL.",
        "content": """<h2>Product Funnel Analysis</h2>
<p>Your product has a conversion funnel: Visit → Sign Up → First Action → Purchase. Each step drops users. SQL helps you quantify exactly where and why.</p>

<h3>1. Full Funnel Conversion Rates</h3>
<p>Compute the conversion rate at each funnel step and the drop-off between steps.</p>
<pre><code class="language-sql">WITH funnel_steps AS (
    SELECT
        user_id,
        CASE
            WHEN page = 'sign_up' THEN 1
            WHEN page = 'first_action' THEN 2
            WHEN page = 'purchase' THEN 3
        END AS step
    FROM page_views
    WHERE page IN ('home', 'sign_up', 'first_action', 'purchase')
),
step_counts AS (
    SELECT
        step,
        COUNT(DISTINCT user_id) AS users_at_step
    FROM funnel_steps
    GROUP BY step
)
SELECT
    s1.step AS step1, s1.users_at_step AS visitors,
    s2.step AS step2, s2.users_at_step AS sign_ups,
    s3.step AS step3 AS first_actions,
    s4.step AS step4 AS purchases,
    ROUND(s4.users_at_step::numeric / s1.users_at_step * 100, 2) AS overall_conversion_pct,
    ROUND(s2.users_at_step::numeric / s1.users_at_step * 100, 2) AS drop_off_visit_to_signup_pct,
    ROUND(s3.users_at_step::numeric / s2.users_at_step * 100, 2) AS drop_off_signup_to_action_pct,
    ROUND(s4.users_at_step::numeric / s3.users_at_step * 100, 2) AS drop_off_action_to_purchase_pct
FROM step_counts s1
JOIN step_counts s2 ON s1.step = 1 AND s2.step = 2
JOIN step_counts s3 ON s1.step = 1 AND s3.step = 3
JOIN step_counts s4 ON s1.step = 1 AND s4.step = 4;</code></pre>

<h3>2. Funnel Drop-off by User Segment</h3>
<p>Compare conversion rates between new users and returning users to identify segment-specific friction.</p>
<pre><code class="language-sql">WITH funnel_steps AS (
    SELECT
        user_id,
        CASE
            WHEN page = 'sign_up' THEN 1
            WHEN page = 'first_action' THEN 2
            WHEN page = 'purchase' THEN 3
        END AS step
    FROM page_views
    WHERE page IN ('home', 'sign_up', 'first_action', 'purchase')
),
segmented AS (
    SELECT
        f.user_id,
        f.step,
        CASE WHEN pv.first_seen_at >= CURRENT_DATE - INTERVAL '30 days' THEN 'new' ELSE 'returning' END AS user_segment
    FROM funnel_steps f
    JOIN user_profiles pv ON f.user_id = pv.user_id
)
SELECT
    user_segment,
    COUNT(DISTINCT CASE WHEN step = 1 THEN user_id END) AS visitors,
    COUNT(DISTINCT CASE WHEN step = 2 THEN user_id END) AS sign_ups,
    ROUND(COUNT(DISTINCT CASE WHEN step = 2 THEN user_id END)::numeric / COUNT(DISTINCT CASE WHEN step = 1 THEN user_id END) * 100, 2) AS signup_rate
FROM segmented
GROUP BY user_segment
ORDER BY signup_rate DESC;</code></pre>

<h3>3. A/B Test: Variant A vs Variant B Conversion</h3>
<p>Compare purchase conversion rates between two product page variants.</p>
<pre><code class="language-sql">WITH purchases AS (
    SELECT
        user_id,
        CASE WHEN EXISTS (
            SELECT 1 FROM page_views pv2
            WHERE pv2.user_id = pv.user_id
              AND pv2.page = 'purchase'
        ) THEN 1 ELSE 0 END AS purchased
    FROM page_views pv
    GROUP BY pv.user_id
),
variant_users AS (
    SELECT
        user_id,
        CASE WHEN page like '%variant_b%' THEN 'B' ELSE 'A' END AS variant
    FROM page_views
    GROUP BY user_id
)
SELECT
    v.variant,
    COUNT(DISTINCT v.user_id) AS total_users,
    COUNT(DISTINCT p.user_id) AS purchasers,
    ROUND(COUNT(DISTINCT p.user_id)::numeric / COUNT(DISTINCT v.user_id) * 100, 2) AS conversion_rate
FROM variant_users v
LEFT JOIN purchases p ON v.user_id = p.user_id AND p.purchased = 1
GROUP BY v.variant
ORDER BY conversion_rate DESC;</code></pre>

<hr/>

<h2>Key Takeaways for Production</h2>
<ul>
  <li>Always <strong>count distinct users</strong>, not events — a single user can trigger multiple events per step.</li>
  <li><strong>Window functions</strong> with <code>LAG</code>/<code>LEAD</sub> can compute step-by-step drop-off rates in a single pass.</li>
  <li>Segment analysis (new vs. returning, by geography, by device) reveals where UX friction is worst.</li>
  <li>Index <code>user_id</code> and <code>page</code> columns for performance on billions of page-view events.</li>
</ul>""",
        "category_name": "Interview Prep & Database",
        "tags": "SQL, Analytics, Funnel, A/B Testing, PostgreSQL",
        "cover_image_url": "https://images.unsplash.com/photo-1566047224667-39c9c787d2dc?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 9,
        "is_featured": False,
        "views_count": 0,
        "likes_count": 0,
    },
    {
        "slug": "sql-interview-supply-chain-optimization",
        "title": "SQL for Supply Chain: Optimizing Inventory Across Multiple Warehouses with Window Functions",
        "excerpt": "Supply chain managers need to balance inventory across warehouses. Learn how to compute total stock, identify imbalances, and recommend transfers with production SQL.",
        "content": """<h2>Multi-Warehouse Inventory Optimization</h2>
<p>Distributing stock across 3+ warehouses while minimizing stockouts and transfer costs requires smart aggregation and window functions.</p>

<h3>1. Total Stock & Imbalance Score per Product</h3>
<p>Show total inventory across all warehouses and flag products that are heavily imbalanced (one warehouse has most of the stock).</p>
<pre><code class="language-sql">SELECT
    product_id,
    SUM(warehouse_stock) AS total_stock,
    AVG(warehouse_stock) AS avg_per_warehouse,
    MAX(warehouse_stock) AS max_stock,
    MIN(warehouse_stock) AS min_stock,
    MAX(warehouse_stock) - MIN(warehouse_stock) AS imbalance_range,
    ROUND(100.0 * (MAX(warehouse_stock) - AVG(warehouse_stock)) / AVG(warehouse_stock), 2) AS imbalance_pct
FROM warehouse_inventory
GROUP BY product_id
ORDER BY imbalance_pct DESC;</code></pre>

<h3>2. Recommend Transfer to Balance Stock</h3>
<p>For imbalanced products, recommend how many units to transfer from the surplus warehouse to the deficit warehouse.</p>
<pre><code class="language-sql">WITH stock_summary AS (
    SELECT
        product_id,
        warehouse_id,
        warehouse_stock,
        AVG(warehouse_stock) OVER (PARTITION BY product_id) AS avg_stock
    FROM warehouse_inventory
),
imbalances AS (
    SELECT
        product_id,
        warehouse_id,
        warehouse_stock,
        warehouse_stock - avg_stock AS diff_from_avg
    FROM stock_summary
    WHERE warehouse_stock > avg_stock  -- Only surplus warehouses
)
SELECT
    product_id,
    warehouse_id,
    warehouse_stock,
    diff_from_avg,
    SUM(diff_from_avg) OVER (PARTITION BY product_id) AS total_surplus
FROM imbalances;</code></pre>

<h3>3. Weekly Stock Trend Analysis</h3>
<p>Compare this week's total stock against the 4-week rolling average to detect seasonal draws or supply disruptions.</p>
<pre><code class="language-sql">WITH weekly_totals AS (
    SELECT
        product_id,
        DATE_TRUNC('week', measurement_date) AS week,
        SUM(warehouse_stock) AS total_stock
    FROM warehouse_inventory
    GROUP BY product_id, week
),
rolling_avg AS (
    SELECT
        product_id,
        week,
        total_stock,
        AVG(total_stock) OVER (
            PARTITION BY product_id
            ORDER BY week
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ) AS avg_4week
    FROM weekly_totals
)
SELECT
    product_id,
    week,
    total_stock,
    ROUND(avg_4week, 2) AS avg_4week,
    CASE WHEN total_stock < avg_4week * 0.8 THEN 'LOW STOCK'
         WHEN total_stock > avg_4week * 1.2 THEN 'OVERSTOCK'
         ELSE 'BALANCED' END AS status
FROM rolling_avg
ORDER BY product_id, week DESC;</code></pre>

<hr/>

<h2>Key Takeaways for Production</h2>
<ul>
  <li><strong>Window functions</strong> with <code>PARTITION BY</code> let you compare each warehouse against the product average — no self-joins needed.</li>
  <li>Imbalance detection (<code>MAX - MIN</code>, <code>MAX / AVG</code>) is the first step before recommending transfers — don't transfer blindly.</li>
  <li>Rolling averages (>3-week) smooth out weekly seasonality and reveal true demand shifts.</li>
  <li>Index <code>product_id</code> and <code>warehouse_id</code> for performance on millions of inventory records.</li>
</ul>""",
        "category_name": "Interview Prep & Database",
        "tags": "SQL, Supply Chain, Inventory, Window Functions, PostgreSQL",
        "cover_image_url": "https://images.unsplash.com/photo-1581091740504-a5c0f1f4d78e?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 10,
        "is_featured": False,
        "views_count": 0,
        "likes_count": 0,
    },
    {
        "slug": "sql-interview-dating-app-matching",
        "title": "SQL for Dating Apps: Finding Matches Within Distance & Filtering by Preferences",
        "excerpt": "Building a scalable matchmaking engine requires efficient distance queries and preference filtering. Learn how to compute Haversine distances, filter by dealbreakers, and rank matches.",
        "content": """<h2>Geolocation-Based Matching</h2>
<p>Dating apps must match users within a radius while respecting preferences (age range, gender, interests). Pure SQL with PostGIS makes this fast at scale.</p>

<h3>1. Haversine Distance Within 50km</h3>
<p>Find all users within 50km of a given location using the Haversine formula — no PostGIS extension required.</p>
<pre><code class="language-sql">SELECT
    user_id,
    username,
    latitude,
    longitude,
    6371 *
        ACOS(
            COS(RADIANS(given_lat)) * COS(RADIANS(latitude))
            + SIN(RADIANS(given_lat)) * SIN(RADIANS(latitude))
            * COS(RADIANS(given_lon - given_lon))
        ) AS distance_km
FROM users
HAVING distance_km <= 50
ORDER BY distance_km;</code></pre>

<h3>2. Filter by Age Range and Dealbreakers</h3>
<p>Apply preference filters: age 18-30, not smoking, and looking for men (if user is woman).</p>
<pre><code class="language-sql">SELECT
    user_id,
    username,
    age,
    smoke,
    gender_preference,
    looking_for_gender
FROM users
WHERE age BETWEEN 18 AND 30
  AND smoke = false
  AND looking_for_gender = 'M'
  AND user_id != given_user_id;  -- Exclude the current user</code></pre>

<h3>3. Rank Matches by Compatibility Score</h3>
<p>Rank matches by shared interests, age proximity, and distance — closest + most compatible first.</p>
<pre><code class="language-sql">SELECT
    u.user_id,
    u.username,
    u.age,
    6371 * ACOS(
        COS(RADIANS(given_lat)) * COS(RADIANS(u.latitude))
        + SIN(RADIANS(given_lat)) * SIN(RADIANS(u.latitude))
        * COS(RADIANS(given_lon - u.longitude))
    ) AS distance_km,
    -- Compatibility: shared interests + age proximity
    (COUNT(DISTINCT i.interest) FILTER (WHERE u.interest = i.interest) * 10
     + 10 - ABS(u.age - given_age)) AS compatibility_score
FROM users u
JOIN interests i ON u.user_id = i.user_id
JOIN interests given_i ON given_user_id = given_i.user_id
WHERE u.user_id != given_user_id
  AND u.age BETWEEN 18 AND 30
  AND u.smoke = false
GROUP BY u.user_id, u.username, u.age
ORDER BY compatibility_score ASC, distance_km ASC;</code></pre>

<hr/>

<h2>Key Takeaways for Production</h2>
<ul>
  <li>The <strong>Haversine formula</strong> computes great-circle distance on a sphere — accurate enough for most dating apps (Earth radius = 6371km).</li>
  <li>For production scale, <strong>PostGIS</strong> with <code><-></code> (operator distance) or <code>DISTANCE</code> is orders of magnitude faster than pure SQL Haversine.</li>
  <li>Always <strong>exclude the current user</code> (<code>user_id != given_user_id</code>) — otherwise they'd see themselves in matches!</li>
  <li>Index <code>latitude</code>, <code>longitude</code>, and <code>gender_preference</code> for performance on millions of users.</li>
</ul>""",
        "category_name": "Interview Prep & Database",
        "tags": "SQL, Dating Apps, Geolocation, Haversine, PostgreSQL",
        "cover_image_url": "https://images.unsplash.com/photo-1519345123381-946a21236a1e?w=1200",
        "author_name": "Kashinath Chavan",
        "author_title": "Founder & Software Engineer",
        "author_avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "read_time_minutes": 9,
        "is_featured": False,
        "views_count": 0,
        "likes_count": 0,
    },
]


class Command(BaseCommand):
    help = 'Seeds the database with 10 SQL interview question blog posts'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting database seed for SQL interview blogs...")

        # Ensure INTERVIEW category exists
        interview_cat, _ = Category.objects.get_or_create(
            name='Interview Prep & Database',
            defaults={'slug': 'interview-prep-database', 'icon': '🎯', 'color': '#a855f7', 'description': 'High-frequency technical interview questions and database scenarios.'}
        )

        seeded_count = 0
        for idx, post_data in enumerate(SQL_INTERVIEW_POSTS):
            # Get or create tags
            tags_str = post_data.pop('tags')
            tag_names = [t.strip().title() for t in tags_str.split(',')]

            # Process tags
            tag_objects = []
            for t_name in tag_names:
                t_slug = slugify(t_name)
                tag_obj, _ = Tag.objects.get_or_create(slug=t_slug, defaults={'name': t_name})
                tag_objects.append(tag_obj)

            # Calculate read time from content length if not set
            read_mins = post_data.get('read_time_minutes', 10)

            # Set published_at
            published_at = timezone.now() - timedelta(days=idx * 2)

            slug = post_data['slug']
            title = post_data['title']
            excerpt = post_data['excerpt']
            content = post_data['content']
            cover_img = post_data['cover_image_url']
            category = interview_cat

            post, created = BlogPost.objects.update_or_create(
                slug=slug,
                defaults={
                    'title': title,
                    'excerpt': excerpt,
                    'content': content,
                    'category': category,
                    'cover_image_url': cover_img,
                    'author_name': post_data['author_name'],
                    'author_title': post_data['author_title'],
                    'author_avatar_url': post_data['author_avatar_url'],
                    'read_time_minutes': read_mins,
                    'is_featured': post_data['is_featured'],
                    'views_count': post_data['views_count'],
                    'likes_count': post_data['likes_count'],
                    'is_published': True,
                    'published_at': published_at,
                }
            )

            # Add tags
            post.tags.set(tag_objects)

            seeded_count += 1
            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"  ✓ {status}: {post.title[:60]}..."))

        self.stdout.write(self.style.SUCCESS(f"\n✨ Successfully seeded {seeded_count} SQL interview blogs!"))