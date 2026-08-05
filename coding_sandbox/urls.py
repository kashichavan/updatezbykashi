from django.urls import path
from . import views

app_name = 'coding_sandbox'

urlpatterns = [
    path('', views.sandbox_view, name='index'),
    path('api/execute/', views.api_execute_code, name='api_execute_code'),
    path('api/debug/', views.api_debug_trace, name='api_debug_trace'),
]
