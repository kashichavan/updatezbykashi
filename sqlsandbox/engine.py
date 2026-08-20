import sqlite3
import time
import re
import threading

DATASETS = {
    'scott_tiger': {
        'id': 'scott_tiger',
        'name': '👑 Classic Scott/Tiger (EMP & DEPT)',
        'description': 'The world-famous Oracle standard Scott/Tiger schema with EMP, DEPT, and SALGRADE tables (King, Scott, Ford, Blake, Smith).',
        'default_query': '''-- 👑 The Classic Scott/Tiger Query: Employees, Managers, Departments & Salary Grades
SELECT
    e.empno AS Emp_ID,
    e.ename AS Employee,
    e.job AS Job,
    COALESCE(m.ename, 'TOP BOSS') AS Manager,
    d.dname AS Department,
    d.loc AS Location,
    e.sal AS Salary,
    COALESCE(e.comm, 0) AS Commission,
    s.grade AS Sal_Grade
FROM emp e
LEFT JOIN emp m ON e.mgr = m.empno
INNER JOIN dept d ON e.deptno = d.deptno
INNER JOIN salgrade s ON e.sal BETWEEN s.losal AND s.hisal
ORDER BY e.sal DESC;''',
        'schema_sql': '''
CREATE TABLE dept (
    deptno INTEGER PRIMARY KEY,
    dname TEXT NOT NULL,
    loc TEXT NOT NULL
);

CREATE TABLE emp (
    empno INTEGER PRIMARY KEY,
    ename TEXT NOT NULL,
    job TEXT NOT NULL,
    mgr INTEGER,
    hiredate DATE NOT NULL,
    sal DECIMAL(7,2) NOT NULL,
    comm DECIMAL(7,2),
    deptno INTEGER NOT NULL,
    FOREIGN KEY (deptno) REFERENCES dept(deptno),
    FOREIGN KEY (mgr) REFERENCES emp(empno)
);

CREATE TABLE salgrade (
    grade INTEGER PRIMARY KEY,
    losal DECIMAL(7,2) NOT NULL,
    hisal DECIMAL(7,2) NOT NULL
);

CREATE TABLE bonus (
    ename TEXT NOT NULL,
    job TEXT NOT NULL,
    sal DECIMAL(7,2) NOT NULL,
    comm DECIMAL(7,2)
);

-- Seed Data: Classic 4 Departments
INSERT INTO dept VALUES
(10, 'ACCOUNTING', 'NEW YORK'),
(20, 'RESEARCH', 'DALLAS'),
(30, 'SALES', 'CHICAGO'),
(40, 'OPERATIONS', 'BOSTON');

-- Seed Data: Classic 14 Employees (King, Scott, Ford, Blake, etc.)
INSERT INTO emp VALUES
(7839, 'KING', 'PRESIDENT', NULL, '1981-11-17', 5000.00, NULL, 10),
(7698, 'BLAKE', 'MANAGER', 7839, '1981-05-01', 2850.00, NULL, 30),
(7782, 'CLARK', 'MANAGER', 7839, '1981-06-09', 2450.00, NULL, 10),
(7566, 'JONES', 'MANAGER', 7839, '1981-04-02', 2975.00, NULL, 20),
(7788, 'SCOTT', 'ANALYST', 7566, '1982-12-09', 3000.00, NULL, 20),
(7902, 'FORD', 'ANALYST', 7566, '1981-12-03', 3000.00, NULL, 20),
(7369, 'SMITH', 'CLERK', 7902, '1980-12-17', 800.00, NULL, 20),
(7499, 'ALLEN', 'SALESMAN', 7698, '1981-02-20', 1600.00, 300.00, 30),
(7521, 'WARD', 'SALESMAN', 7698, '1981-02-22', 1250.00, 500.00, 30),
(7654, 'MARTIN', 'SALESMAN', 7698, '1981-09-28', 1250.00, 1400.00, 30),
(7844, 'TURNER', 'SALESMAN', 7698, '1981-09-08', 1500.00, 0.00, 30),
(7876, 'ADAMS', 'CLERK', 7788, '1983-01-12', 1100.00, NULL, 20),
(7900, 'JAMES', 'CLERK', 7698, '1981-12-03', 950.00, NULL, 30),
(7934, 'MILLER', 'CLERK', 7782, '1982-01-23', 1300.00, NULL, 10);

-- Salary Grades
INSERT INTO salgrade VALUES
(1, 700.00, 1200.00),
(2, 1201.00, 1400.00),
(3, 1401.00, 2000.00),
(4, 2001.00, 3000.00),
(5, 3001.00, 9999.00);

INSERT INTO bonus VALUES
('ALLEN', 'SALESMAN', 1600.00, 300.00),
('WARD', 'SALESMAN', 1250.00, 500.00);
'''
    },
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
    'ott_streaming': {
        'id': 'ott_streaming',
        'name': '🎬 Netflix & OTT Streaming',
        'description': 'Media analytics: subscribers, movies/shows catalog, streaming watch history, subscriptions, and genre categorization.',
        'default_query': '''-- 🎬 Top 3 Most Watched Titles per Genre with Average User Completion Rate
WITH ShowWatchStats AS (
    SELECT
        g.genre_name,
        m.title,
        m.release_year,
        COUNT(w.watch_id) AS total_views,
        ROUND(AVG(w.watch_duration_minutes * 100.0 / m.runtime_minutes), 1) AS avg_completion_pct,
        DENSE_RANK() OVER (PARTITION BY g.genre_name ORDER BY COUNT(w.watch_id) DESC) AS rank_in_genre
    FROM movies_shows m
    INNER JOIN genres g ON m.genre_id = g.genre_id
    LEFT JOIN watch_history w ON m.show_id = w.show_id
    GROUP BY g.genre_name, m.title, m.release_year, m.runtime_minutes
)
SELECT genre_name, title, release_year, total_views, avg_completion_pct
FROM ShowWatchStats
WHERE rank_in_genre <= 3
ORDER BY genre_name, total_views DESC;''',
        'schema_sql': '''
CREATE TABLE genres (
    genre_id INTEGER PRIMARY KEY,
    genre_name TEXT NOT NULL
);

CREATE TABLE movies_shows (
    show_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    genre_id INTEGER NOT NULL,
    content_type TEXT NOT NULL, -- Movie, Series
    runtime_minutes INTEGER NOT NULL,
    release_year INTEGER NOT NULL,
    imdb_rating DECIMAL(3,1),
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id)
);

CREATE TABLE subscribers (
    subscriber_id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    plan_tier TEXT NOT NULL, -- Standard, Premium 4K
    country TEXT NOT NULL,
    joined_date DATE NOT NULL
);

CREATE TABLE watch_history (
    watch_id INTEGER PRIMARY KEY,
    subscriber_id INTEGER NOT NULL,
    show_id INTEGER NOT NULL,
    watch_duration_minutes INTEGER NOT NULL,
    watched_at TIMESTAMP NOT NULL,
    device_type TEXT NOT NULL,
    FOREIGN KEY (subscriber_id) REFERENCES subscribers(subscriber_id),
    FOREIGN KEY (show_id) REFERENCES movies_shows(show_id)
);

INSERT INTO genres VALUES
(1, 'Sci-Fi & Cyberpunk'),
(2, 'Tech & Thriller'),
(3, 'Action & Anime'),
(4, 'Comedy & Drama');

INSERT INTO movies_shows VALUES
(101, 'Interstellar', 1, 'Movie', 169, 2014, 8.7),
(102, 'Blade Runner 2049', 1, 'Movie', 164, 2017, 8.0),
(103, 'Mr. Robot', 2, 'Series', 45, 2015, 8.5),
(104, 'Silicon Valley', 4, 'Series', 30, 2014, 8.5),
(105, 'Attack on Titan', 3, 'Series', 24, 2013, 9.1),
(106, 'The Matrix Resurrections', 1, 'Movie', 148, 2021, 5.7),
(107, 'Severance', 2, 'Series', 55, 2022, 8.7);

INSERT INTO subscribers VALUES
(1, 'alex_coder', 'Premium 4K', 'USA', '2023-01-10'),
(2, 'priya_dev', 'Standard', 'India', '2023-05-15'),
(3, 'lucas_sre', 'Premium 4K', 'Germany', '2024-02-01'),
(4, 'sarah_arch', 'Premium 4K', 'USA', '2023-11-20'),
(5, 'kenji_design', 'Standard', 'Japan', '2024-06-12');

INSERT INTO watch_history VALUES
(1, 1, 101, 169, '2025-02-10 20:15:00', 'Apple TV 4K'),
(2, 1, 103, 45, '2025-02-12 21:00:00', 'MacBook Pro'),
(3, 2, 105, 24, '2025-02-14 18:30:00', 'Smart TV'),
(4, 2, 104, 30, '2025-02-15 19:15:00', 'iPad Pro'),
(5, 3, 107, 55, '2025-02-18 22:00:00', 'Smart TV'),
(6, 4, 101, 169, '2025-02-20 20:00:00', 'LG OLED TV'),
(7, 4, 103, 45, '2025-02-22 21:30:00', 'MacBook Pro'),
(8, 5, 105, 24, '2025-02-25 17:45:00', 'iPhone 15 Pro');
'''
    },
    'ai_compute': {
        'id': 'ai_compute',
        'name': '🧠 AI & GPU Compute Infrastructure',
        'description': 'GPU cluster orchestration: AI foundation models, NVIDIA H100/A100 clusters, distributed training runs, and benchmark evaluations.',
        'default_query': '''-- ⚡ GPU Utilization & Model Training Efficiency Ranking
SELECT
    m.model_name,
    m.parameters_billions || 'B' AS model_size,
    c.cluster_name,
    c.gpu_type,
    t.gpu_count,
    t.training_hours,
    t.cost_usd,
    ROUND(t.cost_usd / NULLIF(t.training_hours, 0), 2) AS hourly_burn_rate,
    b.benchmark_name,
    b.score AS benchmark_accuracy
FROM training_runs t
INNER JOIN models m ON t.model_id = m.model_id
INNER JOIN gpu_clusters c ON t.cluster_id = c.cluster_id
LEFT JOIN benchmarks b ON m.model_id = b.model_id
ORDER BY t.cost_usd DESC;''',
        'schema_sql': '''
CREATE TABLE models (
    model_id INTEGER PRIMARY KEY,
    model_name TEXT NOT NULL,
    architecture TEXT NOT NULL,
    parameters_billions DECIMAL(5,1) NOT NULL,
    release_date DATE NOT NULL
);

CREATE TABLE gpu_clusters (
    cluster_id INTEGER PRIMARY KEY,
    cluster_name TEXT NOT NULL,
    gpu_type TEXT NOT NULL, -- H100 80GB, A100 80GB, L40S
    total_gpus INTEGER NOT NULL,
    cloud_provider TEXT NOT NULL -- AWS, Lambda, GCP, CoreWeave
);

CREATE TABLE training_runs (
    run_id INTEGER PRIMARY KEY,
    model_id INTEGER NOT NULL,
    cluster_id INTEGER NOT NULL,
    gpu_count INTEGER NOT NULL,
    training_hours DECIMAL(6,1) NOT NULL,
    cost_usd DECIMAL(12,2) NOT NULL,
    status TEXT NOT NULL, -- Succeeded, Failed, In Progress
    FOREIGN KEY (model_id) REFERENCES models(model_id),
    FOREIGN KEY (cluster_id) REFERENCES gpu_clusters(cluster_id)
);

CREATE TABLE benchmarks (
    benchmark_id INTEGER PRIMARY KEY,
    model_id INTEGER NOT NULL,
    benchmark_name TEXT NOT NULL, -- MMLU, HumanEval, GSM8K
    score DECIMAL(5,2) NOT NULL,
    FOREIGN KEY (model_id) REFERENCES models(model_id)
);

INSERT INTO models VALUES
(1, 'DeepSeek-V3', 'Mixture-of-Experts (MoE)', 671.0, '2024-12-26'),
(2, 'Llama-3.3-70B', 'Dense Transformer', 70.0, '2024-12-06'),
(3, 'Qwen-2.5-Coder', 'Code LLM', 32.0, '2024-11-15'),
(4, 'Mistral-Large-2', 'Dense Transformer', 123.0, '2024-07-24');

INSERT INTO gpu_clusters VALUES
(101, 'HyperScale Cluster Alpha', 'NVIDIA H100 80GB SXM5', 2048, 'CoreWeave'),
(102, 'Lambda Cloud Cluster Bravo', 'NVIDIA H100 80GB', 512, 'Lambda Labs'),
(103, 'AWS US-East-1 p5.48xlarge', 'NVIDIA H100 SXM5', 256, 'AWS'),
(104, 'GCP A3 High-Mega Cluster', 'NVIDIA H100 80GB', 1024, 'Google Cloud');

INSERT INTO training_runs VALUES
(1, 1, 101, 2048, 672.0, 5800000.00, 'Succeeded'),
(2, 2, 102, 512, 340.0, 850000.00, 'Succeeded'),
(3, 3, 103, 256, 180.0, 320000.00, 'Succeeded'),
(4, 4, 104, 1024, 450.0, 1950000.00, 'Succeeded');

INSERT INTO benchmarks VALUES
(1, 1, 'MMLU Pro', 75.9),
(2, 1, 'HumanEval Code', 82.6),
(3, 2, 'MMLU Pro', 68.4),
(4, 2, 'HumanEval Code', 72.8),
(5, 3, 'HumanEval Code', 86.2);
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
    }
}

# Thread-local storage for in-memory databases per thread/request
_db_cache = {}
_db_lock = threading.Lock()

def get_sandboxed_connection(dataset_id='scott_tiger'):
    if dataset_id not in DATASETS:
        dataset_id = 'scott_tiger'
    
    # Initialize fresh in-memory SQLite connection
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Load schema & seed data
    schema_sql = DATASETS[dataset_id]['schema_sql']
    conn.executescript(schema_sql)
    
    return conn

def execute_sql_sandbox(sql_text, dataset_id='scott_tiger', max_rows=500):
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

def trace_sql_execution(sql_text, dataset_id='scott_tiger'):
    """
    Step-by-Step / Line-by-Line Interactive SQL Execution Tracer.
    Simulates the true SQL Logical Query Processing Pipeline:
    1. FROM (Base buffer creation)
    2. JOIN / ON (Cartesian product & join condition filtering)
    3. WHERE (Row-by-row boolean predicate filtering)
    4. GROUP BY (Aggregate partitioning)
    5. HAVING (Aggregate bucket filtering)
    6. SELECT (Expression projection, aliases & window functions)
    7. DISTINCT (Row tuple deduplication)
    8. ORDER BY (Output buffer sorting)
    9. LIMIT / OFFSET (Result set window slicing)
    """
    if not sql_text or not sql_text.strip():
        return {'success': False, 'error': 'Query is empty. Please enter an SQL query to debug.'}
        
    conn = get_sandboxed_connection(dataset_id)
    cur = conn.cursor()
    
    clean_sql = sql_text.strip().rstrip(';')
    try:
        cur.execute(clean_sql)
        final_cols = [d[0] for d in cur.description] if cur.description else []
        final_rows = [[item for item in r] for r in cur.fetchall()]
    except Exception as e:
        conn.close()
        return {'success': False, 'error': f"SQL Syntax / Execution Error: {str(e)}"}
        
    raw_lines = sql_text.split('\n')
    line_entries = []
    current_clause = None
    
    clause_regex = re.compile(
        r'^\s*(WITH|SELECT\s+DISTINCT|SELECT|FROM|LEFT\s+OUTER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+OUTER\s+JOIN|INNER\s+JOIN|CROSS\s+JOIN|JOIN|WHERE|GROUP\s+BY|HAVING|ORDER\s+BY|LIMIT|OFFSET)\b',
        re.IGNORECASE
    )
    
    for idx, line in enumerate(raw_lines):
        line_num = idx + 1
        stripped = line.strip()
        if not stripped or stripped.startswith('--') or stripped.startswith('/*'):
            continue
        
        m = clause_regex.match(stripped)
        if m:
            matched = m.group(1).upper()
            if 'JOIN' in matched:
                current_clause = 'JOIN'
            elif 'SELECT' in matched:
                current_clause = 'SELECT'
            elif 'GROUP' in matched:
                current_clause = 'GROUP BY'
            else:
                current_clause = matched
        
        line_entries.append({
            'line_number': line_num,
            'line_text': line,
            'clause': current_clause or 'SELECT'
        })
    
    steps = []
    
    from_lines = [e for e in line_entries if e['clause'] == 'FROM']
    join_lines = [e for e in line_entries if e['clause'] == 'JOIN']
    where_lines = [e for e in line_entries if e['clause'] == 'WHERE']
    group_lines = [e for e in line_entries if e['clause'] == 'GROUP BY']
    having_lines = [e for e in line_entries if e['clause'] == 'HAVING']
    select_lines = [e for e in line_entries if e['clause'] == 'SELECT']
    order_lines = [e for e in line_entries if e['clause'] == 'ORDER BY']
    limit_lines = [e for e in line_entries if e['clause'] == 'LIMIT']
    
    from_match = re.search(r'\bFROM\s+([a-zA-Z0-9_]+(?:\s+(?:AS\s+)?[a-zA-Z0-9_]+)?)', clean_sql, re.IGNORECASE)
    from_clause_sql = from_match.group(0) if from_match else 'FROM emp'
    
    # 1. Step FROM
    if from_lines:
        first_from_line = from_lines[0]
        step_from_sql = f"SELECT * {from_clause_sql}"
        try:
            cur.execute(step_from_sql)
            cols = [d[0] for d in cur.description]
            rows = [[item for item in r] for r in cur.fetchall()]
            steps.append({
                'line_number': first_from_line['line_number'],
                'line_text': first_from_line['line_text'],
                'clause': 'FROM',
                'phase_name': '1. FROM Clause (Virtual Table Buffer)',
                'phase_badge': 'FROM',
                'badge_color': '#38bdf8',
                'explanation': f"Loaded base table into virtual memory buffer. Scanned {len(rows)} raw rows.",
                'columns': cols,
                'rows': rows[:100],
                'row_count': len(rows),
                'status_note': f"Materialized {len(rows)} candidate rows."
            })
        except Exception:
            pass

    # 2. Step JOIN
    if join_lines:
        for jl in join_lines:
            join_str = jl['line_text'].strip()
            step_join_sql = f"SELECT * {from_clause_sql} {join_str}"
            try:
                cur.execute(step_join_sql)
                cols = [d[0] for d in cur.description]
                rows = [[item for item in r] for r in cur.fetchall()]
                steps.append({
                    'line_number': jl['line_number'],
                    'line_text': jl['line_text'],
                    'clause': 'JOIN',
                    'phase_name': '2. JOIN & ON Predicate Resolution',
                    'phase_badge': 'JOIN',
                    'badge_color': '#a855f7',
                    'explanation': f"Evaluated join condition '{join_str}'. Matched {len(rows)} composite records in virtual buffer.",
                    'columns': cols,
                    'rows': rows[:100],
                    'row_count': len(rows),
                    'status_note': f"Combined dataset now holds {len(rows)} rows."
                })
            except Exception:
                pass

    # 3. Step WHERE
    if where_lines:
        first_where = where_lines[0]
        where_match = re.search(r'\bWHERE\s+(.*?)(?:\bGROUP\s+BY|\bORDER\s+BY|\bLIMIT|$)', clean_sql, re.IGNORECASE | re.DOTALL)
        where_clause = where_match.group(1).strip() if where_match else ''
        
        joins_match = re.findall(r'((?:LEFT\s+|RIGHT\s+|INNER\s+|CROSS\s+)?JOIN\s+.*?ON\s+.*?)(?=\bWHERE\b|\bGROUP\b|\bORDER\b|\bLIMIT\b|$)', clean_sql, re.IGNORECASE | re.DOTALL)
        joins_part = (' ' + ' '.join(joins_match)) if joins_match else ''
            
        step_where_sql = f"SELECT * {from_clause_sql} {joins_part} WHERE {where_clause}"
        try:
            cur.execute(step_where_sql)
            cols = [d[0] for d in cur.description]
            rows = [[item for item in r] for r in cur.fetchall()]
            prev_count = steps[-1]['row_count'] if steps else len(rows)
            filtered_out = max(0, prev_count - len(rows))
            steps.append({
                'line_number': first_where['line_number'],
                'line_text': first_where['line_text'],
                'clause': 'WHERE',
                'phase_name': '3. WHERE Predicate Row Filtering',
                'phase_badge': 'WHERE',
                'badge_color': '#f59e0b',
                'explanation': f"Evaluated WHERE boolean condition. Filtered out {filtered_out} row(s) that did not qualify. Kept {len(rows)} matching candidate row(s).",
                'columns': cols,
                'rows': rows[:100],
                'row_count': len(rows),
                'status_note': f"Kept {len(rows)} rows ({filtered_out} discarded)."
            })
        except Exception:
            pass

    # 4. Step SELECT (Projections)
    first_sel = select_lines[0] if select_lines else line_entries[0]
    no_order_sql = re.sub(r'\bORDER\s+BY\s+.*$', '', clean_sql, flags=re.IGNORECASE | re.DOTALL)
    no_order_sql = re.sub(r'\bLIMIT\s+.*$', '', no_order_sql, flags=re.IGNORECASE | re.DOTALL)
    try:
        cur.execute(no_order_sql)
        cols = [d[0] for d in cur.description]
        rows = [[item for item in r] for r in cur.fetchall()]
        steps.append({
            'line_number': first_sel['line_number'],
            'line_text': first_sel['line_text'],
            'clause': 'SELECT',
            'phase_name': '4. SELECT Expression & Column Projection',
            'phase_badge': 'SELECT',
            'badge_color': '#10b981',
            'explanation': f"Projected {len(cols)} requested column(s) ({', '.join(cols[:5])}). Computed expressions, aliases, and window calculations.",
            'columns': cols,
            'rows': rows[:100],
            'row_count': len(rows),
            'status_note': f"Projected {len(cols)} columns across {len(rows)} rows."
        })
    except Exception:
        pass

    # 5. Step ORDER BY
    if order_lines:
        first_order = order_lines[0]
        no_limit_sql = re.sub(r'\bLIMIT\s+.*$', '', clean_sql, flags=re.IGNORECASE | re.DOTALL)
        try:
            cur.execute(no_limit_sql)
            cols = [d[0] for d in cur.description]
            rows = [[item for item in r] for r in cur.fetchall()]
            steps.append({
                'line_number': first_order['line_number'],
                'line_text': first_order['line_text'],
                'clause': 'ORDER BY',
                'phase_name': '5. ORDER BY Output Buffer Sorting',
                'phase_badge': 'ORDER BY',
                'badge_color': '#ec4899',
                'explanation': f"Sorted output buffer according to '{first_order['line_text'].strip()}'.",
                'columns': cols,
                'rows': rows[:100],
                'row_count': len(rows),
                'status_note': f"Sorted {len(rows)} rows."
            })
        except Exception:
            pass

    # 6. Step LIMIT
    if limit_lines:
        first_limit = limit_lines[0]
        steps.append({
            'line_number': first_limit['line_number'],
            'line_text': first_limit['line_text'],
            'clause': 'LIMIT',
            'phase_name': '6. LIMIT / OFFSET Result Window Slicing',
            'phase_badge': 'LIMIT',
            'badge_color': '#06b6d4',
            'explanation': f"Applied '{first_limit['line_text'].strip()}' to slice top {len(final_rows)} rows for final response.",
            'columns': final_cols,
            'rows': final_rows[:100],
            'row_count': len(final_rows),
            'status_note': f"Final output: {len(final_rows)} rows."
        })

    if not steps:
        steps.append({
            'line_number': 1,
            'line_text': raw_lines[0] if raw_lines else 'SELECT',
            'clause': 'SELECT',
            'phase_name': 'Query Execution',
            'phase_badge': 'EXECUTE',
            'badge_color': '#38bdf8',
            'explanation': 'Executed SQL query and materialized final result set.',
            'columns': final_cols,
            'rows': final_rows[:100],
            'row_count': len(final_rows),
            'status_note': f"Materialized {len(final_rows)} rows."
        })

    for idx, s in enumerate(steps):
        s['step_index'] = idx
        s['total_steps'] = len(steps)

    conn.close()
    return {
        'success': True,
        'dataset_id': dataset_id,
        'dataset_name': DATASETS.get(dataset_id, {}).get('name', 'Custom DB'),
        'total_steps': len(steps),
        'steps': steps,
        'final_columns': final_cols,
        'final_rows': final_rows[:100],
        'final_row_count': len(final_rows)
    }

