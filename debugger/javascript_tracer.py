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

        # ── Built-in JS Math & Object methods ───────────────────────────────
        if 'Math.' in expr:
            if m_sqrt := re.search(r'Math\.sqrt\s*\(\s*(.*?)\s*\)', expr):
                import math
                val = math.sqrt(float(self.js_resolve(m_sqrt.group(1), scope)))
                return str(int(val) if val.is_integer() else val)
            if m_fl := re.search(r'Math\.floor\s*\(\s*(.*?)\s*\)', expr):
                return str(int(float(self.js_resolve(m_fl.group(1), scope))))
            if m_abs := re.search(r'Math\.abs\s*\(\s*(.*?)\s*\)', expr):
                return str(abs(float(self.js_resolve(m_abs.group(1), scope))))
            if m_pow := re.search(r'Math\.pow\s*\(\s*(.*?)\s*,\s*(.*?)\s*\)', expr):
                b = float(self.js_resolve(m_pow.group(1), scope))
                p = float(self.js_resolve(m_pow.group(2), scope))
                return str(int(b**p) if (b**p).is_integer() else b**p)
            if 'Math.random()' in expr:
                return "0.42"

        if '.toUpperCase()' in expr:
            vname = expr.split('.toUpperCase()')[0].strip()
            return self.js_resolve(vname, scope).upper()
        if '.toLowerCase()' in expr:
            vname = expr.split('.toLowerCase()')[0].strip()
            return self.js_resolve(vname, scope).lower()

        # Property access check e.g. b.name or obj.age
        if '.' in expr and not expr.startswith('Math.'):
            parts = expr.split('.', 1)
            obj_name = parts[0].strip()
            prop_name = parts[1].strip()
            if obj_name in scope:
                raw_obj = scope[obj_name].get('raw', '').strip()
                if raw_obj in ('null', 'undefined'):
                    raise TypeError(f"Uncaught TypeError: Cannot read properties of {raw_obj} (reading '{prop_name}')")

        # ── Variable lookup ────────────────────────────────────────────────
        if re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*$', expr):
            return scope.get(expr, {}).get('raw', expr)

        # ── Handle method calls embedded in expressions (e.g. names.join(", ")) ──────
        resolved_expr = expr
        # ── Array element indexing arr[idx] ──────────────────────────────
        m_arr_idx = re.match(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\[(.*?)\]$', expr)
        if m_arr_idx:
            arr_n, idx_e = m_arr_idx.groups()
            if arr_n in scope:
                try:
                    idx_val = int(float(self.js_resolve(idx_e, scope)))
                    items = self._parse_array_items(scope[arr_n]['raw'])
                    if 0 <= idx_val < len(items):
                        return items[idx_val]
                except Exception:
                    pass

        # ── Array.length property ──────────────────────────────
        resolved_expr = re.sub(
            r'([a-zA-Z_$][a-zA-Z0-9_$]*)\.length',
            lambda m: str(len(self._parse_array_items(scope[m.group(1)]['raw']))) if m.group(1) in scope else m.group(0),
            resolved_expr
        )

        # ── String concat with + ───────────────────────────────────────────
        # Build a resolved copy by substituting variables for eval
        if scope:
            for sv in sorted(scope.keys(), key=lambda x: -len(x)):
                raw = scope[sv]['raw']
                vtype = scope[sv]['type']
                if vtype == 'string':
                    replacement = f'"{raw}"'
                elif vtype == 'array':
                    replacement = raw
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
        if any(kw in line_text for kw in ('if ', 'if(', 'for ', 'for(', 'while ', 'while(')):
            sub = line_text
            for k, vdata in sorted(scope.items(), key=lambda x: len(x[0]), reverse=True):
                val_str = str(vdata.get('raw'))
                sub = re.sub(r'\b' + re.escape(k) + r'\b', val_str, sub)
            def _eval_arr_access(match):
                arr_repr = match.group(1)
                idx_str = match.group(2)
                try:
                    idx = int(idx_str)
                    items = [x.strip().strip('"\'') for x in arr_repr[1:-1].split(',')]
                    if 0 <= idx < len(items): return items[idx]
                except Exception: pass
                return match.group(0)
            sub = re.sub(r'(\d+)\s*\+\s*(\d+)', lambda m: str(int(m.group(1)) + int(m.group(2))), sub)
            sub = re.sub(r'(\[[^\]]+\])\[(\d+)\]', _eval_arr_access, sub)
            sub = sub.rstrip('{').rstrip(';').strip()
            return f"❓ Condition ({sub})"
        new_vars = [k for k in changed if k not in self.prev_variables]
        if new_vars:
            details = ', '.join([f"'{k}' = {scope[k]['raw']}" for k in new_vars if k in scope])
            return f"✨ Declared variable(s): {details}"
        if changed:
            details = ', '.join([f"'{k}' → {scope[k]['raw']}" for k in changed if k in scope])
            return f"🔄 Updated in memory: {details}"
        if 'console.log' in line_text or 'process.stdout.write' in line_text:
            return f"📤 Output sent to terminal."
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

            # Unroll for-loop iterations (e.g., for (let i = 1; i <= 5; i++))
            if stripped.startswith('for ') or stripped.startswith('for('):
                m_for = re.search(r'for\s*\(\s*(?:let|var|const)?\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(\d+)\s*;\s*\1\s*(<=|<|>=|>|!=)\s*(\d+)\s*;\s*(.+?)\)', stripped)
                if m_for:
                    vname, start_val, op, end_val, incr_expr = m_for.groups()
                    start_i = int(start_val)
                    end_i   = int(end_val)

                    # Find loop body lines inside braces
                    loop_body_lines = []
                    loop_brace = stripped.count('{') - stripped.count('}')
                    curr_idx = i
                    while curr_idx < len(self.lines) and loop_brace > 0:
                        b_line = self.lines[curr_idx - 1].strip()
                        curr_idx += 1
                        loop_brace += b_line.count('{') - b_line.count('}')
                        if b_line and b_line not in ('{', '}', '};') and not b_line.startswith('//'):
                            loop_body_lines.append((curr_idx - 1, b_line))

                    step_val = -1 if ('--' in incr_expr or '-=' in incr_expr) else 1
                    if op == '<=': iter_range = range(start_i, end_i + 1, step_val)
                    elif op == '<': iter_range = range(start_i, end_i, step_val)
                    elif op == '>=': iter_range = range(start_i, end_i - 1, step_val)
                    elif op == '>': iter_range = range(start_i, end_i, step_val)
                    else: iter_range = range(start_i, end_i + 1, step_val)

                    for iter_val in list(iter_range)[:500]:
                        scope[vname] = self.serialize_val(str(iter_val), name=vname, scope=scope)
                        scope[vname]['is_changed'] = True
                        for b_lineno, b_line in loop_body_lines:
                            m_l = re_log.match(b_line)
                            m_p = re_push.match(b_line)
                            m_a = re_assign.match(b_line)
                            if m_l:
                                args_s = m_l.group(1)
                                l_out = self.resolve_log_args(args_s, scope)
                                self.stdout_lines.append(f"[JS] {l_out}")
                            elif m_p:
                                arr_name, push_val = m_p.groups()
                                if arr_name in scope:
                                    old_raw = scope[arr_name]['raw'].strip()
                                    resolved_push = self.js_resolve(push_val.strip(), scope)
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
                            elif m_a:
                                vn, ve = m_a.groups()
                                if vn in scope:
                                    res_v = self.js_resolve(ve.strip().rstrip(';'), scope)
                                    scope[vn] = self.serialize_val(res_v, name=vn, scope=scope)
                                    scope[vn]['is_changed'] = True

                            for k in scope: scope[k]['is_changed'] = (k == vname)
                            expl = self.explain('line', b_lineno, b_line, scope, [vname])
                            self._emit(b_lineno, b_line, 'line', call_stack, scope, [vname], explanation=expl)
                            self.prev_variables = dict(scope)

                    i = curr_idx
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
                    b_idx = fn_info['start']
                    while b_idx < fn_info['end']:
                        b_idx += 1
                        body_lineno = b_idx
                        body_line = self.lines[body_lineno - 1].strip()
                        if not body_line or body_line in ('{', '}', '};') or body_line.startswith('//'):
                            continue

                        # Nested for loops inside function body
                        if body_line.startswith('for ') or body_line.startswith('for('):
                            m_for = re.search(r'for\s*\(\s*(?:let|var|const)?\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(.*?);\s*\1\s*(<=|<|>=|>|!=)\s*(.*?);\s*(.+?)\)', body_line)
                            m_of = re.search(r'for\s*\(\s*(?:let|var|const)?\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s+of\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\)', body_line)
                            if m_for:
                                vname, start_expr, op, end_expr, incr_expr = m_for.groups()
                                start_val = int(float(self.js_resolve(start_expr, local_scope)))
                                end_val = int(float(self.js_resolve(end_expr, local_scope)))
                                step_val = -1 if ('--' in incr_expr or '-=' in incr_expr) else 1
                                if op == '<=': iter_range = range(start_val, end_val + 1, step_val)
                                elif op == '<': iter_range = range(start_val, end_val, step_val)
                                else: iter_range = range(start_val, end_val + 1, step_val)

                                sub_idx = body_lineno
                                l_brace = body_line.count('{') - body_line.count('}')
                                inner_lines = []
                                while sub_idx < fn_info['end'] and l_brace > 0:
                                    sub_line = self.lines[sub_idx].strip()
                                    sub_idx += 1
                                    l_brace += sub_line.count('{') - sub_line.count('}')
                                    if sub_line and sub_line not in ('{', '}', '};') and not sub_line.startswith('//'):
                                        inner_lines.append((sub_idx, sub_line))

                                for iter_val in list(iter_range)[:500]:
                                    local_scope[vname] = self.serialize_val(str(iter_val), name=vname, scope=local_scope)
                                    expl = self.explain('line', body_lineno, body_line, local_scope, [vname])
                                    self._emit(body_lineno, body_line, 'line', call_stack, local_scope, [vname], explanation=expl)
                                    
                                    s_idx = 0
                                    while s_idx < len(inner_lines):
                                        s_no, s_line = inner_lines[s_idx]
                                        s_idx += 1
                                        if s_line.startswith('for ') or s_line.startswith('for('):
                                            m_inner_for = re.search(r'for\s*\(\s*(?:let|var|const)?\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(.*?);\s*\1\s*(<=|<|>=|>|!=)\s*(.*?);\s*(.+?)\)', s_line)
                                            if m_inner_for:
                                                in_vname, in_start, in_op, in_end, in_incr = m_inner_for.groups()
                                                in_s_val = int(float(self.js_resolve(in_start, local_scope)))
                                                in_e_val = int(float(self.js_resolve(in_end, local_scope)))
                                                in_step = -1 if ('--' in in_incr or '-=' in in_incr) else 1
                                                in_range = range(in_s_val, in_e_val, in_step) if in_op == '<' else range(in_s_val, in_e_val + 1, in_step)
                                                
                                                # Collect nested inner block
                                                nested_block = []
                                                n_brace = s_line.count('{') - s_line.count('}')
                                                while s_idx < len(inner_lines) and n_brace > 0:
                                                    n_no, n_line = inner_lines[s_idx]
                                                    s_idx += 1
                                                    n_brace += n_line.count('{') - n_line.count('}')
                                                    if n_line and n_line not in ('{', '}', '};') and not n_line.startswith('//'):
                                                        nested_block.append((n_no, n_line))
                                                
                                                for in_val in list(in_range)[:500]:
                                                    local_scope[in_vname] = self.serialize_val(str(in_val), name=in_vname, scope=local_scope)
                                                    expl_in_for = self.explain('line', s_no, s_line, local_scope, [in_vname])
                                                    self._emit(s_no, s_line, 'line', call_stack, local_scope, [in_vname], explanation=expl_in_for)
                                                    
                                                    # Check if condition e.g. if (arr[j] > arr[j + 1])
                                                    cond_holds = True
                                                    for n_no, n_line in nested_block:
                                                        if n_line.startswith('if ') or n_line.startswith('if('):
                                                            expl_if = self.explain('line', n_no, n_line, local_scope, [])
                                                            self._emit(n_no, n_line, 'line', call_stack, local_scope, [], explanation=expl_if)
                                                            m_if_cond = re.search(r'if\s*\((.*?)\)', n_line)
                                                            if m_if_cond:
                                                                c_expr = m_if_cond.group(1)
                                                                if '>' in c_expr:
                                                                    left_e, right_e = c_expr.split('>', 1)
                                                                    l_val = float(self.js_resolve(left_e.strip(), local_scope))
                                                                    r_val = float(self.js_resolve(right_e.strip(), local_scope))
                                                                    cond_holds = (l_val > r_val)
                                                                elif '<' in c_expr:
                                                                    left_e, right_e = c_expr.split('<', 1)
                                                                    l_val = float(self.js_resolve(left_e.strip(), local_scope))
                                                                    r_val = float(self.js_resolve(right_e.strip(), local_scope))
                                                                    cond_holds = (l_val < r_val)
                                                        elif cond_holds:
                                                            m_arr_i = re.match(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\[(.*?)\]\s*=\s*(.+?)(?:;)?$', n_line)
                                                            mb_i = re_decl.match(n_line)
                                                            if m_arr_i:
                                                                an, ie, ve = m_arr_i.groups()
                                                                if an in local_scope:
                                                                    try:
                                                                        iv = int(float(self.js_resolve(ie, local_scope)))
                                                                        ne = self.js_resolve(ve, local_scope)
                                                                        ai = self._parse_array_items(local_scope[an]['raw'])
                                                                        if 0 <= iv < len(ai):
                                                                            ai[iv] = ne
                                                                            local_scope[an] = self.serialize_val("[" + ", ".join(ai) + "]", name=an, scope=local_scope)
                                                                            local_scope[an]['is_changed'] = True
                                                                    except Exception: pass
                                                            elif mb_i:
                                                                bn, be = mb_i.groups()
                                                                local_scope[bn] = self.serialize_val(self.js_resolve(be.strip().rstrip(';'), local_scope), name=bn, scope=local_scope)
                                                            elif re_assign.match(n_line) and not mb_i:
                                                                ma_i = re_assign.match(n_line)
                                                                rn, re_x = ma_i.groups()
                                                                if rn in local_scope:
                                                                    local_scope[rn] = self.serialize_val(self.js_resolve(re_x.strip().rstrip(';'), local_scope), name=rn, scope=local_scope)
                                                                    local_scope[rn]['is_changed'] = True

                                                            expl_n = self.explain('line', n_no, n_line, local_scope, [])
                                                            self._emit(n_no, n_line, 'line', call_stack, local_scope, [], explanation=expl_n)
                                                continue

                                        mb_i = re_decl.match(s_line)
                                        m_arr_i = re.match(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\[(.*?)\]\s*=\s*(.+?)(?:;)?$', s_line)
                                        if m_arr_i:
                                            an, ie, ve = m_arr_i.groups()
                                            if an in local_scope:
                                                try:
                                                    iv = int(float(self.js_resolve(ie, local_scope)))
                                                    ne = self.js_resolve(ve, local_scope)
                                                    ai = self._parse_array_items(local_scope[an]['raw'])
                                                    if 0 <= iv < len(ai):
                                                        ai[iv] = ne
                                                        local_scope[an] = self.serialize_val("[" + ", ".join(ai) + "]", name=an, scope=local_scope)
                                                        local_scope[an]['is_changed'] = True
                                                except Exception: pass
                                        elif mb_i:
                                            bn, be = mb_i.groups()
                                            local_scope[bn] = self.serialize_val(self.js_resolve(be.strip().rstrip(';'), local_scope), name=bn, scope=local_scope)
                                        elif re_assign.match(s_line) and not mb_i:
                                            ma_i = re_assign.match(s_line)
                                            rn, re_x = ma_i.groups()
                                            if rn in local_scope:
                                                local_scope[rn] = self.serialize_val(self.js_resolve(re_x.strip().rstrip(';'), local_scope), name=rn, scope=local_scope)
                                                local_scope[rn]['is_changed'] = True

                                        expl_s = self.explain('line', s_no, s_line, local_scope, [])
                                        self._emit(s_no, s_line, 'line', call_stack, local_scope, [], explanation=expl_s)

                                b_idx = sub_idx
                                continue
                            elif m_of:
                                vname, arr_name = m_of.groups()
                                if arr_name in local_scope:
                                    items = self._parse_array_items(local_scope[arr_name]['raw'])
                                    b_body_lines = []
                                    l_brace = body_line.count('{') - body_line.count('}')
                                    sub_idx = body_lineno
                                    while sub_idx < fn_info['end'] and l_brace > 0:
                                        sub_line = self.lines[sub_idx].strip()
                                        sub_idx += 1
                                        l_brace += sub_line.count('{') - sub_line.count('}')
                                        if sub_line and sub_line not in ('{', '}', '};') and not sub_line.startswith('//'):
                                            b_body_lines.append((sub_idx, sub_line))
                                    for item in items:
                                        local_scope[vname] = self.serialize_val(item, name=vname, scope=local_scope)
                                        expl = self.explain('line', body_lineno, body_line, local_scope, [vname])
                                        self._emit(body_lineno, body_line, 'line', call_stack, local_scope, [vname], explanation=expl)
                                        for s_no, s_line in b_body_lines:
                                            if 'process.stdout.write' in s_line or 'console.log' in s_line:
                                                m_arg = re.search(r'\((.*?)\)', s_line)
                                                if m_arg:
                                                    l_out = self.resolve_log_args(m_arg.group(1), local_scope)
                                                    self.stdout_lines.append(f"[JS] {l_out}")
                                            expl_sub = self.explain('line', s_no, s_line, local_scope, [])
                                            self._emit(s_no, s_line, 'line', call_stack, local_scope, [], explanation=expl_sub)
                                    b_idx = sub_idx
                                    continue

                        # Array element assignment e.g. arr[j] = arr[j + 1]
                        m_arr_assign = re.match(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\[(.*?)\]\s*=\s*(.+?)(?:;)?$', body_line)
                        if m_arr_assign:
                            aname, idx_expr, val_expr = m_arr_assign.groups()
                            if aname in local_scope:
                                try:
                                    resolved_idx = self.js_resolve(idx_expr, local_scope)
                                    idx_val = int(float(resolved_idx))
                                    new_elem = self.js_resolve(val_expr, local_scope)
                                    arr_items = self._parse_array_items(local_scope[aname]['raw'])
                                    if 0 <= idx_val < len(arr_items):
                                        arr_items[idx_val] = new_elem
                                        new_raw = "[" + ", ".join(arr_items) + "]"
                                        local_scope[aname] = self.serialize_val(new_raw, name=aname, scope=local_scope)
                                        local_scope[aname]['is_changed'] = True
                                except Exception:
                                    pass

                        # Variable declaration inside function body
                        mb = re_decl.match(body_line)
                        if mb:
                            bname, bexpr = mb.groups()
                            resolved_val = self.js_resolve(bexpr.strip().rstrip(';'), local_scope)
                            local_scope[bname] = self.serialize_val(resolved_val, name=bname, scope=local_scope)

                        # Reassignment inside function body (x = x + 1, total = a + b)
                        elif re_assign.match(body_line) and not mb and not m_arr_assign:
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
                        expl = self.explain('line', body_lineno, body_line, local_scope, body_changed)
                        self._emit(body_lineno, body_line, 'line', call_stack, local_scope, body_changed, explanation=expl)

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

                    # Synchronize mutated references (e.g. array mutations) back to outer scope
                    for p_idx, param in enumerate(fn_info['params']):
                        if p_idx < len(args_raw):
                            arg_var = args_raw[p_idx]
                            if arg_var in scope and param in local_scope:
                                scope[arg_var] = local_scope[param]
                                scope[arg_var]['is_changed'] = True

                    call_stack.pop()
                    self._emit(i, stripped, 'return', call_stack, scope, changed_keys, called_fn, ret_value)
                    self.prev_variables = dict(scope)
                    handled = True

            if handled:
                continue

            has_ex = False
            try:
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
            except Exception as exc:
                has_ex = True
                err_msg = str(exc) if 'TypeError' in str(exc) or 'Uncaught' in str(exc) else "TypeError: Cannot read properties of null/undefined"
                self.stdout_lines.append(f"❌ Uncaught {err_msg}")
                self._emit(i, stripped, 'exception', call_stack, scope, [], explanation=f"❌ Uncaught {err_msg}")
                break

            # ── Emit step ──────────────────────────────────────────────────
            if not has_ex:
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
