"""
Comprehensive Multi-Language Learning Curriculum (Python 3, Java 17, JavaScript ES6+)
Interactive W3Schools / GeeksforGeeks style tutorials with real-world analogies,
production industry use cases, and live runnable debugger code.
"""

CURRICULUM = {
    'python': {
        'title': 'Python 3 Complete Programming Academy',
        'short_title': 'Python 3',
        'icon': '🐍',
        'color': '#3b82f6',
        'badge': 'Dynamic & High-Level',
        'summary': 'The definitive complete Python 3 masterclass from basic syntax to advanced metaprogramming, OOP, and asynchronous generators.',
        'topics': [
            {
                'slug': 'python-syntax-variables-types',
                'title': '1. Syntax, Variables & Dynamic Typing',
                'category': 'Fundamentals',
                'read_time': '6 min read',
                'analogy': {
                    'title': 'The Warehouse Storage Box with Sticky Labels',
                    'text': 'In Python, a variable is not a physical container holding data. Think of an object (like a string or number) as an item sitting in memory, and a variable as a sticky name tag taped to that item. When you write a = 10, Python places 10 in memory and sticks "a" on it. Assigning b = a simply attaches a second label "b" to the exact same item.'
                },
                'use_case': {
                    'company': 'Instagram & Django REST Framework',
                    'text': 'Dynamic typing allows Django APIs to instantly deserialize JSON payloads from mobile clients into Python dictionaries without rigid schema definitions.'
                },
                'concept_explanation': '''
<h3>1. Indentation as Block Syntax</h3>
<p>Python uses 4-space whitespace indentation instead of curly braces <code>{ }</code> to define code blocks.</p>
<h3>2. Built-in Primitive Types</h3>
<ul>
  <li><code>int</code>: Arbitrary-precision integers (e.g. <code>42</code>)</li>
  <li><code>float</code>: 64-bit IEEE 754 floating-point numbers (e.g. <code>3.14159</code>)</li>
  <li><code>str</code>: Unicode character sequence (e.g. <code>"Hello"</code>)</li>
  <li><code>bool</code>: Boolean truth values (<code>True</code> or <code>False</code>)</li>
</ul>
''',
                'starter_code': '''# Variables & Dynamic Memory Tagging
user_count = 100
app_name = "CloudEngine"
is_active = True
latency_ms = 4.85

print(f"App: {app_name} | Users: {user_count} | Active: {is_active}")
print(f"Type of user_count: {type(user_count).__name__}")
print(f"Memory Address ID: {id(user_count)}")
'''
            },
            {
                'slug': 'python-strings-formatting',
                'title': '2. Strings, Slicing & Modern f-strings',
                'category': 'Fundamentals',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Train of Passenger Compartments',
                    'text': 'A string is like a passenger train where each coach has a 0-indexed seat number. String slicing [start:end:step] is telling the conductor: "Give me coaches from seat 2 up to seat 8, skipping every alternate coach."'
                },
                'use_case': {
                    'company': 'Google Search & NLP Indexers',
                    'text': 'Tokenizing web search queries, stripping punctuation, converting to lowercase, and formatting internationalized strings.'
                },
                'concept_explanation': '''
<h3>String Operations & Immutability</h3>
<p>Python strings are immutable. Every transformation method (<code>.upper()</code>, <code>.strip()</code>, <code>.replace()</code>) returns a brand new string.</p>
''',
                'starter_code': '''# String Slicing & f-string Formatting
raw_query = "   DATA_ENGINEERING_ROADMAP_2026   "
cleaned = raw_query.strip().lower()

# Slicing: [start:stop:step]
prefix = cleaned[:4]
suffix = cleaned[-4:]
reversed_str = cleaned[::-1]

print(f"Cleaned: '{cleaned}'")
print(f"Prefix: '{prefix}' | Suffix: '{suffix}'")
print(f"Reversed: '{reversed_str}'")
'''
            },
            {
                'slug': 'python-operators-boolean-logic',
                'title': '3. Operators, Expressions & Truthiness',
                'category': 'Fundamentals',
                'read_time': '6 min read',
                'analogy': {
                    'title': 'The Airport Security Scanner Gate',
                    'text': 'Comparison and logical operators (and, or, not) act like an airport security checkpoint: you are only allowed to board if (has_ticket AND has_passport) AND NOT (has_prohibited_item).'
                },
                'use_case': {
                    'company': 'Stripe Risk Engines',
                    'text': 'Evaluating multi-factor fraud risk expressions in real-time before charging bank credit cards.'
                },
                'concept_explanation': '''
<h3>Truthiness in Python</h3>
<p>Empty sequences (<code>""</code>, <code>[]</code>, <code>{}</code>), numeric zero (<code>0</code>, <code>0.0</code>), and <code>None</code> evaluate to <code>False</code>. Everything else evaluates to <code>True</code>.</p>
''',
                'starter_code': '''# Operators & Truthiness
balance = 450.0
withdrawal = 200.0
has_pin = True
is_frozen = False

is_approved = (balance >= withdrawal) and has_pin and (not is_frozen)
print(f"Withdrawal Approved: {is_approved}")

# Integer Division & Modulo
dividend, divisor = 17, 5
print(f"Floor Div: {dividend // divisor} | Remainder: {dividend % divisor}")
'''
            },
            {
                'slug': 'python-control-flow-conditionals',
                'title': '4. Conditionals: if, elif, else & Match-Case',
                'category': 'Control Flow',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Railway Track Switch Gate',
                    'text': 'An if-elif-else construct is a railway track switch that guides incoming trains onto track A, track B, or track C based on the sensor signal color.'
                },
                'use_case': {
                    'company': 'AWS IAM Permission Checkers',
                    'text': 'Inspecting role permissions and route access policies based on HTTP methods (GET, POST, DELETE).'
                },
                'concept_explanation': '''
<h3>Pattern Matching (Python 3.10+)</h3>
<p>The <code>match-case</code> statement provides structural pattern matching for cleaner branching than nested if-statements.</p>
''',
                'starter_code': '''# Conditionals & Status Evaluator
http_status = 404

if http_status == 200:
    response = "OK: Request Succeeded"
elif http_status == 401:
    response = "Unauthorized: Access Denied"
elif http_status == 404:
    response = "Not Found: Resource does not exist"
elif 500 <= http_status <= 599:
    response = "Server Error: Gateway failure"
else:
    response = "Unknown Status Code"

print(f"HTTP {http_status} -> {response}")
'''
            },
            {
                'slug': 'python-loops-while-for',
                'title': '5. Loops: for, while, break, continue & else',
                'category': 'Control Flow',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Factory Conveyor Belt',
                    'text': 'A for loop is an assembly line conveyor belt where every item passes under a robotic scanner. A break button stops the entire line immediately; a continue button skips a defective box and immediately inspects the next one.'
                },
                'use_case': {
                    'company': 'Celery Background Cron Workers',
                    'text': 'Polling job queues, retrying failed network socket connections with backoff limits.'
                },
                'concept_explanation': '''
<h3>The `for...else` Construct</h3>
<p>The <code>else</code> block attached to a loop executes ONLY if the loop completed naturally without hitting a <code>break</code>.</p>
''',
                'starter_code': '''# For Loop with Break & Else Check
target_user = "admin_01"
user_list = ["guest_9", "member_4", "admin_01", "moderator_2"]

for idx, user in enumerate(user_list):
    if user == target_user:
        print(f"🎯 Found target '{target_user}' at index position {idx}!")
        break
else:
    print(f"❌ User '{target_user}' not present in database.")
'''
            },
            {
                'slug': 'python-lists-tuples',
                'title': '6. Lists & Tuples: Sequences & Memory Patterns',
                'category': 'Data Structures',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Expandable Binder vs The Laminated Diploma',
                    'text': 'A List is a 3-ring binder: you can add, remove, and replace pages anytime (mutable). A Tuple is a laminated certificate: once sealed in plastic, its contents and order are permanently locked (immutable and hashable).'
                },
                'use_case': {
                    'company': 'PostgreSQL DB Drivers (Psycopg)',
                    'text': 'Database query rows are returned as immutable tuples for thread-safe memory efficiency, while query result collections are mutable lists.'
                },
                'concept_explanation': '''
<h3>List Operations</h3>
<ul>
  <li><code>.append(x)</code>: Add to end — $O(1)$ amortized</li>
  <li><code>.pop()</code>: Remove from end — $O(1)$</li>
  <li><code>.insert(i, x)</code>: Insert at index — $O(N)$ due to element shifting</li>
</ul>
''',
                'starter_code': '''# Lists vs Tuples
coordinates = (37.7749, -122.4194) # Tuple (San Francisco)
print(f"Latitude: {coordinates[0]}, Longitude: {coordinates[1]}")

# Mutable List Operations
servers = ["web-01", "web-02"]
servers.append("web-03")
servers.remove("web-01")

print(f"Active Server Cluster: {servers} | Count: {len(servers)}")
'''
            },
            {
                'slug': 'python-dictionaries-sets',
                'title': '7. Dictionaries & Sets: Hash Tables in Depth',
                'category': 'Data Structures',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Library Card Index & The VIP Club Bouncer',
                    'text': 'A Dictionary is a library index drawer: you look up the author\'s exact name and find the book immediately in O(1) time. A Set is a VIP club bouncer with a strict no-duplicates list: anyone trying to enter twice is instantly rejected.'
                },
                'use_case': {
                    'company': 'Redis Cache & Spotify Graph Engines',
                    'text': 'Key-value caches and finding mutual friend/song intersections in $O(\\min(N, M))$ time.'
                },
                'concept_explanation': '''
<h3>Hash Table Implementation</h3>
<p>Dicts and Sets compute <code>hash(key)</code> to locate buckets instantly in $O(1)$ average time.</p>
''',
                'starter_code': '''# Dictionaries & Sets in Action
user_roles = {
    "alice": "ADMIN",
    "bob": "DEVELOPER",
    "charlie": "VIEWER"
}

# Fast O(1) lookup
print(f"Alice's Role: {user_roles.get('alice', 'GUEST')}")

# Set Operations
team_a = {"Python", "Docker", "AWS", "SQL"}
team_b = {"React", "TypeScript", "Docker", "AWS"}

shared_skills = team_a.intersection(team_b)
all_skills = team_a.union(team_b)

print(f"Shared Stack: {shared_skills}")
print(f"Combined Stack: {all_skills}")
'''
            },
            {
                'slug': 'python-comprehensions',
                'title': '8. List, Dict & Set Comprehensions',
                'category': 'Data Structures',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Industrial Fruit Sorting & Slicing Line',
                    'text': 'Instead of picking up 100 apples, inspecting each one, peeling it, and placing it in a crate across 6 lines of code, a comprehension is an automated conveyor machine that sorts, peels, and crates in one single line.'
                },
                'use_case': {
                    'company': 'Data Engineering ETL Pipelines',
                    'text': 'Cleaning and transforming thousands of raw CSV rows 30% faster using C-optimized bytecode loops.'
                },
                'concept_explanation': '''
<h3>Comprehension Syntax</h3>
<p><code>[expr for item in iterable if condition]</code></p>
<p><code>{k_expr: v_expr for item in iterable if condition}</code></p>
''',
                'starter_code': '''# Advanced Comprehensions
prices = [12.50, 45.00, 120.00, 5.00, 89.90]

# Filter items > $20 and apply 15% tax
taxed_prices = [round(p * 1.15, 2) for p in prices if p > 20.0]
print(f"Taxed Premium Items: {taxed_prices}")

# Dict Comprehension: Square numbers map
squares = {x: x**2 for x in range(1, 6)}
print(f"Squares Map: {squares}")
'''
            },
            {
                'slug': 'python-functions-args-kwargs',
                'title': '9. Functions: Scope, *args & **kwargs',
                'category': 'Functions',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Kitchen Food Processor Appliance',
                    'text': 'A function is a food processor: you drop ingredients in the feeder (arguments), press pulse, and collect the sauce (return value). *args is an expandable hopper accepting any number of veggies, and **kwargs is a labeled spice rack where you specify spicy=True, garlic_cloves=3.'
                },
                'use_case': {
                    'company': 'Flask & FastAPI Request Handlers',
                    'text': 'Passing arbitrary query parameters and URL path variables dynamically to backend microservices.'
                },
                'concept_explanation': '''
<h3>The LEGB Scope Rule</h3>
<p>Python resolves variable names in this order: <strong>L</strong>ocal &rarr; <strong>E</strong>nclosing &rarr; <strong>G</strong>lobal &rarr; <strong>B</strong>uilt-in.</p>
''',
                'starter_code': '''# Flexible Function with *args and **kwargs
def generate_report(title: str, *metrics, **metadata):
    total = sum(metrics)
    avg = total / len(metrics) if metrics else 0.0
    
    print(f"=== {title.upper()} ===")
    print(f"Total Sum: {total} | Average: {avg:.2f}")
    print(f"Author: {metadata.get('author', 'System')}")
    print(f"Environment: {metadata.get('env', 'Production')}")

generate_report("API Latency", 42, 55, 38, 61, 49, author="DevOps Team", env="Prod-US-East")
'''
            },
            {
                'slug': 'python-lambda-higher-order',
                'title': '10. Lambda, Map, Filter & Sorted Keys',
                'category': 'Functions',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Pocket Calculator Function',
                    'text': 'A standard def function is a heavy desk encyclopedia that you bookmark and name permanently. A lambda is a quick calculation scribbled on a napkin: you use it once right inside a sort tool and throw it away.'
                },
                'use_case': {
                    'company': 'Pandas Data Cleaning & Sorting',
                    'text': 'Sorting complex nested dictionaries or JSON records by multiple custom attributes simultaneously.'
                },
                'concept_explanation': '''
<h3>Lambda Syntax</h3>
<p><code>lambda arg1, arg2: expression</code> (Anonymous one-line functions).</p>
''',
                'starter_code': '''# Sorting Complex Records with Lambdas
engineers = [
    {"name": "Sarah", "experience_yrs": 5, "rating": 4.9},
    {"name": "David", "experience_yrs": 8, "rating": 4.6},
    {"name": "Elena", "experience_yrs": 2, "rating": 4.95},
]

# Sort by rating descending
sorted_by_rating = sorted(engineers, key=lambda x: x["rating"], reverse=True)

for eng in sorted_by_rating:
    print(f"{eng['name']} -> Rating: {eng['rating']} ({eng['experience_yrs']} yrs exp)")
'''
            },
            {
                'slug': 'python-oop-classes-objects',
                'title': '11. OOP: Classes, Instances & Encapsulation',
                'category': 'Object-Oriented',
                'read_time': '9 min read',
                'analogy': {
                    'title': 'The Architectural Blueprint & Real Houses',
                    'text': 'A Class is the architectural blueprint defining bedrooms and plumbing. An Object is the actual house constructed from that blueprint. You can build 100 houses (objects) from one blueprint, and each has its own address and furniture.'
                },
                'use_case': {
                    'company': 'Django ORM Models',
                    'text': 'Encapsulating database records, relational foreign keys, and validation business logic inside clean Python classes.'
                },
                'concept_explanation': '''
<h3>Core OOP Concepts</h3>
<ul>
  <li><code>__init__</code>: Constructor initializer method.</li>
  <li><code>self</code>: Explicit reference to the current instance object.</li>
  <li>Private attributes: Indicated by a leading underscore (<code>_variable</code>).</li>
</ul>
''',
                'starter_code': '''# Production OOP: E-Commerce Shopping Cart
class ShoppingCart:
    def __init__(self, owner: str):
        self.owner = owner
        self._items = []

    def add_item(self, name: str, price: float):
        self._items.append({"name": name, "price": price})
        print(f"🛒 Added '{name}' (${price:.2f}) to {self.owner}'s cart.")

    def get_total(self) -> float:
        return sum(item["price"] for item in self._items)

cart = ShoppingCart("Alex")
cart.add_item("Mechanical Keyboard", 120.0)
cart.add_item("USB-C Cable", 15.5)
print(f"Total Cart Due: ${cart.get_total():.2f}")
'''
            },
            {
                'slug': 'python-oop-inheritance-polymorphism',
                'title': '12. Inheritance, Polymorphism & super()',
                'category': 'Object-Oriented',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Smartphone Base Model & Pro Upgrade',
                    'text': 'A base phone has a screen and battery (parent class). The Pro model inherits all of that and adds a telephoto camera (child class). Polymorphism means both phones plug into the same USB-C charger port without caring which model it is.'
                },
                'use_case': {
                    'company': 'AWS Boto3 SDK Clients',
                    'text': 'Base cloud clients sharing retry and authentication logic, with specialized S3, EC2, and DynamoDB child implementations.'
                },
                'concept_explanation': '''
<h3>Method Resolution Order (MRO)</h3>
<p>Python resolves method calls across multi-level inheritance hierarchies using the C3 Linearization algorithm accessible via <code>ClassName.__mro__</code>.</p>
''',
                'starter_code': '''# Inheritance & Polymorphism
class NotificationSender:
    def __init__(self, recipient: str):
        self.recipient = recipient

    def send(self, message: str):
        raise NotImplementedError("Subclasses must implement send()")

class EmailSender(NotificationSender):
    def send(self, message: str):
        print(f"📧 Email to {self.recipient}: {message}")

class PushSender(NotificationSender):
    def send(self, message: str):
        print(f"📲 Push Alert to {self.recipient}: {message}")

channels = [EmailSender("user@kashii.com"), PushSender("Device_8941")]
for ch in channels:
    ch.send("Your build has succeeded!")
'''
            },
            {
                'slug': 'python-exception-handling',
                'title': '13. Exception Handling: try, except, finally & Custom Errors',
                'category': 'Architecture',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Electrical Circuit Breaker',
                    'text': 'When an electrical wire shorts out in your house, the circuit breaker trips instantly: it shuts down power cleanly instead of burning the house down. Exception handling prevents bad user input from crashing your whole web server.'
                },
                'use_case': {
                    'company': 'Payment Gateways (Stripe & PayPal)',
                    'text': 'Catching API timeouts and network glitches cleanly and triggering automatic retry policies.'
                },
                'concept_explanation': '''
<h3>Exception Handling Clauses</h3>
<ul>
  <li><code>try</code>: Code that might raise an error.</li>
  <li><code>except</code>: Handler for specific error types.</li>
  <li><code>else</code>: Runs if NO exception occurred.</li>
  <li><code>finally</code>: ALWAYS runs (used for closing files/sockets).</li>
</ul>
''',
                'starter_code': '''# Custom Exceptions & Safe Execution
class InvalidTransferError(Exception):
    pass

def execute_bank_transfer(sender: str, amount: float, sender_balance: float):
    try:
        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")
        if amount > sender_balance:
            raise InvalidTransferError(f"Insufficient funds: ${sender_balance:.2f} available.")
        
        remaining = sender_balance - amount
        print(f"✅ Transfer of ${amount:.2f} completed! New balance: ${remaining:.2f}")
        return remaining
    except (ValueError, InvalidTransferError) as err:
        print(f"⚠️ Transaction Rejected: {err}")
    finally:
        print("🔒 Transaction audit log finalized.")

execute_bank_transfer("Alice", 150.0, 500.0)
execute_bank_transfer("Bob", 800.0, 200.0)
'''
            },
            {
                'slug': 'python-file-io-json',
                'title': '14. File Handling & JSON Serialization',
                'category': 'Architecture',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'Writing in a Notebook with a Pen Cap',
                    'text': 'Using with open(...) is like picking up a notebook, writing notes, and immediately clicking the pen cap shut when done: even if you get distracted or an error occurs, the notebook is cleanly closed without ink spilling.'
                },
                'use_case': {
                    'company': 'Configuration Management & Web APIs',
                    'text': 'Reading server settings from config.json and serializing database query outputs into JSON responses.'
                },
                'concept_explanation': '''
<h3>JSON Module in Python</h3>
<ul>
  <li><code>json.dumps()</code>: Python dict &rarr; JSON string.</li>
  <li><code>json.loads()</code>: JSON string &rarr; Python dict.</li>
</ul>
''',
                'starter_code': '''# In-Memory JSON Parsing & Transformation
import json

raw_json_payload = """
{
  "service": "ReqPulse API",
  "version": 2.4,
  "cluster": ["node-us-1", "node-us-2"],
  "health_ok": true
}
"""

# Parse JSON string into Python dict
config = json.loads(raw_json_payload)
print(f"Service: {config['service']} (v{config['version']})")
print(f"Cluster Nodes: {config['cluster']}")

# Serialize back with formatting
config["cluster"].append("node-eu-1")
formatted_json = json.dumps(config, indent=2)
print("Updated JSON:\\n" + formatted_json)
'''
            },
            {
                'slug': 'python-generators-decorators',
                'title': '15. Generators, Yield & Function Decorators',
                'category': 'Advanced',
                'read_time': '9 min read',
                'analogy': {
                    'title': 'The Water Tap vs The Water Tanker',
                    'text': 'A regular function is ordering a 10,000-liter water tanker to dump into your living room at once. A Generator (yield) is a water tap: you turn the handle and get one glass at a time, using almost zero storage space without flooding your room.'
                },
                'use_case': {
                    'company': 'Netflix & Spotify Streaming Pipelines',
                    'text': 'Streaming gigabytes of media telemetry logs or database query cursors in constant $O(1)$ RAM.'
                },
                'concept_explanation': '''
<h3>Decorators in Python</h3>
<p>A decorator is a higher-order function that takes another function as an argument and extends its behavior without modifying its source code.</p>
''',
                'starter_code': '''# 1. Generator: Memory-Efficient Fibonacci
def fibonacci_gen(limit: int):
    a, b = 0, 1
    count = 0
    while count < limit:
        yield a
        a, b = b, a + b
        count += 1

print("Fibonacci Stream:", list(fibonacci_gen(8)))

# 2. Custom Timing Decorator
def execution_logger(func):
    def wrapper(*args, **kwargs):
        print(f"⚡ [START] Executing '{func.__name__}'")
        result = func(*args, **kwargs)
        print(f"✨ [DONE] Result = {result}")
        return result
    return wrapper

@execution_logger
def compute_power(base: int, exp: int) -> int:
    return base ** exp

compute_power(2, 10)
'''
            }
        ]
    },
    'java': {
        'title': 'Java 17 Complete Enterprise Academy',
        'short_title': 'Java 17',
        'icon': '☕',
        'color': '#ea580c',
        'badge': 'Static, Typed & JVM',
        'summary': 'The definitive complete Java 17 enterprise academy covering JVM memory models, OOP architectures, Collections, and Multi-Threading.',
        'topics': [
            {
                'slug': 'java-syntax-main-variables',
                'title': '1. Java Syntax, Main Method & Variables',
                'category': 'Fundamentals',
                'read_time': '6 min read',
                'analogy': {
                    'title': 'The Formal Legal Document',
                    'text': 'Java is like a formal legal contract: every variable must declare its exact type in writing upfront, and the public static void main method is the official front entrance where the judge begins reading the contract.'
                },
                'use_case': {
                    'company': 'Banking & Financial Engines',
                    'text': 'Static type safety prevents catastrophic runtime type mismatch errors in multi-billion dollar transaction systems.'
                },
                'concept_explanation': '''
<h3>The Main Method Anatomy</h3>
<p><code>public static void main(String[] args)</code> is the JVM entry point.</p>
''',
                'starter_code': '''public class Main {
    public static void main(String[] args) {
        String serviceName = "AuthenticationEngine";
        int portNumber = 8080;
        boolean isRunning = true;

        System.out.println("Service: " + serviceName);
        System.out.println("Listening on Port: " + portNumber);
        System.out.println("Status Active: " + isRunning);
    }
}
'''
            },
            {
                'slug': 'java-primitive-data-types',
                'title': '2. 8 Primitive Types, Casting & Memory',
                'category': 'Fundamentals',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Precision Measuring Cups',
                    'text': 'Java primitives are like exact kitchen measuring cups: a byte holds 1 cup (-128 to 127), an int holds a 4-liter jug, and a long holds a 50-liter barrel. Pouring a small cup into a big barrel is automatic (widening casting), but pouring a barrel into a cup requires explicit permission (narrowing casting).'
                },
                'use_case': {
                    'company': 'Android OS & High-Performance Graphics',
                    'text': 'Using byte arrays and float buffers to manipulate image pixel matrices with zero object garbage collection overhead.'
                },
                'concept_explanation': '''
<h3>Java\'s 8 Primitive Types</h3>
<p><code>byte (8-bit)</code>, <code>short (16-bit)</code>, <code>int (32-bit)</code>, <code>long (64-bit)</code>, <code>float (32-bit)</code>, <code>double (64-bit)</code>, <code>char (16-bit Unicode)</code>, <code>boolean (1-bit)</code>.</p>
''',
                'starter_code': '''public class Main {
    public static void main(String[] args) {
        int standardInt = 42;
        double decimalVal = 99.95;
        
        // Explicit Casting (Narrowing)
        int roundedPrice = (int) decimalVal;
        
        // Character & Unicode
        char grade = 'A';
        boolean isPassed = true;

        System.out.println("Rounded Price: $" + roundedPrice);
        System.out.println("Grade: " + grade + " (Passed: " + isPassed + ")");
    }
}
'''
            },
            {
                'slug': 'java-operators-expressions',
                'title': '3. Operators, Expressions & Precedence',
                'category': 'Fundamentals',
                'read_time': '6 min read',
                'analogy': {
                    'title': 'The Mechanical Clockwork Gears',
                    'text': 'Operators are interlocking clock gears: arithmetic operators calculate values, relational operators compare sizes, and logical operators decide if the alarm bell should ring.'
                },
                'use_case': {
                    'company': 'E-Commerce Tax & Shipping Engines',
                    'text': 'Calculating tiered discount percentages, state sales taxes, and currency conversions.'
                },
                'concept_explanation': '''
<h3>Ternary Operator</h3>
<p><code>condition ? expressionIfTrue : expressionIfFalse</code></p>
''',
                'starter_code': '''public class Main {
    public static void main(String[] args) {
        double subtotal = 120.00;
        boolean isVip = true;

        double discount = isVip ? 0.20 : 0.05;
        double finalTotal = subtotal * (1.0 - discount);

        System.out.println("Subtotal: $" + subtotal);
        System.out.println("Discount Applied: " + (discount * 100) + "%");
        System.out.println("Final Total: $" + finalTotal);
    }
}
'''
            },
            {
                'slug': 'java-conditionals-control-flow',
                'title': '4. Conditionals: if, else-if & Switch Expressions',
                'category': 'Control Flow',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Automated Postal Sorting Chute',
                    'text': 'Incoming parcels slide down a chute. If destination is Domestic, route left; else if International, route right. A modern switch statement is a 10-way rotunda instantly funneling parcels to specific airport bays.'
                },
                'use_case': {
                    'company': 'Trading Exchange Order Matchers',
                    'text': 'Routing BUY, SELL, STOP_LOSS, and LIMIT orders to respective matching engines.'
                },
                'concept_explanation': '''
<h3>Modern Switch Expressions (Java 14+)</h3>
<p>Use the arrow syntax <code>case "BUY" -&gt; ...</code> which eliminates accidental fall-through bugs.</p>
''',
                'starter_code': '''public class Main {
    public static void main(String[] args) {
        String role = "ADMIN";
        String accessLevel;

        switch (role) {
            case "ADMIN":
                accessLevel = "Full Root & Deployment Access";
                break;
            case "DEVELOPER":
                accessLevel = "Staging & Feature Branch Access";
                break;
            default:
                accessLevel = "Read-Only Dashboard Access";
                break;
        }

        System.out.println("Role [" + role + "] -> " + accessLevel);
    }
}
'''
            },
            {
                'slug': 'java-loops-for-while',
                'title': '5. Loops: for, enhanced for-each, while & do-while',
                'category': 'Control Flow',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Barcode Scanner at Supermarket Checkout',
                    'text': 'The cashier scans items one by one on the conveyor belt (enhanced for-each loop) until the shopping basket is completely empty.'
                },
                'use_case': {
                    'company': 'Batch Database Sync & Migrations',
                    'text': 'Iterating through batch result sets and calculating aggregate reports.'
                },
                'concept_explanation': '''
<h3>Enhanced For-Each Loop</h3>
<p>Syntax: <code>for (Type item : collection) { ... }</code> eliminates index out of bounds bugs.</p>
''',
                'starter_code': '''public class Main {
    public static void main(String[] args) {
        int[] sensorReadings = new int[]{72, 75, 81, 68, 92, 85};
        int sum = 0;
        int maxTemp = sensorReadings[0];

        for (int reading : sensorReadings) {
            sum += reading;
            if (reading > maxTemp) {
                maxTemp = reading;
            }
        }

        double average = (double) sum / sensorReadings.length;
        System.out.println("Average Sensor Reading: " + average);
        System.out.println("Peak Temperature Recorded: " + maxTemp);
    }
}
'''
            },
            {
                'slug': 'java-arrays-multi-dimensional',
                'title': '6. Arrays & Multi-Dimensional Matrix Operations',
                'category': 'Data Structures',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Numbered Post Office Mailbox Wall',
                    'text': 'An array is a fixed wall of 100 numbered mailbox slots. You can open slot #42 in instant O(1) time because the postal clerk knows the exact physical coordinate.'
                },
                'use_case': {
                    'company': 'Game Engines & Financial Grid Matrices',
                    'text': 'Representing chessboard grids, pixel frame buffers, and spatial coordinates.'
                },
                'concept_explanation': '''
<h3>Fixed Memory Allocation</h3>
<p>Java arrays have a fixed size defined at instantiation and cannot dynamically shrink or grow.</p>
''',
                'starter_code': '''public class Main {
    public static void main(String[] args) {
        // 2D Matrix (3x3 Grid)
        int[][] matrix = {
            {1, 2, 3},
            {4, 5, 6},
            {7, 8, 9}
        };

        int diagonalSum = 0;
        for (int i = 0; i < matrix.length; i++) {
            diagonalSum += matrix[i][i];
        }

        System.out.println("Matrix Size: " + matrix.length + "x" + matrix[0].length);
        System.out.println("Main Diagonal Sum: " + diagonalSum);
    }
}
'''
            },
            {
                'slug': 'java-methods-overloading',
                'title': '7. Methods, Signatures & Method Overloading',
                'category': 'Functions',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Multi-Blade Swiss Army Knife',
                    'text': 'Method overloading is having multiple tools all named "cut" on a Swiss knife: one cuts paper (cut(Paper)), one cuts wood (cut(Wood)), and one cuts wire (cut(Wire, Gauge)). The knife picks the right blade based on what you hand it.'
                },
                'use_case': {
                    'company': 'Spring Framework Controllers',
                    'text': 'Handling HTTP requests with optional query parameters and overloaded payload converters.'
                },
                'concept_explanation': '''
<h3>Method Signature</h3>
<p>Composed of the method name and parameter list. Return type is NOT part of the signature.</p>
''',
                'starter_code': '''public class Main {
    // Overloaded calculation methods
    public static double calculatePrice(double basePrice) {
        return basePrice * 1.08; // default tax
    }

    public static double calculatePrice(double basePrice, double customTaxRate) {
        return basePrice * (1.0 + customTaxRate);
    }

    public static void main(String[] args) {
        System.out.println("Default Tax Price: $" + calculatePrice(100.0));
        System.out.println("Custom Tax Price: $" + calculatePrice(100.0, 0.15));
    }
}
'''
            },
            {
                'slug': 'java-classes-objects-constructors',
                'title': '8. OOP: Classes, Objects & Constructors',
                'category': 'Object-Oriented',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Cookie Cutter & Baked Cookies',
                    'text': 'A class is a cookie cutter; an object is a baked cookie. The constructor is the oven timer that bakes each cookie with its specific sugar sprinkles and chocolate chips.'
                },
                'use_case': {
                    'company': 'Enterprise Java (Jakarta EE & Spring)',
                    'text': 'Modeling domain entities like User, Transaction, and Subscription with constructor dependency injection.'
                },
                'concept_explanation': '''
<h3>Constructor Overloading</h3>
<p>Defining multiple constructors with different parameters for flexible object initialization.</p>
''',
                'starter_code': '''class BankCustomer {
    private String name;
    private double balance;

    public BankCustomer(String name, double initialBalance) {
        this.name = name;
        this.balance = initialBalance;
    }

    public void deposit(double amount) {
        this.balance += amount;
        System.out.println("Deposited $" + amount + " to " + name + "'s account.");
    }

    public double getBalance() {
        return this.balance;
    }
}

public class Main {
    public static void main(String[] args) {
        BankCustomer customer = new BankCustomer("Jordan", 750.0);
        customer.deposit(250.0);
        System.out.println("Final Balance: $" + customer.getBalance());
    }
}
'''
            },
            {
                'slug': 'java-inheritance-super-polymorphism',
                'title': '9. Inheritance, super() & Method Overriding',
                'category': 'Object-Oriented',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Universal TV Remote',
                    'text': 'Polymorphism is a universal remote with a Power button: when pointed at a Sony TV, it sends the Sony signal; when pointed at an LG TV, it sends the LG signal. You use one uniform interface without caring about internal circuits.'
                },
                'use_case': {
                    'company': 'Uber Fare Calculation Engine',
                    'text': 'Base RideFareCalculator with specialized UberX, UberBlack, and UberXL child subclasses overriding calculateFare().'
                },
                'concept_explanation': '''
<h3>The `@Override` Annotation</h3>
<p>Instructs the compiler to ensure the child method correctly matches a parent method signature.</p>
''',
                'starter_code': '''class PaymentGateway {
    public void process(double amount) {
        System.out.println("Processing generic payment of $" + amount);
    }
}

class StripeGateway extends PaymentGateway {
    @Override
    public void process(double amount) {
        System.out.println("💳 [Stripe Gateway] Charged $" + amount + " via Card Token");
    }
}

public class Main {
    public static void main(String[] args) {
        PaymentGateway gateway = new StripeGateway();
        gateway.process(199.99); // Polymorphic invocation
    }
}
'''
            },
            {
                'slug': 'java-abstract-classes-interfaces',
                'title': '10. Abstract Classes vs Interfaces',
                'category': 'Object-Oriented',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Standard 3-Pin Wall Socket Interface',
                    'text': 'An interface is a wall socket contract: any appliance with a matching 3-pin plug receives electricity, regardless of whether it is a laptop, TV, or heater.'
                },
                'use_case': {
                    'company': 'Spring Data & JDBC Connections',
                    'text': 'Decoupling database repository contracts from underlying PostgreSQL or MySQL implementations.'
                },
                'concept_explanation': '''
<h3>Interface vs Abstract Class</h3>
<ul>
  <li><code>interface</code>: Pure contract, multiple implementations allowed.</li>
  <li><code>abstract class</code>: Shared state and partial implementation.</li>
</ul>
''',
                'starter_code': '''interface CloudStorage {
    void upload(String filename);
    String getProvider();
}

class S3Storage implements CloudStorage {
    public void upload(String filename) {
        System.out.println("☁️ Uploaded '" + filename + "' to AWS S3 Bucket");
    }
    public String getProvider() { return "Amazon Web Services"; }
}

public class Main {
    public static void main(String[] args) {
        CloudStorage storage = new S3Storage();
        System.out.println("Provider: " + storage.getProvider());
        storage.upload("resume_2026.pdf");
    }
}
'''
            },
            {
                'slug': 'java-encapsulation-access-modifiers',
                'title': '11. Encapsulation & Access Modifiers (public, private)',
                'category': 'Object-Oriented',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The ATM Machine Front Panel vs Internal Vault',
                    'text': 'Encapsulation is like an ATM: customers interact with the keypad and screen (public getters/setters), while the cash cassettes and mechanical rollers inside are locked (private variables).'
                },
                'use_case': {
                    'company': 'Security & Cryptographic Libraries',
                    'text': 'Preventing external code from mutating private encryption keys or account balances directly.'
                },
                'concept_explanation': '''
<h3>Access Modifiers Scope</h3>
<p><code>public</code> (everywhere) &gt; <code>protected</code> (package + subclasses) &gt; <code>package-private</code> (package) &gt; <code>private</code> (class only).</p>
''',
                'starter_code': '''class UserAccount {
    private String username;
    private int securityPin;

    public UserAccount(String username, int pin) {
        this.username = username;
        this.securityPin = pin;
    }

    public boolean authenticate(int enteredPin) {
        return this.securityPin == enteredPin;
    }

    public String getUsername() { return this.username; }
}

public class Main {
    public static void main(String[] args) {
        UserAccount acc = new UserAccount("kashii_dev", 7890);
        System.out.println("User: " + acc.getUsername());
        System.out.println("Auth (Wrong PIN): " + acc.authenticate(1111));
        System.out.println("Auth (Correct PIN): " + acc.authenticate(7890));
    }
}
'''
            },
            {
                'slug': 'java-exception-handling-try-catch',
                'title': '12. Exception Handling: try-catch, throws & Custom Errors',
                'category': 'Architecture',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Bank Emergency Alarm System',
                    'text': 'When an anomaly occurs (like trying to divide by zero or opening a missing file), Java throws an exception. The try-catch block is the security protocol that handles the alarm cleanly instead of crashing the bank.'
                },
                'use_case': {
                    'company': 'Spring Boot Global `@ExceptionHandler`',
                    'text': 'Translating internal SQL and NullPointer errors into clean HTTP 400/500 JSON error responses for frontend clients.'
                },
                'concept_explanation': '''
<h3>Checked vs Unchecked Exceptions</h3>
<p>Checked exceptions (e.g. <code>IOException</code>) MUST be handled or declared in method signature; Unchecked exceptions (e.g. <code>NullPointerException</code>) extend <code>RuntimeException</code>.</p>
''',
                'starter_code': '''public class Main {
    public static void divide(int a, int b) {
        try {
            int result = a / b;
            System.out.println("Result: " + a + " / " + b + " = " + result);
        } catch (ArithmeticException ex) {
            System.out.println("⚠️ Arithmetic Exception Caught: Division by zero is impossible.");
        } finally {
            System.out.println("🔒 Execution cleanup finalized.");
        }
    }

    public static void main(String[] args) {
        divide(100, 5);
        divide(100, 0);
    }
}
'''
            },
            {
                'slug': 'java-collections-arraylist-linkedlist',
                'title': '13. Collections: ArrayList vs LinkedList Performance',
                'category': 'Data Structures',
                'read_time': '9 min read',
                'analogy': {
                    'title': 'The Dynamic Seating Row vs The Human Train Chain',
                    'text': 'An ArrayList is a row of contiguous auditorium seats: accessing seat #50 takes 1 split second (O(1)), but adding a seat in the middle requires everyone to shift. A LinkedList is people holding hands: inserting someone in the middle just takes grabbing new hands (O(1)), but finding person #50 requires counting from person #1.'
                },
                'use_case': {
                    'company': 'Amazon Shopping Cart Items',
                    'text': 'Using ArrayLists for rapid random index lookups when rendering checkout page items.'
                },
                'concept_explanation': '''
<h3>Time Complexity Comparison</h3>
<table style="width:100%; border-collapse:collapse; margin:14px 0;">
  <tr><th>Operation</th><th>ArrayList</th><th>LinkedList</th></tr>
  <tr><td>get(i)</td><td>O(1)</td><td>O(N)</td></tr>
  <tr><td>add() at end</td><td>O(1) amortized</td><td>O(1)</td></tr>
  <tr><td>insert at start</td><td>O(N)</td><td>O(1)</td></tr>
</table>
''',
                'starter_code': '''import java.util.ArrayList;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        List<String> frameworkList = new ArrayList<>();
        frameworkList.add("Spring Boot");
        frameworkList.add("Hibernate");
        frameworkList.add("Micronaut");

        System.out.println("Total Frameworks: " + frameworkList.size());
        System.out.println("First Item: " + frameworkList.get(0));

        frameworkList.remove("Micronaut");
        System.out.println("Updated List: " + frameworkList);
    }
}
'''
            },
            {
                'slug': 'java-collections-hashmap-hashset',
                'title': '14. HashMap & HashSet: Hashing & Treeification',
                'category': 'Data Structures',
                'read_time': '9 min read',
                'analogy': {
                    'title': 'The Supermarket Barcode Laser',
                    'text': 'A HashMap is a supermarket barcode scanner: scanning the barcode (key) immediately jumps to the exact shelf row and returns the price in O(1) time instead of walking down 10,000 aisles.'
                },
                'use_case': {
                    'company': 'High-Throughput In-Memory Caches',
                    'text': 'Mapping user session IDs to auth tokens in microsecond retrieval times.'
                },
                'concept_explanation': '''
<h3>Treeification (Java 8+)</h3>
<p>When bucket collisions exceed 8 elements, linked lists convert to Red-Black Trees for $O(\\log N)$ lookup performance.</p>
''',
                'starter_code': '''import java.util.HashMap;
import java.util.Map;

public class Main {
    public static void main(String[] args) {
        HashMap<String, Integer> stockMap = new HashMap<>();
        stockMap.put("AAPL (Apple)", 185);
        stockMap.put("NVDA (Nvidia)", 125);
        stockMap.put("MSFT (Microsoft)", 440);

        System.out.println("NVDA Price: $" + stockMap.get("NVDA (Nvidia)"));

        for (Map.Entry<String, Integer> entry : stockMap.entrySet()) {
            System.out.println("Ticker: " + entry.getKey() + " -> $" + entry.getValue());
        }
    }
}
'''
            },
            {
                'slug': 'java-multithreading-threads-runnable',
                'title': '15. Multi-Threading: Thread, Runnable & Concurrency',
                'category': 'Concurrency',
                'read_time': '10 min read',
                'analogy': {
                    'title': 'The High-Speed 4-Chef Kitchen',
                    'text': 'Multi-threading is having 4 chefs (threads) simultaneously cooking appetizers, pasta, steaks, and desserts at 4 separate stoves sharing one central spice rack (synchronized memory).'
                },
                'use_case': {
                    'company': 'Apache Kafka & Distributed Brokers',
                    'text': 'Processing millions of streaming IoT device signals across parallel partition consumer threads.'
                },
                'concept_explanation': '''
<h3>Thread vs Runnable</h3>
<p>Implementing <code>Runnable</code> is preferred because Java allows implementing multiple interfaces while only supporting single class inheritance.</p>
''',
                'starter_code': '''public class Main {
    public static void main(String[] args) {
        Runnable taskA = () -> {
            for (int i = 1; i <= 3; i++) {
                System.out.println("🧵 [Worker-A] Processing Batch " + i);
            }
        };

        Runnable taskB = () -> {
            for (int i = 1; i <= 3; i++) {
                System.out.println("⚡ [Worker-B] Indexing Document " + i);
            }
        };

        Thread t1 = new Thread(taskA);
        Thread t2 = new Thread(taskB);

        t1.start();
        t2.start();
    }
}
'''
            }
        ]
    },
    'javascript': {
        'title': 'Modern JavaScript (ES6+) Complete Academy',
        'short_title': 'JavaScript',
        'icon': '⚡',
        'color': '#eab308',
        'badge': 'Asynchronous & Event-Driven',
        'summary': 'The definitive complete Modern JavaScript ES6+ curriculum covering scope, arrow pipelines, async/await, closures, and the browser event loop.',
        'topics': [
            {
                'slug': 'javascript-syntax-variables-datatypes',
                'title': '1. Syntax, Data Types & Dynamic Typing',
                'category': 'Fundamentals',
                'read_time': '6 min read',
                'analogy': {
                    'title': 'The Chameleon Label Maker',
                    'text': 'JavaScript variables are chameleons: you can assign a number, then change it to a string, then to an object. It adapts dynamically to whatever data you feed it.'
                },
                'use_case': {
                    'company': 'Single Page Apps (React & Vue)',
                    'text': 'Rendering dynamic user interface state based on incoming WebSocket payloads.'
                },
                'concept_explanation': '''
<h3>7 Primitive Data Types in JS</h3>
<p><code>string</code>, <code>number</code>, <code>bigint</code>, <code>boolean</code>, <code>undefined</code>, <code>symbol</code>, <code>null</code>.</p>
''',
                'starter_code': '''// JavaScript Primitives & Types
let score = 95;
let username = "alex_code";
let isSubscribed = true;
let emptyRef = null;

console.log("User:", username, "| Score:", score);
console.log("Type of score:", typeof score);
console.log("Type of isSubscribed:", typeof isSubscribed);
console.log("Type of emptyRef:", typeof emptyRef); // 'object' (legacy JS behavior)
'''
            },
            {
                'slug': 'javascript-var-let-const-hoisting',
                'title': '2. var, let, const & The Temporal Dead Zone',
                'category': 'Fundamentals',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Glass Display Case vs Erasable Whiteboard',
                    'text': 'const is a locked glass museum display case: you cannot reassign it to a completely different object. let is an erasable whiteboard inside a meeting room (block-scoped). var is a megaphone echoing through the whole building, leaking variables outside loops.'
                },
                'use_case': {
                    'company': 'React Component Immutability',
                    'text': 'Enforcing immutable state references so React virtual DOM reconciliation detects changes instantly via reference comparison.'
                },
                'concept_explanation': '''
<h3>Block Scope vs Function Scope</h3>
<p><code>let</code> and <code>const</code> respect <code>{ }</code> curly brace block scope and prevent variable hoisting bugs.</p>
''',
                'starter_code': '''// Block Scoping & Immutability
const appConfig = {
  version: "3.2.0",
  environment: "Production"
};

// Properties of const objects can be mutated
appConfig.environment = "Staging";
console.log("Mutated Config:", appConfig);

// Block Scoping with let
let total = 0;
for (let i = 1; i <= 3; i++) {
  let stepBonus = i * 10;
  total += stepBonus;
  console.log(`Step ${i}: Added +${stepBonus} (Total: ${total})`);
}
'''
            },
            {
                'slug': 'javascript-operators-type-coercion',
                'title': '3. Strict Equality (===) vs Loose Equality (==)',
                'category': 'Fundamentals',
                'read_time': '6 min read',
                'analogy': {
                    'title': 'The Strict Passport Border Guard',
                    'text': 'Strict equality (===) is a strict border officer who checks both your name AND your citizenship paper (value and type). Loose equality (==) is a relaxed bouncer who tries to convert numbers to strings and causes bizarre coercion surprises.'
                },
                'use_case': {
                    'company': 'Authentication Token Verification',
                    'text': 'Preventing authentication bypasses by strictly verifying user role IDs against expected integer constants.'
                },
                'concept_explanation': '''
<h3>Always Use `===`</h3>
<p><code>===</code> performs no implicit type conversion. <code>5 === '5'</code> is <code>false</code>.</p>
''',
                'starter_code': '''// Strict vs Loose Equality
console.log("5 === '5':", 5 === '5'); // false (Different types)
console.log("5 == '5':", 5 == '5');   // true (Implicit type coercion)

console.log("0 === false:", 0 === false); // false
console.log("null === undefined:", null === undefined); // false

// Short-circuit Evaluation
const userRole = null;
const effectiveRole = userRole || "GUEST_VIEWER";
console.log("Effective Role:", effectiveRole);
'''
            },
            {
                'slug': 'javascript-conditionals-switch',
                'title': '4. Conditionals: if, else, ternary & switch',
                'category': 'Control Flow',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Traffic Signal Light Junction',
                    'text': 'Conditionals act like traffic signal sensors: if green, flow; else if yellow, slow down; else, stop.'
                },
                'use_case': {
                    'company': 'Feature Flagging Engines',
                    'text': 'Enabling beta feature modules dynamically based on user subscription tiers.'
                },
                'concept_explanation': '''
<h3>Ternary Operator</h3>
<p><code>const status = isOnline ? "Active" : "Offline";</code></p>
''',
                'starter_code': '''// Conditionals & Tier Evaluator
const userTier = "PRO";
let monthlyCredits;

switch (userTier) {
  case "ENTERPRISE":
    monthlyCredits = 100000;
    break;
  case "PRO":
    monthlyCredits = 25000;
    break;
  default:
    monthlyCredits = 1000;
    break;
}

const badge = monthlyCredits > 20000 ? "🌟 High Volume" : "🌱 Starter";
console.log(`Tier [${userTier}]: ${monthlyCredits} API Credits (${badge})`);
'''
            },
            {
                'slug': 'javascript-loops-for-while-forof',
                'title': '5. Loops: for, while, for...of & for...in',
                'category': 'Control Flow',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Supermarket Receipt Printing Wheel',
                    'text': 'A for...of loop prints every item from your cart array sequentially until the receipt paper reaches the final total.'
                },
                'use_case': {
                    'company': 'Canvas & WebGL Rendering Loops',
                    'text': 'Iterating through particle coordinates and rendering 60 FPS visual frames.'
                },
                'concept_explanation': '''
<h3>`for...of` vs `for...in`</h3>
<ul>
  <li><code>for...of</code>: Iterates over values of iterable collections (arrays, strings, sets).</li>
  <li><code>for...in</code>: Iterates over keys/property names of objects.</li>
</ul>
''',
                'starter_code': '''// Modern for...of & for...in Loops
const frameworks = ["React", "Vue", "Svelte", "Solid"];

console.log("--- Frontend Frameworks (for...of) ---");
for (const fw of frameworks) {
  console.log("⚡ Framework:", fw);
}

const serverMetrics = { cpu: "42%", ram: "3.2GB", uptime: "99.9%" };
console.log("\\n--- Server Metrics (for...in) ---");
for (const key in serverMetrics) {
  console.log(`${key.toUpperCase()} -> ${serverMetrics[key]}`);
}
'''
            },
            {
                'slug': 'javascript-functions-declarations-expressions',
                'title': '6. Functions: Declarations vs Expressions & Default Params',
                'category': 'Functions',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Reusable Recipe Card',
                    'text': 'A function is a recipe card for baking a cake: you provide custom flour and sugar amounts (parameters), and it bakes a cake (return value).'
                },
                'use_case': {
                    'company': 'Express.js & Node.js Middleware',
                    'text': 'Encapsulating reusable HTTP response formatters and authentication decorators.'
                },
                'concept_explanation': '''
<h3>Default Parameters (ES6)</h3>
<p>Functions can declare default fallback values for parameters that are not supplied.</p>
''',
                'starter_code': '''// Functions with Default Parameters
function calculateTotalInvoice(subtotal, taxRate = 0.08, flatDiscount = 0.0) {
  const tax = subtotal * taxRate;
  const total = Math.max(0, (subtotal + tax) - flatDiscount);
  return {
    subtotal: subtotal,
    tax: tax.toFixed(2),
    total: total.toFixed(2)
  };
}

console.log("Default Tax Invoice:", calculateTotalInvoice(150.0));
console.log("Custom Discount Invoice:", calculateTotalInvoice(150.0, 0.10, 25.0));
'''
            },
            {
                'slug': 'javascript-arrow-functions-this',
                'title': '7. Arrow Functions & Lexical `this` Binding',
                'category': 'Functions',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Compact Pocket Flashlight',
                    'text': 'An arrow function is a sleek pocket flashlight: it has concise syntax and doesn\'t carry its own heavy "this" battery pack—it automatically inherits "this" from the room it was built in (lexical scoping).'
                },
                'use_case': {
                    'company': 'React Event Handlers & Callbacks',
                    'text': 'Passing click handlers and asynchronous fetch callbacks without requiring manual `.bind(this)`.'
                },
                'concept_explanation': '''
<h3>Arrow Function Characteristics</h3>
<ul>
  <li>Implicit return for single expressions: <code>(x) =&gt; x * 2</code></li>
  <li>Lexical <code>this</code> (does NOT create its own <code>this</code> context).</li>
</ul>
''',
                'starter_code': '''// Arrow Functions & Lexical Scope
const multiply = (a, b) => a * b;
const square = x => x ** 2;

console.log("5 x 6 =", multiply(5, 6));
console.log("8 squared =", square(8));

// Array inline arrow function
const prices = [10, 20, 30];
const doublePrices = prices.map(p => p * 2);
console.log("Doubled Prices:", doublePrices);
'''
            },
            {
                'slug': 'javascript-arrays-methods',
                'title': '8. Array Operations: push, pop, slice & splice',
                'category': 'Data Structures',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Stack of Dinner Plates & Bread Loaf',
                    'text': 'push/pop adds and removes plates from the top of the stack. slice is slicing 3 clean pieces off a bread loaf without destroying the loaf; splice is cutting out pieces and replacing them with cheese.'
                },
                'use_case': {
                    'company': 'Notification Feed Truncation',
                    'text': 'Maintaining circular buffers of the 50 most recent user notifications.'
                },
                'concept_explanation': '''
<h3>Immutable Slice vs Mutating Splice</h3>
<p><code>.slice(start, end)</code> returns a new array; <code>.splice(start, count, ...items)</code> mutates the array in-place.</p>
''',
                'starter_code': '''// Array Manipulation Methods
let queue = ["Job-A", "Job-B", "Job-C"];

queue.push("Job-D"); // Add to end
const completed = queue.shift(); // Remove from front

console.log("Completed:", completed);
console.log("Remaining Queue:", queue);

// Slice (non-mutating)
const subset = queue.slice(0, 2);
console.log("Next 2 Jobs:", subset);
'''
            },
            {
                'slug': 'javascript-array-hof-map-filter-reduce',
                'title': '9. High-Order Array Methods: map, filter & reduce',
                'category': 'Functional JS',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Automated Factory Conveyor Belt',
                    'text': 'Filter removes defective parts from the belt, map paints all remaining parts silver, and reduce boxes all parts into one final shipping container.'
                },
                'use_case': {
                    'company': 'Airbnb Listing Search Filters',
                    'text': 'Filtering available rooms by price, mapping to geo-coordinates, and computing the average cost per night.'
                },
                'concept_explanation': '''
<h3>Method Roles</h3>
<ul>
  <li><code>.filter()</code>: Selects elements based on boolean test.</li>
  <li><code>.map()</code>: Transforms each element into a new item.</li>
  <li><code>.reduce()</code>: Accumulates array into a single value.</li>
</ul>
''',
                'starter_code': '''// Functional Array Pipelines
const catalog = [
  { item: "Laptop Stand", price: 35, inStock: true },
  { item: "Mechanical Keyboard", price: 120, inStock: true },
  { item: "4K Webcam", price: 80, inStock: false },
  { item: "USB Hub", price: 25, inStock: true }
];

// In-stock items total price
const totalCost = catalog
  .filter(p => p.inStock)
  .map(p => p.price)
  .reduce((sum, curr) => sum + curr, 0);

console.log("Total In-Stock Cart Value: $" + totalCost);
'''
            },
            {
                'slug': 'javascript-objects-properties-methods',
                'title': '10. Object Literals, Methods & Object.keys/values',
                'category': 'Data Structures',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Multi-Drawer Filing Cabinet',
                    'text': 'An object is a filing cabinet where each drawer has a labeled name tag (key) holding specific documents (values or methods).'
                },
                'use_case': {
                    'company': 'API JSON Payloads & State Stores',
                    'text': 'Representing user session profiles, shopping cart state, and database models.'
                },
                'concept_explanation': '''
<h3>Object Utility Methods</h3>
<p><code>Object.keys()</code>, <code>Object.values()</code>, and <code>Object.entries()</code>.</p>
''',
                'starter_code': '''// Objects & Utilities
const serverInstance = {
  id: "srv-8942",
  region: "us-east-1",
  cores: 8,
  ramGb: 32,
  getStatus: function() {
    return `${this.id} in ${this.region} is ONLINE`;
  }
};

console.log(serverInstance.getStatus());
console.log("Keys:", Object.keys(serverInstance));
console.log("Values:", Object.values(serverInstance));
'''
            },
            {
                'slug': 'javascript-destructuring-spread-rest',
                'title': '11. Destructuring & Spread/Rest Operators (...)',
                'category': 'Data Structures',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'Unpacking the Travel Suitcase',
                    'text': 'Destructuring is opening a packed suitcase and grabbing just your passport and sunglasses without scattering all your clothes. Spread (...) is photocopying an existing book and inserting two new pages.'
                },
                'use_case': {
                    'company': 'Redux & React State Updaters',
                    'text': 'Creating immutable state updates: `return { ...state, user: newUserData }`.'
                },
                'concept_explanation': '''
<h3>Spread vs Rest</h3>
<p><strong>Spread:</strong> Unpacks items. <strong>Rest:</strong> Gathers remaining items into an array.</p>
''',
                'starter_code': '''// Destructuring & Spread
const user = { name: "Elena", role: "Architect", country: "Sweden", level: 4 };
const { name, role, ...otherDetails } = user;

console.log(`User: ${name} (${role})`);
console.log("Remaining Details:", otherDetails);

// Immutable Object Clone & Update
const updatedUser = {
  ...user,
  level: 5,
  promotedAt: "2026-08-19"
};
console.log("Updated Object:", updatedUser);
'''
            },
            {
                'slug': 'javascript-classes-oop-prototype',
                'title': '12. ES6 Classes, Constructors & Private Fields (#)',
                'category': 'Object-Oriented',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The ATM Keypad and Cash Safe Vault',
                    'text': 'An ES6 Class with private fields (#private) is an ATM: users can press the deposit and withdraw buttons (public methods), but cannot touch the private internal cash vault (#balance).'
                },
                'use_case': {
                    'company': 'Frontend SDKs (Stripe.js, Firebase)',
                    'text': 'Encapsulating secret auth tokens and WebSocket connections in private class fields.'
                },
                'concept_explanation': '''
<h3>Private Fields (ES2022)</h3>
<p>Prefixing an attribute with <code>#</code> guarantees true privacy that cannot be accessed from outside the class instance.</p>
''',
                'starter_code': '''// ES6 Class with Private Fields
class BankVault {
  #secretBalance = 0;

  constructor(owner, initialDeposit) {
    this.owner = owner;
    this.#secretBalance = initialDeposit;
  }

  deposit(amount) {
    if (amount > 0) {
      this.#secretBalance += amount;
      console.log(`Deposited $${amount}. New balance: $${this.#secretBalance}`);
    }
  }

  getBalanceStatement() {
    return `Vault [${this.owner}] contains verified funds.`;
  }
}

const myVault = new BankVault("Taylor", 1000);
myVault.deposit(500);
console.log(myVault.getBalanceStatement());
'''
            },
            {
                'slug': 'javascript-closures-scope-chain',
                'title': '13. Closures & Lexical Scoping Architecture',
                'category': 'Advanced',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Student Backpack in University',
                    'text': 'A Closure is a student\'s personal backpack: when the student graduates and leaves the classroom (the outer function finishes executing), they still carry their backpack containing all their personal notes (inner function permanently retains access to outer variables).'
                },
                'use_case': {
                    'company': 'Redux Store & Event Debouncers',
                    'text': 'Encapsulating private state variables and creating debounced search input handlers.'
                },
                'concept_explanation': '''
<h3>What is a Closure?</h3>
<p>A function bundled together with references to its lexical environment.</p>
''',
                'starter_code': '''// Private State Encapsulation via Closures
function createCounter(initialValue = 0) {
  let count = initialValue; // Private state variable

  return {
    increment: () => ++count,
    decrement: () => --count,
    getValue: () => count
  };
}

const counter = createCounter(10);
console.log("Increment:", counter.increment()); // 11
console.log("Increment:", counter.increment()); // 12
console.log("Current Value:", counter.getValue()); // 12
'''
            },
            {
                'slug': 'javascript-promises-async-await',
                'title': '14. Asynchronous JS: Promises, Async/Await & Fetch',
                'category': 'Async & Network',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Restaurant Vibrating Order Pager',
                    'text': 'When you order coffee, you don\'t stand frozen at the cash register blocking 50 people behind you (blocking synchronous code). The barista gives you a vibrating electronic pager (a Promise). You sit down, check emails, and when the coffee is ready, the pager buzzes (Promise resolved).'
                },
                'use_case': {
                    'company': 'Netflix Video Streaming & WebSockets',
                    'text': 'Fetching movie thumbnails and streaming audio chunks in background tasks without locking the UI thread.'
                },
                'concept_explanation': '''
<h3>Async / Await</h3>
<p>Transforms asynchronous Promise chaining into clean, linear code with <code>try...catch</code> error handling.</p>
''',
                'starter_code': '''// Async/Await Promise Simulation
function mockFetchPrice(ticker) {
  return new Promise((resolve) => {
    resolve({ ticker: ticker, price: 189.50, status: "SUCCESS" });
  });
}

async function loadStockDashboard() {
  console.log("1. Requesting stock ticker data...");
  const data = await mockFetchPrice("NVDA");
  console.log("2. Response Received:", data.ticker, "-> $" + data.price);
  console.log("3. UI Updated Successfully.");
}

loadStockDashboard();
'''
            },
            {
                'slug': 'javascript-dom-events-delegation',
                'title': '15. The Event Loop, Microtasks & Macrotasks',
                'category': 'Advanced',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Bank Teller & The Back-Office Courier',
                    'text': 'The Call Stack is the bank teller serving the person at the front of the line. When a customer has a long loan document to process (setTimeout), the teller hands it to the back-office courier (Web APIs) and immediately serves the next customer in line.'
                },
                'use_case': {
                    'company': 'Browser UI 60FPS Smooth Rendering',
                    'text': 'Preventing UI freezes by scheduling heavy calculations into microtask and macrotask queues.'
                },
                'concept_explanation': '''
<h3>Event Loop Priority</h3>
<p>Call Stack &rarr; Microtasks (Promises, queueMicrotask) &rarr; Macrotasks (setTimeout, setInterval, I/O).</p>
''',
                'starter_code': '''// Event Loop Execution Order Simulation
console.log("1. Synchronous: First");

setTimeout(() => {
  console.log("4. Macrotask (setTimeout): Fourth");
}, 0);

Promise.resolve().then(() => {
  console.log("3. Microtask (Promise): Third");
});

console.log("2. Synchronous: Second");
'''
            }
        ]
    }
}
