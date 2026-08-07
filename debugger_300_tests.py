"""
================================================================================
  EXTREME DEBUGGER TEST SUITE — 300 PROGRAMS (100 Python + 100 JS + 100 Java)
================================================================================
  Tests nested method calls, recursion, loops, OOP, arithmetic, static scope,
  chained calls, and string concatenation across all three tracers.
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

def run_python(label, code, expect_stdout=None):
    try:
        t = PythonExecutionTracer(textwrap.dedent(code).strip())
        out = t.execute()
        return _check(label, 'python', out, expect_stdout)
    except Exception as e:
        return _crash(label, 'python', e)

def run_js(label, code, expect_stdout=None):
    try:
        t = JavaScriptExecutionTracer(textwrap.dedent(code).strip())
        out = t.execute()
        return _check(label, 'javascript', out, expect_stdout)
    except Exception as e:
        return _crash(label, 'javascript', e)

def run_java(label, code, expect_stdout=None):
    try:
        t = JavaExecutionTracer(textwrap.dedent(code).strip())
        out = t.execute()
        return _check(label, 'java', out, expect_stdout)
    except Exception as e:
        return _crash(label, 'java', e)

def _check(label, lang, out, expect_stdout):
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
                issues.append(f"stdout missing: {repr(exp)} | got: {repr(last_stdout[:100])}")

    passed = len(issues) == 0
    results[lang].append({'label': label, 'passed': passed, 'issues': issues, 'steps': len(steps)})
    return passed

def _crash(label, lang, err):
    results[lang].append({'label': label, 'passed': False, 'issues': [f"CRASH: {str(err)}"], 'steps': 0})
    return False

def java_wrap(body, extra_methods=""):
    return f"""public class Main {{
    public static void main(String[] args) {{
{textwrap.indent(textwrap.dedent(body).strip(), '        ')}
    }}
{extra_methods}
}}"""

# ══════════════════════════════════════════════════════════════════════════════
#  PYTHON — 100 PROGRAMS
# ══════════════════════════════════════════════════════════════════════════════
for i in range(1, 101):
    if i == 1: run_python(f"PY{i:03d} Variable assignment", "x = 42\nprint(x)", "42")
    elif i == 2: run_python(f"PY{i:03d} String concat", "a = 'Hello'\nb = 'World'\nprint(a + ' ' + b)", "Hello World")
    elif i == 3: run_python(f"PY{i:03d} f-string", "name = 'Kashi'\nprint(f'Hi {name}')", "Hi Kashi")
    elif i == 4: run_python(f"PY{i:03d} List lookup", "nums = [10, 20]\nprint(nums[1])", "20")
    elif i == 5: run_python(f"PY{i:03d} List append", "items = [1]\nitems.append(2)\nprint(items)", "[1, 2]")
    elif i == 6: run_python(f"PY{i:03d} List len", "print(len([1, 2, 3, 4]))", "4")
    elif i == 7: run_python(f"PY{i:03d} For sum", "total = 0\nfor x in [1, 2, 3]:\n    total += x\nprint(total)", "6")
    elif i == 8: run_python(f"PY{i:03d} While count", "i = 0\nwhile i < 3:\n    i += 1\nprint(i)", "3")
    elif i == 9: run_python(f"PY{i:03d} If condition", "s = 85\nif s >= 80:\n    print('Pass')", "Pass")
    elif i == 10: run_python(f"PY{i:03d} Nested if", "x = 15\nif x > 10:\n    print('B')", "B")
    elif i == 11: run_python(f"PY{i:03d} Function call", "def f(x):\n    return x*2\nprint(f(5))", "10")
    elif i == 12: run_python(f"PY{i:03d} Function sum", "def add(a, b):\n    return a + b\nprint(add(4, 6))", "10")
    elif i == 13: run_python(f"PY{i:03d} Default args", "def p(b, exp=2):\n    return b**exp\nprint(p(4))", "16")
    elif i == 14: run_python(f"PY{i:03d} Recursion", "def fact(n):\n    if n <= 1: return 1\n    return n * fact(n-1)\nprint(fact(4))", "24")
    elif i == 15: run_python(f"PY{i:03d} Fibonacci", "a, b = 0, 1\nfor _ in range(4):\n    a, b = b, a + b\nprint(a)", "3")
    elif i == 16: run_python(f"PY{i:03d} Dict lookup", "d = {'a': 1}\nprint(d['a'])", "1")
    elif i == 17: run_python(f"PY{i:03d} Dict update", "d = {}\nd['k'] = 5\nprint(len(d))", "1")
    elif i == 18: run_python(f"PY{i:03d} String upper", "s = 'test'\nprint(s.upper())", "TEST")
    elif i == 19: run_python(f"PY{i:03d} Split join", "print('-'.join(['a', 'b']))", "a-b")
    elif i == 20: run_python(f"PY{i:03d} List slice", "arr = [10, 20, 30]\nprint(arr[1:])", "[20, 30]")
    elif i <= 30: run_python(f"PY{i:03d} Math op {i}", f"print({i} * 2)", str(i*2))
    elif i <= 40: run_python(f"PY{i:03d} String op {i}", f"s = 'item_{i}'\nprint(s)", f"item_{i}")
    elif i <= 50: run_python(f"PY{i:03d} Array op {i}", f"a = [{i}, {i+1}]\nprint(a[0])", str(i))
    elif i <= 60: run_python(f"PY{i:03d} Fn op {i}", f"def fn(n):\n    return n + 10\nprint(fn({i}))", str(i+10))
    elif i <= 70: run_python(f"PY{i:03d} OOP Class {i}", f"class C:\n    def __init__(self, v):\n        self.v = v\nc = C({i})\nprint(c.v)", str(i))
    elif i <= 80: run_python(f"PY{i:03d} Nested fn {i}", f"def outer(n):\n    def inner(x):\n        return x * 2\n    return inner(n)\nprint(outer({i}))", str(i*2))
    elif i <= 90: run_python(f"PY{i:03d} Chained fn {i}", f"def f(x):\n    return x + 1\ndef g(x):\n    return f(x) * 2\nprint(g({i}))", str((i+1)*2))
    else: run_python(f"PY{i:03d} Final test {i}", f"res = {i} + 100\nprint(res)", str(i+100))

# ══════════════════════════════════════════════════════════════════════════════
#  JAVASCRIPT — 100 PROGRAMS
# ══════════════════════════════════════════════════════════════════════════════
for i in range(1, 101):
    if i == 1: run_js(f"JS{i:03d} Var decl", "let x = 10;\nconsole.log(x);", "[JS] 10")
    elif i == 2: run_js(f"JS{i:03d} String var", "let name = 'Kashi';\nconsole.log(name);", "[JS] Kashi")
    elif i == 3: run_js(f"JS{i:03d} String concat", "let a = 'Hi';\nlet b = 'Kashi';\nconsole.log(a + ' ' + b);", "[JS] Hi Kashi")
    elif i == 4: run_js(f"JS{i:03d} Array decl", "let arr = [1, 2, 3];\nconsole.log(arr.length);", "[JS] 3")
    elif i == 5: run_js(f"JS{i:03d} Array push", "let items = ['a'];\nitems.push('b');\nconsole.log(items.join(', '));", "[JS] a, b")
    elif i == 6: run_js(f"JS{i:03d} Bank account", "let balance = 1000;\nfunction deposit(amt) {\n  return balance + amt;\n}\nfunction withdraw(amt) {\n  return balance - amt;\n}\nbalance = deposit(500);\nbalance = withdraw(200);\nconsole.log('Balance: ' + balance);", "[JS] Balance: 1300")
    elif i == 7: run_js(f"JS{i:03d} Counter", "let count = 0;\nfunction inc() {\n  return count + 1;\n}\ncount = inc();\ncount = inc();\nconsole.log('Count: ' + count);", "[JS] Count: 2")
    elif i == 8: run_js(f"JS{i:03d} Nested calls", "function add(a, b) {\n  return a + b;\n}\nfunction calc(a, b) {\n  return add(a, b) * 2;\n}\nlet res = calc(3, 4);\nconsole.log(res);", "[JS] 14")
    elif i <= 30: run_js(f"JS{i:03d} Math test {i}", f"let val = {i} + 5;\nconsole.log(val);", f"[JS] {i+5}")
    elif i <= 50: run_js(f"JS{i:03d} String test {i}", f"let msg = 'msg_{i}';\nconsole.log(msg);", f"[JS] msg_{i}")
    elif i <= 70: run_js(f"JS{i:03d} Function test {i}", f"function f(n) {{\n  return n * 2;\n}}\nlet r = f({i});\nconsole.log(r);", f"[JS] {i*2}")
    elif i <= 85: run_js(f"JS{i:03d} Object literal {i}", f"let obj = {{ val: {i} }};\nconsole.log(obj.val);", f"[JS] {i}")
    else: run_js(f"JS{i:03d} Class instance {i}", f"class C {{ constructor(v) {{ this.v = v; }} }}\nlet c = new C({i});\nconsole.log(c.v);", f"[JS] {i}")

# ══════════════════════════════════════════════════════════════════════════════
#  JAVA — 100 PROGRAMS
# ══════════════════════════════════════════════════════════════════════════════
for i in range(1, 101):
    if i == 1: run_java(f"JV{i:03d} String var", java_wrap('String name = "Kashi";\nSystem.out.println(name);'), "[JVM] Kashi")
    elif i == 2: run_java(f"JV{i:03d} Integer var", java_wrap('int age = 22;\nSystem.out.println(age);'), "[JVM] 22")
    elif i == 3: run_java(f"JV{i:03d} Double var", java_wrap('double gpa = 3.9;\nSystem.out.println(gpa);'), "[JVM] 3.9")
    elif i == 4: run_java(f"JV{i:03d} Method call", java_wrap('int res = add(10, 20);\nSystem.out.println(res);', '    static int add(int a, int b) { return a + b; }'), "[JVM] 30")
    elif i == 5: run_java(f"JV{i:03d} Nested 4-level static call chain", java_wrap(
        'start();',
        """    static void start() {
        int a = 20;
        int b = 10;
        add(a, b);
    }
    static void add(int a, int b) {
        int sum = a + b;
        System.out.println("Sum = " + sum);
        subtract(a, b);
    }
    static void subtract(int a, int b) {
        int diff = a - b;
        System.out.println("Difference = " + diff);
        multiply(a, b);
    }
    static void multiply(int a, int b) {
        int product = a * b;
        System.out.println("Product = " + product);
    }"""
    ), ["Sum = 30", "Difference = 10", "Product = 200"])
    elif i <= 30: run_java(f"JV{i:03d} Basic math {i}", java_wrap(f'int val = {i} * 3;\nSystem.out.println(val);'), f"[JVM] {i*3}")
    elif i <= 50: run_java(f"JV{i:03d} String concat {i}", java_wrap(f'String text = "Val: " + {i};\nSystem.out.println(text);'), f"[JVM] Val: {i}")
    elif i <= 70: run_java(f"JV{i:03d} Static helper {i}", java_wrap(f'int r = calc({i});\nSystem.out.println(r);', '    static int calc(int n) { return n + 10; }'), f"[JVM] {i+10}")
    elif i <= 85: run_java(f"JV{i:03d} Double math {i}", java_wrap(f'double d = {i};\nSystem.out.println("D: " + d);'), f"[JVM] D: {i}.0")
    else: run_java(f"JV{i:03d} Chained static call {i}", java_wrap(f'int res = step1({i});\nSystem.out.println(res);', '    static int step1(int n) { return step2(n) + 1; }\n    static int step2(int n) { return n * 2; }'), f"[JVM] {(i*2)+1}")

# ══════════════════════════════════════════════════════════════════════════════
#  FINAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{'═'*68}")
print(f"  📊  EXTREME DEBUGGER TEST SUITE — 300 PROGRAM REPORT")
print(f"{'═'*68}{RST}")

grand_pass = grand_fail = 0
for lang, tests in results.items():
    passed = sum(1 for t in tests if t['passed'])
    failed = len(tests) - passed
    grand_pass += passed; grand_fail += failed
    bar_p = '█' * (passed // 2)
    bar_f = '░' * (failed // 2)
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
print(f"\n{BLD}{'─'*68}")
print(f"  TOTAL  {colour}{grand_pass}/{total} programs passed ({pct}%){RST}")
print(f"{'─'*68}{RST}\n")
sys.exit(0 if grand_fail == 0 else 1)
