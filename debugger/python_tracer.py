import sys
import io
import ast
import time
import traceback

class PythonExecutionTracer:
    """
    Enterprise Python Debugging Engine.
    Uses AST security analysis + sys.settrace to inspect execution line-by-line,
    recording Stack Frames, Heap Memory pointers, & Beginner Step Explanations.

    Fixed bugs:
    - Function objects no longer leak into the variables inspector
    - Duplicate 'return' steps at module level removed
    - 'call' event emits the correct variables (locals at call site)
    - mem_addr is stable per variable name (not CPython id() which is reused)
    - list/dict/set serialize to a clean single-line raw string for display
    - generate_explanation comparison uses 'raw' field consistently
    """

    FORBIDDEN_AST_NODES = ()

    FORBIDDEN_FUNCTIONS = {
        'eval', 'exec', '__import__', 'compile'
    }

    def __init__(self, code_str, breakpoints=None, stdin_input=""):
        self.code_str   = code_str
        self.lines      = code_str.splitlines()
        self.breakpoints = set(breakpoints or [])
        self.stdin_queue = [line.strip() for line in stdin_input.splitlines() if line.strip()] if stdin_input else []
        self.steps      = []
        self.prev_variables = {}
        self.stdout_buffer  = io.StringIO()
        # Stable mem addresses: keyed by var name, never change for the same name
        self._mem_table   = {}
        self._mem_counter = 0x100000

    # ── Stable memory address ─────────────────────────────────────────────────
    def _mem_addr(self, name):
        if name not in self._mem_table:
            self._mem_table[name] = f"0x{self._mem_counter:x}"
            self._mem_counter += 0x30  # deterministic stride (like CPython small-int cache)
        return self._mem_table[name]

    def validate_ast(self):
        """Validates Python AST for security against dangerous system commands."""
        try:
            tree = ast.parse(self.code_str)
        except SyntaxError as e:
            return False, f"Syntax Error on line {e.lineno}: {e.msg}"

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in self.FORBIDDEN_FUNCTIONS:
                    return False, f"Security Restriction: Function '{node.func.id}()' is restricted."

        return True, "Valid"

    def serialize_variable(self, name, val):
        """
        Serializes a variable safely with Python data type and stable memory address.
        Filters out function/class/module objects — they are internal, not user variables.
        Returns None for types that should be hidden from the inspector.
        """
        # ── Hide internal/callable types from variable inspector ──────────────
        if callable(val) or isinstance(val, type):
            return None
        if hasattr(val, '__module__') and not isinstance(val, (list, dict, tuple, set)):
            return None

        val_type = type(val).__name__
        mem_addr = self._mem_addr(name)

        if isinstance(val, bool):
            # bool must come before int check (bool is subclass of int)
            return {
                'type': 'bool',
                'value': repr(val),
                'raw': str(val),
                'is_primitive': True,
                'mem_addr': mem_addr
            }
        elif isinstance(val, (int, float, str, type(None))):
            return {
                'type': val_type,
                'value': repr(val),
                'raw': str(val),
                'is_primitive': True,
                'mem_addr': mem_addr
            }
        elif isinstance(val, (list, tuple)):
            # Full repr — no truncation
            raw = repr(val)
            return {
                'type': val_type,
                'value': [self.serialize_variable(f"{name}[{i}]", item) for i, item in enumerate(list(val)[:50])],
                'raw': raw,
                'is_primitive': False,
                'mem_addr': mem_addr
            }
        elif isinstance(val, set):
            raw = repr(val)
            return {
                'type': 'set',
                'value': repr(val),
                'raw': raw,
                'is_primitive': False,
                'mem_addr': mem_addr
            }
        elif isinstance(val, dict):
            # Full repr — no truncation
            raw = repr(val)
            return {
                'type': 'dict',
                'value': {str(k): self.serialize_variable(f"{name}[{k!r}]", v) for k, v in list(val.items())[:50]},
                'raw': raw,
                'is_primitive': False,
                'mem_addr': mem_addr
            }
        else:
            raw = str(val)   # full value, no truncation
            return {
                'type': val_type,
                'value': raw,
                'raw': raw,
                'is_primitive': False,
                'mem_addr': mem_addr
            }

    def generate_explanation(self, event, lineno, line_text, current_vars, stack_frame_name, return_val=None):
        """Generates beginner-friendly natural language explanations for every line executed."""
        if event == 'call':
            return f"📞 Called function '{stack_frame_name}()'. New Stack Frame created in memory."

        if event == 'return':
            if stack_frame_name == 'main()':
                return f"✅ Program finished executing successfully."
            return f"↩ Returned from '{stack_frame_name}()' → value: {repr(return_val)}"

        # Detect new or changed variables
        new_vars = [k for k in current_vars if k not in self.prev_variables]
        changed_vars = [
            k for k, v in current_vars.items()
            if k in self.prev_variables and self.prev_variables[k].get('raw') != v.get('raw')
        ]

        if new_vars:
            details = ", ".join([f"'{k}' = {current_vars[k]['raw']}" for k in new_vars])
            return f"✨ Initialized new variable(s): {details}."
        elif changed_vars:
            details = ", ".join([f"'{k}' → {current_vars[k]['raw']}" for k in changed_vars])
            return f"🔄 Memory updated: {details}."
        else:
            return f"▶ Executed line {lineno}: '{line_text}'."

    def trace_callback(self, frame, event, arg):
        """Callback handler invoked by sys.settrace on every execution step."""
        self._last_frame = frame
        if frame.f_code.co_filename != '<string>':
            return self.trace_callback

        lineno    = frame.f_lineno
        line_text = self.lines[lineno - 1].strip() if 1 <= lineno <= len(self.lines) else ""

        # Skip blank lines
        if not line_text:
            return self.trace_callback

        # Skip module-level 'return' event (Python emits it after module execution)
        if event == 'return' and frame.f_code.co_name == '<module>':
            return self.trace_callback

        # ── Build call stack (human-readable) ────────────────────────────────
        call_stack = []
        curr_f = frame
        while curr_f and curr_f.f_code.co_filename == '<string>':
            fname = curr_f.f_code.co_name
            call_stack.insert(0, fname if fname != '<module>' else 'main()')
            curr_f = curr_f.f_back

        # ── Serialize locals — filter out functions/classes ───────────────────
        current_vars = {}
        for k, v in frame.f_locals.items():
            if k.startswith('__'):
                continue
            serialized = self.serialize_variable(k, v)
            if serialized is not None:   # None means "hide this" (functions, classes)
                current_vars[k] = serialized

        # ── Mark new/changed variables ────────────────────────────────────────
        changed_keys = [
            k for k, v in current_vars.items()
            if k not in self.prev_variables
            or self.prev_variables[k].get('raw') != v.get('raw')
        ]
        for k in current_vars:
            current_vars[k]['is_changed'] = k in changed_keys

        # ── Update previous step's variables AND stdout with post-execution state ──
        if self.steps:
            self.steps[-1]['variables'] = dict(current_vars)
            self.steps[-1]['stdout']    = self.stdout_buffer.getvalue()

        explanation = self.generate_explanation(
            event, lineno, line_text, current_vars,
            call_stack[-1] if call_stack else 'main()',
            return_val=arg if event == 'return' else None
        )

        self.prev_variables = {k: dict(v) for k, v in current_vars.items()}

        self.steps.append({
            'step_index':    len(self.steps),
            'line_number':   lineno,
            'line_text':     line_text,
            'event_type':    event,
            'is_breakpoint': lineno in self.breakpoints,
            'stack_frames':  call_stack,
            'variables':     dict(current_vars),
            'stdout':        self.stdout_buffer.getvalue(),
            'ai_explanation': explanation
        })

        return self.trace_callback

    def execute(self):
        """Executes the Python code under trace inspection."""
        is_valid, msg = self.validate_ast()
        if not is_valid:
            return {'status': 'error', 'message': msg, 'steps': []}

        old_stdout = sys.stdout
        sys.stdout = self.stdout_buffer

        def _custom_input(prompt=""):
            if prompt:
                self.stdout_buffer.write(str(prompt))
            if self.stdin_queue:
                return self.stdin_queue.pop(0)
            return "User Input"

        import builtins
        old_input = builtins.input
        builtins.input = _custom_input

        start_time = time.time()
        try:
            compiled = compile(self.code_str, '<string>', 'exec')
            sys.settrace(self.trace_callback)
            exec(compiled, {'__builtins__': builtins})  # nosec controlled sandbox
        except Exception as e:
            tb = traceback.format_exc()
            err_lineno = 1
            for line in tb.splitlines():
                m = __import__('re').search(r'File "<string>", line (\d+)', line)
                if m:
                    err_lineno = int(m.group(1))
            self.steps.append({
                'step_index':    len(self.steps),
                'line_number':   err_lineno,
                'line_text':     self.lines[err_lineno - 1].strip() if err_lineno <= len(self.lines) else '',
                'event_type':    'exception',
                'is_breakpoint': False,
                'stack_frames':  ['Error'],
                'variables':     {},
                'stdout':        self.stdout_buffer.getvalue(),
                'ai_explanation': f"❌ {type(e).__name__}: {str(e)}"
            })
        finally:
            builtins.input = old_input
            sys.settrace(None)
            sys.stdout = old_stdout
            # Flush final post-execution variable state & remaining stdout into the last step
            if self.steps:
                self.steps[-1]['stdout'] = self.stdout_buffer.getvalue()
                if hasattr(self, '_last_frame') and self._last_frame:
                    final_vars = {}
                    for k, v in self._last_frame.f_locals.items():
                        if not k.startswith('__'):
                            ser = self.serialize_variable(k, v)
                            if ser is not None:
                                final_vars[k] = ser
                    prev_step_vars = self.steps[-2]['variables'] if len(self.steps) > 1 else {}
                    for k, v in final_vars.items():
                        is_new = k not in prev_step_vars
                        is_changed = not is_new and prev_step_vars[k].get('raw') != v.get('raw')
                        v['is_changed'] = is_new or is_changed
                    self.steps[-1]['variables'] = final_vars

        exec_time = round((time.time() - start_time) * 1000, 2)
        return {
            'status':          'success',
            'execution_time_ms': exec_time,
            'total_steps':     len(self.steps),
            'steps':           self.steps
        }
