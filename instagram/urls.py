from django.urls import path
from . import views

app_name = 'instagram'

urlpatterns = [
    # Dashboard & Connection
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_alt'),
    path('connect/', views.dashboard_view, name='connect'),

    # Automation Management Routes
    path('automations/', views.automation_list_view, name='automation_list'),
    path('automations/create/', views.automation_create_view, name='automation_create'),
    path('automations/<uuid:uuid>/', views.automation_detail_view, name='automation_detail'),
    path('automations/<uuid:uuid>/activate/', views.automation_activate_view, name='automation_activate'),
    path('automations/<uuid:uuid>/pause/', views.automation_pause_view, name='automation_pause'),
    path('automations/<uuid:uuid>/delete/', views.automation_delete_view, name='automation_delete'),

    # Webhook Endpoint & Simulation API
    path('webhooks/instagram/', views.webhook_endpoint, name='webhook'),
    path('api/instagram/webhook/', views.webhook_endpoint, name='webhook_legacy'),
    path('api/simulate/', views.api_simulate_trigger, name='api_simulate'),
]
