SQL_CHALLENGES = [
    {
        'id': 'nth-highest-salary',
        'title': '1. Second Highest Salary (LeetCode #176)',
        'difficulty': 'Easy',
        'dataset_id': 'faang',
        'category': 'Window Functions & Aggregation',
        'description': '''Write an SQL query to find the <strong>second highest salary</strong> from the <code>employees</code> table. If there is no second highest salary, the query should return <code>NULL</code> or an empty row.''',
        'starter_sql': '''-- Write a query to find the 2nd highest salary in the company
SELECT DISTINCT salary AS SecondHighestSalary
FROM employees
ORDER BY salary DESC
LIMIT 1 OFFSET 1;''',
        'solution_sql': '''SELECT DISTINCT salary AS SecondHighestSalary
FROM employees
ORDER BY salary DESC
LIMIT 1 OFFSET 1;'''
    },
    {
        'id': 'department-top-3-salaries',
        'title': '2. Department Top 3 Salaries (LeetCode #185)',
        'difficulty': 'Hard',
        'dataset_id': 'faang',
        'category': 'DENSE_RANK & Partitioning',
        'description': '''A company's executives are interested in seeing who earns the most money in each of the company's departments. A high earner in a department is an employee who has a salary in the <strong>top three unique salaries</strong> for that department.<br/><br/>Write a solution to find the employees who are high earners in each of the departments.''',
        'starter_sql': '''-- Find the top 3 unique salaries in each department using DENSE_RANK()
WITH RankedSalaries AS (
    SELECT
        d.department_name AS Department,
        e.first_name || ' ' || e.last_name AS Employee,
        e.salary AS Salary,
        DENSE_RANK() OVER (PARTITION BY e.department_id ORDER BY e.salary DESC) AS rnk
    FROM employees e
    JOIN departments d ON e.department_id = d.department_id
)
SELECT Department, Employee, Salary
FROM RankedSalaries
WHERE rnk <= 3
ORDER BY Department, Salary DESC;''',
        'solution_sql': '''WITH RankedSalaries AS (
    SELECT
        d.department_name AS Department,
        e.first_name || ' ' || e.last_name AS Employee,
        e.salary AS Salary,
        DENSE_RANK() OVER (PARTITION BY e.department_id ORDER BY e.salary DESC) AS rnk
    FROM employees e
    JOIN departments d ON e.department_id = d.department_id
)
SELECT Department, Employee, Salary
FROM RankedSalaries
WHERE rnk <= 3
ORDER BY Department, Salary DESC;'''
    },
    {
        'id': 'employees-earning-more-than-managers',
        'title': '3. Employees Earning More Than Their Managers (LeetCode #181)',
        'difficulty': 'Easy',
        'dataset_id': 'faang',
        'category': 'Self Joins',
        'description': '''Write a solution to find the employees who earn more than their managers. Return the employee's full name and their salary alongside their manager's name and salary.''',
        'starter_sql': '''-- Perform a SELF JOIN on employees where employee salary > manager salary
SELECT
    e.first_name || ' ' || e.last_name AS Employee,
    e.salary AS EmployeeSalary,
    m.first_name || ' ' || m.last_name AS Manager,
    m.salary AS ManagerSalary
FROM employees e
JOIN employees m ON e.manager_id = m.employee_id
WHERE e.salary > m.salary;''',
        'solution_sql': '''SELECT
    e.first_name || ' ' || e.last_name AS Employee,
    e.salary AS EmployeeSalary,
    m.first_name || ' ' || m.last_name AS Manager,
    m.salary AS ManagerSalary
FROM employees e
JOIN employees m ON e.manager_id = m.employee_id
WHERE e.salary > m.salary;'''
    },
    {
        'id': 'customers-who-never-order',
        'title': '4. Customers Who Never Order (LeetCode #183)',
        'difficulty': 'Easy',
        'dataset_id': 'ecommerce',
        'category': 'Anti-Joins & NOT EXISTS',
        'description': '''Write an SQL query to report all customers who never placed any orders. Return customer ID, full name, email, and country.''',
        'starter_sql': '''-- Find customers who have no corresponding records in the orders table
SELECT c.customer_id, c.full_name, c.email, c.country
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;''',
        'solution_sql': '''SELECT c.customer_id, c.full_name, c.email, c.country
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;'''
    },
    {
        'id': 'mom-revenue-growth',
        'title': '5. Month-over-Month (MoM) Revenue Growth Rate',
        'difficulty': 'Medium',
        'dataset_id': 'ecommerce',
        'category': 'Window LAG & Time-Series',
        'description': '''Calculate the total delivered revenue for each month and the percentage growth rate compared to the previous month.''',
        'starter_sql': '''WITH MonthlyRev AS (
    SELECT
        strftime('%Y-%m', order_date) AS order_month,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY strftime('%Y-%m', order_date)
)
SELECT
    order_month,
    revenue,
    LAG(revenue, 1) OVER (ORDER BY order_month) AS prev_revenue,
    ROUND(
        (revenue - LAG(revenue, 1) OVER (ORDER BY order_month)) * 100.0 /
        NULLIF(LAG(revenue, 1) OVER (ORDER BY order_month), 0), 2
    ) AS mom_growth_pct
FROM MonthlyRev;''',
        'solution_sql': '''WITH MonthlyRev AS (
    SELECT
        strftime('%Y-%m', order_date) AS order_month,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY strftime('%Y-%m', order_date)
)
SELECT
    order_month,
    revenue,
    LAG(revenue, 1) OVER (ORDER BY order_month) AS prev_revenue,
    ROUND(
        (revenue - LAG(revenue, 1) OVER (ORDER BY order_month)) * 100.0 /
        NULLIF(LAG(revenue, 1) OVER (ORDER BY order_month), 0), 2
    ) AS mom_growth_pct
FROM MonthlyRev;'''
    },
    {
        'id': 'cumulative-customer-spend',
        'title': '6. Cumulative Running Total per Customer',
        'difficulty': 'Medium',
        'dataset_id': 'ecommerce',
        'category': 'Running Sum Windows',
        'description': '''Write a query to calculate the cumulative running total spent by each customer ordered chronologically by <code>order_date</code>.''',
        'starter_sql': '''SELECT
    order_id,
    customer_id,
    order_date,
    total_amount,
    SUM(total_amount) OVER (
        PARTITION BY customer_id
        ORDER BY order_date, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_customer_total
FROM orders
ORDER BY customer_id, order_date;''',
        'solution_sql': '''SELECT
    order_id,
    customer_id,
    order_date,
    total_amount,
    SUM(total_amount) OVER (
        PARTITION BY customer_id
        ORDER BY order_date, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_customer_total
FROM orders
ORDER BY customer_id, order_date;'''
    },
    {
        'id': 'fraudulent-high-volume-transactions',
        'title': '7. FinTech Suspicious Transaction Spike Detector',
        'difficulty': 'Hard',
        'dataset_id': 'fintech',
        'category': 'Financial Fraud Analytics',
        'description': '''Find all accounts that performed transactions of amount &ge; $3,000.00. Show account holder name, account type, transaction amount, and merchant name.''',
        'starter_sql': '''SELECT
    a.customer_name,
    a.account_type,
    t.transaction_id,
    t.transaction_type,
    t.amount,
    t.merchant,
    t.transaction_time
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
WHERE t.amount >= 3000.00
ORDER BY t.amount DESC;''',
        'solution_sql': '''SELECT
    a.customer_name,
    a.account_type,
    t.transaction_id,
    t.transaction_type,
    t.amount,
    t.merchant,
    t.transaction_time
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
WHERE t.amount >= 3000.00
ORDER BY t.amount DESC;'''
    },
    {
        'id': 'social-most-influential-creators',
        'title': '8. Social Network Influence & Engagement Score',
        'difficulty': 'Medium',
        'dataset_id': 'social',
        'category': 'Aggregation & NULL Handling',
        'description': '''Calculate the total likes, total posts, and engagement ratio for all creators in the social network, ordered by total likes descending.''',
        'starter_sql': '''SELECT
    u.username,
    u.followers_count,
    COUNT(p.post_id) AS total_posts,
    COALESCE(SUM(p.likes_count), 0) AS total_likes,
    COALESCE(SUM(p.comments_count), 0) AS total_comments
FROM users u
LEFT JOIN posts p ON u.user_id = p.user_id
GROUP BY u.user_id, u.username, u.followers_count
ORDER BY total_likes DESC;''',
        'solution_sql': '''SELECT
    u.username,
    u.followers_count,
    COUNT(p.post_id) AS total_posts,
    COALESCE(SUM(p.likes_count), 0) AS total_likes,
    COALESCE(SUM(p.comments_count), 0) AS total_comments
FROM users u
LEFT JOIN posts p ON u.user_id = p.user_id
GROUP BY u.user_id, u.username, u.followers_count
ORDER BY total_likes DESC;'''
    }
]

def get_challenges_list():
    return [
        {
            'id': c['id'],
            'title': c['title'],
            'difficulty': c['difficulty'],
            'dataset_id': c['dataset_id'],
            'category': c['category'],
            'description': c['description'],
            'starter_sql': c['starter_sql']
        }
        for c in SQL_CHALLENGES
    ]

def get_challenge_by_id(challenge_id):
    for c in SQL_CHALLENGES:
        if c['id'] == challenge_id:
            return c
    return None
