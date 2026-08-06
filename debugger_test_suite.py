"""
=============================================================
  DEBUGGER ENGINE — 100-PROGRAM FULL TEST SUITE
  Tests Python (40), JavaScript (35), Java (25) tracers
  Reports: pass/fail, stdout, variable data, step counts
=============================================================
"""
import sys, os, json, textwrap, traceback as tb
sys.path.insert(0, os.path.dirname(__file__))

from debugger.python_tracer     import PythonExecutionTracer
from debugger.javascript_tracer import JavaScriptExecutionTracer
from debugger.java_tracer       import JavaExecutionTracer

# ─── ANSI colours ──────────────────────────────────────────────────────────────
GRN  = '\033[92m'; RED = '\033[91m'; YEL = '\033[93m'
BLU  = '\033[94m'; CYN = '\033[96m'; RST = '\033[0m'; BLD = '\033[1m'

results = {'python': [], 'javascript': [], 'java': []}

# ─── Runner helpers ─────────────────────────────────────────────────────────────
def run_python(label, code, expect_stdout=None, expect_vars=None, expect_steps_gte=1):
    try:
        t   = PythonExecutionTracer(textwrap.dedent(code).strip())
        out = t.execute()
        return _check(label, 'python', out, expect_stdout, expect_vars, expect_steps_gte)
    except Exception as e:
        return _crash(label, 'python', e)

def run_js(label, code, expect_stdout=None, expect_vars=None, expect_steps_gte=1):
    try:
        t   = JavaScriptExecutionTracer(textwrap.dedent(code).strip())
        out = t.execute()
        return _check(label, 'javascript', out, expect_stdout, expect_vars, expect_steps_gte)
    except Exception as e:
        return _crash(label, 'javascript', e)

def run_java(label, code, expect_stdout=None, expect_vars=None, expect_steps_gte=1):
    try:
        t   = JavaExecutionTracer(textwrap.dedent(code).strip())
        out = t.execute()
        return _check(label, 'java', out, expect_stdout, expect_vars, expect_steps_gte)
    except Exception as e:
        return _crash(label, 'java', e)

def _check(label, lang, out, expect_stdout, expect_vars, expect_steps_gte):
    issues = []
    steps  = out.get('steps', [])

    # 1. Steps count
    if len(steps) < expect_steps_gte:
        issues.append(f"only {len(steps)} steps (expected ≥{expect_steps_gte})")

    # 2. No unhandled crashes in steps
    for s in steps:
        if s.get('event_type') == 'exception':
            issues.append(f"exception step at L{s['line_number']}: {s['ai_explanation'][:60]}")

    # 3. Function objects should never appear in variables
    for s in steps:
        for k, v in s.get('variables', {}).items():
            if isinstance(v, dict) and v.get('type') in ('function', 'builtin_function_or_method', 'type'):
                issues.append(f"function leak: '{k}' has type={v['type']}")

    # 4. No truncation with '...' in raw values (Python) or 'undefined' bleed
    for s in steps:
        for k, v in s.get('variables', {}).items():
            if isinstance(v, dict):
                raw = v.get('raw', '')
                if raw.endswith('...]') or raw == '{...}':
                    issues.append(f"truncation in '{k}': {raw[:50]}")

    # 5. Stdout check
    if expect_stdout is not None:
        last_stdout = steps[-1]['stdout'] if steps else ''
        for exp in (expect_stdout if isinstance(expect_stdout, list) else [expect_stdout]):
            if exp not in last_stdout:
                issues.append(f"stdout missing: {repr(exp)} | got: {repr(last_stdout[:80])}")

    # 6. Variable value check
    if expect_vars:
        last_vars = steps[-1].get('variables', {}) if steps else {}
        for vname, expected_raw in expect_vars.items():
            actual = last_vars.get(vname, {}).get('raw', '__MISSING__')
            if str(expected_raw) not in str(actual):
                issues.append(f"var '{vname}': expected '{expected_raw}' got '{actual}'")

    # 7. mem_addr stability per variable
    addr_map = {}
    for s in steps:
        for k, v in s.get('variables', {}).items():
            if isinstance(v, dict):
                addr = v.get('mem_addr', '')
                if k not in addr_map:
                    addr_map[k] = addr
                elif addr_map[k] != addr and addr:
                    issues.append(f"mem unstable: '{k}' changes addr")
                    break

    passed = len(issues) == 0
    results[lang].append({'label': label, 'passed': passed, 'issues': issues, 'steps': len(steps)})
    status = f"{GRN}✅ PASS{RST}" if passed else f"{RED}❌ FAIL{RST}"
    issue_str = f"  {YEL}» {'; '.join(issues)}{RST}" if issues else ''
    print(f"  {status} [{lang[:2].upper()}] {label} ({len(steps)} steps){issue_str}")
    return passed

def _crash(label, lang, exc):
    msg = str(exc)[:80]
    results[lang].append({'label': label, 'passed': False, 'issues': [f'CRASH: {msg}'], 'steps': 0})
    print(f"  {RED}💥 CRASH{RST} [{lang[:2].upper()}] {label}: {msg}")
    return False


# ══════════════════════════════════════════════════════════════════════════════
#  PYTHON TESTS  (40 programs)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{CYN}{'─'*60}\n  🐍 PYTHON TRACER — 40 Programs\n{'─'*60}{RST}")

run_python("P01 Variable assignment",
    "x = 10\ny = 20\nz = x + y\nprint(z)",
    expect_stdout="30", expect_vars={'z': '30'}, expect_steps_gte=3)

run_python("P02 String concatenation",
    "first = 'Kashi'\nlast = 'Chavan'\nfull = first + ' ' + last\nprint(full)",
    expect_stdout="Kashi Chavan", expect_vars={'full': 'Kashi Chavan'})

run_python("P03 f-string formatting",
    "name = 'Kashinath'\nage = 22\nprint(f'{name} is {age} years old')",
    expect_stdout="Kashinath is 22 years old")

run_python("P04 List creation & index",
    "nums = [10, 20, 30, 40]\nfirst = nums[0]\nlast = nums[-1]\nprint(first, last)",
    expect_stdout="10 40")

run_python("P05 List append",
    "skills = ['Python']\nskills.append('Django')\nskills.append('React')\nprint(skills)",
    expect_stdout="['Python', 'Django', 'React']")

run_python("P06 List length",
    "items = [1, 2, 3, 4, 5]\ncount = len(items)\nprint(count)",
    expect_stdout="5", expect_vars={'count': '5'})

run_python("P07 For loop over list",
    "nums = [1, 2, 3]\ntotal = 0\nfor n in nums:\n    total = total + n\nprint(total)",
    expect_stdout="6", expect_vars={'total': '6'})

run_python("P08 While loop",
    "i = 0\nresult = 0\nwhile i < 5:\n    result = result + i\n    i = i + 1\nprint(result)",
    expect_stdout="10")

run_python("P09 If-else condition",
    "x = 15\nif x > 10:\n    label = 'big'\nelse:\n    label = 'small'\nprint(label)",
    expect_stdout="big", expect_vars={'label': 'big'})

run_python("P10 Nested if-elif-else",
    "score = 75\nif score >= 90:\n    grade = 'A'\nelif score >= 70:\n    grade = 'B'\nelse:\n    grade = 'C'\nprint(grade)",
    expect_stdout="B", expect_vars={'grade': 'B'})

run_python("P11 Simple function",
    "def square(n):\n    return n * n\nresult = square(7)\nprint(result)",
    expect_stdout="49", expect_vars={'result': '49'})

run_python("P12 Function with two args",
    "def add(a, b):\n    return a + b\nans = add(15, 25)\nprint(ans)",
    expect_stdout="40")

run_python("P13 Function default args",
    "def greet(name, msg='Hello'):\n    return msg + ' ' + name\nprint(greet('Kashi'))",
    expect_stdout="Hello Kashi")

run_python("P14 Recursive factorial",
    "def fact(n):\n    if n <= 1:\n        return 1\n    return n * fact(n - 1)\nprint(fact(5))",
    expect_stdout="120")

run_python("P15 Fibonacci iterative",
    "a, b = 0, 1\nfor _ in range(7):\n    a, b = b, a + b\nprint(a)",
    expect_stdout="13")

run_python("P16 Dictionary creation",
    "student = {'name': 'Kashi', 'age': 22}\nprint(student['name'])",
    expect_stdout="Kashi")

run_python("P17 Dict update",
    "d = {'x': 1}\nd['y'] = 2\nd['x'] = 99\nprint(d['x'], d['y'])",
    expect_stdout="99 2")

run_python("P18 Dict len",
    "d = {'a': 1, 'b': 2, 'c': 3}\nprint(len(d))",
    expect_stdout="3")

run_python("P19 String upper/lower",
    "s = 'hello World'\nup = s.upper()\nlo = s.lower()\nprint(up)\nprint(lo)",
    expect_stdout=["HELLO WORLD", "hello world"])

run_python("P20 String split & join",
    "words = 'one two three'.split()\njoined = '-'.join(words)\nprint(joined)",
    expect_stdout="one-two-three")

run_python("P21 List slicing",
    "nums = [0, 1, 2, 3, 4, 5]\nslice1 = nums[1:4]\nprint(slice1)",
    expect_stdout="[1, 2, 3]")

run_python("P22 List comprehension",
    "squares = [x*x for x in range(5)]\nprint(squares)",
    expect_stdout="[0, 1, 4, 9, 16]")

run_python("P23 Tuple unpacking",
    "pair = (10, 20)\na, b = pair\nprint(a + b)",
    expect_stdout="30")

run_python("P24 Boolean logic",
    "x = True\ny = False\nprint(x and y)\nprint(x or y)\nprint(not x)",
    expect_stdout=["False", "True", "False"])

run_python("P25 Modulo operator",
    "n = 17\nremainder = n % 5\nprint(remainder)",
    expect_stdout="2", expect_vars={'remainder': '2'})

run_python("P26 Integer division",
    "a = 17\nb = 5\nresult = a // b\nprint(result)",
    expect_stdout="3")

run_python("P27 Power operator",
    "base = 2\nexp = 10\nresult = base ** exp\nprint(result)",
    expect_stdout="1024")

run_python("P28 Max & Min",
    "nums = [3, 1, 4, 1, 5, 9, 2, 6]\nbig = max(nums)\nsmall = min(nums)\nprint(big, small)",
    expect_stdout="9 1")

run_python("P29 Range sum",
    "total = sum(range(1, 11))\nprint(total)",
    expect_stdout="55")

run_python("P30 Sorted list",
    "nums = [5, 2, 8, 1, 9]\nsorted_nums = sorted(nums)\nprint(sorted_nums)",
    expect_stdout="[1, 2, 5, 8, 9]")

run_python("P31 Reverse list",
    "items = [1, 2, 3, 4, 5]\nitems.reverse()\nprint(items)",
    expect_stdout="[5, 4, 3, 2, 1]")

run_python("P32 String contains",
    "sentence = 'Python is awesome'\nhas = 'awesome' in sentence\nprint(has)",
    expect_stdout="True")

run_python("P33 Multiple assignment",
    "a = b = c = 100\nprint(a, b, c)",
    expect_stdout="100 100 100")

run_python("P34 Swap variables",
    "x = 5\ny = 10\nx, y = y, x\nprint(x, y)",
    expect_stdout="10 5")

run_python("P35 Two Sum algorithm",
    """
    def two_sum(nums, target):
        seen = {}
        for i, num in enumerate(nums):
            diff = target - num
            if diff in seen:
                return [seen[diff], i]
            seen[num] = i
        return []
    result = two_sum([2, 7, 11, 15], 9)
    print(result)
    """,
    expect_stdout="[0, 1]")

run_python("P36 Bubble sort",
    """
    arr = [64, 34, 25, 12, 22]
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    print(arr)
    """,
    expect_stdout="[12, 22, 25, 34, 64]")

run_python("P37 Binary search",
    """
    def binary_search(arr, target):
        low, high = 0, len(arr) - 1
        while low <= high:
            mid = (low + high) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                low = mid + 1
            else:
                high = mid - 1
        return -1
    idx = binary_search([1, 3, 5, 7, 9, 11], 7)
    print(idx)
    """,
    expect_stdout="3")

run_python("P38 FizzBuzz",
    """
    output = []
    for i in range(1, 16):
        if i % 15 == 0:
            output.append('FizzBuzz')
        elif i % 3 == 0:
            output.append('Fizz')
        elif i % 5 == 0:
            output.append('Buzz')
        else:
            output.append(str(i))
    print(' '.join(output))
    """,
    expect_stdout="FizzBuzz")

run_python("P39 Palindrome check",
    """
    def is_palindrome(s):
        return s == s[::-1]
    print(is_palindrome('racecar'))
    print(is_palindrome('hello'))
    """,
    expect_stdout=["True", "False"])

run_python("P40 Count vowels",
    """
    def count_vowels(s):
        vowels = 'aeiouAEIOU'
        count = 0
        for ch in s:
            if ch in vowels:
                count = count + 1
        return count
    print(count_vowels('Kashinath'))
    """,
    expect_stdout="3")


# ══════════════════════════════════════════════════════════════════════════════
#  JAVASCRIPT TESTS  (35 programs)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{CYN}{'─'*60}\n  ⚡ JAVASCRIPT TRACER — 35 Programs\n{'─'*60}{RST}")

run_js("J01 Variable declaration",
    "let x = 10;\nlet y = 20;\nlet z = x + y;\nconsole.log(z);",
    expect_stdout="[JS] 30", expect_vars={'z': '30'})

run_js("J02 String variable",
    'let name = "Kashinath";\nlet age = 22;\nconsole.log(name);',
    expect_stdout="[JS] Kashinath")

run_js("J03 String concat",
    'let first = "Kashi";\nlet last = "Chavan";\nlet full = first + " " + last;\nconsole.log(full);',
    expect_stdout="[JS] Kashi Chavan")

run_js("J04 Array declaration",
    'let nums = [10, 20, 30];\nconsole.log(nums);',
    expect_stdout="[JS]")

run_js("J05 Array push",
    'let skills = ["Python"];\nskills.push("Django");\nskills.push("React");\nconsole.log(skills);',
    expect_steps_gte=3)

run_js("J06 Array join",
    'let skills = ["Python", "Django", "JS"];\nconsole.log(skills.join(", "));',
    expect_stdout="[JS] Python, Django, JS")

run_js("J07 Arithmetic operators",
    "let a = 15;\nlet b = 4;\nlet div = a / b;\nlet mod = a % b;\nconsole.log(mod);",
    expect_stdout="[JS] 3")

run_js("J08 Boolean variable",
    "let isStudent = true;\nlet isWorking = false;\nconsole.log(isStudent);",
    expect_stdout="[JS] true")

run_js("J09 Reassignment",
    "let age = 22;\nage = age + 1;\nconsole.log(age);",
    expect_stdout="[JS] 23", expect_vars={'age': '23'})

run_js("J10 Multiple console.log",
    'let name = "Kashi";\nlet city = "Pune";\nconsole.log(name);\nconsole.log(city);',
    expect_stdout=["[JS] Kashi", "[JS] Pune"])

run_js("J11 Template literal",
    'let name = "Kashinath";\nlet age = 22;\nconsole.log(`Name: ${name}, Age: ${age}`);',
    expect_stdout="[JS] Name: Kashinath, Age: 22")

run_js("J12 Compound reassignment",
    "let x = 10;\nx = x * 2;\nx = x + 5;\nconsole.log(x);",
    expect_stdout="[JS] 25")

run_js("J13 String + number concat",
    'let score = 95;\nconsole.log("Score: " + score);',
    expect_stdout="[JS] Score: 95")

run_js("J14 Simple function call",
    "function square(n) {\n  let result = n * n;\n  return result;\n}\nlet ans = square(8);\nconsole.log(ans);",
    expect_stdout="[JS] 64", expect_vars={'ans': '64'})

run_js("J15 Function with string return",
    'function greet(person) {\n  let message = "Hello, " + person + "!";\n  return message;\n}\nlet result = greet("Kashi");\nconsole.log(result);',
    expect_stdout="[JS] Hello, Kashi!", expect_vars={'result': 'Hello, Kashi!'})

run_js("J16 Two-argument function",
    "function add(a, b) {\n  let total = a + b;\n  return total;\n}\nlet sum = add(30, 70);\nconsole.log(sum);",
    expect_stdout="[JS] 100")

run_js("J17 Multiply function",
    "function multiply(x, y) {\n  let product = x * y;\n  return product;\n}\nlet res = multiply(6, 7);\nconsole.log(res);",
    expect_stdout="[JS] 42")

run_js("J18 Stipend calculator",
    "function calculateStipend(base, bonus) {\n  let total = base + bonus;\n  return total;\n}\nlet stipend = calculateStipend(3000, 500);\nconsole.log(stipend);",
    expect_stdout="[JS] 3500", expect_vars={'stipend': '3500'})

run_js("J19 Array join with dash",
    'let words = ["one", "two", "three"];\nconsole.log(words.join("-"));',
    expect_stdout="[JS] one-two-three")

run_js("J20 Variable from function + log",
    "function double(n) {\n  let r = n * 2;\n  return r;\n}\nlet x = double(21);\nconsole.log(x);",
    expect_stdout="[JS] 42")

run_js("J21 const declaration",
    'const PI = 3;\nconst radius = 7;\nconst area = PI * radius;\nconsole.log(area);',
    expect_stdout="[JS] 21")

run_js("J22 Multiple vars logged",
    'let name = "Kashinath";\nlet age = 22;\nconsole.log("Name:", name, "| Age:", age);',
    expect_stdout="[JS] Name: Kashinath | Age: 22")

run_js("J23 Null variable",
    "let result = null;\nconsole.log(result);",
    expect_stdout="[JS] null")

run_js("J24 Numeric types",
    "let integer = 42;\nlet decimal = 3;\nlet sum = integer + decimal;\nconsole.log(sum);",
    expect_stdout="[JS] 45")

run_js("J25 Push multiple items",
    'let arr = ["a"];\narr.push("b");\narr.push("c");\narr.push("d");\nconsole.log(arr.join(""));',
    expect_stdout="[JS] abcd")

run_js("J26 Greeting with template",
    'let city = "Pune";\nconsole.log(`Welcome to ${city}!`);',
    expect_stdout="[JS] Welcome to Pune!")

run_js("J27 Score grading",
    'function grade(score) {\n  let label = "Pass";\n  return label;\n}\nlet g = grade(75);\nconsole.log(g);',
    expect_stdout="[JS] Pass")

run_js("J28 Function reads outer var",
    'let base = 1000;\nfunction calcBonus(pct) {\n  let bonus = base + pct;\n  return bonus;\n}\nlet total = calcBonus(500);\nconsole.log(total);',
    expect_stdout="[JS] 1500")

run_js("J29 Subtraction",
    "let budget = 5000;\nlet expense = 1500;\nlet remaining = budget - expense;\nconsole.log(remaining);",
    expect_stdout="[JS] 3500")

run_js("J30 Division",
    "let total = 100;\nlet parts = 4;\nlet each = total / parts;\nconsole.log(each);",
    expect_stdout="[JS] 25")

run_js("J31 String length via concat",
    'let word = "Kashinath";\nconsole.log("Word: " + word);',
    expect_stdout="[JS] Word: Kashinath")

run_js("J32 Mixed types in log",
    'let name = "AGY";\nlet version = 2;\nconsole.log(name + " v" + version);',
    expect_stdout="[JS] AGY v2")

run_js("J33 Chained function calls",
    "function inc(n) {\n  let r = n + 1;\n  return r;\n}\nlet a = inc(10);\nlet b = inc(a);\nconsole.log(b);",
    expect_stdout="[JS] 12")

run_js("J34 Array of numbers joined",
    'let scores = [90, 85, 92, 78];\nconsole.log(scores.join(", "));',
    expect_stdout="[JS] 90, 85, 92, 78")

run_js("J35 Full JS default code",
    '''
    let name = "Kashinath";
    let age = 22;
    let skills = ["Python", "Django", "JS"];
    age = age + 1;
    skills.push("React");
    console.log("Name:", name, "| Age:", age);
    console.log("Skills:", skills.join(", "));
    function greet(person) {
      let message = "Hello, " + person + "!";
      return message;
    }
    let result = greet(name);
    console.log(result);
    ''',
    expect_stdout=["[JS] Name: Kashinath | Age: 23",
                   "[JS] Skills: Python, Django, JS, React",
                   "[JS] Hello, Kashinath!"])


# ══════════════════════════════════════════════════════════════════════════════
#  JAVA TESTS  (25 programs)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{CYN}{'─'*60}\n  ☕ JAVA TRACER — 25 Programs\n{'─'*60}{RST}")

def java_wrap(body, extra_methods=""):
    return f"""public class Main {{
    public static void main(String[] args) {{
{textwrap.indent(textwrap.dedent(body).strip(), '        ')}
    }}
{extra_methods}
}}"""

run_java("V01 String variable",
    java_wrap('String name = "Kashinath";\nSystem.out.println(name);'),
    expect_stdout="[JVM] Kashinath")

run_java("V02 Integer variable",
    java_wrap('int age = 22;\nSystem.out.println(age);'),
    expect_stdout="[JVM] 22")

run_java("V03 Double variable",
    java_wrap('double gpa = 3.9;\nSystem.out.println(gpa);'),
    expect_stdout="[JVM] 3.9")

run_java("V04 Boolean variable",
    java_wrap('boolean isStudent = true;\nSystem.out.println(isStudent);'),
    expect_stdout="[JVM] true")

run_java("V05 Arithmetic",
    java_wrap('int a = 30;\nint b = 12;\nint sum = a + b;\nSystem.out.println(sum);'),
    expect_stdout="[JVM] 42")

run_java("V06 String concatenation",
    java_wrap('String first = "Kashi";\nString last = "Chavan";\nString full = first + " " + last;\nSystem.out.println(full);'),
    expect_stdout="[JVM] Kashi Chavan")

run_java("V07 Reassignment",
    java_wrap('int x = 10;\nx = x + 5;\nSystem.out.println(x);'),
    expect_stdout="[JVM] 15")

run_java("V08 Multiple variables",
    java_wrap('int a = 5;\nint b = 10;\nint c = a * b;\nSystem.out.println(c);'),
    expect_stdout="[JVM] 50")

run_java("V09 String + number",
    java_wrap('String name = "Score";\nint val = 95;\nSystem.out.println(name + ": " + val);'),
    expect_stdout="[JVM] Score: 95")

run_java("V10 Age increment",
    java_wrap('int age = 22;\nage = age + 1;\nSystem.out.println("Age: " + age);'),
    expect_stdout="[JVM] Age: 23")

run_java("V11 Simple method call",
    java_wrap(
        'int result = square(7);\nSystem.out.println(result);',
        """    static int square(int n) {
        int r = n * n;
        return r;
    }"""
    ),
    expect_stdout="[JVM] 49")

run_java("V12 Add method",
    java_wrap(
        'int ans = add(25, 75);\nSystem.out.println(ans);',
        """    static int add(int a, int b) {
        int total = a + b;
        return total;
    }"""
    ),
    expect_stdout="[JVM] 100")

run_java("V13 Stipend calculator",
    java_wrap(
        'int stipend = calculateStipend(3000, 500);\nSystem.out.println("Stipend: $" + stipend);',
        """    static int calculateStipend(int base, int bonus) {
        int total = base + bonus;
        return total;
    }"""
    ),
    expect_stdout="[JVM] Stipend: $3500")

run_java("V14 Full default Java code",
    """public class Main {
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
}""",
    expect_stdout=["[JVM] Student: Kashinath, Age: 23", "[JVM] Stipend: $3500"])

run_java("V15 Multiply method",
    java_wrap(
        'int product = multiply(6, 7);\nSystem.out.println(product);',
        """    static int multiply(int x, int y) {
        int result = x * y;
        return result;
    }"""
    ),
    expect_stdout="[JVM] 42")

run_java("V16 Subtract operation",
    java_wrap('int budget = 5000;\nint expense = 1500;\nint left = budget - expense;\nSystem.out.println(left);'),
    expect_stdout="[JVM] 3500")

run_java("V17 Power approximation",
    java_wrap('int base = 2;\nint result = base * base * base;\nSystem.out.println(result);'),
    expect_stdout="[JVM] 8")

run_java("V18 String greeting",
    java_wrap('String name = "AGY";\nSystem.out.println("Hello, " + name + "!");'),
    expect_stdout="[JVM] Hello, AGY!")

run_java("V19 Mixed arithmetic",
    java_wrap('int a = 100;\nint b = 3;\nint quotient = a / b;\nSystem.out.println(quotient);'),
    expect_stdout="[JVM] 33")

run_java("V20 Boolean true/false",
    java_wrap('boolean flag = true;\nSystem.out.println("Flag: " + flag);'),
    expect_stdout="[JVM] Flag: true")

run_java("V21 Double arithmetic",
    java_wrap('double x = 10;\ndouble y = 3;\ndouble result = x / y;\nSystem.out.println(result);'),
    expect_stdout="[JVM]")

run_java("V22 Two method calls",
    java_wrap(
        'int a = square(3);\nint b = square(4);\nSystem.out.println(a + b);',
        """    static int square(int n) {
        int r = n * n;
        return r;
    }"""
    ),
    expect_stdout="[JVM] 25")

run_java("V23 Greeting method",
    java_wrap(
        'String msg = greet("Kashinath");\nSystem.out.println(msg);',
        """    static String greet(String name) {
        String result = "Hello, " + name;
        return result;
    }"""
    ),
    expect_stdout="[JVM] Hello, Kashinath")

run_java("V24 Multiple print statements",
    java_wrap('System.out.println("Line 1");\nSystem.out.println("Line 2");\nSystem.out.println("Line 3");'),
    expect_stdout=["[JVM] Line 1", "[JVM] Line 2", "[JVM] Line 3"])

run_java("V25 Compound expression",
    java_wrap('int a = 10;\nint b = 20;\nint c = 30;\nint total = a + b + c;\nSystem.out.println("Total: " + total);'),
    expect_stdout="[JVM] Total: 60")


# ══════════════════════════════════════════════════════════════════════════════
#  FINAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{'═'*62}")
print(f"  📊  FINAL REPORT")
print(f"{'═'*62}{RST}")

grand_pass = grand_fail = 0
for lang, tests in results.items():
    passed = sum(1 for t in tests if t['passed'])
    failed = len(tests) - passed
    grand_pass += passed; grand_fail += failed
    bar_p = '█' * passed
    bar_f = '░' * failed
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
print(f"  TOTAL  {colour}{grand_pass}/{total} tests passed ({pct}%){RST}")
print(f"{'─'*62}{RST}\n")
sys.exit(0 if grand_fail == 0 else 1)
