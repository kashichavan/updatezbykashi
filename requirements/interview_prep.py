import re
import urllib.parse


def generate_interview_prep(title, company, skills, eligibility=""):
    """
    Generates comprehensive preparation materials including:
    - Previously asked interview question links & resources
    - Technical questions & solutions
    - Coding challenges with direct live debugger practice links
    - Company-specific exam pattern & syllabus
    - Behavioral & HR questions with STAR framework tips
    - Round-by-round strategy roadmap
    """
    lower_title = (title or "").lower()
    lower_skills = (skills or "").lower()
    comp_name = company or "Target Company"

    # Determine domain
    is_qa = any(k in lower_title or k in lower_skills for k in ['test', 'qa', 'selenium', 'automation', 'testng', 'quality'])
    is_data = any(k in lower_title or k in lower_skills for k in ['data analyst', 'business analyst', 'tableau', 'power bi', 'excel', 'sql', 'analytics'])
    is_aiml = any(k in lower_title or k in lower_skills for k in ['ai', 'ml', 'machine learning', 'deep learning', 'nlp', 'computer vision'])
    is_dev = not (is_qa or is_data or is_aiml)

    domain_name = "QA & Automation Testing" if is_qa else ("Data Analytics & SQL" if is_data else ("AI & Machine Learning" if is_aiml else "Software Engineering & Full Stack"))

    # 1. Technical Questions & Solutions
    tech_questions = []
    if is_qa:
        tech_questions = [
            {
                "q": "What is the difference between Implicit Wait, Explicit Wait, and Fluent Wait in Selenium?",
                "a": "Implicit Wait sets a global timeout for all element lookups. Explicit Wait pauses execution until a specific ExpectedCondition (e.g. elementToBeClickable) is met. Fluent Wait allows defining polling frequency and ignoring specific exceptions like NoSuchElementException."
            },
            {
                "q": "Explain the Page Object Model (POM) and its advantages in Test Automation.",
                "a": "POM is a design pattern that creates an object repository for web UI elements. It separates test scripts from page locators, reducing code duplication and making maintenance easy when UI elements change."
            },
            {
                "q": "How do you handle dynamic WebElements whose ID changes on page reload?",
                "a": "Use dynamic XPath methods like contains(), starts-with(), text(), or XPath axes (ancestor, following-sibling, parent) instead of brittle absolute paths."
            },
            {
                "q": "What is the difference between @BeforeMethod and @BeforeClass in TestNG?",
                "a": "@BeforeClass runs once before the first test method in the current class, while @BeforeMethod executes before each individual test method."
            },
            {
                "q": "How do you validate REST API response codes and JSON payload using Postman / RestAssured?",
                "a": "In RestAssured: given().when().get('/endpoint').then().assertThat().statusCode(200).body('status', equalTo('ACTIVE'))."
            }
        ]
        practice_lang = "java"
    elif is_data:
        tech_questions = [
            {
                "q": "What is the difference between WHERE and HAVING clauses in SQL?",
                "a": "WHERE filters rows before any groupings are applied, while HAVING filters aggregated groups after GROUP BY has executed."
            },
            {
                "q": "Explain SQL Window functions: ROW_NUMBER(), RANK(), and DENSE_RANK().",
                "a": "ROW_NUMBER() assigns unique sequential integers. RANK() assigns identical ranks to ties and skips ranks. DENSE_RANK() assigns identical ranks to ties without skipping rank numbers."
            },
            {
                "q": "How do you handle NULL and missing values during data cleaning in Python/Pandas?",
                "a": "Use .isna().sum() to identify missing values. Impute with mean/median using .fillna() or remove with .dropna(subset=[...]) depending on variance impact."
            },
            {
                "q": "What is the difference between Star Schema and Snowflake Schema in Data Warehousing?",
                "a": "Star Schema has denormalized dimension tables directly connected to the central Fact table. Snowflake Schema normalizes dimension tables into sub-dimensions to minimize redundancy."
            },
            {
                "q": "How do you calculate MoM (Month-over-Month) growth in SQL?",
                "a": "Use LAG(revenue, 1) OVER (ORDER BY month) to fetch the previous month's revenue and compute (revenue - prev_revenue) / prev_revenue * 100."
            }
        ]
        practice_lang = "python"
    elif is_aiml:
        tech_questions = [
            {
                "q": "What is the bias-variance tradeoff and how do you prevent overfitting?",
                "a": "High bias leads to underfitting (oversimplified model), high variance leads to overfitting (captures noise). Mitigate using L1/L2 Regularization, Dropout, Cross-Validation, and data augmentation."
            },
            {
                "q": "Explain the difference between Precision, Recall, and F1-Score.",
                "a": "Precision = TP / (TP + FP) (correctness of positive predictions). Recall = TP / (TP + FN) (coverage of actual positives). F1-Score is the harmonic mean of Precision and Recall."
            },
            {
                "q": "How does Gradient Descent work and what is the role of Learning Rate?",
                "a": "It optimizes loss functions by iteratively moving weights in the direction of negative gradient. A large learning rate may overshoot the minimum; a small rate causes slow convergence."
            },
            {
                "q": "What is the difference between Supervised, Unsupervised, and Self-Supervised learning?",
                "a": "Supervised uses labeled data (X -> y). Unsupervised finds hidden patterns in unlabeled data (clustering/PCA). Self-supervised generates labels from input data (e.g. masked language modeling in BERT/Transformers)."
            }
        ]
        practice_lang = "python"
    else:
        tech_questions = [
            {
                "q": f"Explain OOP (Object-Oriented Programming) principles with real-world examples in {skills.split(',')[0] if skills else 'Python/Java'}.",
                "a": "1. Encapsulation (data hiding via private fields/getters). 2. Abstraction (hiding implementation complexity). 3. Inheritance (code reusability). 4. Polymorphism (method overriding/overloading)."
            },
            {
                "q": "What is the time and space complexity of QuickSort vs MergeSort?",
                "a": "QuickSort: Average O(N log N) time, O(log N) space. Worst O(N^2). MergeSort: Guaranteed O(N log N) time, but requires O(N) auxiliary space."
            },
            {
                "q": "Explain the difference between SQL Indexing (B-Tree vs Hash) and when not to use an index.",
                "a": "Indexes speed up SELECT queries via B-Trees. However, they slow down INSERT, UPDATE, and DELETE operations because indexes must be updated on disk. Avoid on low-cardinality columns (e.g., boolean flags)."
            },
            {
                "q": "What happens under the hood when you enter a URL in a browser?",
                "a": "1. DNS lookup (resolves IP). 2. TCP 3-way handshake (SYN, SYN-ACK, ACK). 3. TLS negotiation for HTTPS. 4. HTTP GET request sent. 5. Server responds with HTML/CSS/JS. 6. Browser renders DOM & CSSOM tree."
            },
            {
                "q": "What is the difference between REST and GraphQL APIs?",
                "a": "REST uses multiple fixed endpoints with possible over/under-fetching. GraphQL uses a single endpoint allowing clients to query exact fields in a single request."
            }
        ]
        practice_lang = "python"

    # 2. Previously Asked Questions & Online Prep Links
    prep_links = [
        {
            "title": f"{comp_name} Top 50 Most Repeated Interview Questions",
            "tag": "PREVIOUS QUESTIONS",
            "desc": f"Master the frequently asked technical, aptitude, and problem-solving questions reported by candidates in recent {comp_name} hiring drives.",
            "url": f"/guides/mastering-technical-interviews/",
            "is_external": False
        },
        {
            "title": f"{comp_name} National Exam Pattern & Syllabus (2026)",
            "tag": "EXAM PATTERN",
            "desc": f"Complete section-by-section breakdown of Quantitative Aptitude, Logical Reasoning, Verbal Ability, and Coding round weightages for {comp_name}.",
            "url": f"/guides/off-campus-placement-blueprint/",
            "is_external": False
        },
        {
            "title": f"Top 50 {skills.split(',')[0] if skills else 'Coding'} Questions & Cheat Sheet",
            "tag": "CHEAT SHEET",
            "desc": f"High-yield syntax summaries, time complexity tables, and standard algorithmic patterns for technical interview rounds.",
            "url": f"/guides/python-interview-questions-cheat-sheet/",
            "is_external": False
        },
        {
            "title": f"Live Coding Sandbox & Algorithm Debugger",
            "tag": "PRACTICE SANDBOX",
            "desc": f"Practice real-time execution, step-by-step memory pointer tracing, and visual AST debugging in Python, JavaScript, and Java.",
            "url": f"/debugger/",
            "is_external": False
        }
    ]

    # 3. Previously Asked Coding Practice Challenges (Direct Interactive Practice)
    coding_challenges = [
        {
            "title": "Two Sum & Two Pointers Array Optimization",
            "difficulty": "Easy / Medium",
            "frequency": "Asked in 85% tech rounds",
            "url": "/debugger/"
        },
        {
            "title": "Reverse Linked List & Detect Cycle (Floyd's Algorithm)",
            "difficulty": "Medium",
            "frequency": "Frequently asked in core rounds",
            "url": "/debugger/"
        },
        {
            "title": "SQL Nth Highest Salary with DENSE_RANK() & Subqueries",
            "difficulty": "Medium",
            "frequency": "Top standard database question",
            "url": "/debugger/"
        },
        {
            "title": "Valid Parentheses & Stack Implementation",
            "difficulty": "Easy / Medium",
            "frequency": "Standard online assessment problem",
            "url": "/debugger/"
        }
    ]

    # 4. Behavioral & HR Questions
    behavioral_questions = [
        {
            "q": f"Why do you want to join {comp_name} as a {title}?",
            "tip": f"Highlight {comp_name}'s market reputation, recent tech innovations, and how your skills in {skills.split(',')[0] if skills else 'engineering'} directly solve their team's objectives."
        },
        {
            "q": "Describe a challenging bug or academic project roadblock and how you resolved it.",
            "tip": "Use the STAR method: Situation (project context), Task (what needed solving), Action (specific tools/logic applied), Result (quantifiable positive outcome)."
        },
        {
            "q": "How do you handle strict deadlines or sudden scope changes?",
            "tip": "Explain your prioritization strategy, proactive communication with mentors/peers, and agile mindset."
        }
    ]

    # 5. Round-by-Round Strategy Roadmap
    rounds_roadmap = [
        {
            "round": "Round 1: Online Assessment (OA)",
            "focus": "Aptitude, Quantitative Logic & 2 Coding Problems",
            "tips": "Focus on accuracy and speed. Practice arrays, strings, and standard arithmetic puzzles."
        },
        {
            "round": "Round 2: Technical Interview 1",
            "focus": f"Core Tech Stack ({skills}) & Live Code Tracing",
            "tips": "Explain your thought process aloud. Analyze time & space complexities before coding."
        },
        {
            "round": "Round 3: System Design & Problem Solving",
            "focus": "Database Schemas, APIs & Architecture Basics",
            "tips": "Clarify edge cases, diagram schemas cleanly, and discuss scalability trade-offs."
        },
        {
            "round": "Round 4: HR & Cultural Fit Discussion",
            "focus": f"{comp_name} Core Values, Learning Agility & Offer Terms",
            "tips": "Demonstrate passion, strong communication, and readiness for full-time collaboration."
        }
    ]

    return {
        "domain": domain_name,
        "practice_lang": practice_lang,
        "prep_links": prep_links,
        "coding_challenges": coding_challenges,
        "tech_questions": tech_questions,
        "behavioral_questions": behavioral_questions,
        "rounds_roadmap": rounds_roadmap,
    }
