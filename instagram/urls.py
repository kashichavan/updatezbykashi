from django.urls import path
from . import views

app_name = 'instagram'

urlpatterns = [
    # Dashboard View
    path('', views.insta_dashboard_view, name='dashboard'),

    # Meta Webhook Verification & Listener
    path('api/instagram/webhook/', views.meta_webhook_endpoint, name='webhook'),

    # REST APIs for Dashboard UI
    path('api/rules/', views.api_rules_list_create, name='api_rules'),
    path('api/rules/<int:rule_id>/', views.api_rule_toggle_delete, name='api_rule_detail'),
    path('api/logs/', views.api_logs_list, name='api_logs'),
    path('api/simulate/', views.api_simulate_trigger, name='api_simulate'),
]
