import re

def generate_interview_prep(title, company, skills, eligibility=""):
    """
    Generates tailored interview preparation materials including:
    - Technical questions & solutions
    - Coding challenges & live debugger links
    - Behavioral & HR questions
    - Round-by-round strategy roadmap
    """
    lower_title = (title or "").lower()
    lower_skills = (skills or "").lower()

    # Determine domain
    is_qa = any(k in lower_title or k in lower_skills for k in ['test', 'qa', 'selenium', 'automation', 'testng', 'quality'])
    is_data = any(k in lower_title or k in lower_skills for k in ['data analyst', 'business analyst', 'tableau', 'power bi', 'excel', 'sql', 'analytics'])
    is_aiml = any(k in lower_title or k in lower_skills for k in ['ai', 'ml', 'machine learning', 'deep learning', 'nlp', 'computer vision'])
    is_dev = not (is_qa or is_data or is_aiml)

    # 1. Technical Questions
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
                "a": "Use dynamic XPath methods like `contains()`, `starts-with()`, `text()`, or XPath axes (`ancestor`, `following-sibling`, `parent`) instead of brittle absolute paths."
            },
            {
                "q": "What is the difference between `@BeforeMethod` and `@BeforeClass` in TestNG?",
                "a": "`@BeforeClass` runs once before the first test method in the current class, while `@BeforeMethod` executes before each individual test method."
            },
            {
                "q": "How do you validate REST API response codes and JSON payload using Postman / RestAssured?",
                "a": "In RestAssured: `given().when().get('/endpoint').then().assertThat().statusCode(200).body('status', equalTo('ACTIVE'))`."
            }
        ]
        practice_lang = "java"
    elif is_data:
        tech_questions = [
            {
                "q": "What is the difference between WHERE and HAVING clauses in SQL?",
                "a": "`WHERE` filters rows before any groupings are applied, while `HAVING` filters aggregated groups after `GROUP BY` has executed."
            },
            {
                "q": "Explain SQL Window functions: `ROW_NUMBER()`, `RANK()`, and `DENSE_RANK()`.",
                "a": "`ROW_NUMBER()` assigns unique sequential integers. `RANK()` assigns identical ranks to ties and skips ranks. `DENSE_RANK()` assigns identical ranks to ties without skipping rank numbers."
            },
            {
                "q": "How do you handle NULL and missing values during data cleaning in Python/Pandas?",
                "a": "Use `.isna().sum()` to identify missing values. Impute with mean/median using `.fillna()` or remove with `.dropna(subset=[...])` depending on variance impact."
            },
            {
                "q": "What is the difference between Star Schema and Snowflake Schema in Data Warehousing?",
                "a": "Star Schema has denormalized dimension tables directly connected to the central Fact table. Snowflake Schema normalizes dimension tables into sub-dimensions to minimize redundancy."
            },
            {
                "q": "How do you calculate MoM (Month-over-Month) growth in SQL?",
                "a": "Use `LAG(revenue, 1) OVER (ORDER BY month)` to fetch the previous month's revenue and compute `(revenue - prev_revenue) / prev_revenue * 100`."
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

    # 2. Company & Behavioral Questions
    company_name = company or "Target Company"
    behavioral_questions = [
        {
            "q": f"Why do you want to join {company_name} as a {title}?",
            "tip": f"Research {company_name}'s culture, recent client projects, or engineering blog. Connect your passion for {skills.split(',')[0] if skills else 'technology'} with their business goals."
        },
        {
            "q": "Describe a challenging technical bug or academic project roadblock and how you resolved it.",
            "tip": "Use the STAR framework: Situation, Task, Action (specific tools/logic you used), Result (quantified outcome, e.g. 40% performance gain)."
        },
        {
            "q": "How do you stay up-to-date with emerging software tools and industry practices?",
            "tip": "Mention GitHub open-source contributions, technical newsletters, interactive coding platforms, and personal side-projects."
        }
    ]

    # 3. Round-by-Round Strategy Roadmap
    rounds_roadmap = [
        {
            "round": "Round 1: Online Assessment (OA)",
            "focus": "Aptitude, Quantitative Logic & Core Coding",
            "tips": "Practice Speed Math, Data Interpretation, and 2 Medium-level algorithmic coding challenges (Arrays, Strings, HashMaps)."
        },
        {
            "round": "Round 2: Technical Interview 1",
            "focus": f"Core Tech Stack ({skills}) & Live Coding",
            "tips": "Be ready to explain time/space complexities, write clean modular code, and explain your resume projects end-to-end."
        },
        {
            "round": "Round 3: System Design & Problem Solving",
            "focus": "Database Schema, API Design & Scalability",
            "tips": "Diagram your thought process, ask clarifying questions on requirements, and handle edge cases proactively."
        },
        {
            "round": "Round 4: Managerial & HR Discussion",
            "focus": f"Cultural Alignment, Learning Agility & {company_name} Values",
            "tips": "Demonstrate strong communication, team collaboration mindset, and enthusiasm for continuous learning."
        }
    ]

    return {
        "domain": "QA / Automation" if is_qa else ("Data Analytics" if is_data else ("AI / ML" if is_aiml else "Software Engineering")),
        "practice_lang": practice_lang,
        "tech_questions": tech_questions,
        "behavioral_questions": behavioral_questions,
        "rounds_roadmap": rounds_roadmap,
    }
