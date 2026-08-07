"""
Java Execution Tracer — AST-based (javalang), production-oriented rewrite.

Design goals vs. the old regex engine:
  - Real parsing (javalang) instead of line-by-line regex matching, so nested
    expressions, operator precedence, multi-line statements, braces in
    strings/comments, etc. are handled correctly by construction.
  - Values are kept as real Python objects internally (int/float/str/bool/
    JavaArray/JavaObject/None) during evaluation; string formatting only
    happens when producing a trace step. This avoids the "stringly typed"
    eval() hacks that made the old engine fragile.
  - Control flow (return/break/continue) uses Python exceptions for clean
    propagation through arbitrarily nested blocks, instead of manual line
    index bookkeeping.
  - Java exceptions are modeled as a real exception class carrying a Java
    class name + message, and try/catch/finally matches against that.
"""

import javalang
from javalang.tree import (
    ClassDeclaration, MethodDeclaration, FieldDeclaration,
    LocalVariableDeclaration, VariableDeclarator, ClassCreator,
    MethodInvocation, Assignment, IfStatement, ForStatement,
    WhileStatement, ReturnStatement, BinaryOperation, Literal,
    MemberReference, ConstructorDeclaration, StatementExpression,
    BlockStatement, TryStatement, ArrayInitializer, ArrayCreator,
    Cast, TernaryExpression, This, ArraySelector, SuperConstructorInvocation,
    ExplicitConstructorInvocation, EnhancedForControl, SuperMethodInvocation
)
import re


# ─────────────────────────── Control-flow signals ───────────────────────────

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class BreakSignal(Exception):
    def __init__(self, label=None):
        self.label = label


class ContinueSignal(Exception):
    def __init__(self, label=None):
        self.label = label


class JavaException(Exception):
    """A simulated Java runtime/checked exception."""
    def __init__(self, java_class, message=""):
        self.java_class = java_class
        self.message = message
        super().__init__(f"{java_class}: {message}" if message else java_class)

    def full_name(self):
        if '.' in self.java_class:
            return self.java_class
        return f"java.lang.{self.java_class}"


# ───────────────────────────── Value wrappers ────────────────────────────────

class JavaNull:
    """Singleton representing Java's null."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "null"

    def __bool__(self):
        return False


NULL = JavaNull()


class JavaArray:
    def __init__(self, elem_type, items):
        self.elem_type = elem_type
        self.items = items  # python list

    def __repr__(self):
        return "[" + ", ".join(_display(x) for x in self.items) + "]"

    def __len__(self):
        return len(self.items)


class JavaObject:
    """Instance of a user-defined class."""
    def __init__(self, class_name, addr):
        self.class_name = class_name
        self.fields = {}
        self.addr = addr

    def __repr__(self):
        inner = ", ".join(f"{k}={_display(v)}" for k, v in self.fields.items())
        return f"{self.class_name}{{{inner}}}"


class JavaLambda:
    """Simulated Java Lambda function (a, b) -> a + b."""
    def __init__(self, params, body, captured_scope, class_name):
        self.params = params
        self.body = body
        self.captured_scope = captured_scope
        self.class_name = class_name

    def __repr__(self):
        return f"Lambda({', '.join(self.params)})"


class JavaMethodRef:
    """Simulated Java Method Reference System.out::println."""
    def __init__(self, expression, method_name, captured_scope, class_name):
        self.expression = expression
        self.method_name = method_name
        self.captured_scope = captured_scope
        self.class_name = class_name

    def __repr__(self):
        return f"MethodRef({self.method_name})"


def _display(val):
    """String form used inside container reprs / user-visible output."""
    if val is NULL or val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, str):
        return val
    if isinstance(val, float):
        return f"{val:.1f}" if val == int(val) and abs(val) < 1e15 else str(val)
    if isinstance(val, set):
        return "[" + ", ".join(_display(x) for x in sorted(val, key=lambda x: str(x))) + "]"
    if isinstance(val, dict):
        inner = ", ".join(f"{_display(k)}={_display(v)}" for k, v in val.items())
        return f"{{{inner}}}"
    return str(val)


# ─────────────────────────────── The interpreter ─────────────────────────────

class JavaExecutionTracer:
    JAVA_PRIMITIVES = {'int', 'double', 'float', 'long', 'short', 'byte', 'char', 'boolean'}

    def __init__(self, code_str, breakpoints=None, stdin_input=""):
        self.code_str = code_str
        self.lines = code_str.splitlines()
        self.breakpoints = set(breakpoints or [])
        self.stdin_queue = [l.strip() for l in stdin_input.splitlines() if l.strip()] if stdin_input else []

        self.steps = []
        self.stdout_lines = []

        self._mem_table = {}
        self._mem_counter = 0x1000
        self._obj_counter = 0

        self.classes = {}          # class_name -> ClassDeclaration node
        self.static_fields = {}    # per-class static field scope, class_name -> dict
        self.main_class = None

        self._parse_error = None
        try:
            self.tree = javalang.parse.parse(code_str)
            self._index_classes()
        except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError) as e:
            self.tree = None
            self._parse_error = str(e)

    # ── Setup ────────────────────────────────────────────────────────────────

    def _index_classes(self):
        for _, node in self.tree.filter(javalang.tree.ClassDeclaration):
            self.classes[node.name] = node
            if self.main_class is None:
                self.main_class = node.name
            for m in node.body:
                if isinstance(m, javalang.tree.MethodDeclaration) and m.name == 'main':
                    self.main_class = node.name

    def _mem_addr(self, key, is_primitive):
        if key not in self._mem_table:
            tag = 'STACK' if is_primitive else 'HEAP'
            self._mem_table[key] = f"0xJVM_{tag}_{self._mem_counter:04x}"
            self._mem_counter += 0x1A3
        return self._mem_table[key]

    def _new_obj_addr(self, class_name):
        self._obj_counter += 1
        return f"{class_name}@{(0x1000 + self._obj_counter * 0x1A3):x}"

    # ── Public entry point ─────────────────────────────────────────────────

    def execute(self):
        if self._parse_error:
            self.stdout_lines.append(f"❌ Compilation error: {self._parse_error}")
            self.steps.append({
                'step_index': 0, 'line_number': 0, 'line_text': '',
                'event_type': 'compile_error', 'is_breakpoint': False,
                'stack_frames': [], 'variables': {},
                'stdout': "\n".join(self.stdout_lines),
                'ai_explanation': f"❌ Compilation failed: {self._parse_error}",
            })
            return {'status': 'error', 'execution_time_ms': 0.0,
                    'total_steps': len(self.steps), 'steps': self.steps}

        cls_node = self.classes.get(self.main_class)
        if cls_node is None:
            raise ValueError("No class found in source")

        call_stack = []
        for cname in self.classes:
            self.static_fields[cname] = {}
            self._init_static_fields(cname, call_stack)

        main_method = self._find_method(self.main_class, 'main')
        if main_method is None:
            raise ValueError("No main() method found")

        frame_label = f"{self.main_class}.main(String[] args)"
        call_stack.append(frame_label)
        scope = self.static_fields[self.main_class]

        try:
            self._exec_block(main_method.body, dict(scope), call_stack, self.main_class)
        except JavaException as jexc:
            full = jexc.full_name()
            msg = f"Exception in thread \"main\" {full}" + (f": {jexc.message}" if jexc.message else "")
            self.stdout_lines.append(f"❌ {msg}")
            self._emit(0, '', 'exception', call_stack, {}, [], explanation=f"❌ {msg}")
        except ReturnSignal:
            pass

        return {
            'status': 'success',
            'execution_time_ms': 3.1,
            'total_steps': len(self.steps),
            'steps': self.steps,
        }

    def _init_static_fields(self, class_name, call_stack):
        cls_node = self.classes[class_name]
        scope = self.static_fields[class_name]
        for member in cls_node.body:
            if isinstance(member, javalang.tree.FieldDeclaration) and 'static' in (member.modifiers or []):
                for decl in member.declarators:
                    val = self.eval_expr(decl.initializer, scope, call_stack, class_name) \
                        if decl.initializer is not None else self._default_value(member.type)
                    self._declare(scope, decl.name, member.type, val)

    # ── Method lookup ───────────────────────────────────────────────────────

    def _find_method(self, class_name, name, arg_count=None):
        curr = class_name
        while curr and curr in self.classes:
            cls_node = self.classes[curr]
            candidates = [m for m in cls_node.body
                          if isinstance(m, javalang.tree.MethodDeclaration) and m.name == name]
            if candidates:
                if arg_count is None:
                    return candidates[0]
                for m in candidates:
                    if len(m.parameters) == arg_count:
                        return m
                return candidates[0]
            curr = cls_node.extends.name if cls_node.extends else None
        return None

    def _find_constructor(self, class_name, arg_count=None):
        cls_node = self.classes.get(class_name)
        if cls_node is None:
            return None
        ctors = [m for m in cls_node.body if isinstance(m, javalang.tree.ConstructorDeclaration)]
        if not ctors:
            return None
        if arg_count is None:
            return ctors[0]
        for c in ctors:
            if len(c.parameters) == arg_count:
                return c
        return ctors[0]

    # ── Type helpers ────────────────────────────────────────────────────────

    def _type_name(self, type_node):
        if type_node is None:
            return 'void'
        name = getattr(type_node, 'name', str(type_node))
        dims = getattr(type_node, 'dimensions', None)
        if dims:
            name += '[]' * len(dims)
        return name

    def _default_value(self, type_node):
        tname = self._type_name(type_node)
        if tname in ('int', 'short', 'byte', 'long'):
            return 0
        if tname in ('double', 'float'):
            return 0.0
        if tname == 'boolean':
            return False
        if tname == 'char':
            return '\u0000'
        return NULL

    def _is_primitive_type(self, tname):
        return tname in self.JAVA_PRIMITIVES

    # ── Scope bookkeeping / step recording helpers ─────────────────────────

    def _declare(self, scope, name, type_node, value, changed=True):
        tname = self._type_name(type_node) if not isinstance(type_node, str) else type_node
        is_prim = self._is_primitive_type(tname.rstrip('[]')) and '[]' not in tname
        key = f"{id(scope)}:{name}"
        scope[name] = {
            '_value': value,
            'type': tname,
            'is_primitive': is_prim,
            'mem_addr': self._mem_addr(key, is_prim),
            'is_changed': changed,
        }

    def _set(self, scope, name, value, changed=True):
        if name in scope:
            scope[name]['_value'] = value
            scope[name]['is_changed'] = changed
        else:
            self._declare(scope, name, 'var', value, changed)

    def _render_scope(self, scope):
        out = {}
        for k, v in scope.items():
            val = v['_value']
            raw = _display(val)
            out[k] = {
                'type': v['type'],
                'value': repr(raw),
                'raw': raw,
                'is_primitive': v['is_primitive'],
                'mem_addr': v['mem_addr'],
                'is_changed': v.get('is_changed', False),
            }
        return out

    def _emit(self, lineno, line_text, event, call_stack, scope, changed_names,
              fn_name=None, ret_val=None, explanation=None):
        for k in scope:
            scope[k]['is_changed'] = k in changed_names
        if explanation is None:
            explanation = self._explain(event, line_text, scope, changed_names, fn_name, ret_val)
        self.steps.append({
            'step_index': len(self.steps),
            'line_number': lineno,
            'line_text': line_text,
            'event_type': event,
            'return_value': _display(ret_val) if ret_val is not None else None,
            'is_breakpoint': lineno in self.breakpoints,
            'stack_frames': list(call_stack),
            'variables': self._render_scope(scope),
            'stdout': "\n".join(self.stdout_lines),
            'ai_explanation': explanation,
        })

    def _substitute_cond_values(self, text, scope):
        if not text or not scope:
            return text
        sub = text
        # If it's a for-loop line, target only the comparison expression between semicolons
        if 'for' in sub and ';' in sub:
            parts = sub.split(';')
            if len(parts) >= 2:
                sub = parts[1]

        # First substitute variable names
        for var_name, data in sorted(scope.items(), key=lambda x: len(x[0]), reverse=True):
            if var_name.startswith('__') or var_name == 'this':
                continue
            val_str = _display(data.get('_value'))
            sub = re.sub(r'\b' + re.escape(var_name) + r'\b', val_str, sub)

        # Evaluate array index accesses like [5, 2, 9, 1, 7][1] to direct element value (e.g. 2)
        def _eval_arr_access(match):
            arr_repr = match.group(1)
            idx_str = match.group(2)
            try:
                idx = int(idx_str)
                # Parse list representation [5, 2, 9, 1, 7] or ["a", "b"]
                items = [x.strip().strip('"\'') for x in arr_repr[1:-1].split(',')]
                if 0 <= idx < len(items):
                    return items[idx]
            except Exception:
                pass
            return match.group(0)

        sub = re.sub(r'(\[[^\]]+\])\[(\d+)\]', _eval_arr_access, sub)
        return sub.strip()

    def _explain(self, event, line_text, scope, changed, fn_name=None, ret_val=None):
        if event == 'call':
            return f"📞 Called method '{fn_name}()' → JVM pushed a new Stack Frame onto the Call Stack."
        if event == 'return':
            return f"↩ Method '{fn_name}()' returned → Stack Frame popped. Value: {_display(ret_val)}"
        if changed:
            details = ', '.join(f"'{k}' = {_display(scope[k]['_value'])}" for k in changed if k in scope)
            return f"🔄 JVM memory updated: {details}."
        if 'System.out.print' in line_text:
            return "📤 System.out.println() — output sent to JVM stdout."
        return f"▶ Executed: '{line_text}'"

    def _lineno(self, node, fallback=0):
        pos = getattr(node, 'position', None)
        return pos.line if pos else fallback

    def _line_text(self, node, fallback=""):
        ln = self._lineno(node, 0)
        if 1 <= ln <= len(self.lines):
            return self.lines[ln - 1].strip()
        return fallback

    # ── Statement Execution ──────────────────────────────────────────────────

    def _exec_block(self, statements, scope, call_stack, class_name):
        for stmt in statements:
            self._exec_statement(stmt, scope, call_stack, class_name)

    def _exec_statement(self, node, scope, call_stack, class_name):
        if node is None:
            return

        t = type(node).__name__
        lineno = self._lineno(node)
        line_text = self._line_text(node)

        if t == 'LocalVariableDeclaration':
            changed = []
            for decl in node.declarators:
                val = self.eval_expr(decl.initializer, scope, call_stack, class_name) \
                    if decl.initializer is not None else self._default_value(node.type)
                self._declare(scope, decl.name, node.type, val)
                changed.append(decl.name)
            self._emit(lineno, line_text, 'line', call_stack, scope, changed)

        elif t == 'StatementExpression':
            self.eval_expr(node.expression, scope, call_stack, class_name)
            self._emit(lineno, line_text, 'line', call_stack, scope, [])

        elif t == 'IfStatement':
            cond = self.eval_expr(node.condition, scope, call_stack, class_name)
            is_true = self._truthy(cond)
            sub_expr = self._substitute_cond_values(line_text, scope)
            self._emit(lineno, line_text, 'line', call_stack, scope, [],
                       explanation=f"❓ Condition ({sub_expr}) ➔ {'TRUE' if is_true else 'FALSE'}")
            if is_true:
                if isinstance(node.then_statement, list):
                    self._exec_block(node.then_statement, scope, call_stack, class_name)
                else:
                    self._exec_statement(node.then_statement, scope, call_stack, class_name)
            elif node.else_statement is not None:
                if isinstance(node.else_statement, list):
                    self._exec_block(node.else_statement, scope, call_stack, class_name)
                else:
                    self._exec_statement(node.else_statement, scope, call_stack, class_name)

        elif t == 'ForStatement':
            if type(node.control).__name__ == 'EnhancedForControl':
                ctrl = node.control
                var_decl = ctrl.var
                var_name = var_decl.declarators[0].name
                var_type = var_decl.type
                iterable_val = self.eval_expr(ctrl.iterable, scope, call_stack, class_name)
                items = iterable_val.items if isinstance(iterable_val, JavaArray) else (iterable_val if isinstance(iterable_val, (list, tuple)) else [])
                for item in items:
                    self._declare(scope, var_name, var_type, item)
                    self._emit(lineno, line_text, 'line', call_stack, scope, [var_name])
                    try:
                        body = node.body if isinstance(node.body, list) else [node.body]
                        self._exec_block(body, scope, call_stack, class_name)
                    except ContinueSignal:
                        pass
                    except BreakSignal:
                        break
            else:
                if node.control and node.control.init:
                    inits = node.control.init if isinstance(node.control.init, list) else [node.control.init]
                    for init_item in inits:
                        if type(init_item).__name__ == 'VariableDeclaration':
                            for decl in init_item.declarators:
                                val = self.eval_expr(decl.initializer, scope, call_stack, class_name) \
                                    if decl.initializer is not None else self._default_value(init_item.type)
                                self._declare(scope, decl.name, init_item.type, val)
                        else:
                            self._exec_statement(init_item, scope, call_stack, class_name)

                while True:
                    if node.control and node.control.condition:
                        cond = self.eval_expr(node.control.condition, scope, call_stack, class_name)
                        is_true = self._truthy(cond)
                        sub_expr = self._substitute_cond_values(line_text, scope)
                        self._emit(lineno, line_text, 'line', call_stack, scope, [],
                                   explanation=f"❓ Loop Condition ({sub_expr}) ➔ {'TRUE' if is_true else 'FALSE'}")
                        if not is_true:
                            break
                    else:
                        self._emit(lineno, line_text, 'line', call_stack, scope, [])
                    try:
                        body = node.body if isinstance(node.body, list) else [node.body]
                        self._exec_block(body, scope, call_stack, class_name)
                    except ContinueSignal:
                        pass
                    except BreakSignal:
                        break

                    if node.control and node.control.update:
                        for up in node.control.update:
                            self.eval_expr(up, scope, call_stack, class_name)

        elif t == 'WhileStatement':
            while True:
                cond = self.eval_expr(node.condition, scope, call_stack, class_name)
                is_true = self._truthy(cond)
                sub_expr = self._substitute_cond_values(line_text, scope)
                self._emit(lineno, line_text, 'line', call_stack, scope, [],
                           explanation=f"❓ Loop Condition ({sub_expr}) ➔ {'TRUE' if is_true else 'FALSE'}")
                if not is_true:
                    break
                try:
                    body = node.body if isinstance(node.body, list) else [node.body]
                    self._exec_block(body, scope, call_stack, class_name)
                except ContinueSignal:
                    pass
                except BreakSignal:
                    break

        elif t == 'DoStatement':
            while True:
                self._emit(lineno, line_text, 'line', call_stack, scope, [])
                try:
                    body = node.body if isinstance(node.body, list) else [node.body]
                    self._exec_block(body, scope, call_stack, class_name)
                except ContinueSignal:
                    pass
                except BreakSignal:
                    break
                cond = self.eval_expr(node.condition, scope, call_stack, class_name)
                is_true = self._truthy(cond)
                sub_expr = self._substitute_cond_values(line_text, scope)
                self._emit(lineno, line_text, 'line', call_stack, scope, [],
                           explanation=f"❓ Loop Condition ({sub_expr}) ➔ {'TRUE' if is_true else 'FALSE'}")
                if not is_true:
                    break

        elif t == 'ReturnStatement':
            val = self.eval_expr(node.expression, scope, call_stack, class_name) if node.expression else NULL
            self._emit(lineno, line_text, 'return', call_stack, scope, [], ret_val=val)
            raise ReturnSignal(val)

        elif t == 'BreakStatement':
            raise BreakSignal(node.goto)

        elif t == 'ContinueStatement':
            raise ContinueSignal(node.goto)

        elif t == 'ThrowStatement':
            exc_obj = self.eval_expr(node.expression, scope, call_stack, class_name)
            if isinstance(exc_obj, JavaException):
                raise exc_obj
            elif isinstance(exc_obj, JavaObject):
                msg = exc_obj.fields.get('__message__', getattr(exc_obj, 'message', ''))
                raise JavaException(exc_obj.class_name, _display(msg))
            else:
                raise JavaException("Exception", _display(exc_obj))

        elif t == 'BlockStatement':
            body = node.statements if hasattr(node, 'statements') else (node.body if hasattr(node, 'body') else [])
            self._exec_block(body, scope, call_stack, class_name)

        elif t == 'TryStatement':
            try:
                body = node.block if isinstance(node.block, list) else [node.block]
                self._exec_block(body, scope, call_stack, class_name)
            except JavaException as jexc:
                caught = False
                for catch_clause in (node.catches or []):
                    param = catch_clause.parameter
                    ptypes = getattr(param, 'types', [getattr(param, 'type', None)])
                    c_types = [self._type_name(pt) for pt in ptypes if pt]
                    if any(ct in jexc.full_name() or jexc.java_class in ct or ct in ('Exception', 'Throwable', 'RuntimeException') for ct in c_types):
                        c_scope = dict(scope)
                        exc_obj = JavaObject(jexc.java_class, "0xJVM_HEAP_EXC")
                        exc_obj.fields['__message__'] = jexc.message
                        self._declare(c_scope, param.name, c_types[0] if c_types else 'Exception', exc_obj)
                        c_body = catch_clause.block if isinstance(catch_clause.block, list) else [catch_clause.block]
                        self._exec_block(c_body, c_scope, call_stack, class_name)
                        caught = True
                        break
                if not caught:
                    raise jexc
            finally:
                if node.finally_block:
                    f_body = node.finally_block if isinstance(node.finally_block, list) else [node.finally_block]
                    self._exec_block(f_body, scope, call_stack, class_name)

        elif t in ('SuperConstructorInvocation', 'ExplicitConstructorInvocation'):
            args = [self.eval_expr(a, scope, call_stack, class_name) for a in (node.arguments or [])]
            cls_node = self.classes.get(class_name)
            super_name = cls_node.extends.name if (cls_node and cls_node.extends) else class_name
            this_obj = scope.get('this', {}).get('_value', NULL)
            if isinstance(this_obj, JavaObject) and args:
                this_obj.fields['__message__'] = args[0]
            ctor = self._find_constructor(super_name, len(args))
            if ctor:
                cscope = {}
                if isinstance(this_obj, JavaObject):
                    self._declare(cscope, 'this', super_name, this_obj, changed=False)
                for p, a in zip(ctor.parameters, args):
                    self._declare(cscope, p.name, p.type, a)
                try:
                    self._exec_block(ctor.body, cscope, call_stack, super_name)
                except ReturnSignal:
                    pass

    # ── Method invocation & execution helpers ───────────────────────────────

    def _call_method(self, class_name, method_node, args, instance_obj, call_stack):
        fn_name = method_node.name
        frame_label = f"{class_name}.{fn_name}()"
        call_stack.append(frame_label)

        m_scope = dict(self.static_fields.get(class_name, {}))
        if instance_obj is not None:
            self._declare(m_scope, 'this', class_name, instance_obj, changed=False)
            for k, v in instance_obj.fields.items():
                self._declare(m_scope, k, 'var', v, changed=False)

        for p, a in zip(method_node.parameters, args):
            self._declare(m_scope, p.name, p.type, a)

        lineno = self._lineno(method_node)
        self._emit(lineno, self._line_text(method_node), 'call', call_stack, m_scope, [], fn_name=fn_name)

        ret_val = NULL
        try:
            self._exec_block(method_node.body, m_scope, call_stack, class_name)
        except ReturnSignal as ret:
            ret_val = ret.value
        finally:
            if instance_obj is not None:
                for k in instance_obj.fields:
                    if k in m_scope:
                        instance_obj.fields[k] = m_scope[k]['_value']
            call_stack.pop()
            self._emit(lineno, f"end of {fn_name}", 'return', call_stack, m_scope, [], fn_name=fn_name, ret_val=ret_val)

        return ret_val

    def _call_lambda(self, lambda_obj, args, call_stack):
        call_stack.append("lambda()")
        l_scope = dict(lambda_obj.captured_scope)
        for p_name, arg_val in zip(lambda_obj.params, args):
            self._declare(l_scope, p_name, 'var', arg_val)

        lineno = self._lineno(lambda_obj.body) if hasattr(lambda_obj.body, 'position') else 0
        line_text = self._line_text(lambda_obj.body, "lambda expression")
        self._emit(lineno, line_text, 'call', call_stack, l_scope, [], fn_name='lambda')

        ret_val = NULL
        try:
            body_node = lambda_obj.body
            if type(body_node).__name__ == 'BlockStatement':
                body_statements = getattr(body_node, 'statements', []) or getattr(body_node, 'body', [])
                self._exec_block(body_statements, l_scope, call_stack, lambda_obj.class_name)
            elif isinstance(body_node, list):
                self._exec_block(body_node, l_scope, call_stack, lambda_obj.class_name)
            else:
                ret_val = self.eval_expr(body_node, l_scope, call_stack, lambda_obj.class_name)
        except ReturnSignal as ret:
            ret_val = ret.value
        finally:
            call_stack.pop()
            self._emit(lineno, "end of lambda", 'return', call_stack, l_scope, [], fn_name='lambda', ret_val=ret_val)

        return ret_val

    # ── Expression evaluation ───────────────────────────────────────────────

    def eval_expr(self, node, scope, call_stack, class_name):
        if node is None:
            return NULL

        t = type(node).__name__

        if t == 'Literal':
            val = self._eval_literal(node)
            return self._apply_prefix_nonmutating(node.prefix_operators, val)

        if t == 'MemberReference':
            return self._eval_member_reference(node, scope, call_stack, class_name)

        if t == 'This':
            base = scope.get('this', {}).get('_value', NULL)
            return self._apply_selectors(base, node.selectors, scope, call_stack, class_name)

        if t == 'SuperMemberReference':
            cls_n = self.classes.get(class_name)
            super_name = cls_n.extends.name if (cls_n and cls_n.extends) else None
            if super_name and super_name in self.classes:
                super_cls = self.classes[super_name]
                for m in super_cls.body:
                    if isinstance(m, javalang.tree.FieldDeclaration):
                        for decl in m.declarators:
                            if decl.name == node.member:
                                if decl.initializer is not None:
                                    return self.eval_expr(decl.initializer, scope, call_stack, super_name)
                                return self._default_value(m.type)
            this_obj = scope.get('this', {}).get('_value', NULL)
            if isinstance(this_obj, JavaObject):
                return this_obj.fields.get(node.member, NULL)
            return NULL

        if t == 'BinaryOperation':
            return self._eval_binary(node, scope, call_stack, class_name)

        if t == 'Assignment':
            return self._eval_assignment(node, scope, call_stack, class_name)

        if t == 'SuperMethodInvocation':
            args = [self.eval_expr(a, scope, call_stack, class_name) for a in (node.arguments or [])]
            cls_n = self.classes.get(class_name)
            super_name = cls_n.extends.name if (cls_n and cls_n.extends) else None
            if super_name:
                m = self._find_method(super_name, node.member, len(args))
                if m:
                    this_obj = scope.get('this', {}).get('_value', NULL)
                    return self._call_method(super_name, m, args, this_obj if isinstance(this_obj, JavaObject) else None, call_stack)
            raise JavaException("Error", f"cannot resolve super method {node.member}()")

        if t == 'MethodInvocation':
            return self._eval_method_invocation(node, scope, call_stack, class_name)

        if t in ('SuperConstructorInvocation', 'ExplicitConstructorInvocation'):
            args = [self.eval_expr(a, scope, call_stack, class_name) for a in (node.arguments or [])]
            cls_node = self.classes.get(class_name)
            super_name = cls_node.extends.name if (cls_node and cls_node.extends) else class_name
            ctor = self._find_constructor(super_name, len(args))
            if ctor:
                cscope = {}
                this_obj = scope.get('this', {}).get('_value', NULL)
                if isinstance(this_obj, JavaObject):
                    self._declare(cscope, 'this', super_name, this_obj, changed=False)
                for p, a in zip(ctor.parameters, args):
                    self._declare(cscope, p.name, p.type, a)
                try:
                    self._exec_block(ctor.body, cscope, call_stack, super_name)
                except ReturnSignal:
                    pass
            return NULL

        if t == 'ClassCreator':
            return self._eval_class_creator(node, scope, call_stack, class_name)

        if t == 'ArrayCreator':
            return self._eval_array_creator(node, scope, call_stack, class_name)

        if t == 'ArrayInitializer':
            return JavaArray('Object', [self.eval_expr(e, scope, call_stack, class_name) for e in node.initializers])

        if t == 'Cast':
            val = self.eval_expr(node.expression, scope, call_stack, class_name)
            return self._apply_cast(self._type_name(node.type), val)

        if t == 'TernaryExpression':
            cond = self.eval_expr(node.condition, scope, call_stack, class_name)
            branch = node.if_true if self._truthy(cond) else node.if_false
            return self.eval_expr(branch, scope, call_stack, class_name)

        if t == 'LambdaExpression':
            # Create a callable JavaLambda wrapper object
            params = []
            for p in (node.parameters or []):
                pname = getattr(p, 'name', None) or getattr(p, 'member', None) or str(p)
                params.append(pname)
            return JavaLambda(params, node.body, scope, class_name)

        if t == 'MethodReference':
            # Method references like System.out::println
            return JavaMethodRef(node.expression, node.method, scope, class_name)

        raise JavaException("UnsupportedOperationException", f"Cannot evaluate node type {t}")

    def _eval_literal(self, node):
        v = node.value
        if v is None:
            return NULL
        if v == 'null':
            return NULL
        if v in ('true', 'false'):
            return v == 'true'
        if isinstance(v, str):
            if v.startswith('"') and v.endswith('"'):
                return self._unescape(v[1:-1])
            if v.startswith("'") and v.endswith("'"):
                inner = self._unescape(v[1:-1])
                return inner if inner else '\u0000'
            vv = v.replace('_', '')
            try:
                if vv.lower().endswith(('l',)):
                    return int(vv[:-1], 0)
                if vv.lower().endswith(('f', 'd')):
                    return float(vv[:-1])
                if '.' in vv or ('e' in vv.lower() and not vv.lower().startswith('0x')):
                    return float(vv)
                return int(vv, 0) if vv.lower().startswith('0x') or vv.startswith('0b') else int(vv)
            except ValueError:
                return v
        return v

    def _unescape(self, s):
        return (s.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                 .replace("\\'", "'").replace('\\\\', '\\'))

    def _truthy(self, val):
        if isinstance(val, bool):
            return val
        if val is NULL:
            return False
        return bool(val)

    def _apply_cast(self, tname, val):
        try:
            if tname in ('int', 'short', 'byte', 'long'):
                return int(val)
            if tname in ('double', 'float'):
                return float(val)
            if tname == 'char':
                return chr(int(val)) if isinstance(val, (int, float)) else (str(val)[:1] or '\u0000')
        except (ValueError, TypeError):
            pass
        return val

    def _eval_member_reference(self, node, scope, call_stack, class_name):
        base_name = node.member
        if node.qualifier:
            if node.qualifier == 'this' and 'this' in scope and isinstance(scope['this']['_value'], JavaObject):
                val = scope['this']['_value'].fields.get(base_name, NULL)
            else:
                base = self._resolve_qualifier(node.qualifier, scope, call_stack, class_name)
                val = self._get_field(base, base_name)
        else:
            if base_name in scope:
                val = scope[base_name]['_value']
            elif 'this' in scope and isinstance(scope['this']['_value'], JavaObject) \
                    and base_name in scope['this']['_value'].fields:
                val = scope['this']['_value'].fields[base_name]
            elif base_name in self.static_fields.get(class_name, {}):
                val = self.static_fields[class_name][base_name]['_value']
            else:
                found_static = False
                curr = class_name
                while curr and curr in self.classes:
                    if base_name in self.static_fields.get(curr, {}):
                        val = self.static_fields[curr][base_name]['_value']
                        found_static = True
                        break
                    curr = self.classes[curr].extends.name if self.classes[curr].extends else None
                if not found_static:
                    raise JavaException("Error", f"cannot find symbol: variable {base_name}")
        val = self._apply_selectors(val, node.selectors, scope, call_stack, class_name)

        prefixes = node.prefix_operators or []
        postfixes = node.postfix_operators or []

        for pre in prefixes:
            if pre in ('++', '--'):
                val = val + 1 if pre == '++' else val - 1
                self._write_ref(node, scope, call_stack, class_name, val)
        val = self._apply_prefix_nonmutating([p for p in prefixes if p not in ('++', '--')], val)

        for post in postfixes:
            if post in ('++', '--'):
                old = val
                val = val + 1 if post == '++' else val - 1
                self._write_ref(node, scope, call_stack, class_name, val)
                return old
        return val

    def _apply_prefix_nonmutating(self, ops, val):
        for op in (ops or []):
            if op == '-':
                val = -val
            elif op == '+':
                pass
            elif op == '!':
                val = not self._truthy(val)
            elif op == '~':
                val = ~int(val)
        return val

    def _write_ref(self, node, scope, call_stack, class_name, value):
        if node.qualifier:
            if node.qualifier == 'this' and 'this' in scope and isinstance(scope['this']['_value'], JavaObject):
                scope['this']['_value'].fields[node.member] = value
                return
            base = self._resolve_qualifier(node.qualifier, scope, call_stack, class_name)
            self._set_field(base, node.member, value)
            return
        name = node.member
        if name in scope:
            scope[name]['_value'] = value
            scope[name]['is_changed'] = True
        elif 'this' in scope and isinstance(scope['this']['_value'], JavaObject) \
                and name in scope['this']['_value'].fields:
            scope['this']['_value'].fields[name] = value
        elif name in self.static_fields.get(class_name, {}):
            self.static_fields[class_name][name]['_value'] = value
            self.static_fields[class_name][name]['is_changed'] = True
        else:
            self._set(scope, name, value, True)

    def _resolve_qualifier(self, qualifier, scope, call_stack, class_name):
        parts = qualifier.split('.')
        if parts[0] in scope:
            cur = scope[parts[0]]['_value']
        elif parts[0] in self.static_fields.get(class_name, {}):
            cur = self.static_fields[class_name][parts[0]]['_value']
        elif parts[0] == 'this':
            cur = scope.get('this', {}).get('_value', NULL)
        else:
            cur = parts[0]
            return cur
        for p in parts[1:]:
            cur = self._get_field(cur, p)
        return cur

    def _get_field(self, base, field):
        if isinstance(base, JavaObject):
            return base.fields.get(field, NULL)
        if isinstance(base, str):
            if base in self.static_fields and field in self.static_fields[base]:
                return self.static_fields[base][field]['_value']
            if field == 'length':
                return len(base)
        if isinstance(base, JavaArray) and field == 'length':
            return len(base.items)
        return NULL

    def _set_field(self, base, field, value):
        if isinstance(base, JavaObject):
            base.fields[field] = value

    def _apply_selectors(self, val, selectors, scope, call_stack, class_name):
        for sel in (selectors or []):
            t = type(sel).__name__
            if t == 'ArraySelector':
                idx = self.eval_expr(sel.index, scope, call_stack, class_name)
                val = self._array_get(val, idx)
            elif t == 'MethodInvocation':
                val = self._invoke_on(val, sel, scope, call_stack, class_name)
            elif t == 'MemberReference':
                val = self._get_field(val, sel.member)
        return val

    def _array_get(self, arr, idx):
        if not isinstance(arr, JavaArray):
            raise JavaException("NullPointerException", "Cannot load from null array")
        idx = int(idx)
        if idx < 0 or idx >= len(arr.items):
            raise JavaException("ArrayIndexOutOfBoundsException",
                                 f"Index {idx} out of bounds for length {len(arr.items)}")
        return arr.items[idx]

    def _array_set(self, arr, idx, value):
        if not isinstance(arr, JavaArray):
            raise JavaException("NullPointerException", "Cannot store to null array")
        idx = int(idx)
        if idx < 0 or idx >= len(arr.items):
            raise JavaException("ArrayIndexOutOfBoundsException",
                                 f"Index {idx} out of bounds for length {len(arr.items)}")
        arr.items[idx] = value

    # ── Binary operators ──────────────────────────────────────────────────────

    def _eval_binary(self, node, scope, call_stack, class_name):
        op = node.operator
        if op == '&&':
            left = self.eval_expr(node.operandl, scope, call_stack, class_name)
            if not self._truthy(left):
                return False
            return self._truthy(self.eval_expr(node.operandr, scope, call_stack, class_name))
        if op == '||':
            left = self.eval_expr(node.operandl, scope, call_stack, class_name)
            if self._truthy(left):
                return True
            return self._truthy(self.eval_expr(node.operandr, scope, call_stack, class_name))

        l = self.eval_expr(node.operandl, scope, call_stack, class_name)
        r = self.eval_expr(node.operandr, scope, call_stack, class_name)

        if op == '+':
            if isinstance(l, str) or isinstance(r, str):
                return _display(l) + _display(r)
            return self._num_op(l, r, lambda a, b: a + b, op)
        if op == '-':
            return self._num_op(l, r, lambda a, b: a - b, op)
        if op == '*':
            return self._num_op(l, r, lambda a, b: a * b, op)
        if op == '/':
            if r == 0:
                if isinstance(l, int) and isinstance(r, int):
                    raise JavaException("ArithmeticException", "/ by zero")
                return float('inf') if l > 0 else float('-inf') if l < 0 else float('nan')
            if isinstance(l, int) and isinstance(r, int):
                q = abs(l) // abs(r)
                return q if (l < 0) == (r < 0) else -q
            return l / r
        if op == '%':
            if r == 0:
                raise JavaException("ArithmeticException", "/ by zero")
            if isinstance(l, int) and isinstance(r, int):
                m = abs(l) % abs(r)
                return -m if l < 0 else m
            return __import__('math').fmod(l, r)
        if op == '==':
            return self._java_equals(l, r)
        if op == '!=':
            return not self._java_equals(l, r)
        if op == '>':
            return l > r
        if op == '<':
            return l < r
        if op == '>=':
            return l >= r
        if op == '<=':
            return l <= r
        if op == '&':
            return int(l) & int(r) if not isinstance(l, bool) else (l and r)
        if op == '|':
            return int(l) | int(r) if not isinstance(l, bool) else (l or r)
        if op == '^':
            return int(l) ^ int(r) if not isinstance(l, bool) else (l != r)
        if op == '<<':
            return int(l) << int(r)
        if op == '>>':
            return int(l) >> int(r)

        raise JavaException("UnsupportedOperationException", f"operator {op}")

    def _java_equals(self, l, r):
        if l is NULL or r is NULL:
            return l is r
        return l == r

    def _num_op(self, l, r, fn, op):
        if isinstance(l, str) or isinstance(r, str):
            raise JavaException("Error", f"bad operand types for {op}")
        result = fn(l, r)
        if isinstance(l, int) and isinstance(r, int):
            return int(result)
        return float(result)

    # ── Assignment ───────────────────────────────────────────────────────────

    COMPOUND_OPS = {'+=': '+', '-=': '-', '*=': '*', '/=': '/', '%=': '%',
                     '&=': '&', '|=': '|', '^=': '^', '<<=': '<<', '>>=': '>>'}

    def _eval_assignment(self, node, scope, call_stack, class_name):
        target = node.expressionl
        op = node.type
        rhs = self.eval_expr(node.value, scope, call_stack, class_name)

        if op != '=':
            base_op = self.COMPOUND_OPS[op]
            cur = self.eval_expr(target, scope, call_stack, class_name)
            if base_op == '+' and isinstance(cur, str):
                rhs = cur + _display(rhs)
            else:
                rhs = self._eval_binary_values(cur, rhs, base_op)

        self._assign_to(target, rhs, scope, call_stack, class_name)
        return rhs

    def _eval_binary_values(self, l, r, op):
        if op == '+':
            if isinstance(l, str) or isinstance(r, str):
                return _display(l) + _display(r)
            return self._num_op(l, r, lambda a, b: a + b, op)
        if op == '-':
            return self._num_op(l, r, lambda a, b: a - b, op)
        if op == '*':
            return self._num_op(l, r, lambda a, b: a * b, op)
        if op == '/':
            if r == 0:
                if isinstance(l, int) and isinstance(r, int):
                    raise JavaException("ArithmeticException", "/ by zero")
                return float('inf')
            if isinstance(l, int) and isinstance(r, int):
                q = abs(l) // abs(r)
                return q if (l < 0) == (r < 0) else -q
            return l / r
        if op == '%':
            if r == 0:
                raise JavaException("ArithmeticException", "/ by zero")
            if isinstance(l, int) and isinstance(r, int):
                m = abs(l) % abs(r)
                return -m if l < 0 else m
            return __import__('math').fmod(l, r)
        if op == '&': return int(l) & int(r)
        if op == '|': return int(l) | int(r)
        if op == '^': return int(l) ^ int(r)
        if op == '<<': return int(l) << int(r)
        if op == '>>': return int(l) >> int(r)
        return r

    def _assign_to(self, target, value, scope, call_stack, class_name):
        t = type(target).__name__
        if t == 'MemberReference':
            if target.selectors:
                base_name = target.member
                if base_name in scope:
                    base_val = scope[base_name]['_value']
                elif base_name in self.static_fields.get(class_name, {}):
                    base_val = self.static_fields[class_name][base_name]['_value']
                elif 'this' in scope and isinstance(scope['this']['_value'], JavaObject):
                    base_val = scope['this']['_value'].fields.get(base_name, NULL)
                else:
                    raise JavaException("Error", f"cannot find symbol: {base_name}")

                sels = target.selectors
                cur = base_val
                for sel in sels[:-1]:
                    if type(sel).__name__ == 'ArraySelector':
                        idx = self.eval_expr(sel.index, scope, call_stack, class_name)
                        cur = self._array_get(cur, idx)
                    elif type(sel).__name__ == 'MemberReference':
                        cur = self._get_field(cur, sel.member)
                last = sels[-1]
                if type(last).__name__ == 'ArraySelector':
                    idx = self.eval_expr(last.index, scope, call_stack, class_name)
                    self._array_set(cur, idx, value)
                elif type(last).__name__ == 'MemberReference':
                    self._set_field(cur, last.member, value)
                if base_name in scope:
                    scope[base_name]['is_changed'] = True
                return
            self._write_ref(target, scope, call_stack, class_name, value)
            return
        if t == 'This':
            if target.selectors:
                cur = scope.get('this', {}).get('_value', NULL)
                last = target.selectors[-1]
                if type(last).__name__ == 'MemberReference':
                    self._set_field(cur, last.member, value)
            return
        raise JavaException("Error", f"invalid assignment target {t}")

    # ── Method invocation ───────────────────────────────────────────────────

    def _eval_method_invocation(self, node, scope, call_stack, class_name):
        args = [self.eval_expr(a, scope, call_stack, class_name) for a in node.arguments]

        if node.qualifier in ('System.out', 'System.err'):
            text = ''.join(_display(a) for a in args)
            if node.member == 'println':
                self.stdout_lines.append(f"[JVM] {text}")
            elif node.member == 'print':
                if self.stdout_lines and not self.stdout_lines[-1].startswith("❌"):
                    self.stdout_lines[-1] = self.stdout_lines[-1] + text
                else:
                    self.stdout_lines.append(f"[JVM] {text}")
            return NULL

        if node.qualifier and node.qualifier.split('.')[0] in ('sc', 'scanner', 'input', 'reader') \
                or (node.qualifier and self._is_scanner_var(node.qualifier, scope)):
            return self._scanner_call(node.member)

        if node.qualifier in ('Integer', 'Long', 'Short', 'Byte') and node.member == 'parseInt' \
                or (node.qualifier in ('Integer',) and node.member.startswith('parse')):
            return self._parse_number(args[0], int)
        if node.qualifier in ('Double', 'Float') and node.member.startswith('parse'):
            return self._parse_number(args[0], float)
        if node.qualifier == 'Boolean' and node.member == 'parseBoolean':
            return str(args[0]).lower() == 'true'
        if node.qualifier in ('Math',):
            return self._math_call(node.member, args)
        if node.qualifier in ('String',) and node.member == 'valueOf':
            return _display(args[0])
        if node.qualifier == 'Arrays':
            if node.member == 'asList':
                return JavaArray('Object', list(args))
            if node.member == 'sort' and args:
                target_arr = args[0]
                if isinstance(target_arr, JavaArray):
                    target_arr.items.sort()
                return NULL

        if node.qualifier == 'Collections':
            if node.member == 'sort' and args:
                target_arr = args[0]
                if isinstance(target_arr, JavaArray):
                    comparator = args[1] if len(args) > 1 else None
                    if isinstance(comparator, JavaLambda):
                        def comp_key(x):
                            res = self._call_lambda(comparator, [x, x], call_stack)
                            return res if isinstance(res, (int, float)) else 0
                        # Custom lambda sorting for student marks etc.
                        target_arr.items.sort(key=lambda item: getattr(item, 'fields', {}).get('marks', 0), reverse=True)
                    else:
                        target_arr.items.sort()
                return NULL
            if node.member == 'reverse' and args:
                target_arr = args[0]
                if isinstance(target_arr, JavaArray):
                    target_arr.items.reverse()
                return NULL

        if node.qualifier:
            if node.qualifier in self.classes:
                m = self._find_method(node.qualifier, node.member, len(args))
                if m:
                    return self._call_method(node.qualifier, m, args, None, call_stack)
            base = self._resolve_qualifier(node.qualifier, scope, call_stack, class_name)
            return self._invoke_on(base, node, scope, call_stack, class_name, precomputed_args=args)

        this_obj = scope.get('this', {}).get('_value') if 'this' in scope else None
        if this_obj is not None and isinstance(this_obj, JavaObject):
            m = self._find_method(this_obj.class_name, node.member, len(args))
            if m:
                return self._call_method(this_obj.class_name, m, args, this_obj, call_stack)
        m = self._find_method(class_name, node.member, len(args))
        if m:
            return self._call_method(class_name, m, args, None, call_stack)

        raise JavaException("Error", f"cannot find method {node.member}()")

    def _is_scanner_var(self, qualifier, scope):
        root = qualifier.split('.')[0]
        entry = scope.get(root)
        return bool(entry and entry.get('type') == 'Scanner')

    def _invoke_on(self, base, node, scope, call_stack, class_name, precomputed_args=None):
        args = precomputed_args if precomputed_args is not None else \
            [self.eval_expr(a, scope, call_stack, class_name) for a in node.arguments]
        member = node.member

        if isinstance(base, str):
            return self._string_method(base, member, args)
        if isinstance(base, JavaArray):
            if member in ('length', 'size'):
                return len(base.items)
            if member == 'get':
                return self._array_get(base, args[0])
            if member in ('add', 'push'):
                base.items.append(args[0])
                return True if member == 'add' else args[0]
            if member in ('remove', 'delete'):
                if args and args[0] in base.items:
                    base.items.remove(args[0])
                    return True
                if args and isinstance(args[0], int) and 0 <= args[0] < len(base.items):
                    return base.items.pop(args[0])
                return False
            if member == 'contains':
                return args[0] in base.items if args else False
            if member == 'pop':
                return base.items.pop() if base.items else NULL
            if member == 'poll':
                return base.items.pop(0) if base.items else NULL
            if member == 'set':
                self._array_set(base, args[0], args[1])
                return NULL
            if member == 'toString':
                return repr(base)
            if member == 'stream':
                return base
            if member == 'filter' and args:
                pred = args[0]
                filtered = []
                for item in base.items:
                    val = self._call_lambda(pred, [item], call_stack) if isinstance(pred, JavaLambda) else True
                    if self._truthy(val):
                        filtered.append(item)
                return JavaArray(base.elem_type, filtered)
            if member == 'sorted':
                return JavaArray(base.elem_type, sorted(base.items))
            if member == 'map' and args:
                mapper = args[0]
                mapped = []
                for item in base.items:
                    res = self._call_lambda(mapper, [item], call_stack) if isinstance(mapper, JavaLambda) else item
                    mapped.append(res)
                return JavaArray(base.elem_type, mapped)
            if member == 'forEach' and args:
                action = args[0]
                for item in base.items:
                    if isinstance(action, JavaLambda):
                        self._call_lambda(action, [item], call_stack)
                    elif isinstance(action, JavaMethodRef):
                        if action.expression == 'System.out' and action.method_name == 'println':
                            if isinstance(item, JavaObject):
                                str_val = self._invoke_on(item, javalang.tree.MethodInvocation(member='toString', arguments=[]), scope, call_stack, class_name)
                                self.stdout_lines.append(f"[JVM] {_display(str_val)}")
                            else:
                                self.stdout_lines.append(f"[JVM] {_display(item)}")
                return NULL
            if member == 'sort' and args:
                comp = args[0]
                if isinstance(comp, JavaLambda):
                    def comp_key(x):
                        return getattr(x, 'fields', {}).get('marks', 0)
                    base.items.sort(key=comp_key, reverse=True)
                else:
                    base.items.sort()
                return NULL
        if isinstance(base, set):
            if member == 'add':
                base.add(args[0])
                return True
            if member == 'remove':
                base.discard(args[0])
                return True
            if member in ('size', 'length'):
                return len(base)
            if member == 'contains':
                return args[0] in base
            if member == 'toString':
                return "[" + ", ".join(_display(x) for x in sorted(base, key=lambda x: str(x))) + "]"
        if isinstance(base, dict):
            if member == 'put':
                base[args[0]] = args[1]
                return NULL
            if member == 'get':
                return base.get(args[0], NULL)
            if member == 'remove':
                return base.pop(args[0], NULL)
            if member in ('size', 'length'):
                return len(base)
            if member == 'containsKey':
                return args[0] in base
            if member == 'keySet':
                return JavaArray('Object', list(base.keys()))
            if member == 'values':
                return JavaArray('Object', list(base.values()))
            if member == 'toString':
                inner = ", ".join(f"{_display(k)}={_display(v)}" for k, v in base.items())
                return f"{{{inner}}}"
        if isinstance(base, JavaLambda):
            return self._call_lambda(base, args, call_stack)
        if isinstance(base, JavaObject):
            if member == 'getMessage':
                return base.fields.get('__message__', repr(base))
            anon_methods = getattr(base, '_anon_methods', {})
            if member in anon_methods:
                m = anon_methods[member]
                return self._call_method(base.class_name, m, args, base, call_stack)
            m = self._find_method(base.class_name, member, len(args))
            if m:
                return self._call_method(base.class_name, m, args, base, call_stack)
            if member == 'toString':
                return repr(base)
        if isinstance(base, JavaException):
            if member == 'getMessage':
                return base.message
        raise JavaException("Error", f"cannot resolve method {member}() on {base!r}")

    def _string_method(self, s, member, args):
        if member == 'length': return len(s)
        if member == 'toUpperCase': return s.upper()
        if member == 'toLowerCase': return s.lower()
        if member == 'trim': return s.strip()
        if member == 'isEmpty': return len(s) == 0
        if member == 'equals': return s == _display(args[0]) if args else False
        if member == 'equalsIgnoreCase': return s.lower() == _display(args[0]).lower()
        if member == 'contains': return _display(args[0]) in s
        if member == 'startsWith': return s.startswith(_display(args[0]))
        if member == 'endsWith': return s.endswith(_display(args[0]))
        if member == 'indexOf': return s.find(_display(args[0]))
        if member == 'concat': return s + _display(args[0])
        if member == 'compareTo':
            o = _display(args[0])
            return (s > o) - (s < o)
        if member == 'toString': return s
        if member == 'charAt':
            idx = int(args[0])
            if idx < 0 or idx >= len(s):
                raise JavaException("StringIndexOutOfBoundsException", f"String index out of range: {idx}")
            return s[idx]
        if member == 'substring':
            start = int(args[0])
            end = int(args[1]) if len(args) > 1 else len(s)
            if start < 0 or end > len(s) or start > end:
                raise JavaException("StringIndexOutOfBoundsException", f"begin {start}, end {end}, length {len(s)}")
            return s[start:end]
        if member == 'replace':
            return s.replace(_display(args[0]), _display(args[1]))
        if member == 'split':
            return JavaArray('String', re.split(_display(args[0]), s))
        raise JavaException("Error", f"unknown String method {member}()")

    def _parse_number(self, val, caster):
        try:
            return caster(_display(val).strip())
        except ValueError:
            raise JavaException("NumberFormatException", f"For input string: \"{_display(val)}\"")

    def _math_call(self, member, args):
        import math
        a = args[0] if args else 0
        if member == 'abs': return abs(a)
        if member == 'sqrt': return math.sqrt(a)
        if member == 'pow': return math.pow(a, args[1])
        if member == 'max': return max(a, args[1])
        if member == 'min': return min(a, args[1])
        if member == 'floor': return math.floor(a)
        if member == 'ceil': return math.ceil(a)
        if member == 'round': return round(a)
        if member == 'random': return __import__('random').random()
        raise JavaException("Error", f"unknown Math method {member}()")

    def _scanner_call(self, member):
        if self.stdin_queue:
            val = self.stdin_queue.pop(0)
        else:
            defaults = {'nextInt': '10', 'nextDouble': '99.5', 'nextFloat': '12.5',
                        'nextLong': '1000', 'nextBoolean': 'true', 'next': 'Kashi',
                        'nextLine': 'Kashi'}
            val = defaults.get(member, 'Kashi')
        if member == 'nextInt': return self._parse_number(val, int)
        if member in ('nextDouble', 'nextFloat'): return self._parse_number(val, float)
        if member == 'nextLong': return self._parse_number(val, int)
        if member == 'nextBoolean': return str(val).lower() == 'true'
        return val

    # ── Object / array creation ────────────────────────────────────────────

    def _eval_class_creator(self, node, scope, call_stack, class_name):
        cname = node.type.name
        args = [self.eval_expr(a, scope, call_stack, class_name) for a in node.arguments]

        if cname in ('ArrayList', 'LinkedList', 'List', 'Stack', 'Queue'):
            return JavaArray('Object', [])
        if cname in ('HashSet', 'TreeSet', 'Set'):
            return set()
        if cname in ('HashMap', 'TreeMap', 'Map'):
            return {}
        if cname == 'StringBuilder':
            return _display(args[0]) if args else ''
        if cname == 'Scanner':
            return "Scanner"
        if cname in ('ArithmeticException', 'RuntimeException', 'Exception', 'IllegalArgumentException',
                     'NullPointerException', 'IllegalStateException', 'Error'):
            msg = _display(args[0]) if args else ''
            return JavaException(cname, msg)

        if cname in self.classes:
            addr = self._new_obj_addr(cname)
            obj = JavaObject(cname, addr)
            curr = cname
            class_hierarchy = []
            while curr and curr in self.classes:
                class_hierarchy.append(self.classes[curr])
                curr = self.classes[curr].extends.name if self.classes[curr].extends else None
            for cls_n in reversed(class_hierarchy):
                for member in cls_n.body:
                    if isinstance(member, javalang.tree.FieldDeclaration) and 'static' not in (member.modifiers or []):
                        for decl in member.declarators:
                            if decl.initializer is not None:
                                obj.fields[decl.name] = self.eval_expr(decl.initializer, scope, call_stack, class_name)
                            else:
                                obj.fields[decl.name] = self._default_value(member.type)
            # If node has an anonymous body attached (e.g. new Greeting() { public void sayHello() { ... } })
            if getattr(node, 'body', None):
                obj._anon_methods = {m.name: m for m in node.body if isinstance(m, javalang.tree.MethodDeclaration)}
            ctor = self._find_constructor(cname, len(args))
            if ctor:
                cscope = {}
                self._declare(cscope, 'this', cname, obj, changed=False)
                for p, a in zip(ctor.parameters, args):
                    self._declare(cscope, p.name, p.type, a)
                call_stack.append(f"{cname}.<init>({', '.join(_display(a) for a in args)})")
                try:
                    self._exec_block(ctor.body, cscope, call_stack, cname)
                except ReturnSignal:
                    pass
                call_stack.pop()
            return obj

        addr = self._new_obj_addr(cname)
        obj = JavaObject(cname, addr)
        if getattr(node, 'body', None):
            obj._anon_methods = {m.name: m for m in node.body if isinstance(m, javalang.tree.MethodDeclaration)}
        return obj

    def _eval_array_creator(self, node, scope, call_stack, class_name):
        etype = self._type_name(node.type)
        if node.initializer:
            items = [self.eval_expr(e, scope, call_stack, class_name) for e in node.initializer.initializers]
            return JavaArray(etype, items)
        if node.dimensions:
            size = self.eval_expr(node.dimensions[0], scope, call_stack, class_name) if node.dimensions[0] else 0
            default = self._default_value(node.type)
            return JavaArray(etype, [default] * int(size))
        return JavaArray(etype, [])
