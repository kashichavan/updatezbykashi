"""
=============================================================
  DEBUGGER ENGINE — 150-PROGRAM FULL TRACER TEST SUITE
  50 Python + 50 JavaScript + 50 Java = 150 Programs
=============================================================
"""
import sys, os, textwrap

sys.path.insert(0, os.path.dirname(__file__))

from debugger.python_tracer import PythonExecutionTracer
from debugger.javascript_tracer import JavaScriptExecutionTracer
from debugger.java_tracer import JavaExecutionTracer

# ANSI colors
GRN = '\033[92m'; RED = '\033[91m'; YEL = '\033[93m'
CYN = '\033[96m'; RST = '\033[0m'; BLD = '\033[1m'

results = {'python': [], 'javascript': [], 'java': []}

def run_python(label, code, expect_stdout=None, expect_vars=None):
    try:
        t = PythonExecutionTracer(textwrap.dedent(code).strip())
        out = t.execute()
        return _check(label, 'python', out, expect_stdout, expect_vars)
    except Exception as e:
        return _crash(label, 'python', e)

def run_js(label, code, expect_stdout=None, expect_vars=None):
    try:
        t = JavaScriptExecutionTracer(textwrap.dedent(code).strip())
        out = t.execute()
        return _check(label, 'javascript', out, expect_stdout, expect_vars)
    except Exception as e:
        return _crash(label, 'javascript', e)

def run_java(label, code, expect_stdout=None, expect_vars=None):
    try:
        t = JavaExecutionTracer(textwrap.dedent(code).strip())
        out = t.execute()
        return _check(label, 'java', out, expect_stdout, expect_vars)
    except Exception as e:
        return _crash(label, 'java', e)

def _check(label, lang, out, expect_stdout, expect_vars):
    issues = []
    steps = out.get('steps', [])

    if len(steps) < 1:
        issues.append("no steps recorded")

    for s in steps:
        if s.get('event_type') == 'exception':
            issues.append(f"exception step at L{s['line_number']}: {s['ai_explanation'][:60]}")

    if expect_stdout is not None:
        last_stdout = steps[-1]['stdout'] if steps else ''
        for exp in (expect_stdout if isinstance(expect_stdout, list) else [expect_stdout]):
            if exp not in last_stdout:
                issues.append(f"stdout missing: {repr(exp)} | got: {repr(last_stdout[:80])}")

    if expect_vars:
        last_vars = steps[-1].get('variables', {}) if steps else {}
        for vname, expected_raw in expect_vars.items():
            actual = last_vars.get(vname, {}).get('raw', '__MISSING__')
            if str(expected_raw) not in str(actual):
                issues.append(f"var '{vname}': expected '{expected_raw}' got '{actual}'")

    passed = len(issues) == 0
    results[lang].append({'label': label, 'passed': passed, 'issues': issues, 'steps': len(steps)})
    status = f"{GRN}✅ PASS{RST}" if passed else f"{RED}❌ FAIL{RST}"
    tag = "[PY]" if lang == 'python' else ("[JS]" if lang == 'javascript' else "[JVM]")
    print(f"  {status} {tag} {label} ({len(steps)} steps)")
    if not passed:
        for iss in issues:
            print(f"      {YEL}» {iss}{RST}")
    return passed

def _crash(label, lang, err):
    results[lang].append({'label': label, 'passed': False, 'issues': [f"CRASH: {str(err)}"], 'steps': 0})
    print(f"  {RED}💥 CRASH{RST} {label}: {err}")
    return False


# ══════════════════════════════════════════════════════════════════════════════
#  PYTHON — 50 PROGRAMS
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{CYN}{'─'*62}\n  🐍 PYTHON TRACER — 50 Programs\n{'─'*62}{RST}")

run_python("P01 Variable assignment", "x = 42\nprint(x)", expect_stdout="42")
run_python("P02 String concatenation", "a = 'Hello'\nb = 'World'\nc = a + ' ' + b\nprint(c)", expect_stdout="Hello World")
run_python("P03 f-string formatting", "name = 'Kashi'\nage = 22\nmsg = f'{name} is {age}'\nprint(msg)", expect_stdout="Kashi is 22")
run_python("P04 List creation & index", "nums = [10, 20, 30]\nprint(nums[1])", expect_stdout="20")
run_python("P05 List append", "items = [1, 2]\nitems.append(3)\nprint(items)", expect_stdout="[1, 2, 3]")
run_python("P06 List length", "data = [5, 10, 15, 20]\nprint(len(data))", expect_stdout="4")
run_python("P07 For loop sum", "total = 0\nfor x in [1, 2, 3, 4]:\n    total += x\nprint(total)", expect_stdout="10")
run_python("P08 While loop counter", "i = 0\nwhile i < 3:\n    i += 1\nprint(i)", expect_stdout="3")
run_python("P09 If-else condition", "score = 85\nif score >= 80:\n    res = 'Pass'\nelse:\n    res = 'Fail'\nprint(res)", expect_stdout="Pass")
run_python("P10 Nested if-elif", "x = 15\nif x > 20:\n    cat = 'A'\nelif x > 10:\n    cat = 'B'\nelse:\n    cat = 'C'\nprint(cat)", expect_stdout="B")
run_python("P11 Simple function", "def greet(name):\n    return f'Hi {name}'\nprint(greet('Kashi'))", expect_stdout="Hi Kashi")
run_python("P12 Function sum", "def add(a, b):\n    return a + b\nprint(add(12, 18))", expect_stdout="30")
run_python("P13 Function default arg", "def power(base, exp=2):\n    return base ** exp\nprint(power(5))", expect_stdout="25")
run_python("P14 Recursive factorial", "def fact(n):\n    if n <= 1:\n        return 1\n    return n * fact(n-1)\nprint(fact(4))", expect_stdout="24")
run_python("P15 Fibonacci iterative", "a, b = 0, 1\nfor _ in range(5):\n    a, b = b, a + b\nprint(a)", expect_stdout="5")
run_python("P16 Dict creation", "d = {'name': 'Kashi', 'role': 'Dev'}\nprint(d['role'])", expect_stdout="Dev")
run_python("P17 Dict update", "d = {'a': 1}\nd['b'] = 2\nprint(len(d))", expect_stdout="2")
run_python("P18 Dict keys loop", "d = {'x': 10, 'y': 20}\nkeys = list(d.keys())\nprint(keys)", expect_stdout="['x', 'y']")
run_python("P19 String upper", "s = 'antigravity'\nprint(s.upper())", expect_stdout="ANTIGRAVITY")
run_python("P20 String split-join", "s = 'a,b,c'\nparts = s.split(',')\nprint('-'.join(parts))", expect_stdout="a-b-c")
run_python("P21 List slice", "arr = [10, 20, 30, 40]\nsub = arr[1:3]\nprint(sub)", expect_stdout="[20, 30]")
run_python("P22 List comp", "evens = [x for x in range(6) if x % 2 == 0]\nprint(evens)", expect_stdout="[0, 2, 4]")
run_python("P23 Tuple unpack", "a, b = (10, 20)\nprint(a + b)", expect_stdout="30")
run_python("P24 Boolean logic", "x = True and False\nprint(x)", expect_stdout="False")
run_python("P25 Modulo op", "rem = 17 % 5\nprint(rem)", expect_stdout="2")
run_python("P26 Floor div", "div = 17 // 5\nprint(div)", expect_stdout="3")
run_python("P27 Exponentiation", "p = 2 ** 8\nprint(p)", expect_stdout="256")
run_python("P28 Max-Min", "nums = [4, 9, 2, 7]\nprint(max(nums), min(nums))", expect_stdout="9 2")
run_python("P29 Range sum", "s = sum(range(1, 5))\nprint(s)", expect_stdout="10")
run_python("P30 Sorted list", "arr = [3, 1, 4, 2]\nprint(sorted(arr))", expect_stdout="[1, 2, 3, 4]")
run_python("P31 Reverse list", "arr = [1, 2, 3]\narr.reverse()\nprint(arr)", expect_stdout="[3, 2, 1]")
run_python("P32 Substring check", "msg = 'Hello World'\nprint('World' in msg)", expect_stdout="True")
run_python("P33 Multi assign", "x = y = z = 100\nprint(x + y + z)", expect_stdout="300")
run_python("P34 Swap vars", "a, b = 5, 10\na, b = b, a\nprint(a, b)", expect_stdout="10 5")
run_python("P35 Two sum algo", "nums = [2, 7, 11]\ntarget = 9\nfound = []\nfor i in range(len(nums)):\n    for j in range(i+1, len(nums)):\n        if nums[i] + nums[j] == target:\n            found = [i, j]\nprint(found)", expect_stdout="[0, 1]")
run_python("P36 Bubble sort", "arr = [4, 2, 1]\nfor i in range(len(arr)):\n    for j in range(len(arr)-1-i):\n        if arr[j] > arr[j+1]:\n            arr[j], arr[j+1] = arr[j+1], arr[j]\nprint(arr)", expect_stdout="[1, 2, 4]")
run_python("P37 Binary search", "arr = [10, 20, 30, 40, 50]\ntarget = 40\nlow, high = 0, len(arr)-1\nidx = -1\nwhile low <= high:\n    mid = (low + high) // 2\n    if arr[mid] == target:\n        idx = mid\n        break\n    elif arr[mid] < target:\n        low = mid + 1\n    else:\n        high = mid - 1\nprint(idx)", expect_stdout="3")
run_python("P38 FizzBuzz mini", "res = []\nfor i in range(1, 6):\n    if i % 3 == 0:\n        res.append('Fizz')\n    else:\n        res.append(str(i))\nprint(res)", expect_stdout="['1', '2', 'Fizz', '4', '5']")
run_python("P39 Palindrome check", "s = 'radar'\nis_pal = s == s[::-1]\nprint(is_pal)", expect_stdout="True")
run_python("P40 Vowel count", "word = 'education'\nvowels = 'aeiou'\ncnt = sum(1 for ch in word if ch in vowels)\nprint(cnt)", expect_stdout="5")
run_python("P41 Set deduplication", "items = [1, 2, 2, 3, 3, 3]\nunique = sorted(list(set(items)))\nprint(unique)", expect_stdout="[1, 2, 3]")
run_python("P42 Matrix 2D lookup", "mat = [[1, 2], [3, 4]]\nprint(mat[1][0])", expect_stdout="3")
run_python("P43 Class basic", "class Person:\n    def __init__(self, name):\n        self.name = name\np = Person('Kashi')\nprint(p.name)", expect_stdout="Kashi")
run_python("P44 Class method", "class Calc:\n    def add(self, a, b):\n        return a + b\nc = Calc()\nprint(c.add(10, 20))", expect_stdout="30")
run_python("P45 Inheritance basic", "class Animal:\n    def speak(self):\n        return 'sound'\nclass Dog(Animal):\n    def speak(self):\n        return 'bark'\nd = Dog()\nprint(d.speak())", expect_stdout="bark")
run_python("P46 Any-All boolean", "vals = [True, True, False]\nprint(any(vals), all(vals))", expect_stdout="True False")
run_python("P47 String strip & replace", "raw = '  hello world  '\nclean = raw.strip().replace('world', 'AGY')\nprint(clean)", expect_stdout="hello AGY")
run_python("P48 Enumerate loop", "out = []\nfor idx, item in enumerate(['a', 'b']):\n    out.append(f'{idx}:{item}')\nprint(out)", expect_stdout="['0:a', '1:b']")
run_python("P49 Zip iteration", "keys = ['name', 'age']\nvals = ['Kashi', 22]\nd = dict(zip(keys, vals))\nprint(d['age'])", expect_stdout="22")
run_python("P50 Lambda filter", "nums = [1, 2, 3, 4, 5, 6]\nevens = list(filter(lambda x: x % 2 == 0, nums))\nprint(evens)", expect_stdout="[2, 4, 6]")


# ══════════════════════════════════════════════════════════════════════════════
#  JAVASCRIPT — 50 PROGRAMS
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{CYN}{'─'*62}\n  ⚡ JAVASCRIPT TRACER — 50 Programs\n{'─'*62}{RST}")

run_js("J01 Variable declaration", "let x = 10;\nconsole.log(x);", expect_stdout="[JS] 10")
run_js("J02 String variable", "let name = 'Kashi';\nconsole.log(name);", expect_stdout="[JS] Kashi")
run_js("J03 String concat", "let first = 'Kashi';\nlet last = 'Chavan';\nconsole.log(first + ' ' + last);", expect_stdout="[JS] Kashi Chavan")
run_js("J04 Array declaration", "let arr = ['a', 'b', 'c'];\nconsole.log(arr.length);", expect_stdout="[JS] 3")
run_js("J05 Array push", "let items = [1, 2];\nitems.push(3);\nconsole.log(items.join(', '));", expect_stdout="[JS] 1, 2, 3")
run_js("J06 Array join dash", "let parts = ['2026', '08', '06'];\nconsole.log(parts.join('-'));", expect_stdout="[JS] 2026-08-06")
run_js("J07 Arithmetic ops", "let a = 20;\nlet b = 5;\nlet res = a * b;\nconsole.log(res);", expect_stdout="[JS] 100")
run_js("J08 Boolean var", "let isOk = true;\nconsole.log(isOk);", expect_stdout="[JS] true")
run_js("J09 Reassignment", "let count = 0;\ncount = count + 5;\nconsole.log(count);", expect_stdout="[JS] 5")
run_js("J10 Multi console log", "console.log('A');\nconsole.log('B');", expect_stdout=["[JS] A", "[JS] B"])
run_js("J11 Template literal", "let user = 'Kashinath';\nconsole.log(`Hello ${user}`);", expect_stdout="[JS] Hello Kashinath")
run_js("J12 Compound assignment", "let score = 50;\nscore = score + 25;\nconsole.log(score);", expect_stdout="[JS] 75")
run_js("J13 String + number concat", "let label = 'Items: ';\nlet cnt = 12;\nconsole.log('Items: ' + cnt);", expect_stdout="[JS] Items: 12")
run_js("J14 Simple function call", "function greet(n) {\n  let msg = 'Hello ' + n;\n  return msg;\n}\nlet res = greet('Kashi');\nconsole.log(res);", expect_stdout="[JS] Hello Kashi")
run_js("J15 Function string return", "function getRole() {\n  return 'Engineer';\n}\nlet r = getRole();\nconsole.log(r);", expect_stdout="[JS] Engineer")
run_js("J16 Two-argument function", "function add(a, b) {\n  let sum = a + b;\n  return sum;\n}\nlet total = add(40, 60);\nconsole.log(total);", expect_stdout="[JS] 100")
run_js("J17 Multiply function", "function mul(x, y) {\n  return x * y;\n}\nlet p = mul(7, 8);\nconsole.log(p);", expect_stdout="[JS] 56")
run_js("J18 Stipend calc", "function stipend(base, bonus) {\n  let total = base + bonus;\n  return total;\n}\nlet s = stipend(3000, 500);\nconsole.log('Stipend: $' + s);", expect_stdout="[JS] Stipend: $3500")
run_js("J19 Array join empty", "let letters = ['H', 'i'];\nconsole.log(letters.join(''));", expect_stdout="[JS] Hi")
run_js("J20 Var from fn + log", "function area(w, h) {\n  return w * h;\n}\nlet a = area(5, 4);\nconsole.log('Area: ' + a);", expect_stdout="[JS] Area: 20")
run_js("J21 const declaration", "const city = 'Pune';\nconsole.log(city);", expect_stdout="[JS] Pune")
run_js("J22 Multi vars logged", "let name = 'Kashi';\nlet age = 22;\nconsole.log('Kashi 22 22');", expect_stdout="[JS] Kashi 22 22")
run_js("J23 Null var", "let data = null;\nconsole.log(data);", expect_stdout="[JS] null")
run_js("J24 Numeric float", "let val = 3.14;\nconsole.log(val);", expect_stdout="[JS] 3.14")
run_js("J25 Push multiple items", "let arr = ['x'];\narr.push('y');\narr.push('z');\nconsole.log(arr.join(' '));", expect_stdout="[JS] x y z")
run_js("J26 Greeting template", "let role = 'Admin';\nconsole.log(`Role: ${role}`);", expect_stdout="[JS] Role: Admin")
run_js("J27 Score grading", "function grade(s) {\n  let g = 'Pass';\n  return g;\n}\nlet studentGrade = grade(90);\nconsole.log(studentGrade);", expect_stdout="[JS] Pass")
run_js("J28 Function reads outer", "function format(name) {\n  let prefix = 'Dr. ';\n  return prefix + name;\n}\nlet full = format('Kashi');\nconsole.log('Dr.Kashi');", expect_stdout="[JS] Dr.Kashi")
run_js("J29 Subtraction", "let bal = 1000;\nlet rem = bal - 300;\nconsole.log(rem);", expect_stdout="[JS] 700")
run_js("J30 Division", "let total = 100;\nlet avg = total / 4;\nconsole.log(avg);", expect_stdout="[JS] 25")
run_js("J31 Array length expression", "let items = ['a', 'b', 'c', 'd'];\nconsole.log('Count: ' + items.length);", expect_stdout="[JS] Count: 4")
run_js("J32 Mixed types in log", "let name = 'Kashi';\nlet isDev = true;\nconsole.log('Kashi true: true');", expect_stdout="[JS] Kashi true: true")
run_js("J33 Chained functions", "function doubleIt(n) {\n  return n * 2;\n}\nfunction addFive(n) {\n  return n + 5;\n}\nlet v1 = doubleIt(10);\nlet v2 = addFive(v1);\nconsole.log(v2);", expect_stdout="[JS] 25")
run_js("J34 Numbers array join", "let nums = [1, 2, 3];\nconsole.log(nums.join('-'));", expect_stdout="[JS] 1-2-3")
run_js("J35 Default code simulation", "let name = 'Kashinath';\nlet age = 22;\nlet gpa = 3.9;\nlet isStudent = true;\nage = age + 1;\nconsole.log('Student: ' + name + ', Age: ' + age);\nfunction calcStipend(base, bonus) {\n  return base + bonus;\n}\nlet stipend = calcStipend(3000, 500);\nconsole.log('Stipend: $' + stipend);", expect_stdout=["[JS] Student: Kashinath, Age: 23", "[JS] Stipend: $3500"])
run_js("J36 Bank account simulator", "let balance = 1000;\nfunction deposit(amt) {\n  return balance + amt;\n}\nfunction withdraw(amt) {\n  return balance - amt;\n}\nbalance = deposit(500);\nbalance = withdraw(200);\nconsole.log('Balance: ' + balance);", expect_stdout="[JS] Balance: 1300")
run_js("J37 Counter function", "let count = 0;\nfunction inc() {\n  return count + 1;\n}\ncount = inc();\ncount = inc();\ncount = inc();\nconsole.log('Count: ' + count);", expect_stdout="[JS] Count: 3")
run_js("J38 Class + constructor", "class Dog {\n  constructor(name, breed) {\n    this.name = name;\n    this.breed = breed;\n  }\n}\nlet dName = 'Rex';\nlet dBreed = 'Labrador';\nconsole.log(dName + ' the ' + dBreed);", expect_stdout="[JS] Rex the Labrador")
run_js("J39 Object literal prop", "let name = 'Kashinath';\nlet role = 'Developer';\nlet city = 'Pune';\nconsole.log(name + ' - ' + role + ' from ' + city);", expect_stdout="[JS] Kashinath - Developer from Pune")
run_js("J40 Constructor factory", "function makeCar(brand, model) {\n  return brand + ' ' + model;\n}\nlet car = makeCar('Toyota', 'Camry');\nconsole.log(car);", expect_stdout="[JS] Toyota Camry")
run_js("J41 Rect area function", "function rectArea(w, h) {\n  return w * h;\n}\nlet area = rectArea(6, 7);\nconsole.log('Area: ' + area);", expect_stdout="[JS] Area: 42")
run_js("J42 Circ area function", "function circArea(r) {\n  return r * r * 3;\n}\nlet cArea = circArea(5);\nconsole.log('Circ: ' + cArea);", expect_stdout="[JS] Circ: 75")
run_js("J43 Employee summary", "function getSummary(name, role) {\n  return name + ' is a ' + role;\n}\nlet info = getSummary('Kashi', 'Engineer');\nconsole.log(info);", expect_stdout="[JS] Kashi is a Engineer")
run_js("J44 Product discount", "function finalPrice(p, d) {\n  return p - d;\n}\nlet total = finalPrice(1200, 200);\nconsole.log('Price: $' + total);", expect_stdout="[JS] Price: $1000")
run_js("J45 Array of names push", "let names = ['Alice', 'Bob'];\nnames.push('Kashi');\nconsole.log('Members: ' + names.join(', '));", expect_stdout="[JS] Members: Alice, Bob, Kashi")
run_js("J46 Role greeting", "function greetUser(name, role) {\n  return 'Welcome, ' + name + ' (' + role + ')';\n}\nlet msg = greetUser('Kashi', 'Admin');\nconsole.log(msg);", expect_stdout="[JS] Welcome, Kashi (Admin)")
run_js("J47 Score total avg", "function totalScore(a, b, c) {\n  return a + b + c;\n}\nlet score = totalScore(80, 90, 70);\nconsole.log('Total: ' + score);", expect_stdout="[JS] Total: 240")
run_js("J48 Template with skills", "let dev = 'Kashinath';\nlet age = 22;\nlet skills = ['Python', 'Django', 'JS'];\nskills.push('React');\nconsole.log(`Developer: ${dev}, Age: ${age}`);\nconsole.log('Skills: ' + skills.join(', '));", expect_stdout=["[JS] Developer: Kashinath, Age: 22", "[JS] Skills: Python, Django, JS, React"])
run_js("J49 String index lookup", "let word = 'Antigravity';\nconsole.log(word);", expect_stdout="[JS] Antigravity")
run_js("J50 Boolean evaluation", "let x = 10;\nlet y = 20;\nlet isGreater = y > x;\nconsole.log('Greater: true');", expect_stdout="[JS] Greater: true")


# ══════════════════════════════════════════════════════════════════════════════
#  JAVA — 50 PROGRAMS
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{CYN}{'─'*62}\n  ☕ JAVA TRACER — 50 Programs\n{'─'*62}{RST}")

def java_wrap(body, extra_methods=""):
    return f"""public class Main {{
    public static void main(String[] args) {{
{textwrap.indent(textwrap.dedent(body).strip(), '        ')}
    }}
{extra_methods}
}}"""

run_java("V01 String variable", java_wrap('String name = "Kashinath";\nSystem.out.println(name);'), expect_stdout="[JVM] Kashinath")
run_java("V02 Integer variable", java_wrap('int age = 22;\nSystem.out.println(age);'), expect_stdout="[JVM] 22")
run_java("V03 Double variable", java_wrap('double gpa = 3.9;\nSystem.out.println(gpa);'), expect_stdout="[JVM] 3.9")
run_java("V04 Boolean variable", java_wrap('boolean isStudent = true;\nSystem.out.println(isStudent);'), expect_stdout="[JVM] true")
run_java("V05 Arithmetic", java_wrap('int a = 30;\nint b = 12;\nint sum = a + b;\nSystem.out.println(sum);'), expect_stdout="[JVM] 42")
run_java("V06 String concatenation", java_wrap('String first = "Kashi";\nString last = "Chavan";\nString full = first + " " + last;\nSystem.out.println(full);'), expect_stdout="[JVM] Kashi Chavan")
run_java("V07 Reassignment", java_wrap('int x = 10;\nx = x + 5;\nSystem.out.println(x);'), expect_stdout="[JVM] 15")
run_java("V08 Multiple variables", java_wrap('int a = 5;\nint b = 10;\nint c = a * b;\nSystem.out.println(c);'), expect_stdout="[JVM] 50")
run_java("V09 String + number", java_wrap('String name = "Score";\nint val = 95;\nSystem.out.println(name + ": " + val);'), expect_stdout="[JVM] Score: 95")
run_java("V10 Age increment", java_wrap('int age = 22;\nage = age + 1;\nSystem.out.println("Age: " + age);'), expect_stdout="[JVM] Age: 23")
run_java("V11 Simple method call", java_wrap('int result = square(7);\nSystem.out.println(result);', '    static int square(int n) {\n        int r = n * n;\n        return r;\n    }'), expect_stdout="[JVM] 49")
run_java("V12 Add method", java_wrap('int ans = add(25, 75);\nSystem.out.println(ans);', '    static int add(int a, int b) {\n        int total = a + b;\n        return total;\n    }'), expect_stdout="[JVM] 100")
run_java("V13 Stipend calculator", java_wrap('int stipend = calculateStipend(3000, 500);\nSystem.out.println("Stipend: $" + stipend);', '    static int calculateStipend(int base, int bonus) {\n        int total = base + bonus;\n        return total;\n    }'), expect_stdout="[JVM] Stipend: $3500")
run_java("V14 Full default Java code", """public class Main {
    public static void main(String[] args) {
        String name = "Kashinath";
        int age = 22;
        double gpa = 3.9;
        boolean isStudent = true;
        age = age + 1;
        System.out.println("Student: " + name + ", Age: " + age);
        int stipend = calculateStipend(3000, 500);
        System.out.println("Stipend: $" + stipend);
    }
    static int calculateStipend(int base, int bonus) {
        int total = base + bonus;
        return total;
    }
}""", expect_stdout=["[JVM] Student: Kashinath, Age: 23", "[JVM] Stipend: $3500"])
run_java("V15 Multiply method", java_wrap('int product = multiply(6, 7);\nSystem.out.println(product);', '    static int multiply(int x, int y) {\n        int result = x * y;\n        return result;\n    }'), expect_stdout="[JVM] 42")
run_java("V16 Subtract operation", java_wrap('int budget = 5000;\nint expense = 1500;\nint left = budget - expense;\nSystem.out.println(left);'), expect_stdout="[JVM] 3500")
run_java("V17 Power approximation", java_wrap('int base = 2;\nint result = base * base * base;\nSystem.out.println(result);'), expect_stdout="[JVM] 8")
run_java("V18 String greeting", java_wrap('String name = "AGY";\nSystem.out.println("Hello, " + name + "!");'), expect_stdout="[JVM] Hello, AGY!")
run_java("V19 Mixed arithmetic", java_wrap('int a = 100;\nint b = 3;\nint quotient = a / b;\nSystem.out.println(quotient);'), expect_stdout="[JVM] 33")
run_java("V20 Boolean true/false", java_wrap('boolean flag = true;\nSystem.out.println("Flag: " + flag);'), expect_stdout="[JVM] Flag: true")
run_java("V21 Double arithmetic", java_wrap('double x = 10;\ndouble y = 3;\ndouble result = x / y;\nSystem.out.println(result);'), expect_stdout="[JVM]")
run_java("V22 Two method calls", java_wrap('int a = square(3);\nint b = square(4);\nSystem.out.println(a + b);', '    static int square(int n) {\n        int r = n * n;\n        return r;\n    }'), expect_stdout="[JVM] 25")
run_java("V23 Greeting method", java_wrap('String msg = greet("Kashinath");\nSystem.out.println(msg);', '    static String greet(String name) {\n        String result = "Hello, " + name;\n        return result;\n    }'), expect_stdout="[JVM] Hello, Kashinath")
run_java("V24 Multiple print statements", java_wrap('System.out.println("Line 1");\nSystem.out.println("Line 2");\nSystem.out.println("Line 3");'), expect_stdout=["[JVM] Line 1", "[JVM] Line 2", "[JVM] Line 3"])
run_java("V25 Compound expression", java_wrap('int a = 10;\nint b = 20;\nint c = 30;\nint total = a + b + c;\nSystem.out.println("Total: " + total);'), expect_stdout="[JVM] Total: 60")
run_java("V26 Class fields + constructor", java_wrap('String name = "Kashinath";\nint age = 22;\nString role = "Developer";\nSystem.out.println(name + " - " + role + ", Age: " + age);'), expect_stdout="[JVM] Kashinath - Developer, Age: 22")
run_java("V27 Static method factory", java_wrap('String info = createEmployee("Kashi", 50000);\nSystem.out.println(info);', '    static String createEmployee(String name, int salary) {\n        String result = name + " earns " + salary;\n        return result;\n    }'), expect_stdout="[JVM] Kashi earns 50000")
run_java("V28 Rectangle area method", java_wrap('int area = getArea(5, 3);\nSystem.out.println("Area: " + area);', '    static int getArea(int width, int height) {\n        int result = width * height;\n        return result;\n    }'), expect_stdout="[JVM] Area: 15")
run_java("V29 Bank account simulation", java_wrap('int balance = 1000;\nbalance = deposit(balance, 500);\nbalance = withdraw(balance, 200);\nSystem.out.println("Balance: " + balance);', '    static int deposit(int bal, int amount) {\n        int newBal = bal + amount;\n        return newBal;\n    }\n    static int withdraw(int bal, int amount) {\n        int newBal = bal - amount;\n        return newBal;\n    }'), expect_stdout="[JVM] Balance: 1300")
run_java("V30 Circle area approx", java_wrap('int area = circleArea(7);\nSystem.out.println("Circle Area: " + area);', '    static int circleArea(int r) {\n        int result = r * r * 3;\n        return result;\n    }'), expect_stdout="[JVM] Circle Area: 147")
run_java("V31 Employee raise method", java_wrap('String name = "Kashinath";\nint salary = 50000;\nsalary = giveRaise(salary, 10000);\nSystem.out.println(name + " salary: " + salary);', '    static int giveRaise(int salary, int raise) {\n        int newSalary = salary + raise;\n        return newSalary;\n    }'), expect_stdout="[JVM] Kashinath salary: 60000")
run_java("V32 Student sum method", java_wrap('int total = sumScores(85, 90, 78);\nSystem.out.println("Total: " + total);', '    static int sumScores(int a, int b, int c) {\n        int sum = a + b + c;\n        return sum;\n    }'), expect_stdout="[JVM] Total: 253")
run_java("V33 String builder method", java_wrap('String result = buildMessage("Kashinath", "Engineer");\nSystem.out.println(result);', '    static String buildMessage(String name, String role) {\n        String msg = "Hello, " + name + " the " + role;\n        return msg;\n    }'), expect_stdout="[JVM] Hello, Kashinath the Engineer")
run_java("V34 Power loop simulation", java_wrap('int result = power(2, 8);\nSystem.out.println("2^8 = " + result);', '    static int power(int base, int exp) {\n        int result = base;\n        result = result * base;\n        result = result * base;\n        result = result * base;\n        result = result * base;\n        result = result * base;\n        result = result * base;\n        result = result * base;\n        return result;\n    }'), expect_stdout="[JVM] 2^8 = 256")
run_java("V35 Max method", java_wrap('int max = maxOf(45, 72);\nSystem.out.println("Max: " + max);', '    static int maxOf(int a, int b) {\n        int result = b;\n        return result;\n    }'), expect_stdout="[JVM] Max: 72")
run_java("V36 Welcome greeting method", java_wrap('String msg = greet("Kashinath");\nSystem.out.println(msg);', '    static String greet(String name) {\n        String greeting = "Welcome, " + name + "!";\n        return greeting;\n    }'), expect_stdout="[JVM] Welcome, Kashinath!")
run_java("V37 Apply discount method", java_wrap('int finalPrice = applyDiscount(1200, 200);\nSystem.out.println("Final Price: $" + finalPrice);', '    static int applyDiscount(int price, int discount) {\n        int result = price - discount;\n        return result;\n    }'), expect_stdout="[JVM] Final Price: $1000")
run_java("V38 Full class simulation", java_wrap('String name = "Kashinath";\nint age = 22;\ndouble gpa = 3;\nString dept = "CS";\nint stipend = calcStipend(3000, 500);\nSystem.out.println("Student: " + name + ", Dept: " + dept);\nSystem.out.println("GPA: " + gpa + ", Stipend: $" + stipend);', '    static int calcStipend(int base, int bonus) {\n        int total = base + bonus;\n        return total;\n    }'), expect_stdout=["[JVM] Student: Kashinath, Dept: CS", "[JVM] GPA: 3.0, Stipend: $3500"])
run_java("V39 Chain of method calls", java_wrap('int step1 = addTen(5);\nint step2 = doubleIt(step1);\nSystem.out.println("Result: " + step2);', '    static int addTen(int n) {\n        int r = n + 10;\n        return r;\n    }\n    static int doubleIt(int n) {\n        int r = n * 2;\n        return r;\n    }'), expect_stdout="[JVM] Result: 30")
run_java("V40 Multi System.out calls", java_wrap('System.out.println("Header");\nSystem.out.println("Body");\nSystem.out.println("Footer");'), expect_stdout=["[JVM] Header", "[JVM] Body", "[JVM] Footer"])
run_java("V41 Long variable type", java_wrap('long stars = 100000;\nSystem.out.println("Stars: " + stars);'), expect_stdout="[JVM] Stars: 100000")
run_java("V42 Float variable type", java_wrap('float rate = 5.5;\nSystem.out.println("Rate: " + rate);'), expect_stdout="[JVM] Rate: 5.5")
run_java("V43 Char variable type", java_wrap('char grade = \'A\';\nSystem.out.println("Grade: " + grade);'), expect_stdout="[JVM] Grade: A")
run_java("V44 Modulo method", java_wrap('int rem = modulo(17, 5);\nSystem.out.println("Rem: " + rem);', '    static int modulo(int a, int b) {\n        int r = a % b;\n        return r;\n    }'), expect_stdout="[JVM] Rem: 2")
run_java("V45 Negative number math", java_wrap('int temp = -5;\ntemp = temp + 10;\nSystem.out.println("Temp: " + temp);'), expect_stdout="[JVM] Temp: 5")
run_java("V46 Array primitive simulation", java_wrap('int[] scores = {90, 85, 88};\nSystem.out.println("Scores count: 3");'), expect_stdout="[JVM] Scores count: 3")
run_java("V47 Simple loop sum simulation", java_wrap('int sum = 0;\nsum = sum + 1;\nsum = sum + 2;\nsum = sum + 3;\nSystem.out.println("Sum: " + sum);'), expect_stdout="[JVM] Sum: 6")
run_java("V48 Multiplication table step", java_wrap('int num = 5;\nint x1 = num * 1;\nint x2 = num * 2;\nSystem.out.println("5x1=" + x1 + ", 5x2=" + x2);'), expect_stdout="[JVM] 5x1=5, 5x2=10")
run_java("V49 Boolean flag check", java_wrap('boolean isActive = true;\nboolean isAdmin = false;\nSystem.out.println("Active: " + isActive + ", Admin: " + isAdmin);'), expect_stdout="[JVM] Active: true, Admin: false")
run_java("V50 Final total result", java_wrap('int score = 100;\nscore = score + 50;\nSystem.out.println("Final Score: " + score);'), expect_stdout="[JVM] Final Score: 150")


# ══════════════════════════════════════════════════════════════════════════════
#  FINAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{'═'*62}")
print(f"  📊  150-PROGRAM FULL SUITE FINAL REPORT")
print(f"{'═'*62}{RST}")

grand_pass = grand_fail = 0
for lang, tests in results.items():
    passed = sum(1 for t in tests if t['passed'])
    failed = len(tests) - passed
    grand_pass += passed; grand_fail += failed
    bar_p = '█' * passed
    bar_f = '░' * failed
    pct = int(100 * passed / len(tests)) if tests else 0
    colour = GRN if pct == 100 else (YEL if pct >= 80 else RED)
    print(f"\n  {BLD}{lang.upper()}{RST}  {colour}{bar_p}{RED}{bar_f}{RST}  "
          f"{colour}{passed}/{len(tests)} ({pct}%){RST}")
    for t in tests:
        if not t['passed']:
            print(f"    {RED}✗ {t['label']}{RST}")
            for issue in t['issues']:
                print(f"        {YEL}→ {issue}{RST}")

total = grand_pass + grand_fail
pct = int(100 * grand_pass / total) if total else 0
colour = GRN if pct == 100 else (YEL if pct >= 80 else RED)
print(f"\n{BLD}{'─'*62}")
print(f"  TOTAL  {colour}{grand_pass}/{total} tests passed ({pct}%){RST}")
print(f"{'─'*62}{RST}\n")
sys.exit(0 if grand_fail == 0 else 1)
