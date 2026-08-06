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

        if not code:
            return JsonResponse({'status': 'error', 'message': 'Code string is empty'}, status=400)

        tracer = PythonExecutionTracer(code, breakpoints=breakpoints)
        result = tracer.execute()

        if result['status'] == 'error':
            return JsonResponse({'status': 'error', 'message': result['message']}, status=400)

        session = DebugSession.objects.create(
            language='python',
            code=code,
            breakpoints=breakpoints,
            total_steps=result['total_steps']
        )

        return JsonResponse({
            'status': 'success',
            'session_id': str(session.session_id),
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

        session = DebugSession.objects.create(
            language='javascript',
            code=code,
            breakpoints=breakpoints,
            total_steps=result['total_steps']
        )

        return JsonResponse({
            'status': 'success',
            'session_id': str(session.session_id),
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

        if not code:
            return JsonResponse({'status': 'error', 'message': 'Code string is empty'}, status=400)

        tracer = JavaExecutionTracer(code, breakpoints=breakpoints)
        result = tracer.execute()

        session = DebugSession.objects.create(
            language='java',
            code=code,
            breakpoints=breakpoints,
            total_steps=result['total_steps']
        )

        return JsonResponse({
            'status': 'success',
            'session_id': str(session.session_id),
            'language': 'java',
            'total_steps': result['total_steps'],
            'execution_time_ms': result['execution_time_ms'],
            'steps': result['steps']
        })

    except Exception as err:
        return JsonResponse({'status': 'error', 'message': str(err)}, status=400)


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
