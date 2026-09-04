from django.urls import path
from . import views
from debugger.views import learn_topic_view

urlpatterns = [
    path('', views.index_view, name='index'),
    path('intro/', views.intro_view, name='intro'),
    path('welcome/', views.intro_view, name='welcome'),
    path('about/', views.about_view, name='about'),
    path('youtube/', views.youtube_view, name='youtube'),
    
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
    path('sw.js', views.service_worker_view, name='service_worker_sw'),
    path('sw.js/', views.service_worker_view, name='service_worker_sw_slash'),
    path('service-worker.js', views.service_worker_view, name='service_worker_full'),
    path('sitemap.xml', views.sitemap_xml_view, name='sitemap_xml'),
    path('rss.xml', views.rss_feed_view, name='rss_xml'),
    path('feed.xml', views.rss_feed_view, name='feed_xml'),
    path('feed/', views.rss_feed_view, name='feed_slash'),
    path('7e4c3a9d2b1f8e5a0c6d7b8a9e1f2c3d.txt', views.indexnow_key_view, name='indexnow_key'),
    path('indexnow.txt', views.indexnow_key_view, name='indexnow_key_alias'),
    path('robots.txt', views.robots_txt_view, name='robots_txt'),
    path('ads.txt', views.ads_txt_view, name='ads_txt'),
    path('ads.txt/', views.ads_txt_view, name='ads_txt_slash'),
    path('app-ads.txt', views.ads_txt_view, name='app_ads_txt'),
    path('app-ads.txt/', views.ads_txt_view, name='app_ads_txt_slash'),

    path('category/<slug:slug>/', views.category_detail_view, name='category_detail'),
    path('category/<slug:category_slug>/job/<uuid:uuid>/', views.job_detail_view, name='category_job_detail'),
    path('job/<uuid:uuid>/', views.job_detail_view, name='job_detail'),
    path('job/<int:pk>/', views.job_detail_view, name='job_detail_pk'),
    path('group/<slug:slug>/', views.group_detail_view, name='group_detail'),
    path('groups/<slug:slug>/', views.group_detail_view, name='group_detail_alias'),
    path('owner/', views.owner_view, name='owner'),
    path('owner/bulk-parser/', views.owner_view, name='owner_bulk_parser'),
    path('owner/single-parser/', views.owner_view, name='owner_single_parser'),
    path('owner/post-job/', views.owner_view, name='owner_post_job'),
    path('owner/manage-jobs/', views.owner_view, name='owner_manage_jobs'),
    path('owner/jobdexo-sync/', views.owner_view, name='owner_jobdexo_sync'),
    path('owner/analytics/', views.owner_view, name='owner_analytics'),
    path('owner/categories/', views.owner_view, name='owner_categories'),
    path('owner/groups/', views.owner_view, name='owner_groups'),
    path('owner/activity/', views.owner_view, name='owner_activity'),

    # Public API Endpoints
    path('api/ping', views.api_ping, name='api_ping'),
    path('api/ping/', views.api_ping, name='api_ping_slash'),
    path('api/cron/sync-jobs/', views.api_cron_sync_jobs, name='api_cron_sync_jobs'),
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/groups/', views.api_groups, name='api_groups'),
    path('api/jobs/', views.api_jobs, name='api_jobs'),
    path('api/jobs/<int:pk>/', views.api_job_detail, name='api_job_detail'),
    path('api/jobs/<int:pk>/ig-story-image/', views.api_job_ig_story_image, name='api_job_ig_story_image'),
    path('api/youtube/videos/', views.api_youtube_videos, name='api_youtube_videos'),

    # Owner Admin Portal Endpoints
    path('api/admin/login/', views.api_admin_login, name='api_admin_login'),
    path('api/admin/logout/', views.api_admin_logout, name='api_admin_logout'),
    path('api/admin/status/', views.api_admin_status, name='api_admin_status'),
    path('api/owner/categories/', views.api_owner_categories, name='api_owner_categories'),
    path('api/owner/groups/', views.api_owner_groups, name='api_owner_groups'),
    path('api/owner/groups/move-jobs/', views.api_owner_groups_move_jobs, name='api_owner_groups_move_jobs'),
    path('api/owner/groups/auto-organize/', views.api_owner_groups_auto_organize, name='api_owner_groups_auto_organize'),
    path('api/owner/groups/<int:group_pk>/remove-job/<int:job_pk>/', views.api_owner_group_remove_job, name='api_owner_group_remove_job'),
    path('api/owner/groups/<int:pk>/broadcast/', views.api_owner_group_broadcast, name='api_owner_group_broadcast'),
    path('api/owner/groups/<int:pk>/delete/', views.api_owner_group_delete, name='api_owner_group_delete'),
    path('api/owner/jobs/<int:pk>/delete/', views.api_owner_job_delete, name='api_owner_job_delete'),
    path('api/owner/jobs/<int:pk>/update/', views.api_owner_job_update, name='api_owner_job_update'),
    path('api/owner/jobs/<int:pk>/toggle-status/', views.api_owner_job_toggle_status, name='api_owner_job_toggle_status'),
    path('api/owner/parse-and-post/', views.api_owner_parse_and_post, name='api_owner_parse_and_post'),
    path('api/owner/bulk-parse-and-post/', views.api_owner_bulk_parse_and_post, name='api_owner_bulk_parse_and_post'),
    path('api/owner/jobdexo/import-urls/', views.api_owner_jobdexo_import, name='api_owner_jobdexo_import'),
    path('api/owner/jobdexo/fetch-latest/', views.api_owner_jobdexo_fetch_latest, name='api_owner_jobdexo_fetch_latest'),
    path('api/owner/jobdexo/cleanup/', views.api_owner_jobdexo_cleanup_duplicates, name='api_owner_jobdexo_cleanup_duplicates'),
    path('api/owner/analytics/', views.api_owner_analytics, name='api_owner_analytics'),
    path('api/owner/kpi-stats/', views.api_owner_kpi_stats, name='api_owner_kpi_stats'),
]
