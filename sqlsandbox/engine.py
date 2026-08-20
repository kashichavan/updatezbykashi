import sqlite3
import time
import re
import threading

DATASETS = {
    'faang': {
        'id': 'faang',
        'name': '🏢 FAANG Tech Corp',
        'description': 'Enterprise organizational hierarchy, departments, employee compensation history, projects, and performance ratings.',
        'default_query': '''-- 🎯 Top 3 Highest Earners per Department
WITH RankedSalaries AS (
    SELECT
        d.department_name,
        e.first_name || ' ' || e.last_name AS employee_name,
        e.title,
        e.salary,
        DENSE_RANK() OVER (PARTITION BY e.department_id ORDER BY e.salary DESC) AS salary_rank
    FROM employees e
    INNER JOIN departments d ON e.department_id = d.department_id
)
SELECT department_name, employee_name, title, salary, salary_rank
FROM RankedSalaries
WHERE salary_rank <= 3
ORDER BY department_name, salary_rank;''',
        'schema_sql': '''
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    department_name TEXT NOT NULL,
    location TEXT NOT NULL,
    budget DECIMAL(12,2) NOT NULL
);

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    salary DECIMAL(10,2) NOT NULL,
    hire_date DATE NOT NULL,
    department_id INTEGER,
    manager_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
);

CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    project_name TEXT NOT NULL,
    budget DECIMAL(12,2) NOT NULL,
    start_date DATE NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE employee_projects (
    employee_id INTEGER,
    project_id INTEGER,
    role TEXT NOT NULL,
    hours_allocated INTEGER NOT NULL,
    PRIMARY KEY (employee_id, project_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE performance_reviews (
    review_id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    review_year INTEGER NOT NULL,
    rating DECIMAL(3,1) NOT NULL,
    bonus_amount DECIMAL(10,2) DEFAULT 0,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- Seed Data
INSERT INTO departments VALUES
(1, 'Engineering', 'San Francisco', 8500000.00),
(2, 'Product & AI', 'Seattle', 6200000.00),
(3, 'Infrastructure', 'New York', 4900000.00),
(4, 'Design & UX', 'Austin', 2100000.00),
(5, 'Marketing & Growth', 'London', 3400000.00);

INSERT INTO employees VALUES
(1, 'Alex', 'Vance', 'alex.vance@techcorp.io', 'VP of Engineering', 320000.00, '2020-01-15', 1, NULL),
(2, 'Sarah', 'Connor', 'sarah.c@techcorp.io', 'Principal Distributed Systems Architect', 265000.00, '2020-03-01', 1, 1),
(3, 'Marcus', 'Aurelius', 'marcus.a@techcorp.io', 'Lead AI Research Scientist', 280000.00, '2021-02-10', 2, 1),
(4, 'Elena', 'Rostova', 'elena.r@techcorp.io', 'Senior Backend Engineer', 195000.00, '2021-06-15', 1, 2),
(5, 'David', 'Kim', 'david.kim@techcorp.io', 'Senior Backend Engineer', 190000.00, '2022-01-20', 1, 2),
(6, 'Priya', 'Sharma', 'priya.s@techcorp.io', 'Staff Machine Learning Engineer', 240000.00, '2021-09-01', 2, 3),
(7, 'Lucas', 'Muller', 'lucas.m@techcorp.io', 'Senior Site Reliability Engineer', 185000.00, '2022-04-12', 3, 2),
(8, 'Chloe', 'Dubois', 'chloe.d@techcorp.io', 'Head of Product Design', 210000.00, '2020-08-01', 4, 1),
(9, 'Kenji', 'Sato', 'kenji.s@techcorp.io', 'UI/UX Product Designer', 145000.00, '2022-11-01', 4, 8),
(10, 'Amina', 'Diallo', 'amina.d@techcorp.io', 'Director of Global Growth', 225000.00, '2020-05-18', 5, 1),
(11, 'Liam', 'OConnor', 'liam.oc@techcorp.io', 'Growth Marketing Analyst', 125000.00, '2023-02-01', 5, 10),
(12, 'Maya', 'Lin', 'maya.lin@techcorp.io', 'Junior Cloud Engineer', 115000.00, '2023-07-15', 3, 7);

INSERT INTO projects VALUES
(101, 'Athena LLM Copilot', 3500000.00, '2023-01-10', 'In Progress'),
(102, 'HyperScale Edge CDN', 1800000.00, '2022-09-01', 'Active'),
(103, 'Design System Nova', 450000.00, '2023-04-01', 'Completed'),
(104, 'Global Billing V2', 1200000.00, '2023-08-15', 'Planning');

INSERT INTO employee_projects VALUES
(2, 102, 'Lead Architect', 25),
(3, 101, 'Technical Lead', 35),
(4, 101, 'Backend Core Contributor', 30),
(5, 104, 'Payment Gateway Integration', 30),
(6, 101, 'Model Fine-Tuning Engineer', 35),
(7, 102, 'Infrastructure Lead', 30),
(8, 103, 'Design Director', 20),
(9, 103, 'Figma & Token Architect', 35);

INSERT INTO performance_reviews VALUES
(1, 2, 2025, 4.9, 45000.00),
(2, 3, 2025, 5.0, 60000.00),
(3, 4, 2025, 4.7, 28000.00),
(4, 5, 2025, 4.5, 22000.00),
(5, 6, 2025, 4.8, 38000.00),
(6, 7, 2025, 4.6, 25000.00),
(7, 8, 2025, 4.8, 32000.00);
'''
    },
    'ecommerce': {
        'id': 'ecommerce',
        'name': '🛒 E-Commerce Store',
        'description': 'Online marketplace catalog: customers, orders, itemized line items, products, categories, and customer product reviews.',
        'default_query': '''-- 📊 Month-over-Month Revenue Growth & Customer Count
WITH MonthlyStats AS (
    SELECT
        strftime('%Y-%m', order_date) AS order_month,
        COUNT(DISTINCT customer_id) AS active_customers,
        COUNT(order_id) AS total_orders,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY strftime('%Y-%m', order_date)
)
SELECT
    order_month,
    active_customers,
    total_orders,
    ROUND(total_revenue, 2) AS total_revenue,
    ROUND(LAG(total_revenue, 1) OVER (ORDER BY order_month), 2) AS prev_month_revenue,
    ROUND(
        (total_revenue - LAG(total_revenue, 1) OVER (ORDER BY order_month)) * 100.0 /
        NULLIF(LAG(total_revenue, 1) OVER (ORDER BY order_month), 0), 2
    ) AS mom_growth_pct
FROM MonthlyStats
ORDER BY order_month DESC;''',
        'schema_sql': '''
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL,
    parent_category_id INTEGER
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category_id INTEGER,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    country TEXT NOT NULL,
    registered_at DATE NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    status TEXT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE reviews (
    review_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    comment TEXT,
    review_date DATE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

INSERT INTO categories VALUES
(1, 'Electronics', NULL),
(2, 'Laptops & Computers', 1),
(3, 'Audio & Headphones', 1),
(4, 'Home & Office', NULL),
(5, 'Smart Wearables', 1);

INSERT INTO products VALUES
(101, 'MacBook Pro M3 Max 16-inch', 2, 3499.00, 45),
(102, 'Dell XPS 15 OLED', 2, 2199.00, 60),
(103, 'Sony WH-1000XM5 ANC Headphones', 3, 399.00, 150),
(104, 'AirPods Pro 2 USB-C', 3, 249.00, 220),
(105, 'Herman Miller Embody Ergonomic Chair', 4, 1695.00, 30),
(106, 'Apple Watch Ultra 2 Titanium', 5, 799.00, 80),
(107, 'Logitech MX Master 3S Wireless Mouse', 4, 99.00, 300);

INSERT INTO customers VALUES
(1, 'Alice Johnson', 'alice.j@gmail.com', 'USA', '2024-01-10'),
(2, 'Bob Smith', 'bob.smith@outlook.com', 'UK', '2024-02-14'),
(3, 'Carlos Santana', 'carlos.s@techmail.es', 'Spain', '2024-03-01'),
(4, 'Deepa Mehta', 'deepa.mehta@corp.in', 'India', '2024-03-15'),
(5, 'Eva Green', 'eva.green@proton.me', 'France', '2024-04-05'),
(6, 'Frank Wright', 'frank.w@icloud.com', 'USA', '2024-05-12');

INSERT INTO orders VALUES
(1001, 1, '2025-01-15', 'Delivered', 3898.00),
(1002, 2, '2025-01-20', 'Delivered', 249.00),
(1003, 3, '2025-02-05', 'Delivered', 2199.00),
(1004, 1, '2025-02-18', 'Delivered', 399.00),
(1005, 4, '2025-02-28', 'Delivered', 1695.00),
(1006, 5, '2025-03-05', 'Delivered', 1048.00),
(1007, 2, '2025-03-12', 'Processing', 3499.00),
(1008, 6, '2025-03-18', 'Delivered', 99.00);

INSERT INTO order_items VALUES
(1, 1001, 101, 1, 3499.00),
(2, 1001, 103, 1, 399.00),
(3, 1002, 104, 1, 249.00),
(4, 1003, 102, 1, 2199.00),
(5, 1004, 103, 1, 399.00),
(6, 1005, 105, 1, 1695.00),
(7, 1006, 104, 1, 249.00),
(8, 1006, 106, 1, 799.00),
(9, 1007, 101, 1, 3499.00),
(10, 1008, 107, 1, 99.00);

INSERT INTO reviews VALUES
(1, 101, 1, 5, 'Absolute beast for compiling Rust and Python LLM pipelines.', '2025-01-22'),
(2, 103, 1, 4, 'Great noise cancellation on flights.', '2025-02-20'),
(3, 105, 4, 5, 'Best posture chair for 10+ hour coding sessions.', '2025-03-04'),
(4, 104, 2, 5, 'Seamless ANC integration with iPhone.', '2025-01-25');
'''
    },
    'fintech': {
        'id': 'fintech',
        'name': '💳 FinTech & Banking',
        'description': 'High-volume ledger: bank accounts, credit/debit transaction ledger, loan approvals, and customer balance tracking.',
        'default_query': '''-- 🚨 Fraud Detection: Find Accounts with > 2 High-Value Transactions within 24 Hours
WITH FlaggedTx AS (
    SELECT
        t.transaction_id,
        t.account_id,
        a.account_type,
        t.amount,
        t.transaction_type,
        t.transaction_time,
        COUNT(*) OVER (
            PARTITION BY t.account_id
            ORDER BY t.transaction_time
            RANGE BETWEEN INTERVAL 1 DAY PRECEDING AND CURRENT ROW
        ) AS high_value_count_24h
    FROM transactions t
    INNER JOIN accounts a ON t.account_id = a.account_id
    WHERE t.amount >= 2500.00
)
SELECT account_id, account_type, transaction_id, amount, transaction_time, high_value_count_24h
FROM FlaggedTx
ORDER BY transaction_time DESC;''',
        'schema_sql': '''
CREATE TABLE branches (
    branch_id INTEGER PRIMARY KEY,
    branch_name TEXT NOT NULL,
    city TEXT NOT NULL,
    assets DECIMAL(14,2) NOT NULL
);

CREATE TABLE accounts (
    account_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    account_type TEXT NOT NULL, -- Checking, Savings, Investment
    balance DECIMAL(12,2) NOT NULL,
    branch_id INTEGER,
    opened_date DATE NOT NULL,
    status TEXT NOT NULL, -- Active, Frozen, Dormant
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);

CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    transaction_type TEXT NOT NULL, -- Deposit, Withdrawal, Transfer
    amount DECIMAL(10,2) NOT NULL,
    transaction_time TIMESTAMP NOT NULL,
    merchant TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE loans (
    loan_id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    loan_amount DECIMAL(12,2) NOT NULL,
    interest_rate DECIMAL(4,2) NOT NULL,
    loan_status TEXT NOT NULL, -- Approved, Pending, Repaid
    issue_date DATE NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

INSERT INTO branches VALUES
(1, 'Wall Street HQ', 'New York', 450000000.00),
(2, 'Silicon Valley Tech Branch', 'San Francisco', 320000000.00),
(3, 'Chicago Loop', 'Chicago', 180000000.00);

INSERT INTO accounts VALUES
(101, 'Apex Venture Capital', 'Investment', 12500000.00, 2, '2022-01-15', 'Active'),
(102, 'Satoshi Nakamoto LLC', 'Checking', 845000.00, 2, '2023-04-10', 'Active'),
(103, 'Jordan Belfort', 'Savings', 45000.00, 1, '2021-08-20', 'Frozen'),
(104, 'Sophia Loren', 'Checking', 92000.00, 1, '2023-11-05', 'Active'),
(105, 'Quantum Trading Fund', 'Investment', 45000000.00, 1, '2020-03-01', 'Active'),
(106, 'Marcus Brody', 'Savings', 12400.00, 3, '2024-02-12', 'Active');

INSERT INTO transactions VALUES
(1, 101, 'Deposit', 500000.00, '2025-03-01 09:15:00', 'Wire Transfer In'),
(2, 102, 'Withdrawal', 12500.00, '2025-03-01 11:30:00', 'Stripe Merchant Payout'),
(3, 104, 'Withdrawal', 4200.00, '2025-03-01 14:22:00', 'Tiffany & Co.'),
(4, 104, 'Withdrawal', 3100.00, '2025-03-01 17:45:00', 'Apple Store Fifth Ave'),
(5, 105, 'Deposit', 2500000.00, '2025-03-02 08:00:00', 'Goldman Sachs Settlement'),
(6, 102, 'Withdrawal', 15000.00, '2025-03-02 10:15:00', 'AWS Cloud Services'),
(7, 106, 'Deposit', 3500.00, '2025-03-02 12:00:00', 'Direct Deposit Payroll');

INSERT INTO loans VALUES
(501, 102, 250000.00, 6.50, 'Approved', '2024-05-01'),
(502, 104, 60000.00, 7.25, 'Approved', '2024-09-15'),
(503, 106, 15000.00, 8.90, 'Pending', '2025-02-10');
'''
    },
    'social': {
        'id': 'social',
        'name': '🌐 Social Network',
        'description': 'Graph & engagement analytics: users, social posts, likes, followers/following graph, and comments.',
        'default_query': '''-- 🏆 Find Most Influential Users (Followers count + Post Engagement)
SELECT
    u.user_id,
    u.username,
    u.followers_count,
    COUNT(DISTINCT p.post_id) AS total_posts,
    COALESCE(SUM(p.likes_count), 0) AS total_post_likes,
    ROUND(
        COALESCE(SUM(p.likes_count), 0) * 1.0 / NULLIF(COUNT(DISTINCT p.post_id), 0), 1
    ) AS avg_likes_per_post
FROM users u
LEFT JOIN posts p ON u.user_id = p.user_id
GROUP BY u.user_id, u.username, u.followers_count
ORDER BY total_post_likes DESC, u.followers_count DESC;''',
        'schema_sql': '''
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    bio TEXT,
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    created_at DATE NOT NULL
);

CREATE TABLE follows (
    follower_id INTEGER,
    following_id INTEGER,
    followed_at TIMESTAMP NOT NULL,
    PRIMARY KEY (follower_id, following_id),
    FOREIGN KEY (follower_id) REFERENCES users(user_id),
    FOREIGN KEY (following_id) REFERENCES users(user_id)
);

CREATE TABLE posts (
    post_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    caption TEXT NOT NULL,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE comments (
    comment_id INTEGER PRIMARY KEY,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(post_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

INSERT INTO users VALUES
(1, 'kashinath', 'Kashinath Chavan', 'Tech Educator & Python Developer 🚀', 28500, 310, '2023-01-01'),
(2, 'techlead_sam', 'Samantha Lee', 'Staff Engineer @ CloudScale', 14200, 450, '2023-03-15'),
(3, 'ai_researcher', 'Dr. Aris Thorne', 'LLMs & Cognitive AI Research', 51000, 180, '2022-11-20'),
(4, 'dev_fresher', 'Rahul Verma', 'Learning Django & SQL', 850, 620, '2024-06-01'),
(5, 'design_guru', 'Elena Rossi', 'Visual Systems & Figma', 9800, 240, '2023-08-10');

INSERT INTO follows VALUES
(4, 1, '2024-06-02 10:00:00'),
(4, 2, '2024-06-02 10:05:00'),
(4, 3, '2024-06-05 14:30:00'),
(2, 1, '2023-04-10 18:20:00'),
(1, 2, '2023-04-11 09:15:00'),
(5, 1, '2023-09-01 12:00:00'),
(2, 3, '2023-05-12 11:45:00');

INSERT INTO posts VALUES
(101, 1, 'Mastering SQL Window Functions: ROW_NUMBER vs RANK vs DENSE_RANK explained!', 4200, 185, '2025-02-15 10:30:00'),
(102, 1, 'Why B-Tree Indexing is the Backbone of High-Throughput Databases ⚡', 3800, 142, '2025-02-28 14:15:00'),
(103, 3, 'New Benchmark: Evaluating LLM Reasoning on Complex Graph Traversals 🧠', 9500, 420, '2025-03-01 16:45:00'),
(104, 2, 'Top 5 Distributed System Gotchas Every Backend Lead Must Prevent', 2100, 95, '2025-03-02 09:00:00'),
(105, 5, 'Modern Glassmorphic Dark UI Design Patterns for 2026', 1650, 78, '2025-03-03 13:20:00');

INSERT INTO comments VALUES
(1, 101, 4, 'This explanation of DENSE_RANK finally made it click for me!', '2025-02-15 11:00:00'),
(2, 101, 2, 'Great breakdown, Kashinath! Clear and concise.', '2025-02-15 12:30:00'),
(3, 103, 1, 'Exciting results, Dr. Thorne. Looking forward to the paper!', '2025-03-01 17:15:00');
'''
    }
}

# Thread-local storage for in-memory databases per thread/request
_db_cache = {}
_db_lock = threading.Lock()

def get_sandboxed_connection(dataset_id='faang'):
    if dataset_id not in DATASETS:
        dataset_id = 'faang'
    
    # Initialize fresh in-memory SQLite connection
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Load schema & seed data
    schema_sql = DATASETS[dataset_id]['schema_sql']
    conn.executescript(schema_sql)
    
    return conn

def execute_sql_sandbox(sql_text, dataset_id='faang', max_rows=500):
    start_time = time.perf_counter()
    
    if not sql_text or not sql_text.strip():
        return {
            'success': False,
            'error': 'Query string cannot be empty. Please enter a valid SQL query.',
            'execution_time_ms': 0
        }
    
    conn = None
    try:
        conn = get_sandboxed_connection(dataset_id)
        cursor = conn.cursor()
        
        # Clean query text
        statements = [s.strip() for s in sql_text.strip().split(';') if s.strip()]
        if not statements:
            return {'success': False, 'error': 'No executable SQL statements found.'}
        
        last_columns = []
        last_rows = []
        affected_rows_total = 0
        query_plan = []
        
        for idx, statement in enumerate(statements):
            # Check if this is the final statement
            is_last = (idx == len(statements) - 1)
            
            # If it's a SELECT/WITH statement, capture EXPLAIN QUERY PLAN
            is_read_query = bool(re.match(r'^\s*(SELECT|WITH|PRAGMA|EXPLAIN)\b', statement, re.IGNORECASE))
            
            if is_read_query and is_last:
                try:
                    explain_cur = conn.cursor()
                    explain_cur.execute(f"EXPLAIN QUERY PLAN {statement}")
                    plan_rows = explain_cur.fetchall()
                    query_plan = [
                        {
                            'id': row[0] if len(row) > 0 else 0,
                            'parent': row[1] if len(row) > 1 else 0,
                            'notused': row[2] if len(row) > 2 else 0,
                            'detail': row[3] if len(row) > 3 else str(row)
                        }
                        for row in plan_rows
                    ]
                except Exception:
                    query_plan = []
            
            cursor.execute(statement)
            
            if cursor.description:
                last_columns = [desc[0] for desc in cursor.description]
                raw_rows = cursor.fetchmany(max_rows + 1)
                is_truncated = len(raw_rows) > max_rows
                if is_truncated:
                    raw_rows = raw_rows[:max_rows]
                
                # Convert rows to serializable dict / list
                last_rows = [[item for item in row] for row in raw_rows]
            else:
                affected_rows_total += cursor.rowcount if cursor.rowcount > 0 else 0
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Introspect updated schema state
        schema_metadata = inspect_schema(conn)
        
        return {
            'success': True,
            'dataset_id': dataset_id,
            'dataset_name': DATASETS.get(dataset_id, {}).get('name', 'Custom DB'),
            'columns': last_columns,
            'rows': last_rows,
            'row_count': len(last_rows),
            'affected_rows': affected_rows_total,
            'is_truncated': len(last_rows) >= max_rows,
            'execution_time_ms': round(elapsed_ms, 2),
            'query_plan': query_plan,
            'schema': schema_metadata
        }
        
    except sqlite3.OperationalError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            'success': False,
            'error': f"SQL Syntax / Operational Error: {str(e)}",
            'error_type': 'OperationalError',
            'execution_time_ms': round(elapsed_ms, 2)
        }
    except sqlite3.IntegrityError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            'success': False,
            'error': f"Database Integrity Violation: {str(e)}",
            'error_type': 'IntegrityError',
            'execution_time_ms': round(elapsed_ms, 2)
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            'success': False,
            'error': f"Execution Error: {str(e)}",
            'error_type': type(e).__name__,
            'execution_time_ms': round(elapsed_ms, 2)
        }
    finally:
        if conn:
            conn.close()

def inspect_schema(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    
    schema = {}
    for table_name in tables:
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        col_rows = cursor.fetchall()
        
        cursor.execute(f"SELECT COUNT(*) FROM '{table_name}';")
        count = cursor.fetchone()[0]
        
        # Sample preview 3 rows
        cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 3;")
        sample_rows = [[item for item in r] for r in cursor.fetchall()]
        sample_cols = [c[1] for c in col_rows]
        
        schema[table_name] = {
            'table_name': table_name,
            'row_count': count,
            'columns': [
                {
                    'cid': col[0],
                    'name': col[1],
                    'type': col[2] or 'TEXT',
                    'notnull': bool(col[3]),
                    'default_value': col[4],
                    'is_pk': bool(col[5])
                }
                for col in col_rows
            ],
            'sample_columns': sample_cols,
            'sample_rows': sample_rows
        }
    return schema

def get_dataset_catalog():
    catalog = []
    for d_id, data in DATASETS.items():
        conn = get_sandboxed_connection(d_id)
        schema = inspect_schema(conn)
        conn.close()
        catalog.append({
            'id': d_id,
            'name': data['name'],
            'description': data['description'],
            'default_query': data['default_query'],
            'tables_count': len(schema),
            'schema': schema
        })
    return catalog
