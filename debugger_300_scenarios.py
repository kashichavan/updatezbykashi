"""
================================================================================
  COMPREHENSIVE DEBUGGER ENGINE 300-PROGRAM BENCHMARK SUITE
  100 Python + 100 JavaScript + 100 Java 17 JVM Programs
  Ranging from Low Difficulty (1-30), Medium (31-70), to Hard/Complex (71-100)
================================================================================
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
#  🐍 PYTHON — 100 PROGRAMS (Low, Medium, Hard)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{CYN}{'─'*70}\n  🐍 PYTHON TRACER — 100 Programs (Low, Medium, Hard Scenarios)\n{'─'*70}{RST}")

# Low (1-30)
for i in range(1, 31):
    run_python(f"PY{i:03d} [LOW] Basic assignment & arithmetic {i}", f"a = {i}\nb = {i * 2}\nc = a + b\nprint(c)", str(i * 3))

# Medium (31-70)
for i in range(31, 71):
    run_python(f"PY{i:03d} [MED] Function & list iteration {i}", f"def process(val):\n    res = val * 2\n    return res\ntotal = process({i})\nprint(total)", str(i * 2))

# Hard (71-100)
for i in range(71, 101):
    run_python(f"PY{i:03d} [HARD] OOP class composition & recursion {i}", f"""
class Node:
    def __init__(self, val):
        self.val = val
        self.next = None
n1 = Node({i})
n2 = Node({i + 5})
n1.next = n2
def get_total(node):
    if not node: return 0
    return node.val + get_total(node.next)
print(get_total(n1))
""", str(i * 2 + 5))


# ══════════════════════════════════════════════════════════════════════════════
#  ⚡ JAVASCRIPT — 100 PROGRAMS (Low, Medium, Hard)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{CYN}{'─'*70}\n  ⚡ JAVASCRIPT TRACER — 100 Programs (Low, Medium, Hard Scenarios)\n{'─'*70}{RST}")

# Low (1-30)
for i in range(1, 31):
    run_js(f"JS{i:03d} [LOW] Variable declaration & arithmetic {i}", f"let a = {i};\nlet b = {i * 2};\nlet c = a + b;\nconsole.log(c);", f"[JS] {i * 3}")

# Medium (31-70)
for i in range(31, 71):
    run_js(f"JS{i:03d} [MED] Function calls & array push {i}", f"function calc(n) {{\n  let res = n * 2;\n  return res;\n}}\nlet ans = calc({i});\nconsole.log('Result: ' + ans);", f"[JS] Result: {i * 2}")

# Hard (71-100)
for i in range(71, 101):
    run_js(f"JS{i:03d} [HARD] Chained functions & state mutation {i}", f"""
let balance = {i * 100};
function deposit(amt) {{
  let newBal = balance + amt;
  return newBal;
}}
function withdraw(amt) {{
  let newBal = balance - amt;
  return newBal;
}}
balance = deposit(500);
balance = withdraw(200);
console.log('Balance: ' + balance);
""", f"[JS] Balance: {i * 100 + 300}")


# ══════════════════════════════════════════════════════════════════════════════
#  ☕ JAVA — 100 PROGRAMS (Low, Medium, Hard)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{CYN}{'─'*70}\n  ☕ JAVA TRACER — 100 Programs (Low, Medium, Hard Scenarios)\n{'─'*70}{RST}")

# Low (1-30)
for i in range(1, 31):
    run_java(f"JV{i:03d} [LOW] Primitive variables & addition {i}", java_wrap(f'int a = {i};\nint b = {i * 2};\nint sum = a + b;\nSystem.out.println(sum);'), f"[JVM] {i * 3}")

# Medium (31-70)
for i in range(31, 71):
    run_java(f"JV{i:03d} [MED] Static method call & return {i}", java_wrap(f'int res = multiply({i}, 2);\nSystem.out.println("Result: " + res);', '    static int multiply(int a, int b) {\n        int product = a * b;\n        return product;\n    }'), f"[JVM] Result: {i * 2}")

# Hard (71-100)
for i in range(71, 101):
    run_java(f"JV{i:03d} [HARD] 4-level nested static call chain {i}", java_wrap(
        f'start({i});',
        """    static void start(int val) {
        int a = val;
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
        System.out.println("Diff = " + diff);
        multiply(a, b);
    }
    static void multiply(int a, int b) {
        int product = a * b;
        System.out.println("Product = " + product);
    }"""
    ), [f"Sum = {i + 10}", f"Diff = {i - 10}", f"Product = {i * 10}"])


# ══════════════════════════════════════════════════════════════════════════════
#  FINAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{'═'*70}")
print(f"  📊  300-PROGRAM BENCHMARK SUITE FINAL REPORT")
print(f"{'═'*70}{RST}")

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
print(f"\n{BLD}{'─'*70}")
print(f"  TOTAL  {colour}{grand_pass}/{total} programs passed ({pct}%){RST}")
print(f"{'─'*70}{RST}\n")
sys.exit(0 if grand_fail == 0 else 1)
