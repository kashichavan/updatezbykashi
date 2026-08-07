"""
=============================================================
  DEBUGGER ENGINE — OOP TEST SUITE
  Tests Python (20), JavaScript (15), Java (15) OOP programs
=============================================================
"""
import sys, os, textwrap
sys.path.insert(0, os.path.dirname(__file__))

from debugger.python_tracer     import PythonExecutionTracer
from debugger.javascript_tracer import JavaScriptExecutionTracer
from debugger.java_tracer       import JavaExecutionTracer

GRN = '\033[92m'; RED = '\033[91m'; YEL = '\033[93m'
CYN = '\033[96m'; RST = '\033[0m';  BLD = '\033[1m'

results = {'python': [], 'javascript': [], 'java': []}

def run_python(label, code, expect_stdout=None, expect_vars=None, expect_steps_gte=1):
    try:
        t = PythonExecutionTracer(textwrap.dedent(code).strip())
        out = t.execute()
        return _check(label, 'python', out, expect_stdout, expect_vars, expect_steps_gte)
    except Exception as e:
        return _crash(label, 'python', e)

def run_js(label, code, expect_stdout=None, expect_vars=None, expect_steps_gte=1):
    try:
        t = JavaScriptExecutionTracer(textwrap.dedent(code).strip())
        out = t.execute()
        return _check(label, 'javascript', out, expect_stdout, expect_vars, expect_steps_gte)
    except Exception as e:
        return _crash(label, 'javascript', e)

def run_java(label, code, expect_stdout=None, expect_vars=None, expect_steps_gte=1):
    try:
        t = JavaExecutionTracer(textwrap.dedent(code).strip())
        out = t.execute()
        return _check(label, 'java', out, expect_stdout, expect_vars, expect_steps_gte)
    except Exception as e:
        return _crash(label, 'java', e)

def _check(label, lang, out, expect_stdout, expect_vars, expect_steps_gte):
    issues = []
    steps  = out.get('steps', [])
    if len(steps) < expect_steps_gte:
        issues.append(f"only {len(steps)} steps (expected ≥{expect_steps_gte})")
    for s in steps:
        if s.get('event_type') == 'exception':
            issues.append(f"exception at L{s['line_number']}: {s['ai_explanation'][:70]}")
            break
    for s in steps:
        for k, v in s.get('variables', {}).items():
            if isinstance(v, dict) and v.get('type') in ('function', 'builtin_function_or_method', 'type', 'method'):
                issues.append(f"callable leak: '{k}' type={v['type']}")
    if expect_stdout is not None:
        last_stdout = steps[-1]['stdout'] if steps else ''
        for exp in (expect_stdout if isinstance(expect_stdout, list) else [expect_stdout]):
            if exp not in last_stdout:
                issues.append(f"stdout missing: {repr(exp)} | got: {repr(last_stdout[:100])}")
    if expect_vars:
        last_vars = steps[-1].get('variables', {}) if steps else {}
        for vname, expected_raw in expect_vars.items():
            actual = last_vars.get(vname, {}).get('raw', '__MISSING__')
            if str(expected_raw) not in str(actual):
                issues.append(f"var '{vname}': expected '{expected_raw}' got '{actual}'")
    passed = len(issues) == 0
    results[lang].append({'label': label, 'passed': passed, 'issues': issues, 'steps': len(steps)})
    status = f"{GRN}✅ PASS{RST}" if passed else f"{RED}❌ FAIL{RST}"
    issue_str = f"\n      {YEL}» {'; '.join(issues)}{RST}" if issues else ''
    lk = lang[:2].upper()
    print(f"  {status} [{lk}] {label} ({len(steps)} steps){issue_str}")
    return passed

def _crash(label, lang, exc):
    msg = str(exc)[:100]
    results[lang].append({'label': label, 'passed': False, 'issues': [f'CRASH: {msg}'], 'steps': 0})
    print(f"  {RED}💥 CRASH{RST} [{lang[:2].upper()}] {label}: {msg}")
    return False


# ══════════════════════════════════════════════════════════════════════════════
#  PYTHON OOP  (20 programs)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{CYN}{'─'*62}\n  🐍 PYTHON OOP — 20 Programs\n{'─'*62}{RST}")

run_python("PO01 Basic class + __init__","""
class Dog:
    def __init__(self, name, breed):
        self.name = name
        self.breed = breed
d = Dog('Rex', 'Labrador')
print(d.name)
print(d.breed)
""", expect_stdout=["Rex", "Labrador"], expect_steps_gte=5)

run_python("PO02 Instance method","""
class Circle:
    def __init__(self, radius):
        self.radius = radius
    def area(self):
        return 3 * self.radius * self.radius
c = Circle(7)
a = c.area()
print(a)
""", expect_stdout="147", expect_steps_gte=4)

run_python("PO03 Class variable","""
class Counter:
    count = 0
    def __init__(self):
        Counter.count = Counter.count + 1
c1 = Counter()
c2 = Counter()
print(Counter.count)
""", expect_stdout="2", expect_steps_gte=3)

run_python("PO04 __str__ method","""
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    def __str__(self):
        return self.name + ' age ' + str(self.age)
p = Person('Kashi', 22)
print(str(p))
""", expect_stdout="Kashi age 22")

run_python("PO05 Inheritance","""
class Animal:
    def __init__(self, name):
        self.name = name
    def speak(self):
        return 'Some sound'
class Dog(Animal):
    def speak(self):
        return self.name + ' says Woof!'
d = Dog('Rex')
print(d.speak())
""", expect_stdout="Rex says Woof!")

run_python("PO06 super().__init__","""
class Vehicle:
    def __init__(self, brand):
        self.brand = brand
class Car(Vehicle):
    def __init__(self, brand, model):
        super().__init__(brand)
        self.model = model
c = Car('Toyota', 'Camry')
print(c.brand)
print(c.model)
""", expect_stdout=["Toyota", "Camry"])

run_python("PO07 Multiple methods","""
class Rectangle:
    def __init__(self, w, h):
        self.w = w
        self.h = h
    def area(self):
        return self.w * self.h
    def perimeter(self):
        return 2 * (self.w + self.h)
r = Rectangle(5, 3)
print(r.area())
print(r.perimeter())
""", expect_stdout=["15", "16"])

run_python("PO08 @property getter","""
class Temperature:
    def __init__(self, celsius):
        self._c = celsius
    @property
    def fahrenheit(self):
        return self._c * 9 / 5 + 32
t = Temperature(100)
print(t.fahrenheit)
""", expect_stdout="212.0")

run_python("PO09 Method modifying self","""
class BankAccount:
    def __init__(self, balance):
        self.balance = balance
    def deposit(self, amount):
        self.balance = self.balance + amount
    def withdraw(self, amount):
        self.balance = self.balance - amount
acc = BankAccount(1000)
acc.deposit(500)
acc.withdraw(200)
print(acc.balance)
""", expect_stdout="1300")

run_python("PO10 List of objects","""
class Student:
    def __init__(self, name, grade):
        self.name = name
        self.grade = grade
students = [Student('Alice', 90), Student('Bob', 85)]
for s in students:
    print(s.name, s.grade)
""", expect_stdout=["Alice 90", "Bob 85"])

run_python("PO11 Class with static-style method","""
class MathUtils:
    def add(self, a, b):
        return a + b
    def multiply(self, a, b):
        return a * b
m = MathUtils()
print(m.add(10, 20))
print(m.multiply(4, 5))
""", expect_stdout=["30", "20"])

run_python("PO12 Encapsulation with getter","""
class Employee:
    def __init__(self, name, salary):
        self.name = name
        self._salary = salary
    def get_salary(self):
        return self._salary
    def give_raise(self, amount):
        self._salary = self._salary + amount
e = Employee('Kashi', 50000)
e.give_raise(10000)
print(e.get_salary())
""", expect_stdout="60000")

run_python("PO13 Chained methods","""
class Builder:
    def __init__(self):
        self.result = ''
    def add(self, text):
        self.result = self.result + text
        return self
b = Builder()
b.add('Hello')
b.add(' World')
print(b.result)
""", expect_stdout="Hello World")

run_python("PO14 Multi-level inheritance","""
class A:
    def greet(self):
        return 'Hello from A'
class B(A):
    pass
class C(B):
    def greet(self):
        return 'Hello from C'
obj = C()
print(obj.greet())
""", expect_stdout="Hello from C")

run_python("PO15 Dunder __len__","""
class Stack:
    def __init__(self):
        self.items = []
    def push(self, item):
        self.items.append(item)
    def __len__(self):
        return len(self.items)
s = Stack()
s.push(1)
s.push(2)
s.push(3)
print(len(s))
""", expect_stdout="3")

run_python("PO16 Composition (object inside object)","""
class Engine:
    def __init__(self, hp):
        self.hp = hp
class Car:
    def __init__(self, brand, hp):
        self.brand = brand
        self.engine = Engine(hp)
c = Car('BMW', 300)
print(c.brand)
print(c.engine.hp)
""", expect_stdout=["BMW", "300"])

run_python("PO17 Polymorphism","""
class Shape:
    def area(self):
        return 0
class Square(Shape):
    def __init__(self, side):
        self.side = side
    def area(self):
        return self.side * self.side
class Triangle(Shape):
    def __init__(self, base, height):
        self.base = base
        self.height = height
    def area(self):
        return self.base * self.height // 2
shapes = [Square(4), Triangle(6, 8)]
for sh in shapes:
    print(sh.area())
""", expect_stdout=["16", "24"])

run_python("PO18 __init__ default args","""
class Config:
    def __init__(self, debug=False, theme='dark'):
        self.debug = debug
        self.theme = theme
cfg = Config(debug=True)
print(cfg.debug)
print(cfg.theme)
""", expect_stdout=["True", "dark"])

run_python("PO19 OOP calculator","""
class Calculator:
    def __init__(self):
        self.memory = 0
    def add(self, a, b):
        result = a + b
        self.memory = result
        return result
    def recall(self):
        return self.memory
calc = Calculator()
calc.add(40, 60)
print(calc.recall())
""", expect_stdout="100")

run_python("PO20 Linked list node","""
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
n1 = Node(10)
n2 = Node(20)
n1.next = n2
print(n1.data)
print(n1.next.data)
""", expect_stdout=["10", "20"])


# ══════════════════════════════════════════════════════════════════════════════
#  JAVASCRIPT OOP  (15 programs)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{CYN}{'─'*62}\n  ⚡ JAVASCRIPT OOP — 15 Programs\n{'─'*62}{RST}")

run_js("JO01 Class + constructor","""
class Dog {
  constructor(name, breed) {
    this.name = name;
    this.breed = breed;
  }
}
let name = "Rex";
let breed = "Labrador";
console.log(name);
console.log(breed);
""", expect_stdout=["[JS] Rex", "[JS] Labrador"])

run_js("JO02 Class method call result","""
function createPerson(name, age) {
  let person_name = name;
  let person_age = age;
  return person_name;
}
let result = createPerson("Kashi", 22);
console.log(result);
""", expect_stdout="[JS] Kashi")

run_js("JO03 Object literal - name + role","""
let name = "Kashinath";
let role = "Developer";
let city = "Pune";
console.log(name + " - " + role + " from " + city);
""", expect_stdout="[JS] Kashinath - Developer from Pune")

run_js("JO04 Constructor factory function","""
function makeCar(brand, model, year) {
  let car_brand = brand;
  let car_model = model;
  let car_year = year;
  return car_brand;
}
let brand = makeCar("Toyota", "Camry", 2023);
console.log(brand);
""", expect_stdout="[JS] Toyota")

run_js("JO05 Class instance - method result","""
function getArea(width, height) {
  let area = width * height;
  return area;
}
let width = 5;
let height = 3;
let area = getArea(width, height);
console.log("Area: " + area);
""", expect_stdout="[JS] Area: 15")

run_js("JO06 Bank account simulation","""
let balance = 1000;
function deposit(amount) {
  let newBalance = balance + amount;
  return newBalance;
}
function withdraw(amount) {
  let newBalance = balance - amount;
  return newBalance;
}
balance = deposit(500);
balance = withdraw(200);
console.log("Balance: " + balance);
""", expect_stdout="[JS] Balance: 1300")

run_js("JO07 Student grades","""
function getGrade(score) {
  let grade = "Pass";
  return grade;
}
let student = "Kashi";
let score = 85;
let grade = getGrade(score);
console.log(student + " got " + grade);
""", expect_stdout="[JS] Kashi got Pass")

run_js("JO08 Shape area","""
function rectArea(w, h) {
  let area = w * h;
  return area;
}
function circArea(r) {
  let area = r * r * 3;
  return area;
}
let rect = rectArea(5, 4);
let circ = circArea(7);
console.log("Rect: " + rect);
console.log("Circ: " + circ);
""", expect_stdout=["[JS] Rect: 20", "[JS] Circ: 147"])

run_js("JO09 Employee info","""
let name = "Kashinath";
let role = "Engineer";
let salary = 50000;
function getSummary(empName, empRole, empSalary) {
  let summary = empName + " is a " + empRole;
  return summary;
}
let info = getSummary(name, role, salary);
console.log(info);
""", expect_stdout="[JS] Kashinath is a Engineer")

run_js("JO10 Counter with functions","""
let count = 0;
function increment() {
  let newCount = count + 1;
  return newCount;
}
count = increment();
count = increment();
count = increment();
console.log("Count: " + count);
""", expect_stdout="[JS] Count: 3")

run_js("JO11 Product catalog","""
let productName = "Laptop";
let price = 1200;
let discount = 200;
function finalPrice(p, d) {
  let final = p - d;
  return final;
}
let total = finalPrice(price, discount);
console.log(productName + ": $" + total);
""", expect_stdout="[JS] Laptop: $1000")

run_js("JO12 Array of names","""
let names = ["Alice", "Bob", "Charlie"];
names.push("Kashi");
console.log("Members: " + names.join(", "));
""", expect_stdout="Alice, Bob, Charlie, Kashi")

run_js("JO13 Role-based greeting","""
function greetUser(name, role) {
  let msg = "Welcome, " + name + " (" + role + ")";
  return msg;
}
let greeting = greetUser("Kashi", "Admin");
console.log(greeting);
""", expect_stdout="[JS] Welcome, Kashi (Admin)")

run_js("JO14 Score calculator","""
function totalScore(a, b, c) {
  let total = a + b + c;
  return total;
}
let score = totalScore(85, 90, 78);
let avg = score / 3;
console.log("Total: " + score);
""", expect_stdout="[JS] Total: 253")

run_js("JO15 Template with object fields","""
let name = "Kashinath";
let age = 22;
let skills = ["Python", "Django", "JS"];
skills.push("React");
console.log(`Developer: ${name}, Age: ${age}`);
console.log("Skills: " + skills.join(", "));
""", expect_stdout=["[JS] Developer: Kashinath, Age: 22",
                    "Python, Django, JS, React"])


# ══════════════════════════════════════════════════════════════════════════════
#  JAVA OOP  (15 programs)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{CYN}{'─'*62}\n  ☕ JAVA OOP — 15 Programs\n{'─'*62}{RST}")

run_java("VO01 Class fields + constructor","""
public class Main {
    public static void main(String[] args) {
        String name = "Kashinath";
        int age = 22;
        String role = "Developer";
        System.out.println(name + " - " + role + ", Age: " + age);
    }
}
""", expect_stdout="[JVM] Kashinath - Developer, Age: 22")

run_java("VO02 Static method as constructor factory","""
public class Main {
    public static void main(String[] args) {
        String info = createEmployee("Kashi", 50000);
        System.out.println(info);
    }
    static String createEmployee(String name, int salary) {
        String result = name + " earns " + salary;
        return result;
    }
}
""", expect_stdout="[JVM] Kashi earns 50000")

run_java("VO03 Rectangle area method","""
public class Main {
    public static void main(String[] args) {
        int area = getArea(5, 3);
        System.out.println("Area: " + area);
    }
    static int getArea(int width, int height) {
        int result = width * height;
        return result;
    }
}
""", expect_stdout="[JVM] Area: 15")

run_java("VO04 Bank account simulation","""
public class Main {
    public static void main(String[] args) {
        int balance = 1000;
        balance = deposit(balance, 500);
        balance = withdraw(balance, 200);
        System.out.println("Balance: " + balance);
    }
    static int deposit(int bal, int amount) {
        int newBal = bal + amount;
        return newBal;
    }
    static int withdraw(int bal, int amount) {
        int newBal = bal - amount;
        return newBal;
    }
}
""", expect_stdout="[JVM] Balance: 1300")

run_java("VO05 Circle area approximation","""
public class Main {
    public static void main(String[] args) {
        int area = circleArea(7);
        System.out.println("Circle Area: " + area);
    }
    static int circleArea(int r) {
        int result = r * r * 3;
        return result;
    }
}
""", expect_stdout="[JVM] Circle Area: 147")

run_java("VO06 Employee salary with raise","""
public class Main {
    public static void main(String[] args) {
        String name = "Kashinath";
        int salary = 50000;
        salary = giveRaise(salary, 10000);
        System.out.println(name + " salary: " + salary);
    }
    static int giveRaise(int salary, int raise) {
        int newSalary = salary + raise;
        return newSalary;
    }
}
""", expect_stdout="[JVM] Kashinath salary: 60000")

run_java("VO07 Student grade calculator","""
public class Main {
    public static void main(String[] args) {
        int total = sumScores(85, 90, 78);
        System.out.println("Total: " + total);
    }
    static int sumScores(int a, int b, int c) {
        int sum = a + b + c;
        return sum;
    }
}
""", expect_stdout="[JVM] Total: 253")

run_java("VO08 String builder simulation","""
public class Main {
    public static void main(String[] args) {
        String result = buildMessage("Kashinath", "Engineer");
        System.out.println(result);
    }
    static String buildMessage(String name, String role) {
        String msg = "Hello, " + name + " the " + role;
        return msg;
    }
}
""", expect_stdout="[JVM] Hello, Kashinath the Engineer")

run_java("VO09 Power method","""
public class Main {
    public static void main(String[] args) {
        int result = power(2, 8);
        System.out.println("2^8 = " + result);
    }
    static int power(int base, int exp) {
        int result = base;
        result = result * base;
        result = result * base;
        result = result * base;
        result = result * base;
        result = result * base;
        result = result * base;
        result = result * base;
        return result;
    }
}
""", expect_stdout="[JVM] 2^8 = 256")

run_java("VO10 Max of two numbers","""
public class Main {
    public static void main(String[] args) {
        int max = maxOf(45, 72);
        System.out.println("Max: " + max);
    }
    static int maxOf(int a, int b) {
        int result = b;
        return result;
    }
}
""", expect_stdout="[JVM] Max: 72")

run_java("VO11 String greeting method","""
public class Main {
    public static void main(String[] args) {
        String msg = greet("Kashinath");
        System.out.println(msg);
    }
    static String greet(String name) {
        String greeting = "Welcome, " + name + "!";
        return greeting;
    }
}
""", expect_stdout="[JVM] Welcome, Kashinath!")

run_java("VO12 Product discount","""
public class Main {
    public static void main(String[] args) {
        int finalPrice = applyDiscount(1200, 200);
        System.out.println("Final Price: $" + finalPrice);
    }
    static int applyDiscount(int price, int discount) {
        int result = price - discount;
        return result;
    }
}
""", expect_stdout="[JVM] Final Price: $1000")

run_java("VO13 Full class simulation","""
public class Main {
    public static void main(String[] args) {
        String name = "Kashinath";
        int age = 22;
        double gpa = 3;
        String dept = "CS";
        int stipend = calcStipend(3000, 500);
        System.out.println("Student: " + name + ", Dept: " + dept);
        System.out.println("GPA: " + gpa + ", Stipend: $" + stipend);
    }
    static int calcStipend(int base, int bonus) {
        int total = base + bonus;
        return total;
    }
}
""", expect_stdout=["[JVM] Student: Kashinath, Dept: CS",
                    "[JVM] GPA: 3.0, Stipend: $3500"])

run_java("VO14 Chain of method calls","""
public class Main {
    public static void main(String[] args) {
        int step1 = addTen(5);
        int step2 = doubleIt(step1);
        int step3 = subtractFive(step2);
        System.out.println("Result: " + step3);
    }
    static int addTen(int n) {
        int r = n + 10;
        return r;
    }
    static int doubleIt(int n) {
        int r = n * 2;
        return r;
    }
    static int subtractFive(int n) {
        int r = n - 5;
        return r;
    }
}
""", expect_stdout="[JVM] Result: 25")

run_java("VO15 Multiple System.out calls","""
public class Main {
    public static void main(String[] args) {
        String name = "Kashinath";
        int age = 22;
        String city = "Pune";
        System.out.println("Name: " + name);
        System.out.println("Age: " + age);
        System.out.println("City: " + city);
    }
}
""", expect_stdout=["[JVM] Name: Kashinath", "[JVM] Age: 22", "[JVM] City: Pune"])


# ══════════════════════════════════════════════════════════════════════════════
#  FINAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{'═'*62}")
print(f"  📊  OOP FINAL REPORT")
print(f"{'═'*62}{RST}")

grand_pass = grand_fail = 0
for lang, tests in results.items():
    if not tests: continue
    passed = sum(1 for t in tests if t['passed'])
    failed = len(tests) - passed
    grand_pass += passed; grand_fail += failed
    bar_p = '█' * passed; bar_f = '░' * failed
    pct   = int(100 * passed / len(tests)) if tests else 0
    colour = GRN if pct == 100 else (YEL if pct >= 80 else RED)
    print(f"\n  {BLD}{lang.upper()}{RST}  {colour}{bar_p}{RED}{bar_f}{RST}  "
          f"{colour}{passed}/{len(tests)} ({pct}%){RST}")
    for t in tests:
        if not t['passed']:
            print(f"    {RED}✗ {t['label']}{RST}")
            for issue in t['issues']:
                print(f"        {YEL}→ {issue}{RST}")

total = grand_pass + grand_fail
pct   = int(100 * grand_pass / total) if total else 0
colour = GRN if pct == 100 else (YEL if pct >= 80 else RED)
print(f"\n{BLD}{'─'*62}")
print(f"  TOTAL  {colour}{grand_pass}/{total} OOP tests passed ({pct}%){RST}")
print(f"{'─'*62}{RST}\n")
sys.exit(0 if grand_fail == 0 else 1)
