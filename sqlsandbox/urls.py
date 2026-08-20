from django.urls import path
from .views import (
    sql_sandbox_view,
    sql_execute_api,
    sql_trace_api,
    sql_schema_api,
    sql_reset_api,
    sql_challenge_verify_api
)

app_name = 'sqlsandbox'

urlpatterns = [
    path('', sql_sandbox_view, name='sandbox'),
    path('api/execute/', sql_execute_api, name='api_execute'),
    path('api/trace/', sql_trace_api, name='api_trace'),
    path('api/schema/', sql_schema_api, name='api_schema'),
    path('api/reset/', sql_reset_api, name='api_reset'),
    path('api/verify/', sql_challenge_verify_api, name='api_verify'),
]
