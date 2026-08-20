SQL_CHALLENGES = [
    {
        'id': 'scott-tiger-emp-mgr',
        'title': '1. Scott/Tiger: Employees & Their Direct Managers',
        'difficulty': 'Easy',
        'dataset_id': 'scott_tiger',
        'category': 'Self Joins & NULL Handling',
        'description': '''Using the classic Scott/Tiger <code>emp</code> table, list every employee's name (<code>ENAME</code>), their job title (<code>JOB</code>), and their direct manager's name (<code>MGR_NAME</code>). If an employee has no manager (e.g. <code>KING</code>), display <code>'TOP BOSS'</code>.''',
        'starter_sql': '''-- Self Join on emp to get employee and manager names
SELECT
    e.ename AS employee_name,
    e.job,
    COALESCE(m.ename, 'TOP BOSS') AS manager_name
FROM emp e
LEFT JOIN emp m ON e.mgr = m.empno
ORDER BY e.ename;''',
        'solution_sql': '''SELECT
    e.ename AS employee_name,
    e.job,
    COALESCE(m.ename, 'TOP BOSS') AS manager_name
FROM emp e
LEFT JOIN emp m ON e.mgr = m.empno
ORDER BY e.ename;'''
    },
    {
        'id': 'scott-tiger-salgrade',
        'title': '2. Scott/Tiger: Department Salary Grades Breakdown',
        'difficulty': 'Medium',
        'dataset_id': 'scott_tiger',
        'category': 'Multi-Table Joins & Non-Equi Joins',
        'description': '''Find all employees, their department name, their salary, and their salary grade from <code>salgrade</code> where salary is between <code>losal</code> and <code>hisal</code>. Order by salary descending.''',
        'starter_sql': '''SELECT
    e.ename,
    d.dname AS department,
    e.sal AS salary,
    s.grade AS salary_grade
FROM emp e
JOIN dept d ON e.deptno = d.deptno
JOIN salgrade s ON e.sal BETWEEN s.losal AND s.hisal
ORDER BY e.sal DESC;''',
        'solution_sql': '''SELECT
    e.ename,
    d.dname AS department,
    e.sal AS salary,
    s.grade AS salary_grade
FROM emp e
JOIN dept d ON e.deptno = d.deptno
JOIN salgrade s ON e.sal BETWEEN s.losal AND s.hisal
ORDER BY e.sal DESC;'''
    },
    {
        'id': 'nth-highest-salary',
        'title': '3. Second Highest Salary (LeetCode #176)',
        'difficulty': 'Easy',
        'dataset_id': 'faang',
        'category': 'Window Functions & Aggregation',
        'description': '''Write an SQL query to find the <strong>second highest salary</strong> from the <code>employees</code> table.''',
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
        'title': '4. Department Top 3 Salaries (LeetCode #185)',
        'difficulty': 'Hard',
        'dataset_id': 'faang',
        'category': 'DENSE_RANK & Partitioning',
        'description': '''Find the top 3 unique salaries in each department using <code>DENSE_RANK()</code>.''',
        'starter_sql': '''WITH RankedSalaries AS (
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
        'id': 'ott-top-shows',
        'title': '5. Netflix OTT: Top 3 Most Streamed Titles per Genre',
        'difficulty': 'Medium',
        'dataset_id': 'ott_streaming',
        'category': 'OTT Media Analytics & Partitioning',
        'description': '''Find the top streaming titles in each genre by total view count from <code>watch_history</code>.''',
        'starter_sql': '''WITH GenreViews AS (
    SELECT
        g.genre_name,
        m.title,
        COUNT(w.watch_id) AS total_views,
        DENSE_RANK() OVER (PARTITION BY g.genre_name ORDER BY COUNT(w.watch_id) DESC) AS rnk
    FROM movies_shows m
    JOIN genres g ON m.genre_id = g.genre_id
    LEFT JOIN watch_history w ON m.show_id = w.show_id
    GROUP BY g.genre_name, m.title
)
SELECT genre_name, title, total_views
FROM GenreViews
WHERE rnk <= 3
ORDER BY genre_name, total_views DESC;''',
        'solution_sql': '''WITH GenreViews AS (
    SELECT
        g.genre_name,
        m.title,
        COUNT(w.watch_id) AS total_views,
        DENSE_RANK() OVER (PARTITION BY g.genre_name ORDER BY COUNT(w.watch_id) DESC) AS rnk
    FROM movies_shows m
    JOIN genres g ON m.genre_id = g.genre_id
    LEFT JOIN watch_history w ON m.show_id = w.show_id
    GROUP BY g.genre_name, m.title
)
SELECT genre_name, title, total_views
FROM GenreViews
WHERE rnk <= 3
ORDER BY genre_name, total_views DESC;'''
    },
    {
        'id': 'ai-gpu-burn-rate',
        'title': '6. AI Compute: Expensive Training Runs Exceeding $500k',
        'difficulty': 'Easy',
        'dataset_id': 'ai_compute',
        'category': 'GPU Infrastructure & Cost Analysis',
        'description': '''Find all AI model training runs that cost &ge; $500,000. Show model name, GPU cluster, GPU count, and total cost in USD.''',
        'starter_sql': '''SELECT
    m.model_name,
    c.cluster_name,
    c.gpu_type,
    t.gpu_count,
    t.training_hours,
    t.cost_usd
FROM training_runs t
JOIN models m ON t.model_id = m.model_id
JOIN gpu_clusters c ON t.cluster_id = c.cluster_id
WHERE t.cost_usd >= 500000.00
ORDER BY t.cost_usd DESC;''',
        'solution_sql': '''SELECT
    m.model_name,
    c.cluster_name,
    c.gpu_type,
    t.gpu_count,
    t.training_hours,
    t.cost_usd
FROM training_runs t
JOIN models m ON t.model_id = m.model_id
JOIN gpu_clusters c ON t.cluster_id = c.cluster_id
WHERE t.cost_usd >= 500000.00
ORDER BY t.cost_usd DESC;'''
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
