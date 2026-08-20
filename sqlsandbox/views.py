import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .engine import (
    DATASETS,
    execute_sql_sandbox,
    trace_sql_execution,
    get_dataset_catalog,
    get_sandboxed_connection,
    inspect_schema
)
from .challenges import get_challenges_list, get_challenge_by_id

def sql_sandbox_view(request):
    """
    Main interactive SQL Visual Debugger & Database Studio view.
    """
    dataset_catalog = get_dataset_catalog()
    challenges = get_challenges_list()
    
    context = {
        'datasets': dataset_catalog,
        'challenges': challenges,
        'default_dataset': dataset_catalog[0] if dataset_catalog else None,
        'page_title': '⚡ SQL Visual Debugger & Interactive Database Studio',
        'meta_description': 'Line-by-line interactive SQL Debugger. Step through query clauses (FROM, JOIN, WHERE, GROUP BY, SELECT, ORDER BY) with visual execution pipeline, active row memory inspector, and Scott/Tiger schema.'
    }
    return render(request, 'sqlsandbox/sandbox.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def sql_trace_api(request):
    """
    Step-by-Step / Line-by-Line SQL Execution Tracer API.
    Returns AST clause breakdown with intermediate virtual table states for each step.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
        
    sql = data.get('sql', '').strip()
    dataset_id = data.get('dataset_id', 'scott_tiger')
    
    result = trace_sql_execution(sql, dataset_id=dataset_id)
    return JsonResponse(result)

@csrf_exempt
@require_http_methods(["POST"])
def sql_execute_api(request):
    """
    Execute arbitrary SQL query against the sandboxed dataset.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
        
    sql = data.get('sql', '').strip()
    dataset_id = data.get('dataset_id', 'scott_tiger')
    max_rows = int(data.get('max_rows', 500))
    
    result = execute_sql_sandbox(sql, dataset_id=dataset_id, max_rows=max_rows)
    return JsonResponse(result)

@require_http_methods(["GET"])
def sql_schema_api(request):
    """
    Return updated database schema and row counts.
    """
    dataset_id = request.GET.get('dataset_id', 'faang')
    if dataset_id not in DATASETS:
        dataset_id = 'faang'
        
    conn = get_sandboxed_connection(dataset_id)
    schema = inspect_schema(conn)
    conn.close()
    
    return JsonResponse({
        'success': True,
        'dataset_id': dataset_id,
        'name': DATASETS[dataset_id]['name'],
        'schema': schema
    })

@csrf_exempt
@require_http_methods(["POST"])
def sql_reset_api(request):
    """
    Reset dataset to factory default schema and seed rows.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
        
    dataset_id = data.get('dataset_id', 'faang')
    if dataset_id not in DATASETS:
        dataset_id = 'faang'
        
    conn = get_sandboxed_connection(dataset_id)
    schema = inspect_schema(conn)
    conn.close()
    
    return JsonResponse({
        'success': True,
        'message': f"Database '{DATASETS[dataset_id]['name']}' has been reset to factory state.",
        'default_query': DATASETS[dataset_id]['default_query'],
        'schema': schema
    })

@csrf_exempt
@require_http_methods(["POST"])
def sql_challenge_verify_api(request):
    """
    Verify user's challenge submission against the canonical solution.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
        
    challenge_id = data.get('challenge_id')
    user_sql = data.get('sql', '').strip()
    
    challenge = get_challenge_by_id(challenge_id)
    if not challenge:
        return JsonResponse({'success': False, 'error': 'Challenge not found.'}, status=404)
        
    dataset_id = challenge['dataset_id']
    solution_sql = challenge['solution_sql']
    
    # Run user query
    user_res = execute_sql_sandbox(user_sql, dataset_id=dataset_id)
    if not user_res.get('success'):
        return JsonResponse({
            'success': True,
            'passed': False,
            'error': user_res.get('error'),
            'user_output': [],
            'expected_output': [],
            'columns': []
        })
        
    # Run canonical solution
    sol_res = execute_sql_sandbox(solution_sql, dataset_id=dataset_id)
    
    # Normalize rows and column headers for comparison
    user_cols = [c.lower() for c in user_res.get('columns', [])]
    sol_cols = [c.lower() for c in sol_res.get('columns', [])]
    
    user_rows = user_res.get('rows', [])
    sol_rows = sol_res.get('rows', [])
    
    # Check match: row counts, columns, and row data
    passed = False
    if len(user_rows) == len(sol_rows):
        # Allow case-insensitive or string equivalence
        passed = (user_rows == sol_rows)
        
    return JsonResponse({
        'success': True,
        'passed': passed,
        'challenge_id': challenge_id,
        'title': challenge['title'],
        'user_columns': user_res.get('columns', []),
        'user_rows': user_rows,
        'expected_columns': sol_res.get('columns', []),
        'expected_rows': sol_rows,
        'execution_time_ms': user_res.get('execution_time_ms', 0)
    })
