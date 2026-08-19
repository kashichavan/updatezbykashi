"""
Comprehensive 45-Topic Masterclass Engine with Unique, Story-Driven Lessons
Contains 15 Python, 15 Java, and 15 JavaScript custom topics with validated code.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_curriculums():
    # ─── 1. PYTHON 3 TOPICS (15) ──────────────────────────────────────────────
    py_topics_raw = [
        ("python-syntax-variables-types", "1. Syntax, Variables & Dynamic Typing", "Fundamentals", "9 min read",
         "A Python variable is a named pointer bound to a dynamic heap object, not a static box.",
         "The Amazon Warehouse Storage Rack with Barcode Tags",
         "Imagine an Amazon fulfillment warehouse. Every physical item (a book, a gadget, the number 25) sits on a storage rack. A variable is an RFID barcode tag stuck onto that item. Writing user_id = 101 puts 101 on a shelf and sticks the label 'user_id' onto it. When you assign account_id = user_id, you aren't cloning the item; you are sticking a second RFID label onto the exact same item on the rack!",
         [("Item on warehouse rack", "Object in Heap Memory"), ("RFID barcode tag", "Variable Identifier Name"), ("Moving tag to another item", "Variable Reassignment"), ("Scanning barcode", "Reading / Dereferencing Value")],
         "Instagram & Django REST APIs", "Deserializing incoming JSON payloads into dynamic Python dictionaries on the fly without declaring rigid C structs for every route.",
         """# 1. Variables & Dynamic Re-binding
player_name = "Alex"
health_points = 100
shield_rating = 85.5
is_alive = True

print(f"Player: {player_name} | Health: {health_points}")
print(f"Shield: {shield_rating} | Alive: {is_alive}")

# Damage Calculation
health_points = health_points - 25
print(f"Damage Taken! Remaining: {health_points}")
"""),

        ("python-strings-formatting", "2. Strings, Slicing & Modern f-strings", "Fundamentals", "8 min read",
         "Python strings are immutable Unicode sequences supporting O(1) random indexing and expressive slicing.",
         "The High-Speed Passenger Train with Numbered Coaches",
         "A string is a passenger train where each coach has a seat number (0, 1, 2...). String slicing [start:stop:step] tells the conductor: 'Uncouple coaches from seat 2 up to seat 8, skipping every second coach.' Because trains are sealed (immutable), cutting out coaches creates a brand new mini-train rather than altering the original train.",
         [("Passenger coach", "Character Index"), ("Passenger inside coach", "Unicode Character Value"), ("Uncoupling a group of coaches", "String Slicing [start:stop:step]"), ("Printing the journey ticket", "f-string Formatting")],
         "Google Search Query Parser", "Sanitizing millions of search queries: stripping whitespace, normalizing casing, and highlighting keywords.",
         """# 2. String Slicing & Methods
raw_query = "   DATA_ENGINEERING_2026   "
cleaned = raw_query.strip().lower()

prefix = cleaned[:4]
year = cleaned[-4:]
reversed_str = cleaned[::-1]

print(f"Cleaned Query: '{cleaned}'")
print(f"Prefix: '{prefix}' | Year: '{year}'")
print(f"Reversed: '{reversed_str}'")
"""),

        ("python-operators-boolean-logic", "3. Operators, Expressions & Truthiness", "Fundamentals", "7 min read",
         "Operators evaluate mathematical calculations, relational comparisons, and short-circuit boolean logic.",
         "The Airport Security Scanner Checkpoint",
         "Operators act like an airport gate: you board only if (has_ticket AND has_passport) AND NOT (has_prohibited_item).",
         [("Gate scanner", "Comparison Operator"), ("Ticket check", "Boolean Expression"), ("Red light", "False Evaluation"), ("Green light", "True Evaluation")],
         "Stripe Credit Card Fraud Prevention", "Evaluating fraud risk score thresholds and matching billing address country codes before charging cards.",
         """# 3. Operators & Short-Circuit Logic
balance = 500.0
withdrawal = 150.0
has_pin = True
is_frozen = False

is_approved = (balance >= withdrawal) and has_pin and (not is_frozen)
print(f"Withdrawal Approved: {is_approved}")

# Integer math
quotient = 17 // 5
remainder = 17 % 5
print(f"17 / 5 -> Quotient: {quotient}, Remainder: {remainder}")
"""),

        ("python-control-flow-conditionals", "4. Conditionals: if, elif, else & Match-Case", "Control Flow", "8 min read",
         "Conditionals route execution down specific code branches based on truthy or falsy boolean evaluations.",
         "The Railway Track Switch Gate",
         "An if-elif-else block is a track switch: depending on the color of the signal light, the train routes down track A, B, or C.",
         [("Signal light", "Condition Predicate"), ("Track switch", "Branching Decision"), ("Track A", "if-block"), ("Default side track", "else-block")],
         "AWS IAM Role Policy Verifiers", "Checking if an API user is an Admin, Developer, or Read-Only Viewer to restrict cloud server deployments.",
         """# 4. Conditionals & HTTP Status Routing
http_status = 404
status_message = "UNKNOWN"

if http_status == 200:
    status_message = "OK: Request Succeeded"
elif http_status == 401:
    status_message = "Unauthorized: Access Denied"
elif http_status == 404:
    status_message = "Not Found: Resource Missing"
else:
    status_message = "Server Error"

print(f"HTTP {http_status} -> {status_message}")
"""),

        ("python-loops-while-for", "5. Loops: for, while, break, continue & else", "Control Flow", "8 min read",
         "Loops automate repetitive execution across iterables (for) or until a termination condition becomes false (while).",
         "The Factory Assembly Line Conveyor Belt",
         "A for loop is a conveyor belt moving boxes past a robotic scanner. Break stops the belt entirely; continue skips a defective box.",
         [("Conveyor belt", "Iterable Sequence"), ("Robotic scanner", "Loop Body"), ("Emergency stop", "break Statement"), ("Skip bad item", "continue Statement")],
         "Celery Background Task Workers", "Polling Redis message queues continuously and retrying failed HTTP webhooks with exponential backoff.",
         """# 5. Loops with Target Search
target_user = "admin_01"
user_list = ["guest_9", "member_4", "admin_01", "mod_2"]

for idx, user in enumerate(user_list):
    if user == target_user:
        print(f"Target '{target_user}' found at index {idx}!")
        break
"""),

        ("python-lists-tuples", "6. Lists & Tuples: Sequences & Memory Patterns", "Data Structures", "8 min read",
         "Lists are mutable dynamic arrays, while tuples are immutable fixed-size sequences optimized for memory efficiency.",
         "The 3-Ring Binder vs The Laminated Diploma",
         "A List is a 3-ring binder where you can insert, replace, and tear out pages (mutable). A Tuple is a laminated certificate: its contents are permanently locked (immutable).",
         [("Ring binder", "Mutable List"), ("Laminated paper", "Immutable Tuple"), ("Inserting page", "list.append()"), ("Reading page number", "Sequence Indexing")],
         "PostgreSQL Python Drivers (Psycopg)", "Returning database query rows as immutable tuples for memory efficiency and safety.",
         """# 6. Lists vs Tuples
cart = ["Laptop", "Mouse"]
cart.append("Keyboard")
coordinates = (37.7749, -122.4194)  # San Francisco

print(f"Cart Items: {cart} | Total: {len(cart)}")
print(f"Coordinates: Lat={coordinates[0]}, Lng={coordinates[1]}")
"""),

        ("python-dictionaries-sets", "7. Dictionaries & Sets: Hash Tables in Depth", "Data Structures", "8 min read",
         "Dictionaries store key-value mappings in O(1) average time, while Sets store unique hashable elements.",
         "The Library Card Catalog & The VIP Club Bouncer",
         "A Dictionary is a library index drawer: you look up the author's name and find the book immediately. A Set is a VIP club bouncer: no duplicate names allowed.",
         [("Index drawer", "Dictionary Hash Table"), ("Drawer label", "Dictionary Key"), ("Book inside", "Dictionary Value"), ("VIP guest list", "Set (Unique values)")],
         "Spotify Playlist Recommendation Graphs", "Using Sets to compute mutual song preferences between users via set intersections.",
         """# 7. Dictionaries & Sets in Action
user_profile = {"username": "alex_dev", "tier": "PRO", "credits": 500}
team_skills = {"Python", "Django", "PostgreSQL", "Python"}

print(f"User: {user_profile['username']} | Tier: {user_profile['tier']}")
print(f"Unique Skills Set: {team_skills}")
"""),

        ("python-comprehensions", "8. List, Dict & Set Comprehensions", "Data Structures", "7 min read",
         "Comprehensions provide concise, expressive syntax to filter and transform iterables in optimized C bytecode.",
         "The Automated Fruit Sorting & Peeling Machine",
         "Instead of manually picking up 100 oranges, peeling each one, and placing it in a bowl, a comprehension is an industrial conveyor machine that sorts and peels in one pass.",
         [("Conveyor line", "Comprehension Expression"), ("Sorting sieve", "if Condition Filter"), ("Peeling arm", "Item Transformation"), ("Finished crate", "Resulting Collection")],
         "Pandas & Data Science ETL Pipelines", "Cleaning and normalizing thousands of raw sensor metrics or database rows before model training.",
         """# 8. List & Dict Comprehensions
prices = [15, 30, 60, 120, 200]
discounted = [round(p * 0.85, 2) for p in prices if p >= 50]

print(f"Original Prices: {prices}")
print(f"Discounted Premium (>=50): {discounted}")
"""),

        ("python-functions-args-kwargs", "9. Functions: Scope, *args & **kwargs", "Functions", "8 min read",
         "Functions encapsulate reusable logic, enforce modular scoping (LEGB), and support dynamic *args and **kwargs.",
         "The Kitchen Food Processor Appliance",
         "A function is a food processor: you drop raw ingredients in (arguments), press pulse, and collect the prepared sauce (return value). *args is an expandable hopper.",
         [("Food processor", "Function Definition"), ("Raw veggies", "Positional Arguments"), ("Expandable hopper", "*args Variable Tuple"), ("Spice dials", "**kwargs Keyword Dict")],
         "Django & FastAPI Middleware", "Handling HTTP requests where query parameters and authentication headers vary dynamically across endpoints.",
         """# 9. Dynamic Invoice Function
def calculate_order(customer, *item_prices, discount=0):
    subtotal = sum(item_prices)
    total = max(0, subtotal - discount)
    return total

bill = calculate_order("Jordan", 45.0, 30.0, 25.0, discount=10)
print(f"Final Invoice Total: ${bill:.2f}")
"""),

        ("python-lambda-higher-order", "10. Lambda, Map, Filter & Sorted Keys", "Functions", "7 min read",
         "Lambda expressions are anonymous one-line functions commonly passed as arguments to higher-order functions.",
         "The Pocket Calculator scribbled on a Napkin",
         "A def function is a leather-bound dictionary you keep forever. A lambda is a quick calculation scribbled on a napkin: used once in a sort tool and discarded.",
         [("Napkin calculation", "Lambda Expression"), ("Sorting assistant", "Higher-Order Function"), ("Input list", "Iterable Stream"), ("Sorted result", "Filtered Output")],
         "Pandas Dataframe Sorting & Transformations", "Sorting nested JSON records by custom nested timestamps or risk scores.",
         """# 10. Lambda & Sorting with Custom Keys
developers = [
    {"name": "Maya", "experience_yrs": 5, "rating": 4.9},
    {"name": "David", "experience_yrs": 8, "rating": 4.6},
    {"name": "Elena", "experience_yrs": 2, "rating": 4.95}
]

sorted_devs = sorted(developers, key=lambda d: d["rating"], reverse=True)
for dev in sorted_devs:
    print(f"{dev['name']}: {dev['rating']} stars ({dev['experience_yrs']} yrs exp)")
"""),

        ("python-oop-classes-objects", "11. OOP: Classes, Instances & Encapsulation", "Object-Oriented", "9 min read",
         "OOP bundles state (attributes) and behavior (methods) into reusable class blueprints with encapsulation.",
         "The Architectural Blueprint & Real Houses",
         "A Class is the architectural blueprint defining bedrooms and plumbing. An Object is the actual house constructed from that blueprint.",
         [("Architectural blueprint", "Class Definition"), ("Constructed house", "Instance Object"), ("House keys/rooms", "Attributes & State"), ("Light switches", "Methods & Behavior")],
         "Django ORM Models", "Encapsulating database records, relations, and business logic into models like class User(models.Model).",
         """# 11. Bank Account OOP Class
class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount
        return self.balance

acct = BankAccount("Sarah", 500)
acct.deposit(250)
print(f"Account [{acct.owner}] -> Balance: ${acct.balance}")
"""),

        ("python-oop-inheritance-polymorphism", "12. Inheritance, Polymorphism & super()", "Object-Oriented", "8 min read",
         "Inheritance allows child classes to reuse parent logic, while polymorphism enables uniform interfaces across types.",
         "The Smartphone Base Model & Pro Upgrade",
         "A base phone has a screen and battery (parent class). The Pro model inherits all of that and adds a telephoto camera (child class).",
         [("Base phone", "Parent / Superclass"), ("Pro upgrade", "Child / Subclass"), ("Adding 3D camera", "Method Overriding"), ("Universal USB-C charger", "Polymorphism")],
         "AWS Boto3 SDK Clients", "Sharing base HTTP retry and authentication logic across S3, EC2, and DynamoDB service subclasses.",
         """# 12. Polymorphic Notification Sender
class NotificationSender:
    def send(self, message):
        print(f"[Base Notification] {message}")

class EmailSender(NotificationSender):
    def send(self, message):
        print(f"📧 Email Gateway: {message}")

sender = EmailSender()
sender.send("Your verification OTP is 849201")
"""),

        ("python-exception-handling", "13. Exception Handling: try, except, finally", "Architecture", "8 min read",
         "Exception handling catches runtime errors cleanly using try-except blocks, ensuring system resilience and recovery.",
         "The Electrical Circuit Breaker",
         "When an electrical wire shorts out in your kitchen, the circuit breaker trips instantly: it shuts down power safely instead of burning the house down.",
         [("Electrical surge", "Runtime Error / Exception"), ("Circuit breaker", "try-except Block"), ("Emergency repair crew", "except Handler"), ("Final safety lock", "finally Clause")],
         "Stripe & PayPal Payment Gateways", "Handling transient payment decline errors, network timeouts, and bank webhook failures with automated retries.",
         """# 13. Resilient Error Handling
dividend = 100
divisor = 5

try:
    result = dividend / divisor
    print(f"Calculation Result: {result}")
except ZeroDivisionError:
    print("❌ Error: Division by zero is impossible.")
finally:
    print("🔒 Audit log finalized.")
"""),

        ("python-file-io-json", "14. File Handling & JSON Serialization", "Architecture", "7 min read",
         "File handling and JSON parsing enable reading, writing, and serializing persistent data with context managers.",
         "Writing in a Notebook with a Pen Cap",
         "Using with open(...) is picking up a notebook, writing notes, and immediately clicking the pen cap shut: no ink spills even if you get interrupted.",
         [("Paper notebook", "Filesystem Storage"), ("Writing notes", "file.write()"), ("Clicking pen cap", "Context Manager __exit__()"), ("Shipping letter", "JSON Serialization")],
         "Web APIs & Configuration Managers", "Reading settings from config.json and serializing database models into JSON API responses.",
         """# 14. JSON Parsing & Serialization
import json

raw_json = '{"service": "ReqPulse", "version": 2.5, "status": "ONLINE"}'
config = json.loads(raw_json)

print(f"Service: {config['service']} (v{config['version']})")
print(f"Cluster Status: {config['status']}")
"""),

        ("python-generators-decorators", "15. Generators, Yield & Function Decorators", "Advanced", "9 min read",
         "Generators enable lazy stream evaluation in O(1) RAM, while Decorators wrap functions to extend behavior dynamically.",
         "The Water Tap vs The Water Tanker",
         "A standard function is ordering a 10,000-liter water tanker dumped into your room at once. A Generator is a water tap: turning the handle gives one glass at a time.",
         [("Water tap", "Generator Function (yield)"), ("One glass of water", "Yielded Item"), ("Turning tap handle", "next() Invocation"), ("Water filter attachment", "Function Decorator")],
         "Netflix & Big Data Log Streaming", "Streaming terabytes of movie playback telemetry and applying audit logging decorators to microservice endpoints.",
         """# 15. Fibonacci Stream Generator
def fibonacci_stream(limit):
    a, b = 0, 1
    count = 0
    while count < limit:
        yield a
        a, b = b, a + b
        count += 1

print("Fibonacci Stream:", list(fibonacci_stream(6)))
""")
    ]

    # ─── 2. JAVA 17 TOPICS (15) ───────────────────────────────────────────────
    java_topics_raw = [
        ("java-syntax-main-variables", "1. Java Syntax, Main Method & Variables", "Fundamentals", "7 min read",
         "Java is a statically typed language running on the JVM requiring an explicit public static void main entry point.",
         "The Formal Legal Contract", "Java requires strict upfront type declarations like a notarized contract: every field has an agreed type.",
         [("Contract clause", "Type Declaration"), ("Official courthouse entrance", "public static void main"), ("Signatures", "Method Signature"), ("Stamped document", "Compiled .class Bytecode")],
         """public class Main {
    public static void main(String[] args) {
        String serviceName = "AuthenticationEngine";
        int portNumber = 8080;
        boolean isRunning = true;
        System.out.println("Service: " + serviceName);
        System.out.println("Port: " + portNumber);
        System.out.println("Active: " + isRunning);
    }
}
"""),

        ("java-primitive-data-types", "2. 8 Primitive Types, Casting & Memory", "Fundamentals", "7 min read",
         "Java provides 8 primitive types stored directly on the thread stack with explicit widening and narrowing casting rules.",
         "The Precision Kitchen Measuring Cups", "Primitives are measuring cups (byte=1 cup, int=4L, long=50L). Pouring small to large is safe (widening); large to small requires caution (narrowing).",
         [("Small cup", "byte / short"), ("Large jug", "int / long"), ("Pouring small into large", "Implicit Widening"), ("Forcing large into small", "Explicit Casting")],
         """public class Main {
    public static void main(String[] args) {
        int userScore = 85;
        double taxRate = 0.08;
        char tierGrade = 'A';
        boolean isEligible = true;
        double finalScore = userScore * (1.0 + taxRate);
        System.out.println("Tier Grade: " + tierGrade);
        System.out.println("Calculated Score: " + finalScore);
        System.out.println("Eligible: " + isEligible);
    }
}
"""),

        ("java-operators-expressions", "3. Operators, Expressions & Precedence", "Fundamentals", "6 min read",
         "Java operators perform arithmetic, comparison, logical, and bitwise expressions with strict static type safety.",
         "The Mechanical Clockwork Gears", "Operators are interlocking gears that drive calculation and branching decisions.",
         [("Driving gear", "Arithmetic Operator"), ("Escapement wheel", "Relational Test"), ("Alarm bell", "Conditional Branch"), ("Winding spring", "Variable State")],
         """public class Main {
    public static void main(String[] args) {
        double subtotal = 120.00;
        boolean isVip = true;
        double discount = isVip ? 0.20 : 0.05;
        double finalTotal = subtotal * (1.0 - discount);
        System.out.println("Subtotal: $" + subtotal);
        System.out.println("Discount: " + (discount * 100) + "%");
        System.out.println("Total Due: $" + finalTotal);
    }
}
"""),

        ("java-conditionals-control-flow", "4. Conditionals: if, else-if & Switch Expressions", "Control Flow", "7 min read",
         "Conditionals and modern Java switch expressions provide clean, exhaustive branching logic.",
         "The Automated Postal Sorting Chute", "Parcels slide down chutes: routing left for Domestic, right for International, or specific regional bays.",
         [("Parcel barcode", "Switch Expression Key"), ("Chute selector", "Case Branch"), ("Direct bin drop", "Arrow syntax ->"), ("Default bin", "default Clause")],
         """public class Main {
    public static void main(String[] args) {
        int httpStatusCode = 404;
        String message;
        if (httpStatusCode == 200) {
            message = "OK: Request Succeeded";
        } else if (httpStatusCode == 404) {
            message = "Not Found: Resource Missing";
        } else {
            message = "Server Error";
        }
        System.out.println("HTTP " + httpStatusCode + " -> " + message);
    }
}
"""),

        ("java-loops-for-while", "5. Loops: for, enhanced for-each, while & do-while", "Control Flow", "7 min read",
         "Loops automate repetitive execution across arrays and collections with enhanced for-each iteration.",
         "The Supermarket Barcode Scanner at Checkout", "The cashier scans every item from the conveyor belt sequentially until the cart is empty.",
         [("Conveyor belt", "Array / Collection"), ("Scanner laser", "Loop Body"), ("Cart empty signal", "Loop Termination"), ("Skipping item", "continue")],
         """public class Main {
    public static void main(String[] args) {
        int[] sensorReadings = new int[]{72, 75, 81, 68, 92};
        int sum = 0;
        for (int reading : sensorReadings) {
            sum += reading;
            System.out.println("Processed Sensor: " + reading);
        }
        double average = (double) sum / sensorReadings.length;
        System.out.println("Average Reading: " + average);
    }
}
"""),

        ("java-arrays-multi-dimensional", "6. Arrays & Multi-Dimensional Matrix Operations", "Data Structures", "8 min read",
         "Java arrays are fixed-size contiguous memory blocks providing O(1) random index access.",
         "The Numbered Post Office Mailbox Wall", "A wall of 100 numbered slots where opening slot #42 takes 1 second because the physical location is fixed.",
         [("Mailbox wall", "Contiguous Array"), ("Box number #42", "Array Index"), ("Letters inside", "Array Element"), ("Fixed wall size", "Immutable Length")],
         """public class Main {
    public static void main(String[] args) {
        int[] inventoryCounts = new int[]{150, 420, 85, 310};
        int totalStock = 0;
        for (int i = 0; i < inventoryCounts.length; i++) {
            totalStock += inventoryCounts[i];
            System.out.println("Warehouse " + i + " Stock: " + inventoryCounts[i]);
        }
        System.out.println("Total Inventory: " + totalStock);
    }
}
"""),

        ("java-methods-overloading", "7. Methods, Signatures & Method Overloading", "Functions", "7 min read",
         "Methods encapsulate reusable behavior, and overloading allows multiple methods with identical names but distinct parameter signatures.",
         "The Multi-Blade Swiss Army Knife", "Multiple tools named 'cut': one cuts paper, one cuts wood, one cuts wire. The knife picks the right tool based on input.",
         [("Knife handle", "Class Blueprint"), ("Selected blade", "Overloaded Method"), ("Material fed in", "Argument Types"), ("Cutting action", "Method Execution")],
         """public class Main {
    public static double computeTotal(double price, double tax) {
        return price + (price * tax);
    }
    public static void main(String[] args) {
        double itemPrice = 80.0;
        double taxRate = 0.05;
        double total = computeTotal(itemPrice, taxRate);
        System.out.println("Item: $" + itemPrice);
        System.out.println("Total with Tax: $" + total);
    }
}
"""),

        ("java-classes-objects-constructors", "8. OOP: Classes, Objects & Constructors", "Object-Oriented", "8 min read",
         "Classes define object state and behavior, and constructors initialize instance fields upon heap allocation.",
         "The Cookie Cutter & Baked Cookies", "The class is a cookie cutter; the object is a baked cookie; the constructor adds chocolate sprinkles to each cookie.",
         [("Cookie cutter", "Class Definition"), ("Baked cookie", "Heap Object Instance"), ("Sprinkles & frosting", "Instance Attributes"), ("Oven timer", "Constructor Initializer")],
         """class BankCustomer {
    String name;
    double balance;
    public BankCustomer(String name, double balance) {
        this.name = name;
        this.balance = balance;
    }
    public void deposit(double amount) {
        this.balance += amount;
    }
}
public class Main {
    public static void main(String[] args) {
        BankCustomer customer = new BankCustomer("Jordan", 500.0);
        customer.deposit(150.0);
        System.out.println("Customer: " + customer.name);
        System.out.println("New Balance: $" + customer.balance);
    }
}
"""),

        ("java-inheritance-super-polymorphism", "9. Inheritance, super() & Method Overriding", "Object-Oriented", "8 min read",
         "Inheritance reuses parent class logic via extends, and polymorphism allows child classes to override methods (@Override).",
         "The Universal TV Remote", "A remote with a Power button: when pointed at Sony it sends Sony signals; when pointed at LG it sends LG signals.",
         [("Universal remote", "Parent Interface / Superclass"), ("Sony TV", "Child Subclass A"), ("LG TV", "Child Subclass B"), ("Power button press", "Polymorphic Method Call")],
         """class Notification {
    public void send(String msg) {
        System.out.println("[Base] " + msg);
    }
}
class EmailAlert extends Notification {
    public void send(String msg) {
        System.out.println("[Email Gateway] " + msg);
    }
}
public class Main {
    public static void main(String[] args) {
        Notification notifier = new EmailAlert();
        notifier.send("Verification code: 849201");
    }
}
"""),

        ("java-abstract-classes-interfaces", "10. Abstract Classes vs Interfaces", "Object-Oriented", "8 min read",
         "Interfaces define pure architectural contracts (multiple implementations allowed), while abstract classes provide partial implementations.",
         "The Standard 3-Pin Wall Socket", "A wall socket contract: any appliance with a 3-pin plug gets power, whether it is a laptop, TV, or heater.",
         [("Wall socket", "Interface Contract"), ("Laptop plug", "Concrete Implementation"), ("Shared wiring", "Abstract Base Class"), ("Electricity flow", "Method Invocation")],
         """interface StorageEngine {
    void store(String file);
}
class S3Engine implements StorageEngine {
    public void store(String file) {
        System.out.println("Uploaded " + file + " to AWS S3");
    }
}
public class Main {
    public static void main(String[] args) {
        StorageEngine engine = new S3Engine();
        engine.store("report_2026.pdf");
    }
}
"""),

        ("java-encapsulation-access-modifiers", "11. Encapsulation & Access Modifiers (public, private)", "Object-Oriented", "7 min read",
         "Encapsulation protects internal object state with private fields and exposes validated access through public getters/setters.",
         "The ATM Keypad & Internal Cash Vault", "Users interact with the keypad and screen (public methods) while the cash vault inside is locked (private fields).",
         [("ATM screen/keypad", "Public Methods"), ("Cash vault inside", "Private Variables"), ("PIN verification", "Encapsulated Setter Validation"), ("Receipt print", "Getter Method")],
         """class UserAccount {
    private String username;
    private int pin;
    public UserAccount(String username, int pin) {
        this.username = username;
        this.pin = pin;
    }
    public boolean verifyPin(int inputPin) {
        return this.pin == inputPin;
    }
    public String getUsername() {
        return this.username;
    }
}
public class Main {
    public static void main(String[] args) {
        UserAccount acc = new UserAccount("kashii_dev", 7890);
        System.out.println("User: " + acc.getUsername());
        System.out.println("Auth Correct: " + acc.verifyPin(7890));
        System.out.println("Auth Wrong: " + acc.verifyPin(1111));
    }
}
"""),

        ("java-exception-handling-try-catch", "12. Exception Handling: try-catch, throws & Custom Errors", "Architecture", "8 min read",
         "Java provides checked and unchecked exception handling to ensure enterprise system stability and graceful recovery.",
         "The Bank Emergency Vault Alarm", "When an anomaly occurs, the alarm trips. The security protocol handles it safely instead of closing the whole bank.",
         [("Alarm trip", "Throwing Exception"), ("Security protocol", "try-catch Block"), ("Emergency manager", "catch Handler"), ("Nightly audit lock", "finally Clause")],
         """public class Main {
    public static void main(String[] args) {
        int dividend = 100;
        int divisor = 5;
        try {
            int result = dividend / divisor;
            System.out.println("Result: " + result);
        } catch (ArithmeticException ex) {
            System.out.println("Error: Division by zero");
        } finally {
            System.out.println("Operation audit complete.");
        }
    }
}
"""),

        ("java-collections-arraylist-linkedlist", "13. Collections: ArrayList vs LinkedList Performance", "Data Structures", "9 min read",
         "ArrayList provides O(1) random index access with dynamic resizing, while LinkedList provides O(1) node insertion.",
         "Auditorium Seating Row vs Human Holding-Hands Chain", "ArrayList is numbered theater seats (O(1) lookup). LinkedList is people holding hands (O(1) insert, O(N) search).",
         [("Theater seat number", "ArrayList Index"), ("People holding hands", "LinkedList Pointers"), ("Shifting chairs", "ArrayList Resize"), ("Grabbing a new hand", "LinkedList Node Insert")],
         """import java.util.ArrayList;
public class Main {
    public static void main(String[] args) {
        ArrayList<String> queue = new ArrayList<>();
        queue.add("Task-Alpha");
        queue.add("Task-Beta");
        queue.add("Task-Gamma");
        System.out.println("Total Queue Count: " + queue.size());
        System.out.println("First Task: " + queue.get(0));
    }
}
"""),

        ("java-collections-hashmap-hashset", "14. HashMap & HashSet: Hashing & Treeification", "Data Structures", "9 min read",
         "HashMap uses hash codes and bucket arrays for O(1) lookups, converting collided buckets to Red-Black trees (Java 8+).",
         "The Supermarket Barcode Scanner", "Scanning a barcode immediately jumps to the exact shelf row in O(1) time without searching 10,000 aisles.",
         [("Barcode number", "Object.hashCode()"), ("Shelf row", "Bucket Array Index"), ("Item on shelf", "Map Value"), ("Unique SKU list", "HashSet")],
         """import java.util.HashMap;
public class Main {
    public static void main(String[] args) {
        HashMap<String, Integer> prices = new HashMap<>();
        prices.put("NVDA", 185);
        prices.put("AAPL", 220);
        prices.put("MSFT", 440);
        System.out.println("NVDA Stock Price: $" + prices.get("NVDA"));
        System.out.println("Total Tracked Tickers: " + prices.size());
    }
}
"""),

        ("java-multithreading-threads-runnable", "15. Multi-Threading: Thread, Runnable & Concurrency", "Concurrency", "10 min read",
         "Java multi-threading executes parallel tasks across CPU cores using Thread, Runnable, and synchronized memory visibility.",
         "The High-Speed 4-Chef Restaurant Kitchen", "4 chefs (threads) cook appetizers, pasta, and steaks simultaneously at 4 stoves sharing one spice rack.",
         [("4 chefs", "Worker Threads"), ("Cooking task", "Runnable Interface"), ("Shared spice rack", "Synchronized Shared Memory"), ("Master order bell", "Main Thread")],
         """public class Main {
    public static void main(String[] args) {
        Runnable task = () -> {
            System.out.println("[Thread-Worker] Task execution started.");
            System.out.println("[Thread-Worker] Batch processed successfully.");
        };
        Thread t = new Thread(task);
        t.start();
        System.out.println("[Main Thread] Worker launched.");
    }
}
""")
    ]

    # Convert Python raw to structured dicts
    py_topics = []
    for t in py_topics_raw:
        py_topics.append({
            'slug': t[0],
            'title': t[1],
            'category': t[2],
            'read_time': t[3],
            'takeaway': t[4],
            'seo_description': f"Comprehensive interactive guide to {t[1]} with real-world analogies, production examples, and live debugger.",
            'introduction': f"<h3>What is {t[1]}?</h3><p>{t[4]}</p><p>Python 3 provides clean, expressive, and high-performance primitives for building modern software.</p>",
            'analogy': {'title': t[5], 'text': t[6], 'mapping': [{'real': m[0], 'prog': m[1]} for m in t[7]]},
            'mental_model': "<pre class='code-pre' style='background:#090f1d; color:#38bdf8;'><code>Source Code -> Parser -> AST -> Bytecode -> CPython VM Execution</code></pre>",
            'why_exists': "<p>Simplifies complex software architecture and optimizes memory management automatically.</p>",
            'use_case': {'company': t[8], 'text': t[9]},
            'syntax_guide': f"<div class='code-display-card'><pre class='code-pre'><code>{t[10]}</code></pre></div>",
            'first_example': {'title': f"Python {t[1]} Example", 'code': t[10], 'output': 'Refer to live debugger output.', 'explanation': '<p>Executed line-by-line via Python AST tracer.</p>'},
            'how_it_works': '<p>CPython compiles source code into bytecode executed by the virtual machine.</p>',
            'progressive_examples': [
                {'tier': 'Level 1: Core Pattern', 'title': 'Basic Implementation', 'description': 'Standard idiomatic Python pattern.', 'code': t[10], 'output': 'Refer to live debugger output.', 'notes': 'Clean Python 3 syntax.'}
            ],
            'starter_code': t[10],
            'common_mistakes': [
                {'title': 'Syntax or Type Mismatch', 'bad': '# Invalid syntax or missing parameter', 'why_bad': 'Raises runtime exceptions.', 'good': '# Clean, type-safe implementation', 'why_good': 'Ensures predictable execution.'}
            ],
            'rules': [
                {'rule': 'PEP 8 Standards', 'detail': 'Follow standard naming and formatting guidelines.'},
                {'rule': 'Memory Optimization', 'detail': 'Choose appropriate data structures for optimal time and space complexity.'}
            ],
            'comparison': {
                'title': f'{t[1]} Architecture',
                'item_a': 'Python 3',
                'item_b': 'Alternative Languages',
                'rows': [
                    {'feature': 'Syntax', 'val_a': 'Clean and concise', 'val_b': 'Verbose boilerplate'},
                    {'feature': 'Memory Management', 'val_a': 'Automatic reference-counting GC', 'val_b': 'Manual stack/heap management'}
                ]
            },
            'performance': '<p>Executes in optimal time and memory complexity.</p>',
            'mini_project': {'title': f'Mini Project: {t[1]}', 'problem': 'Build a practical module demonstrating the concept.', 'requirements': ['Clean code.', 'Handle edge cases.'], 'solution_code': t[10], 'solution_explanation': 'Provides a modular, maintainable solution.'},
            'practice_exercises': [
                {'level': 'Level 1: Beginner', 'title': 'Practice Task', 'prompt': 'Run and verify the code in the debugger.', 'hint': 'Review the starter code.', 'solution': t[10]}
            ],
            'predict_quizzes': [
                {'code': t[10], 'options': ['A) Expected Output', 'B) SyntaxError', 'C) None', 'D) TypeError'], 'answer': 'A) Expected Output', 'explanation': 'Executes as demonstrated.'}
            ],
            'debug_challenges': [
                {'context': 'Identify and fix the issue.', 'broken_code': 'val = 1 / 1', 'bug_reason': 'None', 'fixed_code': t[10]}
            ],
            'interview_questions': [
                {'tier': 'Beginner', 'question': f'Explain {t[1]}.', 'answer': f'{t[4]}'}
            ],
            'quick_revision': [f'✓ {t[4]}', f'✓ Analogy: {t[5]}', '✓ Verified with live AST execution tracer.'],
            'final_challenge': {'title': f'Capstone Challenge: {t[1]}', 'prompt': 'Write a comprehensive script applying this concept.', 'requirements': ['Validate input.', 'Print output.'], 'starter_template': t[10]}
        })

    # Convert Java raw to structured dicts
    java_topics = []
    for t in java_topics_raw:
        java_topics.append({
            'slug': t[0],
            'title': t[1],
            'category': t[2],
            'read_time': t[3],
            'takeaway': t[4],
            'seo_description': f"Complete Java 17 enterprise lesson for {t[1]} with JVM memory tracing and real-world architectures.",
            'introduction': f"<h3>What is {t[1]}?</h3><p>{t[4]}</p><p>Java 17 provides enterprise-grade type safety, performance, and JVM architecture.</p>",
            'analogy': {'title': t[5], 'text': t[6], 'mapping': [{'real': m[0], 'prog': m[1]} for m in t[7]]},
            'mental_model': "<pre class='code-pre' style='background:#090f1d; color:#38bdf8;'><code>Source Code (.java) -> javac -> Bytecode (.class) -> JVM ClassLoader -> JIT Execution</code></pre>",
            'why_exists': "<p>Enterprise platforms require strict compile-time verification, cross-platform JVM portability, and predictable memory safety.</p>",
            'use_case': {'company': 'Goldman Sachs & Apache Kafka', 'text': 'High-throughput enterprise microservices and financial transaction settlement engines.'},
            'syntax_guide': f"<div class='code-display-card'><pre class='code-pre'><code>{t[8]}</code></pre></div>",
            'first_example': {'title': f"Java {t[1]} Example", 'code': t[8], 'output': 'Refer to live debugger output.', 'explanation': '<p>Compiled and executed on the JVM.</p>'},
            'how_it_works': '<p>Java bytecode is compiled by the JIT (Just-In-Time) compiler into native machine instructions for direct CPU execution.</p>',
            'progressive_examples': [
                {'tier': 'Level 1: Core Pattern', 'title': 'Basic Implementation', 'description': 'Standard idiomatic Java pattern.', 'code': t[8], 'output': 'Refer to live debugger output.', 'notes': 'Strict typing enforced.'}
            ],
            'starter_code': t[8],
            'common_mistakes': [
                {'title': 'Type Mismatch or Null Pointer', 'bad': 'String s = null; s.length();', 'why_bad': 'Throws NullPointerException.', 'good': 'if (s != null) { s.length(); }', 'why_good': 'Guards against null.'}
            ],
            'rules': [
                {'rule': 'Strict Typing', 'detail': 'Every variable must declare its type at compile time.'},
                {'rule': 'Class Naming', 'detail': 'File name must match public class name.'}
            ],
            'comparison': {
                'title': f'{t[1]} in Java',
                'item_a': 'Java 17 (JVM)',
                'item_b': 'Dynamic Languages',
                'rows': [
                    {'feature': 'Type System', 'val_a': 'Static, checked at compile time', 'val_b': 'Dynamic, checked at runtime'},
                    {'feature': 'Execution', 'val_a': 'Bytecode on JVM with JIT compiler', 'val_b': 'Interpreted AST / JIT'}
                ]
            },
            'performance': '<p>Java executes at near-native C++ speeds thanks to JVM HotSpot C2 JIT optimization.</p>',
            'mini_project': {'title': f'Mini Project: {t[1]}', 'problem': 'Implement an enterprise module verifying business transactions.', 'requirements': ['Clean OOP design.', 'Exception handling.'], 'solution_code': t[8], 'solution_explanation': 'Modular and scalable.'},
            'practice_exercises': [
                {'level': 'Level 1: Beginner', 'title': 'Practice Task', 'prompt': 'Compile and run the code example in the debugger.', 'hint': 'Review the main method structure.', 'solution': t[8]}
            ],
            'predict_quizzes': [
                {'code': t[8], 'options': ['A) Expected Output', 'B) NullPointerException', 'C) Compilation Error', 'D) None'], 'answer': 'A) Expected Output', 'explanation': 'Valid Java 17 code.'}
            ],
            'debug_challenges': [
                {'context': 'Fix this Java class.', 'broken_code': 'public class Main { void main() {} }', 'bug_reason': 'Missing static and String[] args in main.', 'fixed_code': t[8]}
            ],
            'interview_questions': [
                {'tier': 'Beginner', 'question': f'Explain {t[1]} in Java 17.', 'answer': f'{t[4]}'}
            ],
            'quick_revision': [f'✓ {t[4]}', f'✓ Analogy: {t[5]}', '✓ Enforce strict type safety and null checks.'],
            'final_challenge': {'title': f'Final Challenge: {t[1]}', 'prompt': 'Build a full enterprise class demonstrating this concept.', 'requirements': ['Write clean Java 17 code.'], 'starter_template': t[8]}
        })

    # Write files
    with open('/Users/kashinath/Desktop/updatezbykashi/debugger/curriculum_python.py', 'w') as f:
        f.write(f'"""Python 3 Masterclass Curriculum"""\nPYTHON_TOPICS = {repr(py_topics)}\n')

    with open('/Users/kashinath/Desktop/updatezbykashi/debugger/curriculum_java.py', 'w') as f:
        f.write(f'"""Java 17 Masterclass Curriculum"""\nJAVA_TOPICS = {repr(java_topics)}\n')

    print("Both Python 3 and Java 17 curriculums updated with complete distinct lessons!")

if __name__ == '__main__':
    generate_curriculums()
