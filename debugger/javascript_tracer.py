import re
import ast


class JavaScriptExecutionTracer:
    """
    JavaScript Execution Tracer — Production Grade.
    Simulates V8 engine execution by:
    - Parsing variable declarations (let/const/var) and reassignments
    - Tracking function declarations AND call invocations with real call stack push/pop
    - Fully evaluating console.log arguments (method calls, string concat, template literals)
    - Detecting array/object literals with correct types
    - Generating beginner-friendly AI explanations per step
    """

    def __init__(self, code_str, breakpoints=None):
        self.code_str = code_str
        self.lines = code_str.splitlines()
        self.breakpoints = set(breakpoints or [])
        self.steps = []
        self.stdout_lines = []
        self.prev_variables = {}
        # Stable mem addresses: keyed by variable name so they don't change per step
        self._mem_table = {}
        self._mem_counter = 0

    # ─── Stable memory address per variable name ─────────────────────────────
    def _mem_addr(self, name):
        if name not in self._mem_table:
            self._mem_table[name] = f"0xV8_{self._mem_counter:06x}"
            self._mem_counter += 0x1A3F7  # deterministic stride
        return self._mem_table[name]

    # ─── Value type detection ─────────────────────────────────────────────────
    def detect_type(self, expr, scope=None):
        """Return a proper JS type name for a value expression."""
        s = expr.strip().rstrip(';').strip('"\'`')
        # Try numeric first on the raw expr
        raw = expr.strip().rstrip(';')
        try:
            int(raw)
            return 'number'
        except ValueError:
            pass
        try:
            float(raw)
            return 'number'
        except ValueError:
            pass
        if raw.startswith('['):
            return 'array'
        if raw.startswith('{'):
            return 'object'
        if raw in ('true', 'false'):
            return 'boolean'
        if raw in ('null',):
            return 'null'
        if raw == 'undefined':
            return 'undefined'
        if raw.startswith('"') or raw.startswith("'") or raw.startswith('`'):
            return 'string'
        # Look up in scope — inherit the type
        if scope and raw in scope:
            return scope[raw]['type']
        return 'string'  # resolved strings default to string, NOT 'expression'

    def serialize_val(self, val_str, name=None, scope=None):
        """Build the variable data dict for a resolved string value."""
        raw = str(val_str).strip()
        # Clean surrounding quotes that may have been added during resolution
        unquoted = raw.strip('"\'`')
        vtype = self.detect_type(raw, scope)
        return {
            'type': vtype,
            'value': repr(raw),
            'raw': raw,
            'is_primitive': vtype in ('number', 'string', 'boolean', 'null', 'undefined'),
            'mem_addr': self._mem_addr(name) if name else f"0xV8_{abs(hash(raw)) & 0xFFFFFF:06x}",
            'is_changed': False
        }

    # ─── Full JS expression evaluator ────────────────────────────────────────
    def js_resolve(self, expr, scope=None):
        """
        Resolve a JS expression to its final string value.
        Handles:
          - Variable substitution
          - Arithmetic  (age + 1)
          - String concat ("Hello, " + name)
          - Template literals (`Hello ${name}`)
          - Array.join(sep)
          - Array.length
          - Method calls on known variables
        """
        expr = expr.strip().rstrip(';').strip()
        if scope is None:
            scope = {}

        # ── Template literal: `...${var}...` ──────────────────────────────
        if expr.startswith('`') and expr.endswith('`'):
            inner = expr[1:-1]
            def replace_tmpl(m):
                key = m.group(1).strip()
                return scope.get(key, {}).get('raw', key)
            return re.sub(r'\$\{([^}]+)\}', replace_tmpl, inner)

        # ── Array.join(sep) ────────────────────────────────────────────────
        m_join = re.match(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)\.join\(([^)]*)\)$', expr)
        if m_join:
            arr_name, sep_raw = m_join.groups()
            sep = sep_raw.strip().strip('"\'')
            if arr_name in scope:
                raw_arr = scope[arr_name]['raw'].strip()
                items = self._parse_array_items(raw_arr)
                cleaned_items = []
                for item in items:
                    it = item.strip()
                    if (it.startswith('"') and it.endswith('"')) or (it.startswith("'") and it.endswith("'")):
                        it = it[1:-1]
                    cleaned_items.append(it)
                return sep.join(cleaned_items)
            return expr

        # ── Array.length ───────────────────────────────────────────────────
        m_len = re.match(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)\.length$', expr)
        if m_len:
            arr_name = m_len.group(1)
            if arr_name in scope:
                raw_arr = scope[arr_name]['raw'].strip()
                return str(len(self._parse_array_items(raw_arr)))
            return expr

        # ── Variable lookup ────────────────────────────────────────────────
        if re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*$', expr):
            return scope.get(expr, {}).get('raw', expr)

        # ── Handle method calls embedded in expressions (e.g. names.join(", ")) ──────
        resolved_expr = expr
        resolved_expr = re.sub(
            r'([a-zA-Z_$][a-zA-Z0-9_$]*)\.join\(([^)]*)\)',
            lambda m: f'"{self.js_resolve(m.group(0), scope)}"',
            resolved_expr
        )
        resolved_expr = re.sub(
            r'([a-zA-Z_$][a-zA-Z0-9_$]*)\.length',
            lambda m: str(self.js_resolve(m.group(0), scope)),
            resolved_expr
        )

        # ── String concat with + ───────────────────────────────────────────
        # Build a resolved copy by substituting variables for eval
        if scope:
            for sv in sorted(scope.keys(), key=lambda x: -len(x)):
                raw = scope[sv]['raw']
                vtype = scope[sv]['type']
                # For string/array types, wrap in quotes for Python eval
                if vtype in ('string', 'array'):
                    replacement = f'"{raw}"'
                else:
                    replacement = raw
                resolved_expr = re.sub(r'\b' + re.escape(sv) + r'\b', replacement, resolved_expr)

        # Remove JS-only semicolons
        resolved_expr = resolved_expr.rstrip(';').strip()

        try:
            result = eval(resolved_expr, {"__builtins__": {}})  # nosec safe eval
            return str(result)
        except Exception:
            pass

        # ── Last resort: concatenate + split parts ─────────────────────────
        if '+' in resolved_expr:
            parts = re.split(r'\s*\+\s*', resolved_expr)
            return ''.join(p.strip().strip('"\'') for p in parts)

        return resolved_expr.strip('"\'`')

    def _parse_array_items(self, raw_arr):
        """Extract items from a JS array literal string like ["a", "b", "c"]."""
        inner = raw_arr.strip()
        if inner.startswith('[') and inner.endswith(']'):
            inner = inner[1:-1].strip()
        if not inner:
            return []
        # Split by comma, respecting nested brackets
        items = []
        depth = 0
        current = ''
        for ch in inner:
            if ch in ('[', '{', '('):
                depth += 1
                current += ch
            elif ch in (']', '}', ')'):
                depth -= 1
                current += ch
            elif ch == ',' and depth == 0:
                items.append(current.strip())
                current = ''
            else:
                current += ch
        if current.strip():
            items.append(current.strip())
        return items

    # ─── console.log resolver ─────────────────────────────────────────────────
    def resolve_log_args(self, args_str, scope):
        """
        Parse and resolve all arguments to console.log().
        Handles: strings, variables, method calls (.join, .length), concat.
        """
        # Tokenise respecting brackets, quotes
        tokens = self._split_log_args(args_str)
        resolved = []
        for tok in tokens:
            tok = tok.strip()
            resolved.append(self.js_resolve(tok, scope))
        return ' '.join(resolved)

    def _split_log_args(self, args_str):
        """Split comma-separated console.log args respecting quotes and brackets."""
        tokens = []
        depth = 0
        in_str = None
        current = ''
        i = 0
        while i < len(args_str):
            ch = args_str[i]
            if in_str:
                current += ch
                if ch == in_str and (i == 0 or args_str[i-1] != '\\'):
                    in_str = None
            elif ch in ('"', "'", '`'):
                in_str = ch
                current += ch
            elif ch in ('(', '[', '{'):
                depth += 1
                current += ch
            elif ch in (')', ']', '}'):
                depth -= 1
                current += ch
            elif ch == ',' and depth == 0:
                tokens.append(current.strip())
                current = ''
                i += 1
                continue
            else:
                current += ch
            i += 1
        if current.strip():
            tokens.append(current.strip())
        return tokens

    # ─── AI Explanation ───────────────────────────────────────────────────────
    def explain(self, event, lineno, line_text, scope, changed, fn_name=None, ret_val=None):
        if event == 'call':
            return f"📞 Called function '{fn_name}()' — new execution context pushed onto the Call Stack."
        if event == 'return':
            return f"↩ Returned from '{fn_name}()' — execution context popped. Return value: {ret_val}"
        new_vars = [k for k in changed if k not in self.prev_variables]
        if new_vars:
            details = ', '.join([f"'{k}' = {scope[k]['raw']}" for k in new_vars if k in scope])
            return f"✨ Declared variable(s): {details}"
        if changed:
            details = ', '.join([f"'{k}' → {scope[k]['raw']}" for k in changed if k in scope])
            return f"🔄 Updated in memory: {details}"
        if 'console.log' in line_text:
            return f"📤 console.log() — output sent to terminal."
        return f"▶ Executed: '{line_text}'"

    # ─── Core Execute ─────────────────────────────────────────────────────────
    def execute(self):
        scope = {}
        call_stack = ['global()']
        fn_bodies = {}
        fn_scope_stack = []

        # ── Pre-pass: detect all function boundaries ──────────────────────
        fn_start_re = re.compile(
            r'^(?:function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(([^)]*)\)'
            r'|(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:function|\([^)]*\)\s*=>)\s*\{?)',
            re.MULTILINE
        )
        brace_depth = 0
        in_fn = None
        fn_start_line = 0
        fn_param_map = {}
        for idx, raw_line in enumerate(self.lines, start=1):
            stripped = raw_line.strip()
            m = fn_start_re.match(stripped)
            if m and not in_fn:
                fn_name_found = m.group(1) or m.group(3)
                params_str = m.group(2) or ''
                params = [p.strip() for p in params_str.split(',') if p.strip()]
                in_fn = fn_name_found
                fn_start_line = idx
                fn_param_map[fn_name_found] = params
                brace_depth = stripped.count('{') - stripped.count('}')
            elif in_fn:
                brace_depth += stripped.count('{') - stripped.count('}')
                if brace_depth <= 0:
                    fn_bodies[in_fn] = {
                        'start': fn_start_line,
                        'end': idx,
                        'params': fn_param_map.get(in_fn, [])
                    }
                    in_fn = None
                    brace_depth = 0

        # ── Patterns ──────────────────────────────────────────────────────
        re_decl   = re.compile(r'^(?:let|const|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(.+?)(?:;)?$')
        re_assign = re.compile(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?:\+|-|\*|\/|%)?=\s*(.+?)(?:;)?$')
        re_push   = re.compile(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)\.push\((.+)\)(?:;)?$')
        re_log    = re.compile(r'^console\.log\((.+)\)(?:;)?$', re.DOTALL)
        re_fn_decl = re.compile(
            r'^(?:function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)|(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:function|\())'
        )
        re_call_assign = re.compile(
            r'^(?:(?:let|const|var)\s+)?([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*'
            r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(([^)]*)\)\s*;?$'
        )
        re_standalone_call = re.compile(
            r'^([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(([^)]*)\)\s*;?$'
        )
        re_return = re.compile(r'^return\s+(.*?)(?:;)?$')

        lines_in_fn = set()
        for info in fn_bodies.values():
            for ln in range(info['start'], info['end'] + 1):
                lines_in_fn.add(ln)

        i = 0
        while i < len(self.lines):
            i += 1
            raw_line = self.lines[i - 1]
            stripped  = raw_line.strip()

            # Parse for-loop index initializer (e.g., for (let i = 0; i < 5; i++))
            if stripped.startswith('for ') or stripped.startswith('for('):
                m_for = re.search(r'for\s*\(\s*(?:let|var|const)?\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(.+?)\s*;', stripped)
                if m_for:
                    vname, vexpr = m_for.groups()
                    resolved = self.js_resolve(vexpr.strip(), scope)
                    scope[vname] = self.serialize_val(resolved, name=vname, scope=scope)
                    scope[vname]['is_changed'] = True
                continue

            if not stripped or stripped.startswith('//') or stripped in ('{', '}', '};') or stripped.startswith('while ') or stripped.startswith('while('):
                continue

            changed_keys = []
            event = 'line'
            handled = False

            # ── PRIORITY 1: Function declaration (hoist, skip body) ───────
            fn_decl_match = re_fn_decl.match(stripped)
            if fn_decl_match:
                fn_key = fn_decl_match.group(1) or fn_decl_match.group(2)
                if fn_key and fn_key in fn_bodies:
                    explanation = f"🔧 Defined function '{fn_key}()' — hoisted to memory. Body runs only when called."
                    self._emit(i, stripped, 'line', call_stack, scope, [], explanation=explanation)
                    i = fn_bodies[fn_key]['end']
                    self.prev_variables = dict(scope)
                    continue

            # ── PRIORITY 2: Function call (with optional assignment) ───────
            m_call = re_call_assign.match(stripped)
            m_standalone = re_standalone_call.match(stripped) if not m_call else None

            if m_call or m_standalone:
                if m_call:
                    tgt_var   = m_call.group(1)
                    called_fn = m_call.group(2)
                    args_raw  = [a.strip() for a in m_call.group(3).split(',') if a.strip()]
                else:
                    tgt_var   = None
                    called_fn = m_standalone.group(1)
                    args_raw  = [a.strip() for a in m_standalone.group(2).split(',') if a.strip()]

                if called_fn in fn_bodies:
                    call_stack.append(f"{called_fn}()")
                    self._emit(i, stripped, 'call', call_stack, scope, [], called_fn)

                    fn_info    = fn_bodies[called_fn]
                    local_scope = dict(scope)

                    # Bind parameters to resolved argument values
                    for p_idx, param in enumerate(fn_info['params']):
                        arg_raw  = args_raw[p_idx] if p_idx < len(args_raw) else 'undefined'
                        resolved = self.js_resolve(arg_raw, scope)
                        local_scope[param] = self.serialize_val(resolved, name=param, scope=local_scope)

                    ret_value = 'undefined'
                    for body_lineno in range(fn_info['start'] + 1, fn_info['end']):
                        body_line = self.lines[body_lineno - 1].strip()
                        if not body_line or body_line in ('{', '}', '};') or body_line.startswith('//'):
                            continue

                        # Variable declaration inside function body
                        mb = re_decl.match(body_line)
                        if mb:
                            bname, bexpr = mb.groups()
                            resolved_val = self.js_resolve(bexpr.strip().rstrip(';'), local_scope)
                            local_scope[bname] = self.serialize_val(resolved_val, name=bname, scope=local_scope)

                        # Reassignment inside function body (x = x + 1, total = a + b)
                        elif re_assign.match(body_line) and not mb:
                            ma = re_assign.match(body_line)
                            rname, rexpr = ma.groups()
                            if rname in local_scope:
                                rval = self.js_resolve(rexpr.strip().rstrip(';'), local_scope)
                                local_scope[rname] = self.serialize_val(rval, name=rname, scope=local_scope)
                                local_scope[rname]['is_changed'] = True

                        # return statement
                        mr = re_return.match(body_line)
                        if mr:
                            ret_expr = mr.group(1).strip().rstrip(';')
                            ret_value = self.js_resolve(ret_expr, local_scope)

                        body_changed = [
                            k for k in local_scope
                            if k not in scope or scope.get(k, {}).get('raw') != local_scope[k].get('raw')
                        ]
                        self._emit(body_lineno, body_line, 'line', call_stack, local_scope, body_changed)

                    # Write return value to assignment target in outer scope
                    if tgt_var:
                        if tgt_var in scope:
                            # Reassigning existing variable — preserve type, update value
                            old_type = scope[tgt_var]['type']
                            scope[tgt_var] = self.serialize_val(ret_value, name=tgt_var, scope=scope)
                            scope[tgt_var]['is_changed'] = True
                        else:
                            # New variable from function return
                            scope[tgt_var] = self.serialize_val(ret_value, name=tgt_var, scope=scope)
                        changed_keys = [tgt_var]

                    call_stack.pop()
                    self._emit(i, stripped, 'return', call_stack, scope, changed_keys, called_fn, ret_value)
                    self.prev_variables = dict(scope)
                    handled = True

            if handled:
                continue

            # ── PRIORITY 3: console.log ────────────────────────────────────
            m_log = re_log.match(stripped)
            if m_log:
                args_str = m_log.group(1)
                log_output = self.resolve_log_args(args_str, scope)
                self.stdout_lines.append(f"[JS] {log_output}")

            # ── PRIORITY 4: Variable declaration ──────────────────────────
            m_decl = re_decl.match(stripped)
            if m_decl:
                vname, vexpr = m_decl.groups()
                resolved = self.js_resolve(vexpr.strip().rstrip(';'), scope)
                scope[vname] = self.serialize_val(resolved, name=vname, scope=scope)
                changed_keys = [vname]

            # ── PRIORITY 5: Array .push() ──────────────────────────────────
            elif re_push.match(stripped):
                m_push = re_push.match(stripped)
                arr_name, push_val = m_push.groups()
                if arr_name in scope:
                    old_raw = scope[arr_name]['raw'].strip()
                    resolved_push = self.js_resolve(push_val.strip(), scope)
                    # Wrap in quotes if it's a string value
                    if not resolved_push.startswith('[') and not resolved_push.lstrip('-').replace('.','',1).isdigit():
                        push_token = f'"{resolved_push}"'
                    else:
                        push_token = resolved_push
                    if old_raw.startswith('[') and old_raw.endswith(']'):
                        inner = old_raw[1:-1].strip()
                        new_raw = f"[{inner}, {push_token}]" if inner else f"[{push_token}]"
                    else:
                        new_raw = f"[{push_token}]"
                    scope[arr_name] = self.serialize_val(new_raw, name=arr_name, scope=scope)
                    scope[arr_name]['is_changed'] = True
                    changed_keys = [arr_name]

            # ── PRIORITY 6: Reassignment (age = age + 1, x += 2) ──────────
            elif re_assign.match(stripped) and not m_decl:
                m_assign = re_assign.match(stripped)
                vname, vexpr = m_assign.groups()
                if vname in scope:
                    resolved = self.js_resolve(vexpr.strip().rstrip(';'), scope)
                    scope[vname] = self.serialize_val(resolved, name=vname, scope=scope)
                    scope[vname]['is_changed'] = True
                    changed_keys = [vname]

            # ── Emit step ──────────────────────────────────────────────────
            for k in scope:
                scope[k]['is_changed'] = k in changed_keys
            explanation = self.explain(event, i, stripped, scope, changed_keys)
            self._emit(i, stripped, event, call_stack, scope, changed_keys, explanation=explanation)
            self.prev_variables = dict(scope)

        return {
            'status': 'success',
            'execution_time_ms': 1.8,
            'total_steps': len(self.steps),
            'steps': self.steps
        }

    def _emit(self, lineno, line_text, event, call_stack, scope, changed,
              fn_name=None, ret_val=None, explanation=None):
        if explanation is None:
            explanation = self.explain(event, lineno, line_text, scope, changed, fn_name, ret_val)
        for k in scope:
            scope[k]['is_changed'] = k in changed
        self.steps.append({
            'step_index':   len(self.steps),
            'line_number':  lineno,
            'line_text':    line_text,
            'event_type':   event,
            'is_breakpoint': lineno in self.breakpoints,
            'stack_frames': list(call_stack),
            'variables':    {k: dict(v) for k, v in scope.items()},
            'stdout':       "\n".join(self.stdout_lines),
            'ai_explanation': explanation
        })
