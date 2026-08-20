from django.urls import path, include
from . import views
from debugger.views import learn_topic_view
from sqlsandbox.views import (
    sql_sandbox_view,
    sql_execute_api,
    sql_schema_api,
    sql_reset_api,
    sql_challenge_verify_api
)

urlpatterns = [
    path('', views.index_view, name='index'),
    path('about/', views.about_view, name='about'),
    path('youtube/', views.youtube_view, name='youtube'),
    
    # SQL Sandbox & Studio Direct Routes
    path('sql/', sql_sandbox_view, name='sql_sandbox_root'),
    path('sql-sandbox/', sql_sandbox_view, name='sql_sandbox_alias'),
    path('sql/api/execute/', sql_execute_api, name='sql_api_execute_direct'),
    path('sql/api/schema/', sql_schema_api, name='sql_api_schema_direct'),
    path('sql/api/reset/', sql_reset_api, name='sql_api_reset_direct'),
    path('sql/api/verify/', sql_challenge_verify_api, name='sql_api_verify_direct'),
    
    # Interactive Developer Academy (Python, Java, JavaScript with Analogies & Live Debugger)
    path('learn/', learn_topic_view, name='learn_root'),
    path('learn/<slug:lang>/', learn_topic_view, name='learn_lang'),
    path('learn/<slug:lang>/<slug:topic_slug>/', learn_topic_view, name='learn_topic_detail'),

    # Guides & Educational Articles Hub (AdSense High Value Content)
    path('guides/', views.guides_list_view, name='guides_list'),
    path('guides/<slug:slug>/', views.guide_detail_view, name='guide_detail'),
    path('tutorials/', views.guides_list_view, name='tutorials_list'),

    # Mandatory Legal & Compliance Pages (AdSense Policy Requirements)
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('privacy/', views.privacy_policy_view, name='privacy_policy_alias'),
    path('terms/', views.terms_view, name='terms'),
    path('terms-and-conditions/', views.terms_view, name='terms_alias'),
    path('disclaimer/', views.disclaimer_view, name='disclaimer'),
    path('contact/', views.contact_view, name='contact'),
    path('contact-us/', views.contact_view, name='contact_alias'),

    # Search Engine & Crawler Discovery Endpoints
    path('sitemap.xml', views.sitemap_xml_view, name='sitemap_xml'),
    path('robots.txt', views.robots_txt_view, name='robots_txt'),
    path('ads.txt', views.ads_txt_view, name='ads_txt'),

    path('category/<slug:slug>/', views.category_detail_view, name='category_detail'),
    path('category/<slug:category_slug>/job/<uuid:uuid>/', views.job_detail_view, name='category_job_detail'),
    path('job/<uuid:uuid>/', views.job_detail_view, name='job_detail'),
    path('job/<int:pk>/', views.job_detail_view, name='job_detail_pk'),
    path('owner/', views.owner_view, name='owner'),
    path('owner/bulk-parser/', views.owner_view, name='owner_bulk_parser'),
    path('owner/single-parser/', views.owner_view, name='owner_single_parser'),
    path('owner/post-job/', views.owner_view, name='owner_post_job'),
    path('owner/manage-jobs/', views.owner_view, name='owner_manage_jobs'),
    path('owner/categories/', views.owner_view, name='owner_categories'),

    # Public API Endpoints
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/jobs/', views.api_jobs, name='api_jobs'),
    path('api/jobs/<int:pk>/', views.api_job_detail, name='api_job_detail'),
    path('api/jobs/<int:pk>/ig-story-image/', views.api_job_ig_story_image, name='api_job_ig_story_image'),
    path('api/youtube/videos/', views.api_youtube_videos, name='api_youtube_videos'),

    # Owner Admin Portal Endpoints
    path('api/admin/login/', views.api_admin_login, name='api_admin_login'),
    path('api/admin/logout/', views.api_admin_logout, name='api_admin_logout'),
    path('api/admin/status/', views.api_admin_status, name='api_admin_status'),
    path('api/owner/categories/', views.api_owner_categories, name='api_owner_categories'),
    path('api/owner/jobs/<int:pk>/delete/', views.api_owner_job_delete, name='api_owner_job_delete'),
    path('api/owner/jobs/<int:pk>/update/', views.api_owner_job_update, name='api_owner_job_update'),
    path('api/owner/jobs/<int:pk>/toggle-status/', views.api_owner_job_toggle_status, name='api_owner_job_toggle_status'),
    path('api/owner/parse-and-post/', views.api_owner_parse_and_post, name='api_owner_parse_and_post'),
    path('api/owner/bulk-parse-and-post/', views.api_owner_bulk_parse_and_post, name='api_owner_bulk_parse_and_post'),
]
