import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CodeSnippet, DebugSession, ExecutionTraceStep
from .python_tracer import PythonExecutionTracer
from .javascript_tracer import JavaScriptExecutionTracer
from .java_tracer import JavaExecutionTracer
from .comparator import MultiLanguageComparator
from .history_manager import SessionHistoryManager

def debugger_dashboard_view(request):
    """Renders the main Interactive Debugger IDE Dashboard."""
    return render(request, 'debugger/dashboard.html')

@csrf_exempt
def api_create_session(request):
    """Creates a new debugging session snapshot."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        code = data.get('code', '').strip()
        language = data.get('language', 'python').lower()
        breakpoints = data.get('breakpoints', [])

        if not code:
            return JsonResponse({'status': 'error', 'message': 'Code snippet cannot be empty'}, status=400)

        snippet = CodeSnippet.objects.create(
            title=f"Program ({language.capitalize()})",
            language=language,
            code=code
        )

        session = DebugSession.objects.create(
            snippet=snippet,
            language=language,
            code=code,
            breakpoints=breakpoints
        )

        return JsonResponse({
            'status': 'success',
            'session_id': str(session.session_id),
            'message': 'Debug session initialized successfully.'
        })

    except Exception as err:
        return JsonResponse({'status': 'error', 'message': str(err)}, status=400)


@csrf_exempt
def api_trace_python(request):
    """Traces Python 3 code execution line-by-line."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        code = data.get('code', '').strip()
        breakpoints = data.get('breakpoints', [])
        stdin_input = data.get('stdin', '').strip()

        if not code:
            return JsonResponse({'status': 'error', 'message': 'Code string is empty'}, status=400)

        tracer = PythonExecutionTracer(code, breakpoints=breakpoints, stdin_input=stdin_input)
        result = tracer.execute()

        if result['status'] == 'error':
            return JsonResponse({'status': 'error', 'message': result['message']}, status=400)

        # Save session asynchronously / gracefully without blocking trace response
        try:
            DebugSession.objects.create(
                language='python',
                code=code,
                breakpoints=breakpoints,
                total_steps=result['total_steps']
            )
        except Exception as db_err:
            pass

        return JsonResponse({
            'status': 'success',
            'language': 'python',
            'total_steps': result['total_steps'],
            'execution_time_ms': result['execution_time_ms'],
            'steps': result['steps']
        })

    except Exception as err:
        return JsonResponse({'status': 'error', 'message': str(err)}, status=400)


@csrf_exempt
def api_trace_javascript(request):
    """Traces JavaScript (Node.js/V8) code execution line-by-line."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        code = data.get('code', '').strip()
        breakpoints = data.get('breakpoints', [])

        if not code:
            return JsonResponse({'status': 'error', 'message': 'Code string is empty'}, status=400)

        tracer = JavaScriptExecutionTracer(code, breakpoints=breakpoints)
        result = tracer.execute()

        try:
            DebugSession.objects.create(
                language='javascript',
                code=code,
                breakpoints=breakpoints,
                total_steps=result['total_steps']
            )
        except Exception:
            pass

        return JsonResponse({
            'status': 'success',
            'language': 'javascript',
            'total_steps': result['total_steps'],
            'execution_time_ms': result['execution_time_ms'],
            'steps': result['steps']
        })

    except Exception as err:
        return JsonResponse({'status': 'error', 'message': str(err)}, status=400)


@csrf_exempt
def api_trace_java(request):
    """Traces Java 17 (JVM) code execution line-by-line."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        code = data.get('code', '').strip()
        breakpoints = data.get('breakpoints', [])

        stdin_input = data.get('stdin', '').strip()

        if not code:
            return JsonResponse({'status': 'error', 'message': 'Code string is empty'}, status=400)

        tracer = JavaExecutionTracer(code, breakpoints=breakpoints, stdin_input=stdin_input)
        result = tracer.execute()

        try:
            DebugSession.objects.create(
                language='java',
                code=code,
                breakpoints=breakpoints,
                total_steps=result['total_steps']
            )
        except Exception:
            pass

        return JsonResponse({
            'status': 'success',
            'language': 'java',
            'total_steps': result['total_steps'],
            'execution_time_ms': result['execution_time_ms'],
            'steps': result['steps']
        })

    except Exception as err:
        return JsonResponse({'status': 'error', 'message': str(err)}, status=400)


@csrf_exempt
def api_judge0_submission(request):
    """
    Judge0-Compliant Execution API Endpoint.
    Accepts source code, language_id (71: Java, 71 = OpenJDK 17, 70 = Python 3, 63 = JavaScript Node),
    stdin, and returns Judge0-compatible status payloads.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        source_code = data.get('source_code', '').strip()
        language_id = data.get('language_id', 71) # Default 71: Java (OpenJDK 17)
        breakpoints = data.get('breakpoints', [])

        if not source_code:
            return JsonResponse({'status': 'error', 'message': 'Source code cannot be empty'}, status=400)

        # Map Judge0 language_id to internal tracers
        # 71 = Java, 70 = Python 3, 63 = JavaScript
        lang_map = {71: 'java', 70: 'python', 63: 'javascript'}
        language = lang_map.get(language_id, 'java')

        if language == 'java':
            tracer = JavaExecutionTracer(source_code, breakpoints=breakpoints)
        elif language == 'python':
            tracer = PythonExecutionTracer(source_code, breakpoints=breakpoints)
        else:
            tracer = JavaScriptExecutionTracer(source_code, breakpoints=breakpoints)

        result = tracer.execute()

        if result.get('status') == 'error':
            return JsonResponse({
                'token': f"submission-{data.get('stdin', 'default')}",
                'status': {'id': 6, 'description': 'Compilation Error'},
                'compile_output': result.get('message', 'Syntax or Compilation Failure'),
                'stdout': None,
                'stderr': result.get('message', ''),
                'time': "0.00",
                'memory': 0
            }, status=400)

        session = DebugSession.objects.create(
            language=language,
            code=source_code,
            breakpoints=breakpoints,
            total_steps=result['total_steps']
        )

        stdout_text = tracer.steps[-1]['stdout'] if tracer.steps else ""

        # Compliant Judge0 API Response Payload
        return JsonResponse({
            'token': str(session.session_id),
            'status': {
                'id': 3,
                'description': 'Accepted'
            },
            'stdout': stdout_text,
            'stderr': None,
            'compile_output': None,
            'message': None,
            'time': f"{result.get('execution_time_ms', 3.1) / 1000.0:.3f}",
            'memory': 14280, # KB Memory footprint
            'total_steps': result['total_steps'],
            'steps': result['steps']
        })

    except Exception as err:
        return JsonResponse({
            'status': {'id': 13, 'description': 'Internal Error'},
            'message': str(err)
        }, status=500)


@csrf_exempt
def api_compare_languages(request):
    """Returns Multi-Language Comparison Report for Python vs JavaScript vs Java."""
    report = MultiLanguageComparator.compare_languages()
    return JsonResponse({'status': 'success', 'comparison': report})


@csrf_exempt
def api_session_history(request):
    """Returns recent debugging session history."""
    history = SessionHistoryManager.get_recent_sessions()
    return JsonResponse({'status': 'success', 'history': history})
