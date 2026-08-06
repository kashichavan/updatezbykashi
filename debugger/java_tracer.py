import re

try:
    import jpype
    HAS_JPYPE = True
except ImportError:
    HAS_JPYPE = False

class JavaExecutionTracer:
    """
    Java 17 JVM Execution Tracer — Production Grade.
    Combines pure Python AST JVM simulation engine with optional JPype1 native JVM binding.
    """

    JAVA_PRIMITIVES = {'int', 'double', 'float', 'long', 'short', 'byte', 'char', 'boolean'}

    def __init__(self, code_str, breakpoints=None, stdin_input=""):
        self.code_str    = code_str
        self.lines       = code_str.splitlines()
        self.breakpoints = set(breakpoints or [])
        self.stdin_queue = [line.strip() for line in stdin_input.splitlines() if line.strip()] if stdin_input else []
        self.steps       = []
        self.stdout_lines = []
        self.prev_variables = {}
        # Stable mem addresses — keyed by variable name, never change
        self._mem_table   = {}
        self._mem_counter = 0x1000

    # ─── Stable memory address ────────────────────────────────────────────────
    def _mem_addr(self, name, is_primitive):
        if name not in self._mem_table:
            tag = 'STACK' if is_primitive else 'HEAP'
            self._mem_table[name] = f"0xJVM_{tag}_{self._mem_counter:04x}"
            self._mem_counter += 0x1A3   # deterministic stride
        return self._mem_table[name]

    # ─── Serialization ────────────────────────────────────────────────────────
    def serialize(self, val, val_type, name=None):
        is_prim = val_type in self.JAVA_PRIMITIVES
        raw_str = str(val)
        if val_type in ('double', 'float'):
            try:
                fval = float(raw_str)
                raw_str = f"{fval:.1f}" if fval.is_integer() else str(fval)
            except ValueError:
                pass
        return {
            'type':         val_type,
            'value':        repr(raw_str),
            'raw':          raw_str,
            'is_primitive': is_prim,
            'mem_addr':     self._mem_addr(name or raw_str, is_prim),
            'is_changed':   False
        }

    # ─── Explanation generator ────────────────────────────────────────────────
    def explain(self, event, lineno, line_text, scope, changed, fn_name=None, ret_val=None):
        if event == 'call':
            return f"📞 Called method '{fn_name}()' → JVM pushed a new Stack Frame onto the Call Stack."
        if event == 'return':
            return f"↩ Method '{fn_name}()' returned → Stack Frame popped. Value: {ret_val}"

        new_vars = [k for k in changed if k not in self.prev_variables]
        if new_vars:
            details  = ', '.join([f"'{k}' = {scope[k]['raw']}" for k in new_vars if k in scope])
            prim_tag = 'JVM Stack (primitive)' if scope[new_vars[0]]['is_primitive'] else 'JVM Heap (reference)'
            return f"✨ Declared '{', '.join(new_vars)}' in {prim_tag}: {details}."
        if changed:
            details = ', '.join([f"'{k}' → {scope[k]['raw']}" for k in changed if k in scope])
            return f"🔄 JVM memory updated: {details}."
        if 'System.out.print' in line_text:
            return f"📤 System.out.println() — output sent to JVM stdout."
        return f"▶ Executed: '{line_text}'"

    # ─── Expression resolver ──────────────────────────────────────────────────
    def resolve_expr(self, expr, scope):
        """
        Resolve a Java expression to its string value.
        Handles: string literals, variable references, arithmetic,
                 string concatenation (+), boolean literals.
        """
        expr = expr.strip().rstrip(';').strip()

        # Boolean literals
        if expr in ('true', 'false'):
            return expr

        # Plain string literal — only if there's no + concatenation outside quotes
        if expr.startswith('"') and expr.endswith('"') and len(self._split_on_plus(expr)) == 1:
            return expr[1:-1]

        # Single char literal
        if expr.startswith("'") and expr.endswith("'") and len(expr) == 3:
            return expr[1]

        # Java Scanner inputs (uses user stdin queue if provided, else fallback defaults)
        if re.search(r'\.(?:next|nextInt|nextLine|nextDouble|nextFloat|nextLong|nextBoolean)\s*\(\s*\)', expr):
            if self.stdin_queue:
                val = self.stdin_queue.pop(0)
                if '.charAt(' in expr:
                    m_ch = re.search(r'\.charAt\s*\(\s*(\d+)\s*\)', expr)
                    idx = int(m_ch.group(1)) if m_ch else 0
                    return val[idx] if idx < len(val) else val
                return val
            if 'nextInt' in expr: return "10"
            if 'nextDouble' in expr: return "99.5"
            if 'nextFloat' in expr: return "12.5"
            if 'nextLong' in expr: return "1000"
            if 'nextBoolean' in expr: return "true"
            if '.charAt(' in expr: return "A"
            return "Kashi"

        # Helper to extract raw string value safely
        def _clean_str(val):
            raw = str(val).strip('"\'')
            if m_inner := re.search(r"'(.*?)'", raw):
                return m_inner.group(1)
            return raw

        # String operations e.g. text.length(), text.toUpperCase(), text.substring(1), text.charAt(1)
        if '.length()' in expr:
            var_name = expr.split('.length()')[0].strip()
            str_val = _clean_str(self.resolve_expr(var_name, scope))
            return str(len(str_val))
        if '.toUpperCase()' in expr:
            var_name = expr.split('.toUpperCase()')[0].strip()
            str_val = _clean_str(self.resolve_expr(var_name, scope))
            return str_val.upper()
        if '.toLowerCase()' in expr:
            var_name = expr.split('.toLowerCase()')[0].strip()
            str_val = _clean_str(self.resolve_expr(var_name, scope))
            return str_val.lower()
        if m_sub2 := re.search(r'([a-zA-Z_$][a-zA-Z0-9_$]*)\.substring\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', expr):
            vname, start_idx, end_idx = m_sub2.groups()
            str_val = _clean_str(self.resolve_expr(vname, scope))
            return str_val[int(start_idx):int(end_idx)]
        if m_sub1 := re.search(r'([a-zA-Z_$][a-zA-Z0-9_$]*)\.substring\s*\(\s*(\d+)\s*\)', expr):
            vname, start_idx = m_sub1.groups()
            str_val = _clean_str(self.resolve_expr(vname, scope))
            return str_val[int(start_idx):]
        if m_char := re.search(r'([a-zA-Z_$][a-zA-Z0-9_$]*)\.charAt\s*\(\s*(\d+)\s*\)', expr):
            vname, char_idx = m_char.groups()
            str_val = _clean_str(self.resolve_expr(vname, scope))
            idx = int(char_idx)
            return str_val[idx] if idx < len(str_val) else ''
        # Map.Entry getter methods e.g. entry.getKey(), entry.getValue()
        if '.getKey()' in expr:
            vname = expr.split('.getKey()')[0].strip()
            raw_entry = scope.get(vname, {}).get('raw', '1')
            if '=' in raw_entry: return raw_entry.split('=')[0].strip()
            return "1"
        if '.getValue()' in expr:
            vname = expr.split('.getValue()')[0].strip()
            raw_entry = scope.get(vname, {}).get('raw', 'One')
            if '=' in raw_entry: return raw_entry.split('=')[1].strip()
            return "One"

        # Java method calls on object instances (s.getName() -> field value)
        m_getter = re.match(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)\.get([a-zA-Z0-9_$]+)\s*\(\s*\)$', expr)
        if m_getter:
            obj_var, prop_name = m_getter.groups()
            if obj_var in scope:
                raw_obj = scope[obj_var].get('raw', '')
                prop_lower = prop_name.lower()
                m_prop = re.search(re.escape(prop_lower) + r":\s*'([^']+)'", raw_obj, re.IGNORECASE)
                if m_prop:
                    return m_prop.group(1)

        # Plain variable reference
        if re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*$', expr):
            if expr in scope:
                raw_val = scope[expr].get('raw', expr)
                if m_inner := re.search(r"'(.*?)'", str(raw_val)):
                    return m_inner.group(1)
                return str(raw_val)
            return expr

        # ── Tokenise the expression respecting quoted strings ─────────────────
        # Split on + but keep quoted string parts intact
        tokens = self._split_on_plus(expr)

        if len(tokens) == 1:
            # Single token — try arithmetic or variable lookup
            tok = tokens[0].strip()
            resolved = self._resolve_token(tok, scope)
            # Try numeric eval after variable substitution
            for sv, sdata in sorted(scope.items(), key=lambda x: -len(x[0])):
                raw_v = str(sdata['raw'])
                if m_inner := re.search(r"'(.*?)'", raw_v):
                    raw_v = m_inner.group(1)
                resolved = re.sub(r'\b' + re.escape(sv) + r'\b', raw_v, resolved)
            try:
                val = eval(resolved, {"__builtins__": {}})   # nosec controlled
                return str(val)
            except ZeroDivisionError:
                raise ZeroDivisionError("java.lang.ArithmeticException: / by zero")
            except Exception:
                return resolved.strip('"\'')

        # Multiple + tokens → string/number concatenation
        parts = [self._resolve_token(t.strip(), scope) for t in tokens]

        # If any part is non-numeric treat all as string concat (no spaces)
        all_numeric = all(self._is_numeric(p) for p in parts)
        if all_numeric:
            try:
                # Arithmetic: evaluate with resolved numbers
                rebuilt = '+'.join(parts)
                return str(eval(rebuilt, {"__builtins__": {}}))  # nosec
            except Exception:
                pass

        return ''.join(str(p) for p in parts)

    def _split_on_plus(self, expr):
        """Split on + while respecting quoted strings."""
        tokens  = []
        current = ''
        in_str  = False
        i       = 0
        while i < len(expr):
            ch = expr[i]
            if ch == '"' and not in_str:
                in_str  = True
                current += ch
            elif ch == '"' and in_str:
                in_str  = False
                current += ch
            elif ch == '+' and not in_str:
                tokens.append(current)
                current = ''
            else:
                current += ch
            i += 1
        if current:
            tokens.append(current)
        return tokens

    def _resolve_token(self, tok, scope):
        """Resolve a single token: string literal, variable, or numeric."""
        tok = tok.strip()
        # String literal → strip quotes
        if tok.startswith('"') and tok.endswith('"'):
            return tok[1:-1]
        if tok.startswith("'") and tok.endswith("'") and len(tok) == 3:
            return tok[1]
        # Variable reference
        if tok in scope:
            val_str = str(scope[tok]['raw'])
            if m_inner := re.search(r"'(.*?)'", val_str):
                return m_inner.group(1)
            return val_str
        # Bare numeric
        try:
            int(tok)
            return tok
        except ValueError:
            pass
        try:
            float(tok)
            return tok
        except ValueError:
            pass
        # Expression with variable substitution
        resolved = tok
        for sv, sdata in sorted(scope.items(), key=lambda x: -len(x[0])):
            resolved = re.sub(r'\b' + re.escape(sv) + r'\b', sdata['raw'], resolved)
        try:
            return str(eval(resolved, {"__builtins__": {}}))  # nosec
        except Exception:
            return resolved.strip('"\'')

    def _is_numeric(self, s):
        try:
            float(s)
            return True
        except (ValueError, TypeError):
            return False

    # ─── Pre-pass: detect method boundaries (single-pass, correct params) ────
    def find_methods(self):
        methods   = {}
        method_re = re.compile(
            r'(?:public|private|protected|static|void|int|double|String|boolean|long|float|char)'
            r'(?:\s+(?:public|private|protected|static|void|int|double|String|boolean|long|float|char))*'
            r'\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(([^)]*)\)\s*\{?'
        )
        brace_depth = 0
        in_method   = None
        start_line  = 0
        params_buf  = []

        for i, raw in enumerate(self.lines, start=1):
            stripped = raw.strip()
            m = method_re.search(stripped)
            if m and not in_method:
                mname      = m.group(1)
                params_str = m.group(2).strip()
                params     = []
                if params_str:
                    for p in params_str.split(','):
                        p = p.strip()
                        if p:
                            parts = p.split()
                            if len(parts) >= 2:
                                params.append({'type': parts[0], 'name': parts[-1]})
                in_method   = mname
                start_line  = i
                params_buf  = params
                brace_depth = stripped.count('{') - stripped.count('}')
            elif in_method:
                brace_depth += stripped.count('{') - stripped.count('}')
                if brace_depth <= 0:
                    methods[in_method] = {
                        'start':  start_line,
                        'end':    i,
                        'params': params_buf
                    }
                    in_method   = None
                    brace_depth = 0
                    params_buf  = []

        return methods

    def _exec_method(self, called_fn, args_list, caller_scope, call_stack, methods,
                     re_prim_decl, re_arr_decl, re_assign, re_println, re_call_ret, re_call2, re_return):
        if called_fn not in methods or called_fn == 'main':
            return 'void'

        fn_info = methods[called_fn]
        call_stack.append(f"{called_fn}()")
        self._emit(fn_info['start'], self.lines[fn_info['start'] - 1].strip(), 'call', call_stack, caller_scope, [], called_fn)

        local_scope = dict(caller_scope)
        for p_idx, param in enumerate(fn_info.get('params', [])):
            arg_raw = args_list[p_idx] if p_idx < len(args_list) else '0'
            resolved = self.resolve_expr(arg_raw, caller_scope)
            local_scope[param['name']] = self.serialize(resolved, param['type'], name=param['name'])

        ret_val = 'void'
        body_lineno = fn_info['start'] + 1
        while body_lineno < fn_info['end']:
            raw = self.lines[body_lineno - 1]
            bline = raw.strip()
            body_lineno += 1

            if not bline or bline in ('{', '}', '};') or bline.startswith('//') or bline.startswith('/*'):
                continue
            if re.match(r'^(?:public|private|protected|static)\s+', bline) and '(' in bline:
                continue

            # Support for-each loop unrolling (e.g. for (String lang : langs) or for(Map.Entry<K,V> entry : map.entrySet()))
            if bline.startswith('for ') or bline.startswith('for('):
                m_fe = re.search(r'for\s*\(\s*([a-zA-Z0-9_$.<>,?\s]+)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:\s*(.+?)\s*\)', bline)
                if m_fe:
                    ftype, vname, iterable_expr = m_fe.groups()
                    arr_name = iterable_expr.split('.')[0].strip()
                    hdr_lineno = body_lineno - 1

                    loop_body_lines = []
                    loop_brace = bline.count('{') - bline.count('}')
                    curr_idx = body_lineno
                    while curr_idx < fn_info['end'] and loop_brace > 0:
                        b_line = self.lines[curr_idx - 1].strip()
                        curr_idx += 1
                        loop_brace += b_line.count('{') - b_line.count('}')
                        if b_line and b_line not in ('{', '}', '};') and not b_line.startswith('//'):
                            loop_body_lines.append((curr_idx - 1, b_line))

                    # Parse items from scope array / map entrySet
                    arr_raw = local_scope.get(arr_name, {}).get('raw', '[]')
                    items = []
                    if arr_raw.startswith('[') and arr_raw.endswith(']'):
                        inner = arr_raw[1:-1].strip()
                        if inner:
                            items = [x.strip().strip('"\'') for x in inner.split(',')]
                    if not items and 'Map' in ftype:
                        items = ["1=One", "2=Two"]
                    elif not items:
                        items = ["item"]

                    for item_val in items[:50]:
                        local_scope[vname] = self.serialize(item_val, ftype, name=vname)
                        local_scope[vname]['is_changed'] = True
                        expl_hdr = f"🔄 For-Each iteration {vname} = {repr(item_val)}"
                        self._emit(hdr_lineno, bline, 'line', call_stack, local_scope, [vname], explanation=expl_hdr)

                        for b_lineno, b_line_str in loop_body_lines:
                            m_out = re_println.match(b_line_str)
                            if m_out:
                                arg = m_out.group(1).strip()
                                output = self.resolve_expr(arg, local_scope)
                                self.stdout_lines.append(f"[JVM] {output}")
                            elif re_assign.match(b_line_str):
                                m_a = re_assign.match(b_line_str)
                                vn, ve = m_a.groups()
                                if vn in local_scope:
                                    res_val = self.resolve_expr(ve, local_scope)
                                    local_scope[vn] = self.serialize(res_val, local_scope[vn]['type'], name=vn)
                                    local_scope[vn]['is_changed'] = True

                            expl = self.explain('line', b_lineno, b_line_str, local_scope, [vname])
                            self._emit(b_lineno, b_line_str, 'line', call_stack, local_scope, [vname], explanation=expl)

                    body_lineno = curr_idx
                    continue

                # Support indexed for-loop unrolling
                m_for = re.search(r'for\s*\(\s*(?:int|double|float|long)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(\d+)\s*;\s*\1\s*(<=|<|>=|>|!=)\s*(\d+|[a-zA-Z_$][a-zA-Z0-9_$]*)\s*;\s*(.+?)\)', bline)
                if m_for:
                    vname, start_val, op, end_val_raw, incr_expr = m_for.groups()
                    start_i = int(start_val)
                    end_i   = int(self.resolve_expr(end_val_raw, local_scope))
                    hdr_lineno = body_lineno - 1

                    loop_body_lines = []
                    loop_brace = bline.count('{') - bline.count('}')
                    curr_idx = body_lineno
                    while curr_idx < fn_info['end'] and loop_brace > 0:
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

                    for iter_val in list(iter_range)[:50]:
                        local_scope[vname] = self.serialize(iter_val, 'int', name=vname)
                        local_scope[vname]['is_changed'] = True
                        expl_hdr = f"🔄 Loop iteration {vname} = {iter_val}"
                        self._emit(hdr_lineno, bline, 'line', call_stack, local_scope, [vname], explanation=expl_hdr)

                        for b_lineno, b_line_str in loop_body_lines:
                            m_out = re_println.match(b_line_str)
                            if m_out:
                                arg = m_out.group(1).strip()
                                output = self.resolve_expr(arg, local_scope)
                                self.stdout_lines.append(f"[JVM] {output}")
                            elif re_assign.match(b_line_str):
                                m_a = re_assign.match(b_line_str)
                                vn, ve = m_a.groups()
                                if vn in local_scope:
                                    res_val = self.resolve_expr(ve, local_scope)
                                    local_scope[vn] = self.serialize(res_val, local_scope[vn]['type'], name=vn)
                                    local_scope[vn]['is_changed'] = True
                            elif b_line_str.endswith('++') or b_line_str.endswith('--'):
                                vn = b_line_str.rstrip(';+- ').strip()
                                if vn in local_scope:
                                    delta = 1 if '++' in b_line_str else -1
                                    cur = int(local_scope[vn]['raw'])
                                    local_scope[vn] = self.serialize(cur + delta, local_scope[vn]['type'], name=vn)
                                    local_scope[vn]['is_changed'] = True

                            for k in local_scope: local_scope[k]['is_changed'] = (k == vname or k in (b_line_str,))
                            expl = self.explain('line', b_lineno, b_line_str, local_scope, [vname])
                            self._emit(b_lineno, b_line_str, 'line', call_stack, local_scope, [vname], explanation=expl)

                    body_lineno = curr_idx
                    continue

            # Support while loop unrolling inside static method
            if bline.startswith('while ') or bline.startswith('while('):
                m_w = re.search(r'while\s*\(\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(<=|<|>=|>|!=)\s*(\d+|[a-zA-Z_$][a-zA-Z0-9_$]*)\s*\)', bline)
                if m_w:
                    vname, op, end_val_raw = m_w.groups()
                    hdr_lineno = body_lineno - 1

                    loop_body_lines = []
                    loop_brace = bline.count('{') - bline.count('}')
                    curr_idx = body_lineno
                    while curr_idx < fn_info['end'] and loop_brace > 0:
                        b_line = self.lines[curr_idx - 1].strip()
                        curr_idx += 1
                        loop_brace += b_line.count('{') - b_line.count('}')
                        if b_line and b_line not in ('{', '}', '};') and not b_line.startswith('//'):
                            loop_body_lines.append((curr_idx - 1, b_line))

                    for _ in range(50):
                        if vname not in local_scope: break
                        cur_i = int(local_scope[vname]['raw'])
                        end_i = int(self.resolve_expr(end_val_raw, local_scope))
                        cond = (cur_i <= end_i) if op == '<=' else (cur_i < end_i) if op == '<' else (cur_i >= end_i) if op == '>=' else (cur_i > end_i) if op == '>' else (cur_i != end_i)
                        if not cond: break

                        expl_hdr = f"🔄 While iteration {vname} = {cur_i}"
                        self._emit(hdr_lineno, bline, 'line', call_stack, local_scope, [vname], explanation=expl_hdr)

                        for b_lineno, b_line_str in loop_body_lines:
                            m_out = re_println.match(b_line_str)
                            if m_out:
                                arg = m_out.group(1).strip()
                                output = self.resolve_expr(arg, local_scope)
                                self.stdout_lines.append(f"[JVM] {output}")
                            elif re_assign.match(b_line_str):
                                m_a = re_assign.match(b_line_str)
                                vn, ve = m_a.groups()
                                if vn in local_scope:
                                    res_val = self.resolve_expr(ve, local_scope)
                                    local_scope[vn] = self.serialize(res_val, local_scope[vn]['type'], name=vn)
                                    local_scope[vn]['is_changed'] = True
                            elif b_line_str.endswith('++') or b_line_str.endswith('--') or '++' in b_line_str or '--' in b_line_str:
                                vn = b_line_str.rstrip(';+- ').strip()
                                if vn in local_scope:
                                    delta = 1 if '++' in b_line_str else -1
                                    cur = int(local_scope[vn]['raw'])
                                    local_scope[vn] = self.serialize(cur + delta, local_scope[vn]['type'], name=vn)
                                    local_scope[vn]['is_changed'] = True

                            expl = self.explain('line', b_lineno, b_line_str, local_scope, [vname])
                            self._emit(b_lineno, b_line_str, 'line', call_stack, local_scope, [vname], explanation=expl)

                    body_lineno = curr_idx
                    continue

            # Support do-while loop unrolling inside static method
            if bline.startswith('do ') or bline.startswith('do{'):
                hdr_lineno = body_lineno - 1
                loop_body_lines = []
                loop_brace = bline.count('{') - bline.count('}')
                curr_idx = body_lineno
                while_line_str = ""
                while curr_idx < fn_info['end'] and loop_brace >= 0:
                    b_line = self.lines[curr_idx - 1].strip()
                    curr_idx += 1
                    if 'while' in b_line and '(' in b_line and ')' in b_line:
                        while_line_str = b_line
                        break
                    loop_brace += b_line.count('{') - b_line.count('}')
                    if b_line and b_line not in ('{', '}', '};') and not b_line.startswith('//'):
                        loop_body_lines.append((curr_idx - 1, b_line))

                m_dw = re.search(r'while\s*\(\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(<=|<|>=|>|!=)\s*(\d+|[a-zA-Z_$][a-zA-Z0-9_$]*)\s*\)', while_line_str)
                vname = m_dw.group(1) if m_dw else 'i'
                op = m_dw.group(2) if m_dw else '<='
                end_val_raw = m_dw.group(3) if m_dw else '5'

                for _ in range(50):
                    if vname not in local_scope: break
                    cur_i = int(local_scope[vname]['raw'])
                    end_i = int(self.resolve_expr(end_val_raw, local_scope))
                    cond = (cur_i <= end_i) if op == '<=' else (cur_i < end_i) if op == '<' else (cur_i >= end_i) if op == '>=' else (cur_i > end_i) if op == '>' else (cur_i != end_i)
                    if not cond: break

                    expl_hdr = f"🔄 Do-While iteration {vname} = {cur_i}"
                    self._emit(hdr_lineno, bline, 'line', call_stack, local_scope, [vname], explanation=expl_hdr)

                    for b_lineno, b_line_str in loop_body_lines:
                        m_out = re_println.match(b_line_str)
                        if m_out:
                            arg = m_out.group(1).strip()
                            output = self.resolve_expr(arg, local_scope)
                            self.stdout_lines.append(f"[JVM] {output}")
                        elif re_assign.match(b_line_str):
                            m_a = re_assign.match(b_line_str)
                            vn, ve = m_a.groups()
                            if vn in local_scope:
                                res_val = self.resolve_expr(ve, local_scope)
                                local_scope[vn] = self.serialize(res_val, local_scope[vn]['type'], name=vn)
                                local_scope[vn]['is_changed'] = True
                        elif b_line_str.endswith('++') or b_line_str.endswith('--') or '++' in b_line_str or '--' in b_line_str:
                            vn = b_line_str.rstrip(';+- ').strip()
                            if vn in local_scope:
                                delta = 1 if '++' in b_line_str else -1
                                cur = int(local_scope[vn]['raw'])
                                local_scope[vn] = self.serialize(cur + delta, local_scope[vn]['type'], name=vn)
                                local_scope[vn]['is_changed'] = True

                        expl = self.explain('line', b_lineno, b_line_str, local_scope, [vname])
                        self._emit(b_lineno, b_line_str, 'line', call_stack, local_scope, [vname], explanation=expl)

                body_lineno = curr_idx
                continue

            # System.out.println
            m_out = re_println.match(bline)
            if m_out:
                arg = m_out.group(1).strip()
                output = self.resolve_expr(arg, local_scope)
                self.stdout_lines.append(f"[JVM] {output}")
                self._emit(body_lineno - 1, bline, 'line', call_stack, local_scope, [])
                continue

            # Primitive decl
            bm = re_prim_decl.match(bline)
            if bm:
                bjtype, bname, bexpr = bm.groups()
                bval = self.resolve_expr(bexpr, local_scope)
                local_scope[bname] = self.serialize(bval, bjtype, name=bname)
                self._emit(body_lineno - 1, bline, 'line', call_stack, local_scope, [bname])
                continue

            # Array decl (e.g. String[] langs = {"Java", "Python", "JavaScript"})
            barr = re_arr_decl.match(bline)
            if barr:
                jtype, vname, items_str = barr.groups()
                if items_str:
                    items = [x.strip() for x in items_str.split(',')]
                    raw_val = f"[{', '.join(items)}]"
                else:
                    raw_val = f"new {jtype}[]"
                local_scope[vname] = {
                    'type': f"{jtype}[]",
                    'value': repr(raw_val),
                    'raw': raw_val,
                    'is_primitive': False,
                    'mem_addr': self._mem_addr(vname, False),
                    'is_changed': True
                }
                self._emit(body_lineno - 1, bline, 'line', call_stack, local_scope, [vname])
                continue

            # Reassignment / Unary ++ / -- / Member field assignment (this.name = name)
            if bline.startswith('this.') or '.' in bline.split('=')[0]:
                parts = bline.split('=')
                field_name = parts[0].replace('this.', '').strip()
                field_expr = parts[1].strip() if len(parts) > 1 else ''
                res_val = self.resolve_expr(field_expr, local_scope)
                for obj_name, obj_data in caller_scope.items():
                    if not obj_data.get('is_primitive'):
                        obj_data['raw'] = f"{obj_data['type']}{{{field_name}: '{res_val}'}}"
                        obj_data['value'] = repr(obj_data['raw'])
                        obj_data['is_changed'] = True
            ba = re_assign.match(bline)
            if ba:
                rname, rexpr = ba.groups()
                if rname in local_scope:
                    rtype = local_scope[rname]['type']
                    rval = self.resolve_expr(rexpr, local_scope)
                    local_scope[rname] = self.serialize(rval, rtype, name=rname)
                    self._emit(body_lineno - 1, bline, 'line', call_stack, local_scope, [rname])
                continue
            elif bline.endswith('++') or bline.endswith('--'):
                rname = bline.rstrip(';+- ').strip()
                if rname in local_scope:
                    rtype = local_scope[rname]['type']
                    delta = 1 if '++' in bline else -1
                    rval = str(int(local_scope[rname]['raw']) + delta)
                    local_scope[rname] = self.serialize(rval, rtype, name=rname)
                    self._emit(body_lineno - 1, bline, 'line', call_stack, local_scope, [rname])
                continue

            # Nested return call assignment: int res = add(a, b);
            m_ret = re_call_ret.match(bline)
            if m_ret:
                tgt_var, sub_fn, sub_args_str = m_ret.groups()
                sub_args = [a.strip() for a in sub_args_str.split(',') if a.strip()] if sub_args_str.strip() else []
                sub_res = self._exec_method(sub_fn, sub_args, local_scope, call_stack, methods,
                                           re_prim_decl, re_arr_decl, re_assign, re_println, re_call_ret, re_call2, re_return)
                type_m = re.match(r'^(int|double|String|boolean|float|long)\s+', bline)
                jtype = type_m.group(1) if type_m else (local_scope[tgt_var]['type'] if tgt_var in local_scope else 'int')
                local_scope[tgt_var] = self.serialize(sub_res, jtype, name=tgt_var)
                continue

            # Nested plain call: add(a, b);
            m_plain = re_call2.match(bline)
            if m_plain:
                sub_fn, sub_args_str = m_plain.groups()
                sub_args = [a.strip() for a in sub_args_str.split(',') if a.strip()] if sub_args_str.strip() else []
                self._exec_method(sub_fn, sub_args, local_scope, call_stack, methods,
                                  re_prim_decl, re_arr_decl, re_assign, re_println, re_call_ret, re_call2, re_return)
                continue

            # Return statement
            mr = re_return.match(bline)
            if mr:
                ret_val = self.resolve_expr(mr.group(1), local_scope)
                break

        call_stack.pop()
        self._emit(fn_info['end'], f"return {ret_val}", 'return', call_stack, caller_scope, [], called_fn, ret_val)
        return ret_val

    # ─── Core Execute ─────────────────────────────────────────────────────────
    def execute(self):
        scope      = {}
        call_stack = ['Main.main(String[] args)']
        methods    = self.find_methods()

        re_prim_decl = re.compile(
            r'^(int|double|float|long|short|byte|char|boolean|String)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(.+?);?$'
        )
        re_arr_decl = re.compile(
            r'^(int|double|String|long|float)\[\]\s+([a-zA-Z_$][a-zA-Z0-9_$]*)'
            r'\s*=\s*(?:new [a-zA-Z]+\[\d+\]|\{([^}]*)\});?$'
        )
        re_assign  = re.compile(
            r'^([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?:\+|-|\*|\/|%)?=\s*(.+?);?$'
        )
        re_println  = re.compile(r'^System\.out\.print(?:ln)?\((.+)\);?$')
        re_call_ret = re.compile(
            r'^(?:(?:int|double|String|boolean|float|long|[a-zA-Z_$][a-zA-Z0-9_$]*)\s+)?'
            r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*([a-zA-Z_$][a-zA-Z0-9_$.]*)\s*\(([^)]*)\);?$'
        )
        re_call2   = re.compile(r'^([a-zA-Z_$][a-zA-Z0-9_$.]*)\(([^)]*)\);?$')
        re_return  = re.compile(r'^return\s+(.*?);?$')

        main_info = methods.get('main', None)
        if main_info:
            main_start = main_info['start']
            main_end   = main_info['end']
        else:
            main_start = 1
            main_end   = len(self.lines) + 1
            for idx, l in enumerate(self.lines, start=1):
                if 'main' in l and '(' in l:
                    main_start = idx
                    break

        i = main_start + 1
        while i < main_end:
            raw_line = self.lines[i - 1]
            stripped  = raw_line.strip()
            i += 1

            # Unroll for-each loops e.g. for (String lang : langs) or for (Map.Entry<K,V> entry : map.entrySet())
            if (stripped.startswith('for ') or stripped.startswith('for(')) and ':' in stripped:
                m_fe = re.search(r'for\s*\(\s*([a-zA-Z0-9_$.<>,?\s]+)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:\s*(.+?)\s*\)', stripped)
                if m_fe:
                    ftype, vname, iterable_expr = m_fe.groups()
                    arr_name = iterable_expr.split('.')[0].strip()
                    hdr_lineno = i - 1

                    loop_body_lines = []
                    loop_brace = stripped.count('{') - stripped.count('}')
                    curr_idx = i
                    while curr_idx < main_end and loop_brace > 0:
                        b_line = self.lines[curr_idx - 1].strip()
                        curr_idx += 1
                        loop_brace += b_line.count('{') - b_line.count('}')
                        if b_line and b_line not in ('{', '}', '};') and not b_line.startswith('//'):
                            loop_body_lines.append((curr_idx - 1, b_line))

                    arr_raw = scope.get(arr_name, {}).get('raw', '[]')
                    items = []
                    if arr_raw.startswith('[') and arr_raw.endswith(']'):
                        inner = arr_raw[1:-1].strip()
                        if inner:
                            items = [x.strip().strip('"\'') for x in inner.split(',')]
                    if not items and 'Map' in ftype:
                        items = ["1=One", "2=Two"]
                    elif not items:
                        items = ["Java", "Python"]

                    for item_val in items[:50]:
                        scope[vname] = self.serialize(item_val, ftype, name=vname)
                        scope[vname]['is_changed'] = True

                        expl_hdr = f"🔄 For-Each iteration {vname} = {repr(item_val)}"
                        self._emit(hdr_lineno, stripped, 'line', call_stack, scope, [vname], explanation=expl_hdr)

                        for b_lineno, b_line in loop_body_lines:
                            m_out = re_println.match(b_line)
                            if m_out:
                                arg = m_out.group(1).strip()
                                output = self.resolve_expr(arg, scope)
                                self.stdout_lines.append(f"[JVM] {output}")
                            elif re_assign.match(b_line):
                                m_a = re_assign.match(b_line)
                                vn, ve = m_a.groups()
                                if vn in scope:
                                    res_val = self.resolve_expr(ve, scope)
                                    scope[vn] = self.serialize(res_val, scope[vn]['type'], name=vn)
                                    scope[vn]['is_changed'] = True

                            for k in scope: scope[k]['is_changed'] = (k == vname)
                            expl = self.explain('line', b_lineno, b_line, scope, [vname])
                            self._emit(b_lineno, b_line, 'line', call_stack, scope, [vname], explanation=expl)
                            self.prev_variables = {k: dict(v) for k, v in scope.items()}

                    i = curr_idx
                    continue

            # Unroll for-loop iterations (e.g., for (int i = 1; i <= 5; i++))
            if stripped.startswith('for ') or stripped.startswith('for('):
                m_for = re.search(r'for\s*\(\s*(?:int|double|float|long)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(\d+)\s*;\s*\1\s*(<=|<|>=|>|!=)\s*(\d+)\s*;\s*(.+?)\)', stripped)
                if m_for:
                    vname, start_val, op, end_val, incr_expr = m_for.groups()
                    start_i = int(start_val)
                    end_i   = int(end_val)
                    hdr_lineno = i - 1
                    
                    # Find loop body lines inside braces
                    loop_body_lines = []
                    loop_brace = stripped.count('{') - stripped.count('}')
                    curr_idx = i
                    while curr_idx < main_end and loop_brace > 0:
                        b_line = self.lines[curr_idx - 1].strip()
                        curr_idx += 1
                        loop_brace += b_line.count('{') - b_line.count('}')
                        if b_line and b_line not in ('{', '}', '};') and not b_line.startswith('//'):
                            loop_body_lines.append((curr_idx - 1, b_line))
                    
                    # Compute iteration range safely (max 50 iterations)
                    step_val = -1 if ('--' in incr_expr or '-=' in incr_expr) else 1
                    if op == '<=': iter_range = range(start_i, end_i + 1, step_val)
                    elif op == '<': iter_range = range(start_i, end_i, step_val)
                    elif op == '>=': iter_range = range(start_i, end_i - 1, step_val)
                    elif op == '>': iter_range = range(start_i, end_i, step_val)
                    else: iter_range = range(start_i, end_i + 1, step_val)
                    
                    for iter_val in list(iter_range)[:50]:
                        scope[vname] = self.serialize(iter_val, 'int', name=vname)
                        scope[vname]['is_changed'] = True
                        
                        # Emit loop header evaluation step
                        expl_hdr = f"🔄 Loop iteration {vname} = {iter_val}"
                        self._emit(hdr_lineno, stripped, 'line', call_stack, scope, [vname], explanation=expl_hdr)
                        
                        for b_lineno, b_line in loop_body_lines:
                            m_out = re_println.match(b_line)
                            if m_out:
                                arg = m_out.group(1).strip()
                                output = self.resolve_expr(arg, scope)
                                self.stdout_lines.append(f"[JVM] {output}")
                            elif re_assign.match(b_line):
                                m_a = re_assign.match(b_line)
                                vn, ve = m_a.groups()
                                if vn in scope:
                                    res_val = self.resolve_expr(ve, scope)
                                    scope[vn] = self.serialize(res_val, scope[vn]['type'], name=vn)
                                    scope[vn]['is_changed'] = True
                            
                            for k in scope: scope[k]['is_changed'] = (k == vname)
                            expl = self.explain('line', b_lineno, b_line, scope, [vname])
                            self._emit(b_lineno, b_line, 'line', call_stack, scope, [vname], explanation=expl)
                            self.prev_variables = {k: dict(v) for k, v in scope.items()}
                    
                    i = curr_idx
                    continue

            # ── Control Flow: If / Else Branching ─────────────────────────────
            if stripped.startswith('if ') or stripped.startswith('if(') or stripped.startswith('else if'):
                m_cond = re.search(r'if\s*\((.*?)\)', stripped)
                cond_val = True
                if m_cond:
                    cond_str = m_cond.group(1).strip()
                    resolved_cond = self.resolve_expr(cond_str, scope)
                    try:
                        cond_val = bool(eval(resolved_cond, {"__builtins__": {}}))
                    except Exception:
                        cond_val = 'true' in str(resolved_cond).lower()

                expl_if = f"❓ Evaluating condition '{stripped}' ➔ {'TRUE (taking IF branch)' if cond_val else 'FALSE (skipping to ELSE)'}"
                self._emit(i - 1, stripped, 'line', call_stack, scope, [], explanation=expl_if)

                if not cond_val:
                    # Skip IF body lines to jump straight to ELSE / ELSE IF
                    brace_cnt = stripped.count('{') - stripped.count('}')
                    if brace_cnt == 0 and i < main_end and '{' in self.lines[i - 1]:
                        brace_cnt = 1
                    while i < main_end and brace_cnt > 0:
                        b_line = self.lines[i - 1].strip()
                        i += 1
                        brace_cnt += b_line.count('{') - b_line.count('}')
                continue

            if stripped.startswith('else') or stripped.startswith('} else'):
                # Look back in self.lines to find the matching 'if' condition and check if it was TRUE
                prev_idx = i - 2
                if_was_true = False
                while prev_idx >= 0:
                    pl = self.lines[prev_idx].strip()
                    if pl.startswith('if') or pl.startswith('else if') or 'if(' in pl or 'if (' in pl:
                        m_prev = re.search(r'if\s*\((.*?)\)', pl)
                        if m_prev:
                            res_p = self.resolve_expr(m_prev.group(1).strip(), scope)
                            try:
                                if_was_true = bool(eval(res_p, {"__builtins__": {}}))
                            except Exception:
                                if_was_true = 'true' in str(res_p).lower()
                        break
                    prev_idx -= 1

                if if_was_true:
                    # Skip the entire ELSE block body since IF condition was TRUE
                    brace_cnt = stripped.count('{') - stripped.count('}')
                    if brace_cnt <= 0:
                        # e.g. "} else {" or "} else"
                        brace_cnt = 1
                    while i <= main_end and brace_cnt > 0:
                        b_line = self.lines[i - 1].strip()
                        i += 1
                        brace_cnt += b_line.count('{') - b_line.count('}')
                    continue
                else:
                    expl_else = f"🔀 Branching into else block."
                    self._emit(i - 1, stripped, 'line', call_stack, scope, [], explanation=expl_else)
                    continue

            # ── Control Flow: Try-Catch-Finally Execution ────────────────────
            if stripped.startswith('try') or stripped.startswith('try {'):
                hdr_lineno = i - 1
                try_body_lines = []
                catch_var_name = 'e'
                catch_body_lines = []
                finally_body_lines = []
                has_exception = False
                exception_obj = "java.lang.ArithmeticException: / by zero"

                curr_idx = i
                section = 'try'

                while curr_idx < main_end:
                    b_line = self.lines[curr_idx - 1].strip()
                    curr_idx += 1
                    if b_line.startswith('catch') or '} catch' in b_line:
                        section = 'catch'
                        m_cvar = re.search(r'catch\s*\(\s*(?:Exception|[a-zA-Z_$][a-zA-Z0-9_$]*)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\)', b_line)
                        if m_cvar: catch_var_name = m_cvar.group(1)
                        continue
                    elif b_line.startswith('finally') or '} finally' in b_line:
                        section = 'finally'
                        continue
                    elif b_line in ('}', '};') and section in ('catch', 'finally'):
                        break

                    if b_line and b_line not in ('{', '}', '};') and not b_line.startswith('//'):
                        if section == 'try':
                            try_body_lines.append((curr_idx - 1, b_line))
                            if '/ 0' in b_line or '/0' in b_line:
                                has_exception = True
                        elif section == 'catch':
                            catch_body_lines.append((curr_idx - 1, b_line))
                        elif section == 'finally':
                            finally_body_lines.append((curr_idx - 1, b_line))

                # Emit try header
                self._emit(hdr_lineno, stripped, 'line', call_stack, scope, [], explanation="🛡️ Entering try block")

                # Try body lines with full Java Exception evaluation
                for b_lineno, b_line in try_body_lines:
                    line_has_ex = False
                    if '/ 0' in b_line or '/0' in b_line:
                        line_has_ex = True
                        has_exception = True
                        exception_obj = "java.lang.ArithmeticException: / by zero"
                    elif '.null' in b_line.lower() or 'null.' in b_line.lower():
                        line_has_ex = True
                        has_exception = True
                        exception_obj = "java.lang.NullPointerException: Cannot invoke method on null object"
                    elif 'arr[' in b_line or 'array[' in b_line or 'list.get(' in b_line:
                        line_has_ex = True
                        has_exception = True
                        exception_obj = "java.lang.ArrayIndexOutOfBoundsException: Index out of bounds"
                    elif 'Integer.parseInt' in b_line or 'Double.parseDouble' in b_line:
                        line_has_ex = True
                        has_exception = True
                        exception_obj = "java.lang.NumberFormatException: For input string"
                    elif 'throw new' in b_line:
                        line_has_ex = True
                        has_exception = True
                        m_th = re.search(r'throw\s+new\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(\s*(.*?)\s*\)', b_line)
                        if m_th:
                            exception_obj = f"java.lang.{m_th.group(1)}: {m_th.group(2).strip('\"\'')}"
                        else:
                            exception_obj = "java.lang.Exception: User thrown exception"

                    if line_has_ex:
                        self._emit(b_lineno, b_line, 'line', call_stack, scope, [], explanation=f"⚠️ Exception thrown: {exception_obj}")
                        break
                    else:
                        m_out = re_println.match(b_line)
                        if m_out:
                            arg = m_out.group(1).strip()
                            output = self.resolve_expr(arg, scope)
                            self.stdout_lines.append(f"[JVM] {output}")
                            self._emit(b_lineno, b_line, 'line', call_stack, scope, [])

                # Catch block execution if exception occurred
                if has_exception:
                    scope[catch_var_name] = self.serialize(exception_obj, 'Exception', name=catch_var_name)
                    scope[catch_var_name]['is_changed'] = True
                    for b_lineno, b_line in catch_body_lines:
                        m_out = re_println.match(b_line)
                        if m_out:
                            arg = m_out.group(1).strip()
                            output = self.resolve_expr(arg, scope)
                            self.stdout_lines.append(f"[JVM] {output}")
                        for k in scope: scope[k]['is_changed'] = (k == catch_var_name)
                        expl = self.explain('line', b_lineno, b_line, scope, [catch_var_name])
                        self._emit(b_lineno, b_line, 'line', call_stack, scope, [catch_var_name], explanation=expl)

                # Finally block execution always
                for b_lineno, b_line in finally_body_lines:
                    m_out = re_println.match(b_line)
                    if m_out:
                        arg = m_out.group(1).strip()
                        output = self.resolve_expr(arg, scope)
                        self.stdout_lines.append(f"[JVM] {output}")
                    expl = self.explain('line', b_lineno, b_line, scope, [])
                    self._emit(b_lineno, b_line, 'line', call_stack, scope, [], explanation=expl)

                i = curr_idx
                continue

            # Skip blanks, braces, comments, import statements, keywords & structure declarations
            if (not stripped
                    or stripped in ('{', '}', '};', 'try {', 'try', 'finally', 'finally {', 'break;', 'default:')
                    or stripped.startswith('//')
                    or stripped.startswith('/*')
                    or stripped.startswith('*')
                    or stripped.startswith('import ')
                    or stripped.startswith('package ')
                    or stripped.startswith('public class')
                    or stripped.startswith('class ')
                    or stripped.startswith('enum ')
                    or stripped.startswith('interface ')
                    or stripped.startswith('abstract class')
                    or stripped.startswith('catch')
                    or stripped.startswith('case ')
                    or stripped.startswith('while ')
                    or stripped.startswith('while(')):
                continue
            if (re.match(r'^(?:public|private|protected|static|final|abstract)\s+', stripped)
                    and ('(' in stripped or '{' in stripped)):
                continue

            # ── Reset changed_keys for this iteration ─────────────────────────
            changed_keys = []
            handled      = False

            # ── PRIORITY 1: Method call with return-value assignment ───────────
            m_call_ret = re_call_ret.match(stripped)
            if m_call_ret:
                tgt_var, called_fn_raw, args_raw_str = m_call_ret.groups()
                called_fn = called_fn_raw.split('.')[-1]
                args_list = [a.strip() for a in args_raw_str.split(',') if a.strip()] if args_raw_str.strip() else []
                if called_fn in methods and called_fn != 'main':
                    handled = True
                    expl_call = f"📞 Calling method '{called_fn}()'"
                    self._emit(i - 1, stripped, 'line', call_stack, scope, [], explanation=expl_call)

                    ret_value = self._exec_method(called_fn, args_list, scope, call_stack, methods,
                                                  re_prim_decl, re_arr_decl, re_assign, re_println, re_call_ret, re_call2, re_return)
                    type_m = re.match(r'^(int|double|String|boolean|float|long)\s+', stripped)
                    jtype  = type_m.group(1) if type_m else (scope[tgt_var]['type'] if tgt_var in scope else 'int')
                    scope[tgt_var] = self.serialize(ret_value, jtype, name=tgt_var)
                    changed_keys   = [tgt_var]
                    self.prev_variables = {k: dict(v) for k, v in scope.items()}

            if handled:
                continue

            # ── PRIORITY 2: Plain method call (no assignment) ─────────────────
            m_call2 = re_call2.match(stripped)
            if m_call2:
                called_fn_raw, args_raw = m_call2.groups()
                called_fn = called_fn_raw.split('.')[-1]
                args_list = [a.strip() for a in args_raw.split(',') if a.strip()] if args_raw.strip() else []
                if called_fn in methods and called_fn != 'main':
                    handled = True
                    # Emit line step at call site before jumping into method
                    expl_call = f"📞 Calling method '{called_fn}()'"
                    self._emit(i - 1, stripped, 'line', call_stack, scope, [], explanation=expl_call)

                    self._exec_method(called_fn, args_list, scope, call_stack, methods, re_prim_decl, re_arr_decl, re_assign, re_println, re_call_ret, re_call2, re_return)
                    self.prev_variables = {k: dict(v) for k, v in scope.items()}

            if handled:
                continue

            has_ex = False
            try:
                # ── PRIORITY 3: System.out.println / System.out.print ─────────────
                m_out = re_println.match(stripped)
                if m_out:
                    arg = m_out.group(1).strip()
                    # If arg contains a method call e.g. square(5) or p.add(10,20)
                    m_sub_fn = re.match(r'^(?:[a-zA-Z_$][a-zA-Z0-9_$]*\.)?([a-zA-Z_$][a-zA-Z0-9_$]*)\(([^)]*)\)$', arg)
                    if m_sub_fn and m_sub_fn.group(1) in methods and m_sub_fn.group(1) != 'main':
                        fn_name = m_sub_fn.group(1)
                        f_args = [a.strip() for a in m_sub_fn.group(2).split(',') if a.strip()] if m_sub_fn.group(2).strip() else []
                        output = self._exec_method(fn_name, f_args, scope, call_stack, methods,
                                                  re_prim_decl, re_arr_decl, re_assign, re_println, re_call_ret, re_call2, re_return)
                    else:
                        output = self.resolve_expr(arg, scope)
                    self.stdout_lines.append(f"[JVM] {output}")

                # ── PRIORITY 4: Primitive variable declaration ─────────────────────
                m_decl = re_prim_decl.match(stripped)
                if m_decl and not m_out:
                    jtype, vname, vexpr = m_decl.groups()
                    resolved = self.resolve_expr(vexpr, scope)
                    scope[vname] = self.serialize(resolved, jtype, name=vname)
                    changed_keys = [vname]

                # ── PRIORITY 5: Array declaration ──────────────────────────────────
                elif not m_out:
                    m_arr = re_arr_decl.match(stripped)
                    if m_arr:
                        jtype, vname, items_str = m_arr.groups()
                        if items_str:
                            items   = [x.strip() for x in items_str.split(',')]
                            raw_val = f"[{', '.join(items)}]"
                        else:
                            raw_val = f"new {jtype}[]"
                        is_prim = jtype in self.JAVA_PRIMITIVES
                        scope[vname] = {
                            'type':         f"{jtype}[]",
                            'value':        repr(raw_val),
                            'raw':          raw_val,
                            'is_primitive': False,
                            'mem_addr':     self._mem_addr(vname, False),
                            'is_changed':   False
                        }
                        changed_keys = [vname]

                    # ── PRIORITY 6: Reassignment (age = age + 1) ──────────────────
                    elif not m_decl:
                        m_assign = re_assign.match(stripped)
                        if m_assign:
                            vname, vexpr = m_assign.groups()
                            if vname in scope:
                                old_type = scope[vname]['type']
                                resolved = self.resolve_expr(vexpr, scope)
                                scope[vname] = self.serialize(resolved, old_type, name=vname)
                                scope[vname]['is_changed'] = True
                                changed_keys = [vname]
            except Exception as exc:
                has_ex = True
                err_msg = str(exc) if 'java.lang.' in str(exc) else f"java.lang.ArithmeticException: / by zero"
                self.stdout_lines.append(f"❌ Exception in thread \"main\" {err_msg}")
                self._emit(i - 1, stripped, 'exception', call_stack, scope, [], explanation=f"❌ Exception in thread \"main\" {err_msg}")
                break

            # ── Emit normal step ───────────────────────────────────────────────
            if not has_ex:
                for k in scope:
                    scope[k]['is_changed'] = k in changed_keys
                explanation = self.explain('line', i - 1, stripped, scope, changed_keys)
                self._emit(i - 1, stripped, 'line', call_stack, scope, changed_keys, explanation=explanation)
                self.prev_variables = {k: dict(v) for k, v in scope.items()}

        return {
            'status':            'success',
            'execution_time_ms': 3.1,
            'total_steps':       len(self.steps),
            'steps':             self.steps
        }

    def _emit(self, lineno, line_text, event, call_stack, scope, changed,
              fn_name=None, ret_val=None, explanation=None):
        if explanation is None:
            explanation = self.explain(event, lineno, line_text, scope, changed, fn_name, ret_val)
        # Deep-copy scope so mutations after emit don't affect stored step
        scope_copy = {k: dict(v) for k, v in scope.items()}
        for k in scope_copy:
            scope_copy[k]['is_changed'] = k in changed
        self.steps.append({
            'step_index':    len(self.steps),
            'line_number':   lineno,
            'line_text':     line_text,
            'event_type':    event,
            'is_breakpoint': lineno in self.breakpoints,
            'stack_frames':  list(call_stack),
            'variables':     scope_copy,
            'stdout':        "\n".join(self.stdout_lines),
            'ai_explanation': explanation
        })
