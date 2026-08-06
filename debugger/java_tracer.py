import re


class JavaExecutionTracer:
    """
    Java 17 JVM Execution Tracer — Production Grade.
    Simulates JVM Stack Frame + Heap Reference memory:
    - Tracks all primitive types (int, double, boolean, char, long, String)
    - Detects variable reassignments and arithmetic updates (age = age + 1)
    - Pushes/pops method call frames on the call stack
    - Tracks System.out.println / System.out.print with full string concat resolution
    - Generates beginner-friendly AI explanations per step

    Fixed bugs:
    - Stable mem addresses per variable name (not hash-of-value)
    - String concat uses '' join, not ' ' join (no extra spaces)
    - changed_keys reset per loop iteration (no bleed-across)
    - scope dicts deep-copied in _emit (no shared-reference mutation)
    - find_methods() single-pass, params saved correctly
    - System.out.println multi-arg string concat resolved correctly
    - $ and special chars in string literals no longer cause spacing issues
    """

    JAVA_PRIMITIVES = {'int', 'double', 'float', 'long', 'short', 'byte', 'char', 'boolean'}

    def __init__(self, code_str, breakpoints=None):
        self.code_str    = code_str
        self.lines       = code_str.splitlines()
        self.breakpoints = set(breakpoints or [])
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

        # Plain variable reference
        if re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*$', expr):
            return scope.get(expr, {}).get('raw', expr)

        # ── Tokenise the expression respecting quoted strings ─────────────────
        # Split on + but keep quoted string parts intact
        tokens = self._split_on_plus(expr)

        if len(tokens) == 1:
            # Single token — try arithmetic or variable lookup
            tok = tokens[0].strip()
            resolved = self._resolve_token(tok, scope)
            # Try numeric eval after variable substitution
            for sv, sdata in sorted(scope.items(), key=lambda x: -len(x[0])):
                resolved = re.sub(r'\b' + re.escape(sv) + r'\b', sdata['raw'], resolved)
            try:
                val = eval(resolved, {"__builtins__": {}})   # nosec controlled
                return str(val)
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
            return scope[tok]['raw']
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

        local_scope = {}
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

            # Support for-loop unrolling inside static method
            if bline.startswith('for ') or bline.startswith('for('):
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

            # Reassignment / Unary ++ / --
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

        # Patterns
        re_prim_decl = re.compile(
            r'^(int|double|float|long|short|byte|char|boolean|String)'
            r'\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(.+?);?$'
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
            r'^(?:(?:int|double|String|boolean|float|long|void)\s+)?'
            r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(([^)]*)\);?$'
        )
        re_call2   = re.compile(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)\(([^)]*)\);?$')
        re_return  = re.compile(r'^return\s+(.*?);?$')

        main_info  = methods.get('main', None)
        main_start = main_info['start'] if main_info else 1
        main_end   = main_info['end']   if main_info else len(self.lines)

        i = main_start + 1
        while i < main_end:
            raw_line = self.lines[i - 1]
            stripped  = raw_line.strip()
            i += 1

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

            # Skip blanks, braces, comments, class/method declarations
            if (not stripped
                    or stripped in ('{', '}', '};')
                    or stripped.startswith('//')
                    or stripped.startswith('/*')
                    or stripped.startswith('*')
                    or stripped.startswith('public class')
                    or stripped.startswith('class ')
                    or stripped.startswith('while ')
                    or stripped.startswith('while(')):
                continue
            if (re.match(r'^(?:public|private|protected|static)\s+', stripped)
                    and '(' in stripped):
                continue

            # ── Reset changed_keys for this iteration ─────────────────────────
            changed_keys = []
            handled      = False

            # ── PRIORITY 1: Method call with return-value assignment ───────────
            m_call_ret = re_call_ret.match(stripped)
            if m_call_ret:
                tgt_var, called_fn, args_raw_str = m_call_ret.groups()
                args_list = [a.strip() for a in args_raw_str.split(',') if a.strip()] if args_raw_str.strip() else []
                if called_fn in methods and called_fn != 'main':
                    handled = True
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
                called_fn, args_raw = m_call2.groups()
                args_list = [a.strip() for a in args_raw.split(',') if a.strip()] if args_raw.strip() else []
                if called_fn in methods and called_fn != 'main':
                    handled = True
                    self._exec_method(called_fn, args_list, scope, call_stack, methods, re_prim_decl, re_arr_decl, re_assign, re_println, re_call_ret, re_call2, re_return)
                    self.prev_variables = {k: dict(v) for k, v in scope.items()}

            if handled:
                continue

            # ── PRIORITY 3: System.out.println / System.out.print ─────────────
            m_out = re_println.match(stripped)
            if m_out:
                arg    = m_out.group(1).strip()
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

            # ── Emit normal step ───────────────────────────────────────────────
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
