import unittest
from debugger.java_tracer import JavaExecutionTracer

class Test20JavaExecutionFlowScenarios(unittest.TestCase):

    def test_01_constructor_chaining(self):
        code = '''
class GrandParent {
    GrandParent() { System.out.println("1. GrandParent"); }
}
class Parent extends GrandParent {
    Parent() { System.out.println("2. Parent"); }
}
class Child extends Parent {
    Child() { System.out.println("3. Child"); }
}
public class Main {
    public static void main(String[] args) {
        Child c = new Child();
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        output = res['steps'][-1]['stdout']
        self.assertIn("1. GrandParent", output)
        self.assertIn("2. Parent", output)
        self.assertIn("3. Child", output)

    def test_02_abstract_template_pattern(self):
        code = '''
abstract class Game {
    abstract void initialize();
    abstract void start();
    public final void play() {
        initialize();
        start();
    }
}
class Chess extends Game {
    void initialize() { System.out.println("Chess Init"); }
    void start() { System.out.println("Chess Start"); }
}
public class Main {
    public static void main(String[] args) {
        Game g = new Chess();
        g.play();
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        output = res['steps'][-1]['stdout']
        self.assertIn("Chess Init", output)
        self.assertIn("Chess Start", output)

    def test_03_interface_default_methods(self):
        code = '''
interface Loggable {
    default void log(String msg) {
        System.out.println("LOG: " + msg);
    }
}
class Service implements Loggable {}
public class Main {
    public static void main(String[] args) {
        Service s = new Service();
        s.log("Running task");
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("LOG: Running task", res['steps'][-1]['stdout'])

    def test_04_inner_class_access(self):
        code = '''
class Outer {
    private String secret = "TopSecret";
    class Inner {
        void reveal() {
            System.out.println("Secret: " + secret);
        }
    }
}
public class Main {
    public static void main(String[] args) {
        Outer out = new Outer();
        Outer.Inner in = out.new Inner();
        in.reveal();
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("Secret: TopSecret", res['steps'][-1]['stdout'])

    def test_05_method_overloading(self):
        code = '''
class Calculator {
    void add(int a, int b) { System.out.println("int-int"); }
    void add(double a, double b) { System.out.println("double-double"); }
}
public class Main {
    public static void main(String[] args) {
        Calculator c = new Calculator();
        c.add(10, 20);
        c.add(10.5, 20.5);
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        output = res['steps'][-1]['stdout']
        self.assertIn("int-int", output)
        self.assertIn("double-double", output)

    def test_06_recursive_factorial_stack(self):
        code = '''
public class Main {
    static int fact(int n) {
        if (n <= 1) return 1;
        return n * fact(n - 1);
    }
    public static void main(String[] args) {
        int res = fact(4);
        System.out.println("Fact: " + res);
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("Fact: 24", res['steps'][-1]['stdout'])

    def test_07_try_catch_finally_flow(self):
        code = '''
public class Main {
    public static void main(String[] args) {
        try {
            System.out.println("1. Try");
            int x = 10 / 0;
        } catch (ArithmeticException e) {
            System.out.println("2. Catch");
        } finally {
            System.out.println("3. Finally");
        }
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        output = res['steps'][-1]['stdout']
        self.assertIn("1. Try", output)
        self.assertIn("2. Catch", output)
        self.assertIn("3. Finally", output)

    def test_08_pass_by_value_reference(self):
        code = '''
class Data { int val = 10; }
public class Main {
    static void modify(Data d) {
        d.val = 99;
    }
    public static void main(String[] args) {
        Data obj = new Data();
        modify(obj);
        System.out.println("Val: " + obj.val);
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("Val: 99", res['steps'][-1]['stdout'])

    def test_09_custom_toString_concatenation(self):
        code = '''
class User {
    String name;
    int age;
    User(String name, int age) {
        this.name = name;
        this.age = age;
    }
    public String toString() { return name + " (" + age + ")"; }
}
public class Main {
    public static void main(String[] args) {
        User u = new User("Kashinath", 23);
        System.out.println("User: " + u);
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("User: Kashinath (23)", res['steps'][-1]['stdout'])

    def test_10_strategy_pattern_lambdas(self):
        code = '''
interface Operation {
    int apply(int a, int b);
}
public class Main {
    public static void main(String[] args) {
        Operation add = (a, b) -> a + b;
        Operation mult = (a, b) -> a * b;
        System.out.println("Add: " + add.apply(4, 5));
        System.out.println("Mult: " + mult.apply(4, 5));
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        output = res['steps'][-1]['stdout']
        self.assertIn("Add: 9", output)
        self.assertIn("Mult: 20", output)

    def test_11_nested_loops_matrix_transpose(self):
        code = '''
public class Main {
    public static void main(String[] args) {
        int sum = 0;
        for (int i = 1; i <= 3; i++) {
            for (int j = 1; j <= 2; j++) {
                sum += i * j;
            }
        }
        System.out.println("Sum: " + sum);
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("Sum: 18", res['steps'][-1]['stdout'])

    def test_12_ternary_short_circuit(self):
        code = '''
public class Main {
    public static void main(String[] args) {
        int age = 20;
        String status = (age >= 18) ? "Adult" : "Minor";
        System.out.println("Status: " + status);
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("Status: Adult", res['steps'][-1]['stdout'])

    def test_13_arraylist_stream_filter(self):
        code = '''
import java.util.*;
public class Main {
    public static void main(String[] args) {
        List<Integer> nums = Arrays.asList(1, 2, 3, 4, 5, 6);
        nums.stream().filter(n -> n % 2 == 0).forEach(System.out::println);
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        output = res['steps'][-1]['stdout']
        self.assertIn("2", output)
        self.assertIn("4", output)
        self.assertIn("6", output)

    def test_14_custom_exception_throw_catch(self):
        code = '''
class InsufficientFundsException extends Exception {
    InsufficientFundsException(String msg) { super(msg); }
}
public class Main {
    public static void main(String[] args) {
        try {
            throw new InsufficientFundsException("Balance too low");
        } catch (InsufficientFundsException e) {
            System.out.println("Caught: " + e.getMessage());
        }
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("Caught: Balance too low", res['steps'][-1]['stdout'])

    def test_15_anonymous_inner_class_override(self):
        code = '''
interface Printer {
    void print();
}
public class Main {
    public static void main(String[] args) {
        Printer p = new Printer() {
            public void print() {
                System.out.println("Anon Print");
            }
        };
        p.print();
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("Anon Print", res['steps'][-1]['stdout'])

    def test_16_generic_box_type(self):
        code = '''
class Box<T> {
    private T item;
    Box(T item) { this.item = item; }
    public T getItem() { return item; }
}
public class Main {
    public static void main(String[] args) {
        Box<String> b = new Box<>("Java 17");
        System.out.println("Box: " + b.getItem());
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("Box: Java 17", res['steps'][-1]['stdout'])

    def test_17_collections_sort_comparator_lambda(self):
        code = '''
import java.util.*;
class Student {
    String name;
    int score;
    Student(String name, int score) {
        this.name = name;
        this.score = score;
    }
}
public class Main {
    public static void main(String[] args) {
        List<Student> list = Arrays.asList(new Student("Alice", 85), new Student("Bob", 95));
        Collections.sort(list, (a, b) -> b.score - a.score);
        System.out.println("Top: " + list.get(0).name);
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("Bob", res['steps'][-1]['stdout'])

    def test_18_string_builder_append(self):
        code = '''
public class Main {
    public static void main(String[] args) {
        StringBuilder sb = new StringBuilder("Hello");
        sb.append(" World");
        System.out.println(sb.toString());
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("Hello World", res['steps'][-1]['stdout'])

    def test_19_while_loop_accumulator(self):
        code = '''
public class Main {
    public static void main(String[] args) {
        int i = 0, sum = 0;
        while (i < 5) {
            sum += i;
            i++;
        }
        System.out.println("Sum: " + sum);
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("Sum: 10", res['steps'][-1]['stdout'])

    def test_20_polymorphic_method_dispatch(self):
        code = '''
class Animal {
    public void speak() { System.out.println("Animal sound"); }
}
class Dog extends Animal {
    public void speak() { System.out.println("Woof woof"); }
}
public class Main {
    public static void main(String[] args) {
        Animal a = new Dog();
        a.speak();
    }
}
'''
        tracer = JavaExecutionTracer(code)
        res = tracer.execute()
        self.assertEqual(res['status'], 'success')
        self.assertIn("Woof woof", res['steps'][-1]['stdout'])

if __name__ == '__main__':
    unittest.main()
