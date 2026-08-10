from django.urls import path
from . import views
from .webhooks.instagram import instagram_webhook

app_name = 'instaautomation'

urlpatterns = [
    # Dashboard & Connection
    path('', views.dashboard_view, name='dashboard'),
    path('connect/', views.connect_view, name='connect'),
    path('oauth/callback/', views.oauth_callback_view, name='oauth_callback'),
    path('reconnect/', views.reconnect_view, name='reconnect'),
    path('reconnect/<int:pk>/', views.reconnect_view, name='reconnect_pk'),
    path('disconnect/', views.disconnect_view, name='disconnect'),
    path('disconnect/<int:pk>/', views.disconnect_view, name='disconnect_pk'),
    path('switch/<int:pk>/', views.switch_account_view, name='switch_account'),
    path('account/', views.account_detail_view, name='account'),

    # Automation CRUD
    path('automations/', views.automation_list_view, name='automation_list'),
    path('automations/create/', views.automation_create_view, name='automation_create'),
    path('automations/<int:pk>/edit/', views.automation_edit_view, name='automation_edit'),
    path('automations/<int:pk>/toggle/', views.automation_toggle_view, name='automation_toggle'),
    path('automations/<int:pk>/delete/', views.automation_delete_view, name='automation_delete'),

    # Conversations & Chat Logs
    path('conversations/', views.conversations_view, name='conversations'),
    path('conversations/<int:pk>/', views.conversation_detail_view, name='conversation_detail'),

    # Meta Webhook Endpoint
    path('api/instagram/webhook/', instagram_webhook, name='webhook'),
]
