from django.urls import path
from . import views

app_name = 'debugger'

urlpatterns = [
    path('', views.debugger_dashboard_view, name='dashboard'),
    
    # Interactive Academy & Topic Learning Engine
    path('learn/', views.learn_topic_view, name='learn_root'),
    path('learn/<slug:lang>/', views.learn_topic_view, name='learn_lang'),
    path('learn/<slug:lang>/<slug:topic_slug>/', views.learn_topic_view, name='learn_topic_detail'),

    path('api/session/create/', views.api_create_session, name='api_create_session'),
    path('api/python/trace/', views.api_trace_python, name='api_trace_python'),
    path('api/javascript/trace/', views.api_trace_javascript, name='api_trace_javascript'),
    path('api/java/trace/', views.api_trace_java, name='api_trace_java'),
    path('api/compare/', views.api_compare_languages, name='api_compare_languages'),
    path('api/history/', views.api_session_history, name='api_session_history'),
    path('api/submissions/', views.api_judge0_submission, name='api_judge0_submission'),
]

