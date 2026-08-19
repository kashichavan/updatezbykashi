"""
Comprehensive Multi-Language Learning Curriculum (Python, Java, JavaScript)
Interactive W3Schools / GeeksforGeeks style tutorials with real-world analogies,
production industry use cases, and live runnable debugger code.
"""

CURRICULUM = {
    'python': {
        'title': 'Python 3 Programming Academy',
        'short_title': 'Python 3',
        'icon': '🐍',
        'color': '#3b82f6',
        'badge': 'High-Level & Dynamic',
        'summary': 'Master Python from fundamentals to advanced metaprogramming with real-world industry mental models and live execution tracing.',
        'topics': [
            {
                'slug': 'python-variables-data-types',
                'title': 'Variables, Memory Models & Dynamic Typing',
                'category': 'Fundamentals',
                'read_time': '6 min read',
                'analogy': {
                    'title': 'The Warehouse Storage Box with Sticky Labels',
                    'text': 'In Python, a variable is NOT a fixed container that holds data. Instead, think of an object (like a string or integer) as an item stored in a warehouse, and a variable as a sticky name tag taped to that item. When you write a = 10, Python places 10 in memory and sticks the label "a" on it. When you assign b = a, you are just sticking another label "b" on the exact same item.'
                },
                'use_case': {
                    'company': 'Instagram & Django REST APIs',
                    'text': 'Instagram handles millions of dynamic JSON payloads per second. Python\'s dynamic typing allows rapid JSON dictionary deserialization without declaring rigid boilerplate schemas for every incoming HTTP payload.'
                },
                'concept_explanation': '''
<h3>1. Dynamic Typing vs Static Typing</h3>
<p>Python is dynamically typed: you don't need to specify types (like <code>int a = 10</code> in C++/Java). Python determines types at runtime.</p>

<h3>2. Immutability & Memory IDs</h3>
<p>Numbers, strings, and tuples are <strong>immutable</strong> (cannot be changed in-place). When you modify a string, Python allocates a new object in memory and updates the variable tag.</p>
''',
                'starter_code': '''# Variables, Memory Address & Object Mutation
name = "Alex"
print(f"Initial name: {name}, Memory ID: {id(name)}")

# Reassigning variable (Points to a brand new memory address)
name = "Jordan"
print(f"Updated name: {name}, New Memory ID: {id(name)}")

# Lists are mutable (Retains the same Memory ID upon modification)
cart = ["Laptop", "Mouse"]
print(f"Initial Cart ID: {id(cart)}")

cart.append("Keyboard")
print(f"Mutated Cart: {cart}, Cart ID: {id(cart)}")
'''
            },
            {
                'slug': 'python-control-flow-loops',
                'title': 'Conditionals, Loops & Branching Logic',
                'category': 'Control Flow',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Railway Track Switch & Automated Gate',
                    'text': 'Think of an if-elif-else block as a railway switch track. Depending on the color of the signal light (True or False condition), the train is routed down track A, track B, or the default emergency track. Loops are conveyor belts that move items past a robotic arm one by one until the basket is empty.'
                },
                'use_case': {
                    'company': 'Stripe Payment Processing',
                    'text': 'Stripe uses complex conditional branching trees to inspect credit card country codes, charge amounts, and risk scores. If a transaction risk score exceeds 85, it triggers two-factor SMS authentication; otherwise, it executes instant settlement.'
                },
                'concept_explanation': '''
<h3>1. Conditionals with Truthy and Falsy Values</h3>
<p>Python evaluates non-empty collections, non-zero numbers, and <code>True</code> as truthy. Empty strings <code>""</code>, <code>0</code>, <code>None</code>, and <code>[]</code> evaluate to falsy.</p>

<h3>2. For-In Iteration over Iterables</h3>
<p>Unlike C-style indexing loops, Python loops consume items directly from any iterable sequence using the iterator protocol.</p>
''',
                'starter_code': '''# Transaction Risk Evaluator & Filter Loop
transactions = [
    {"user": "Alice", "amount": 120, "risk_score": 12},
    {"user": "Bob", "amount": 9500, "risk_score": 88},
    {"user": "Charlie", "amount": 450, "risk_score": 34},
    {"user": "Diana", "amount": 12000, "risk_score": 92},
]

flagged_users = []
approved_total = 0

for tx in transactions:
    if tx["risk_score"] > 80 or tx["amount"] > 10000:
        flagged_users.append(tx["user"])
        print(f"🚨 FLAGGED: {tx['user']} (Risk: {tx['risk_score']})")
    else:
        approved_total += tx["amount"]
        print(f"✅ Approved: {tx['user']} (${tx['amount']})")

print(f"Total Approved Volume: ${approved_total}")
print(f"Flagged for Review: {flagged_users}")
'''
            },
            {
                'slug': 'python-lists-dicts-sets',
                'title': 'Data Structures: Lists, Dicts, Sets & Tuples',
                'category': 'Data Structures',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Library Catalog & VIP Club Guest List',
                    'text': 'A List is a numbered row of lockers (0, 1, 2...). A Dictionary is a library index card drawer where you know the author/keyword name and immediately pull up the book in O(1) time. A Set is a VIP club bouncer with a checklist: you cannot be added twice, and checking if someone is on the list takes one split second.'
                },
                'use_case': {
                    'company': 'Spotify Music Recommendations',
                    'text': 'Spotify uses Sets to compute song playlist intersections (songs both you and your friend like) in O(min(len(A), len(B))) time, and Dictionaries to store cached user playback preferences.'
                },
                'concept_explanation': '''
<h3>1. Time Complexity Breakdown</h3>
<ul>
  <li><strong>Dictionary / Set Lookup:</strong> <code>O(1)</code> average time complexity via hash tables.</li>
  <li><strong>List Append:</strong> <code>O(1)</code> amortized time.</li>
  <li><strong>List Search:</strong> <code>O(N)</code> linear scan.</li>
</ul>
''',
                'starter_code': '''# Data Structures in Action: Social Graph & Analytics
user_interests = {
    "Alex": {"Python", "AI", "Django", "Robotics"},
    "Maya": {"Django", "React", "AI", "Cloud"},
    "Sam": {"Java", "Spring", "Kubernetes", "Cloud"}
}

# 1. Set Intersection: Mutual interests between Alex & Maya
mutual_alex_maya = user_interests["Alex"].intersection(user_interests["Maya"])
print(f"Mutual Interests (Alex & Maya): {mutual_alex_maya}")

# 2. Dictionary Frequency Counter
tags = ["python", "ai", "web", "python", "cloud", "ai", "python"]
frequency = {}
for tag in tags:
    frequency[tag] = frequency.get(tag, 0) + 1

print(f"Tag Frequency Count: {frequency}")
'''
            },
            {
                'slug': 'python-oop-classes-objects',
                'title': 'Object-Oriented Programming (OOP): Classes, Inheritance & Encapsulation',
                'category': 'Architecture',
                'read_time': '9 min read',
                'analogy': {
                    'title': 'The Architectural Blueprint & Real Houses',
                    'text': 'A Class is the architectural blueprint drawn on paper: it defines walls, doors, and electrical circuits. An Object is the physical house built from that blueprint. You can build 50 houses (objects) from one blueprint, and each house can have different wall paint and owners while sharing the same structure.'
                },
                'use_case': {
                    'company': 'Django ORM & E-Commerce Platforms',
                    'text': 'Django uses OOP classes (`class JobPosting(models.Model)`) to encapsulate database queries, schema validation, and table migrations into reusable, testable components.'
                },
                'concept_explanation': '''
<h3>Core Pillars of OOP in Python</h3>
<ul>
  <li><strong>Encapsulation:</strong> Bundling data and methods that operate on that data within classes.</li>
  <li><strong>Inheritance:</strong> Reusing common logic from parent classes to child classes.</li>
  <li><strong>Polymorphism:</strong> Defining uniform interfaces across different object types.</li>
</ul>
''',
                'starter_code': '''# Production OOP Pattern: Bank Account with Encapsulation

class BankAccount:
    def __init__(self, account_holder: str, initial_deposit: float = 0.0):
        self.holder = account_holder
        self._balance = initial_deposit
        self._ledger = []

    def deposit(self, amount: float):
        if amount <= 0:
            return "Invalid deposit amount"
        self._balance += amount
        self._ledger.append(f"+${amount:.2f} Deposit")
        return f"Deposited ${amount:.2f}. New Balance: ${self._balance:.2f}"

    def withdraw(self, amount: float):
        if amount > self._balance:
            return "❌ Insufficient Funds"
        self._balance -= amount
        self._ledger.append(f"-${amount:.2f} Withdrawal")
        return f"Withdrew ${amount:.2f}. Remaining Balance: ${self._balance:.2f}"

    def get_statement(self):
        return f"Account [{self.holder}]: Balance=${self._balance:.2f} | TxCount={len(self._ledger)}"

# Testing our OOP instance
acct = BankAccount("Sarah Conner", 500.0)
print(acct.deposit(250.0))
print(acct.withdraw(100.0))
print(acct.get_statement())
'''
            },
            {
                'slug': 'python-generators-decorators',
                'title': 'Generators, Lazy Evaluation & Function Decorators',
                'category': 'Advanced',
                'read_time': '9 min read',
                'analogy': {
                    'title': 'The Water Tap vs The Water Tanker',
                    'text': 'A regular function that returns a list is like ordering a 10,000-liter water tanker to dump into your living room at once. A Generator function (using yield) is a water tap: it gives you exactly one glass of water when you turn the handle, uses almost zero storage space, and can produce infinite water without flooding your room.'
                },
                'use_case': {
                    'company': 'Netflix & Big Data Log Pipelines',
                    'text': 'Streaming terabytes of movie viewing logs or audio metrics without running out of RAM (Out of Memory error) requires Python generator pipelines.'
                },
                'concept_explanation': '''
<h3>1. Lazy Evaluation with `yield`</h3>
<p>Generators save execution state and resume right where they left off upon calling <code>next()</code>.</p>

<h3>2. Decorators (`@wrapper`)</h3>
<p>Decorators wrap existing functions to inject logging, authentication checks, or caching without modifying the original function code.</p>
''',
                'starter_code': '''# 1. Generator: Fibonacci Streamer (Constant O(1) RAM)
def fibonacci_stream(limit: int):
    a, b = 0, 1
    count = 0
    while count < limit:
        yield a
        a, b = b, a + b
        count += 1

print("--- Fibonacci Generator ---")
for num in fibonacci_stream(8):
    print(f"Fibonacci Item: {num}")

# 2. Custom Function Decorator
def audit_logger(func):
    def wrapper(*args, **kwargs):
        print(f"⚙️ [AUDIT] Calling function '{func.__name__}' with args={args}")
        result = func(*args, **kwargs)
        print(f"✨ [AUDIT] Function '{func.__name__}' returned result={result}")
        return result
    return wrapper

@audit_logger
def calculate_payout(hours: float, rate: float):
    return hours * rate

payout = calculate_payout(40, 45.50)
'''
            }
        ]
    },
    'java': {
        'title': 'Java 17 Enterprise Academy',
        'short_title': 'Java 17',
        'icon': '☕',
        'color': '#ea580c',
        'badge': 'Static, Typed & JVM',
        'summary': 'Master Core Java, OOP hierarchies, JVM memory models, Collections Framework, and Multi-Threading with real enterprise architectural patterns.',
        'topics': [
            {
                'slug': 'java-variables-primitives-heap',
                'title': 'Variables, Primitive Types & JVM Stack vs Heap',
                'category': 'Fundamentals',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'Cash in Wallet vs Bank Vault Safe Box',
                    'text': 'In Java, a primitive variable (int, double, boolean) is cash held in your front pocket wallet (stored on the fast thread Stack). An Object (String, Array, Custom Class) is a gold bar stored in a bank vault (Heap Memory); your variable on the stack only holds the safe box number key (Memory Reference).'
                },
                'use_case': {
                    'company': 'High-Frequency Trading & Banking Engines',
                    'text': 'Financial platforms like Goldman Sachs and Morgan Stanley carefully avoid unnecessary object allocations to minimize JVM Garbage Collection (GC) pauses during trade executions.'
                },
                'concept_explanation': '''
<h3>1. Primitives vs Reference Types</h3>
<ul>
  <li><strong>Primitives:</strong> <code>byte, short, int, long, float, double, boolean, char</code> (stored directly on Stack).</li>
  <li><strong>References:</strong> Points to heap memory locations where objects reside.</li>
</ul>
''',
                'starter_code': '''// JVM Memory & Variable Scoping Demonstration
public class Main {
    public static void main(String[] args) {
        // Primitives on Stack
        int balance = 5000;
        boolean isActive = true;
        
        System.out.println("User Balance: $" + balance);
        System.out.println("Account Active: " + isActive);
        
        // Reference Type on Heap
        int[] scores = new int[]{98, 85, 92, 78};
        int total = 0;
        
        for (int s : scores) {
            total += s;
        }
        
        double average = (double) total / scores.length;
        System.out.println("Calculated Average: " + average);
    }
}
'''
            },
            {
                'slug': 'java-oop-inheritance-polymorphism',
                'title': 'OOP Architecture: Classes, Inheritance & Polymorphism',
                'category': 'Architecture',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Universal Remote & Multi-Brand Devices',
                    'text': 'Think of Polymorphism as a Universal TV remote. The remote has a standard button labeled "Power On". When pressed in front of a Sony TV, it sends the Sony signal; when pressed in front of an LG TV, it sends the LG signal. The caller uses one uniform interface without caring about internal manufacturer details.'
                },
                'use_case': {
                    'company': 'Uber & Ride-Sharing Fare Engines',
                    'text': 'Uber implements base `RideFareCalculator` classes. `UberX`, `UberBlack`, and `UberPool` inherit from it and override `calculateFare()` to apply specific multipliers without breaking the booking service.'
                },
                'concept_explanation': '''
<h3>Key Java OOP Features</h3>
<ul>
  <li><strong>Method Overriding (`@Override`):</strong> Runtime polymorphism where child classes provide specific implementations of parent methods.</li>
  <li><strong>Encapsulation:</strong> Using <code>private</code> variables with <code>getters</code> and <code>setters</code>.</li>
</ul>
''',
                'starter_code': '''// Polymorphism in Java: Notification Engine
class NotificationService {
    public void send(String message) {
        System.out.println("[Default] Sending: " + message);
    }
}

class EmailNotification extends NotificationService {
    @Override
    public void send(String message) {
        System.out.println("📧 [Email Gateway] Sent: " + message);
    }
}

class SMSNotification extends NotificationService {
    @Override
    public void send(String message) {
        System.out.println("📱 [Twilio SMS] Sent: " + message);
    }
}

public class Main {
    public static void main(String[] args) {
        NotificationService[] services = new NotificationService[]{
            new EmailNotification(),
            new SMSNotification()
        };

        for (NotificationService s : services) {
            s.send("Your verification OTP is 849201");
        }
    }
}
'''
            },
            {
                'slug': 'java-collections-arraylist-hashmap',
                'title': 'Java Collections Framework: ArrayList, HashMap & HashSet',
                'category': 'Data Structures',
                'read_time': '9 min read',
                'analogy': {
                    'title': 'The Supermarket Barcode Scanner',
                    'text': 'A Java HashMap is like a supermarket barcode scanner. Instead of looking through 10,000 items on shelves one by one (O(N) linear scan), the laser scans the barcode (key hash), instantly jumps to the exact shelf row and returns the price in O(1) constant time.'
                },
                'use_case': {
                    'company': 'Amazon Product Catalog & Cart Checkout',
                    'text': 'Amazon uses HashMaps to map SKU barcode numbers to inventory stock counts, ensuring instant price lookups during million-item flash sales.'
                },
                'concept_explanation': '''
<h3>Internal HashMap Mechanism</h3>
<p>HashMap calculates bucket indices using <code>(n - 1) & hash</code>. In Java 8+, when bucket collisions exceed 8 elements, linked lists transform into red-black trees for O(log N) lookup speed.</p>
''',
                'starter_code': '''// Java Collections: ArrayList & HashMap Operations
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

public class Main {
    public static void main(String[] args) {
        // 1. Dynamic ArrayList
        ArrayList<String> departments = new ArrayList<>();
        departments.add("Engineering");
        departments.add("Design");
        departments.add("Product");
        
        System.out.println("Total Departments: " + departments.size());

        // 2. HashMap Key-Value Storage
        HashMap<String, Integer> salaryMap = new HashMap<>();
        salaryMap.put("Alice (Lead)", 125000);
        salaryMap.put("Bob (DevOps)", 115000);
        salaryMap.put("Charlie (Frontend)", 95000);

        for (Map.Entry<String, Integer> entry : salaryMap.entrySet()) {
            System.out.println("Employee: " + entry.getKey() + " -> $" + entry.getValue());
        }
    }
}
'''
            }
        ]
    },
    'javascript': {
        'title': 'Modern JavaScript (ES6+) Academy',
        'short_title': 'JavaScript',
        'icon': '⚡',
        'color': '#eab308',
        'badge': 'Event-Driven & Asynchronous',
        'summary': 'Master Modern JavaScript ES6+, arrow functions, closures, Async/Await promises, and the browser event loop with hands-on live debugging.',
        'topics': [
            {
                'slug': 'javascript-variables-let-const',
                'title': 'Variables: let, const vs var & Scope Rules',
                'category': 'Fundamentals',
                'read_time': '6 min read',
                'analogy': {
                    'title': 'The Glass Display Case vs Erasable Whiteboard',
                    'text': 'const is a locked glass museum display case: you cannot replace the item with a completely different object (cannot reassign identifier). let is an erasable whiteboard inside a meeting room: whatever is written can be changed, but disappears once you leave that room (block-scoped). var is a megaphone echoing through the whole building, leaking variables everywhere.'
                },
                'use_case': {
                    'company': 'React.js State Immutability',
                    'text': 'React relies on `const` and immutable data patterns so virtual DOM reconciliation can quickly check object references (`prevProps === nextProps`) to prevent unnecessary re-renders.'
                },
                'concept_explanation': '''
<h3>Block Scope vs Function Scope</h3>
<p><code>let</code> and <code>const</code> are block-scoped (confined inside <code>{ }</code> brackets), preventing accidental memory leaks and variable shadowing bugs common with old <code>var</code>.</p>
''',
                'starter_code': '''// Modern JS Variable Scoping & Mutation
const userProfile = {
  id: 104,
  name: "Taylor",
  role: "Engineer"
};

// Object properties can be mutated inside const
userProfile.role = "Senior Architect";
console.log("Updated User Role:", userProfile.role);

// Block Scoping with let
let totalScore = 0;
for (let i = 1; i <= 3; i++) {
  let bonus = i * 10;
  totalScore += bonus;
  console.log(`Round ${i}: Added +${bonus} (Total: ${totalScore})`);
}
'''
            },
            {
                'slug': 'javascript-arrow-functions-callbacks',
                'title': 'Arrow Functions & Array Methods (map, filter, reduce)',
                'category': 'Functional JS',
                'read_time': '7 min read',
                'analogy': {
                    'title': 'The Factory Conveyor Belt Pipeline',
                    'text': 'Think of map, filter, and reduce as an automated manufacturing line. Raw materials move down the belt: filter removes defective items, map paints and polishes remaining items, and reduce boxes all finished items into a single final shipment crate.'
                },
                'use_case': {
                    'company': 'Airbnb & E-Commerce Search Filtering',
                    'text': 'Filtering listings by price range, mapping them to coordinates on Mapbox, and reducing them into average nightly rates is executed in one seamless functional pipeline.'
                },
                'concept_explanation': '''
<h3>Functional Array Pipeline Methods</h3>
<ul>
  <li><code>.filter()</code>: Returns a new array with items that satisfy the boolean predicate.</li>
  <li><code>.map()</code>: Transforms every item into a new value.</li>
  <li><code>.reduce()</code>: Accumulates array elements into a single result.</li>
</ul>
''',
                'starter_code': '''// Functional Array Pipelines in Modern JS
const products = [
  { name: "Mechanical Keyboard", price: 120, inStock: true },
  { name: "USB-C Hub", price: 35, inStock: false },
  { name: "Gaming Mouse", price: 65, inStock: true },
  { name: "Monitor Arm", price: 80, inStock: true }
];

// 1. Filter: In-stock items only
const available = products.filter(p => p.inStock);

// 2. Map: Format price tags
const priceTags = available.map(p => `${p.name}: $${p.price}`);
console.log("Available Items:", priceTags);

// 3. Reduce: Calculate Cart Total
const totalCost = available.reduce((acc, curr) => acc + curr.price, 0);
console.log("Cart Subtotal: $" + totalCost);
'''
            },
            {
                'slug': 'javascript-async-await-promises',
                'title': 'Asynchronous JS: Promises, Async/Await & Event Loop',
                'category': 'Async & Network',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Coffee Shop Vibrating Order Buzzer',
                    'text': 'When you order an espresso, the barista does NOT make you stand frozen at the register blocking 20 customers behind you (blocking synchronous code). Instead, you receive a vibrating electronic pager (a Promise). You sit down, read a book, and when the espresso is ready, the pager buzzes (Promise resolved).'
                },
                'use_case': {
                    'company': 'Netflix Video Streaming & Buffering',
                    'text': 'Netflix uses asynchronous promises to stream video chunks and fetch subtitles concurrently in background worker threads without freezing the playback UI.'
                },
                'concept_explanation': '''
<h3>Promises & Async/Await</h3>
<p><code>async/await</code> is syntactic sugar built over JavaScript Promises, transforming asynchronous callback pyramids into clean, readable linear code with <code>try...catch</code> error blocks.</p>
''',
                'starter_code': '''// Asynchronous Execution & Promise Simulation
function mockFetchUserData(userId) {
  return new Promise((resolve, reject) => {
    if (userId > 0) {
      resolve({ id: userId, username: "dev_kashi", status: "Active Pro" });
    } else {
      reject(new Error("Invalid User ID"));
    }
  });
}

async function loadDashboard() {
  console.log("1. Starting user fetch request...");
  try {
    const user = await mockFetchUserData(42);
    console.log("2. Data received successfully:", user.username);
    console.log("3. User Status:", user.status);
  } catch (err) {
    console.log("Error loading dashboard:", err.message);
  }
}

loadDashboard();
'''
            },
            {
                'slug': 'javascript-closures-scope',
                'title': 'Closures & Lexical Scoping Architecture',
                'category': 'Advanced',
                'read_time': '8 min read',
                'analogy': {
                    'title': 'The Student Backpack in Grad School',
                    'text': 'A Closure is like a student\'s personal backpack. When the student leaves the high school classroom (the outer function finishes executing and pops off the call stack), they still carry their backpack containing all their notes and pencils (the inner function permanently retains access to outer scope variables).'
                },
                'use_case': {
                    'company': 'Redux Store & Secure Token Managers',
                    'text': 'Closures enable private state encapsulation in JavaScript without exposing internal variables to external modification on the global `window` object.'
                },
                'concept_explanation': '''
<h3>What is a Closure?</h3>
<p>A closure is the combination of a function bundled together with references to its surrounding lexical environment. Functions in JavaScript retain scope bindings across invocations.</p>
''',
                'starter_code': '''// Encapsulated Counter using Closures
function createBankVault(initialSecret) {
  let secretCode = initialSecret;
  let accessCount = 0;

  return {
    validate: function(inputCode) {
      accessCount++;
      return inputCode === secretCode;
    },
    getAttempts: function() {
      return `Total vault security checks: ${accessCount}`;
    }
  };
}

const vault = createBankVault("pass123");
console.log("Check 1:", vault.validate("wrong"));
console.log("Check 2:", vault.validate("pass123"));
console.log(vault.getAttempts());
'''
            }
        ]
    }
}
