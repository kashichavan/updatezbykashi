"""
=============================================================
  JAVA TRACER & PARSER ADVANCED TEST SUITE
  Covers OOP, Advanced Strings, Lambdas & Functional Streams
=============================================================
"""
import sys, os, textwrap
sys.path.insert(0, os.path.dirname(__file__))

from debugger.java_tracer import JavaExecutionTracer

GRN = '\033[92m'; RED = '\033[91m'; YEL = '\033[93m'
CYN = '\033[96m'; RST = '\033[0m';  BLD = '\033[1m'

results = []

def test_java(label, code, expect_stdout=None):
    try:
        t = JavaExecutionTracer(textwrap.dedent(code).strip())
        out = t.execute()
        steps = out.get('steps', [])
        issues = []
        if len(steps) == 0:
            issues.append("0 steps generated")
        for s in steps:
            if s.get('event_type') == 'exception':
                issues.append(f"exception at L{s['line_number']}: {s.get('ai_explanation', '')[:70]}")
                break
        if expect_stdout is not None:
            last_stdout = steps[-1]['stdout'] if steps else ''
            for exp in (expect_stdout if isinstance(expect_stdout, list) else [expect_stdout]):
                if exp not in last_stdout:
                    issues.append(f"stdout missing: {repr(exp)} | got: {repr(last_stdout[:100])}")
        passed = len(issues) == 0
        results.append({'label': label, 'passed': passed, 'issues': issues, 'steps': len(steps)})
        status = f"{GRN}✅ PASS{RST}" if passed else f"{RED}❌ FAIL{RST}"
        issue_str = f"\n      {YEL}» {'; '.join(issues)}{RST}" if issues else ''
        print(f"  {status} [JAVA] {label} ({len(steps)} steps){issue_str}")
        return passed
    except Exception as e:
        msg = str(e)[:100]
        results.append({'label': label, 'passed': False, 'issues': [f'CRASH: {msg}'], 'steps': 0})
        print(f"  {RED}💥 CRASH{RST} [JAVA] {label}: {msg}")
        return False

print(f"\n{BLD}{CYN}{'─'*62}\n  ☕ ADVANCED JAVA TEST SUITE — OOP, Strings, Lambdas & Streams\n{'─'*62}{RST}")

# ── 1. Advanced OOP Tests ─────────────────────────────────────────────────────

test_java("JOOP_01 Interface Default & Static Methods", """
interface Calculator {
    int compute(int a, int b);
    default int add(int a, int b) {
        return a + b;
    }
    static int multiply(int a, int b) {
        return a * b;
    }
}

class BasicCalc implements Calculator {
    @Override
    public int compute(int a, int b) {
        return add(a, b);
    }
}

public class Main {
    public static void main(String[] args) {
        Calculator calc = new BasicCalc();
        System.out.println("Add: " + calc.compute(10, 20));
        System.out.println("Mul: " + Calculator.multiply(5, 4));
    }
}
""", expect_stdout=["[JVM] Add: 30", "[JVM] Mul: 20"])

test_java("JOOP_02 Multi-level Polymorphism & Method Overriding", """
abstract class Vehicle {
    abstract String getType();
    public void start() {
        System.out.println(getType() + " engine starting...");
    }
}

class Car extends Vehicle {
    @Override
    String getType() {
        return "Car";
    }
}

class ElectricCar extends Car {
    @Override
    String getType() {
        return "Electric Car";
    }
}

public class Main {
    public static void main(String[] args) {
        Vehicle v1 = new Car();
        Vehicle v2 = new ElectricCar();
        v1.start();
        v2.start();
    }
}
""", expect_stdout=["[JVM] Car engine starting...", "[JVM] Electric Car engine starting..."])

test_java("JOOP_03 Static Field Inheritance & Counter", """
class Base {
    protected static int count = 0;
    public Base() {
        count++;
    }
}

class Sub extends Base {
    public static int getCount() {
        return count;
    }
}

public class Main {
    public static void main(String[] args) {
        new Base();
        new Sub();
        new Sub();
        System.out.println("Total Count: " + Sub.getCount());
    }
}
""", expect_stdout="[JVM] Total Count: 3")


# ── 2. Advanced String Operations ─────────────────────────────────────────────

test_java("JSTR_01 String Manipulation & Regex Parsing", """
public class Main {
    public static void main(String[] args) {
        String data = "   Kashi,   24  , Developer  ";
        String[] parts = data.split(",");
        String name = parts[0].trim();
        int age = Integer.parseInt(parts[1].trim());
        String role = parts[2].trim().toUpperCase();

        System.out.println("Name: " + name);
        System.out.println("Age: " + age);
        System.out.println("Role: " + role);
    }
}
""", expect_stdout=["[JVM] Name: Kashi", "[JVM] Age: 24", "[JVM] Role: DEVELOPER"])

test_java("JSTR_02 StringBuilder Reverse & Replace", """
public class Main {
    public static void main(String[] args) {
        StringBuilder sb = new StringBuilder("Hello World");
        sb.reverse();
        System.out.println("Reversed: " + sb.toString());
        
        String formatted = String.format("User: %s, Score: %d", "Kashi", 95);
        System.out.println("Formatted: " + formatted);
    }
}
""", expect_stdout=["[JVM] Reversed: dlroW olleH", "[JVM] Formatted: User: Kashi, Score: 95"])

test_java("JSTR_03 Substring IndexOf & Case Transformation", """
public class Main {
    public static void main(String[] args) {
        String email = "contact@antigravity.ai";
        int atIdx = email.indexOf("@");
        String username = email.substring(0, atIdx);
        String domain = email.substring(atIdx + 1);

        System.out.println("User: " + username.toUpperCase());
        System.out.println("Domain: " + domain);
        System.out.println("Contains ai: " + domain.contains("ai"));
    }
}
""", expect_stdout=["[JVM] User: CONTACT", "[JVM] Domain: antigravity.ai", "[JVM] Contains ai: true"])


# ── 3. Advanced Lambdas & Stream API ──────────────────────────────────────────

test_java("JLAM_01 Stream Filter, Map & Reduce", """
import java.util.Arrays;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        List<Integer> nums = Arrays.asList(1, 2, 3, 4, 5, 6);
        int sumOfEvens = nums.stream()
                            .filter(n -> n % 2 == 0)
                            .map(n -> n * 10)
                            .reduce(0, (a, b) -> a + b);

        System.out.println("Sum of Even Multiples: " + sumOfEvens);
    }
}
""", expect_stdout="[JVM] Sum of Even Multiples: 120")

test_java("JLAM_02 Functional Interfaces & Consumer Chaining", """
import java.util.function.Function;
import java.util.function.Predicate;

public class Main {
    public static void main(String[] args) {
        Function<Integer, Integer> square = x -> x * x;
        Function<Integer, Integer> addFive = x -> x + 5;
        Predicate<Integer, Boolean> isEven = x -> x % 2 == 0;

        int res = addFive.apply(square.apply(4));
        System.out.println("Result: " + res);
    }
}
""", expect_stdout="[JVM] Result: 21")

test_java("JLAM_03 Lambda Method Reference & List Sorting", """
import java.util.Arrays;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        List<String> names = Arrays.asList("Kashi", "Alex", "Bob", "Charlie");
        names.sort((a, b) -> a.compareTo(b));
        System.out.println("Sorted: " + names);
    }
}
""", expect_stdout="[JVM] Sorted: [Alex, Bob, Charlie, Kashi]")


# ══════════════════════════════════════════════════════════════════════════════
#  FINAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BLD}{'═'*62}")
print(f"  📊  ADVANCED JAVA TEST SUITE REPORT")
print(f"{'═'*62}{RST}")

passed = sum(1 for t in results if t['passed'])
failed = len(results) - passed
bar_p = '█' * passed; bar_f = '░' * failed
pct   = int(100 * passed / len(results)) if results else 0
colour = GRN if pct == 100 else (YEL if pct >= 80 else RED)

print(f"\n  {BLD}JAVA PARSER & TRACER{RST}  {colour}{bar_p}{RED}{bar_f}{RST}  "
      f"{colour}{passed}/{len(results)} ({pct}%){RST}")
for t in results:
    if not t['passed']:
        print(f"    {RED}✗ {t['label']}{RST}")
        for issue in t['issues']:
            print(f"        {YEL}→ {issue}{RST}")

print(f"\n{BLD}{'─'*62}")
print(f"  TOTAL  {colour}{passed}/{len(results)} Advanced Java tests passed ({pct}%){RST}")
print(f"{'─'*62}{RST}\n")
