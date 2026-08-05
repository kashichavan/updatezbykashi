import sys
import io
import time
import json
import traceback
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def sandbox_view(request):
    """Render the Interactive Python Visual Debugger & Memory Allocator Page."""
    return render(request, 'content/sandbox.html')

@csrf_exempt
def api_execute_code(request):
    """Safe Code Execution API Endpoint."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        code = data.get('code', '')
        language = data.get('language', 'python').lower()

        if not code.strip():
            return JsonResponse({
                'status': 'success',
                'output': '⚠️ Warning: Code string is empty.',
                'execution_time_ms': 0
            })

        start_time = time.time()

        if language == 'python':
            forbidden_keywords = ['import os', 'import subprocess', 'import sys', 'eval(', 'exec(', '__import__', 'open(']
            for kw in forbidden_keywords:
                if kw in code:
                    return JsonResponse({
                        'status': 'error',
                        'output': f'⛔ Security Error: Access to "{kw}" is restricted in sandbox mode.',
                        'execution_time_ms': round((time.time() - start_time) * 1000, 2)
                    })

            old_stdout = sys.stdout
            old_stderr = sys.stderr
            captured_stdout = io.StringIO()
            captured_stderr = io.StringIO()

            sys.stdout = captured_stdout
            sys.stderr = captured_stderr

            exec_globals = {'__builtins__': __builtins__}
            exec_locals = {}

            try:
                exec(code, exec_globals, exec_locals)
                output = captured_stdout.getvalue()
                err_output = captured_stderr.getvalue()
                if err_output:
                    output += "\n" + err_output
                if not output.strip():
                    output = "✅ Code executed successfully with no output."
            except Exception as e:
                output = f"❌ Execution Error:\n{traceback.format_exc()}"
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            execution_time = round((time.time() - start_time) * 1000, 2)
            return JsonResponse({
                'status': 'success',
                'output': output,
                'execution_time_ms': execution_time
            })

        else:
            return JsonResponse({
                'status': 'success',
                'output': f'⚡ JavaScript/Browser execution handled live in client sandbox engine.',
                'execution_time_ms': 1
            })

    except Exception as err:
        return JsonResponse({
            'status': 'error',
            'output': f'❌ Server Error: {str(err)}',
            'execution_time_ms': 0
        }, status=400)


@csrf_exempt
def api_debug_trace(request):
    """
    Python Visual Debugger & Memory Allocation Tracer API.
    Traces Python code line-by-line and records Stack Frames, Heap Memory, & Line Explanations.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        code = data.get('code', '')

        if not code.strip():
            return JsonResponse({'status': 'error', 'message': 'Empty code'}, status=400)

        forbidden_keywords = ['import os', 'import subprocess', 'import sys', 'eval(', 'exec(', '__import__', 'open(']
        for kw in forbidden_keywords:
            if kw in code:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Security Error: "{kw}" is restricted in visual debugger.'
                }, status=403)

        lines = code.splitlines()
        steps = []
        stdout_buf = io.StringIO()
        prev_vars = {}

        def get_var_repr(val):
            val_type = type(val).__name__
            val_id = f"0x{id(val):x}"
            if isinstance(val, (int, float, str, bool, type(None))):
                return {'type': val_type, 'value': repr(val), 'is_primitive': True, 'id': val_id}
            elif isinstance(val, (list, tuple, set)):
                return {'type': val_type, 'value': [get_var_repr(x) for x in val], 'is_primitive': False, 'id': val_id}
            elif isinstance(val, dict):
                return {'type': val_type, 'value': {str(k): get_var_repr(v) for k, v in val.items()}, 'is_primitive': False, 'id': val_id}
            else:
                return {'type': val_type, 'value': str(val), 'is_primitive': False, 'id': val_id}

        def tracer(frame, event, arg):
            if frame.f_code.co_filename != '<string>':
                return tracer

            lineno = frame.f_lineno
            line_text = lines[lineno - 1].strip() if 1 <= lineno <= len(lines) else ""
            if not line_text:
                return tracer

            local_vars = {k: get_var_repr(v) for k, v in frame.f_locals.items() if not k.startswith('__')}

            if event == 'call':
                func_name = frame.f_code.co_name
                explanation = f"📞 Called function '{func_name}()'. Creating new Stack Frame in memory."
            elif event == 'return':
                explanation = f"↩ Returning from function with return value: {repr(arg)}."
            else:
                new_vars = [k for k in local_vars if k not in prev_vars]
                changed_vars = [k for k, v in local_vars.items() if k in prev_vars and prev_vars[k] != v]

                if new_vars:
                    names_str = ", ".join([f"'{k}' = {local_vars[k]['value']}" for k in new_vars])
                    explanation = f"✨ Line {lineno}: Initialized & allocated variable {names_str} in Heap Memory."
                elif changed_vars:
                    names_str = ", ".join([f"'{k}' updated to {local_vars[k]['value']}" for k in changed_vars])
                    explanation = f"🔄 Line {lineno}: Updated memory allocation for {names_str}."
                else:
                    explanation = f"▶ Line {lineno}: Executed statement '{line_text}'."

            prev_vars.clear()
            prev_vars.update(local_vars)

            steps.append({
                'step': len(steps) + 1,
                'line': lineno,
                'line_text': line_text,
                'event': event,
                'explanation': explanation,
                'stack_frame': frame.f_code.co_name if frame.f_code.co_name != '<module>' else 'Global Stack Frame',
                'variables': local_vars,
                'stdout': stdout_buf.getvalue()
            })
            return tracer

        old_stdout = sys.stdout
        sys.stdout = stdout_buf

        try:
            compiled = compile(code, '<string>', 'exec')
            sys.settrace(tracer)
            exec(compiled, {'__builtins__': __builtins__})
        except Exception as e:
            steps.append({
                'step': len(steps) + 1,
                'line': getattr(e, 'lineno', 1),
                'line_text': 'Exception Error',
                'event': 'exception',
                'explanation': f"❌ Exception Error: {str(e)}",
                'stack_frame': 'Error',
                'variables': {},
                'stdout': stdout_buf.getvalue() + f"\n{traceback.format_exc()}"
            })
        finally:
            sys.settrace(None)
            sys.stdout = old_stdout

        return JsonResponse({
            'status': 'success',
            'total_steps': len(steps),
            'steps': steps
        })

    except Exception as err:
        return JsonResponse({
            'status': 'error',
            'message': str(err)
        }, status=400)
