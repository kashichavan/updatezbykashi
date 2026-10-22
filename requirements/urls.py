from django.urls import path
from django.views.generic import RedirectView
from . import views
from debugger.views import learn_topic_view

urlpatterns = [
    path('', views.index_view, name='index'),
    path('intro/', views.intro_view, name='intro'),
    path('welcome/', views.intro_view, name='welcome'),
    path('about/', views.about_view, name='about'),
    path('youtube/', views.youtube_view, name='youtube'),
    
    # Redirect removed academy routes cleanly to home
    path('learn/', RedirectView.as_view(url='/', permanent=False), name='learn_root'),
    path('learn/<path:subpath>/', RedirectView.as_view(url='/', permanent=False)),

    # Guides & Educational Articles Hub (AdSense High Value Content)
    path('guides/', views.guides_list_view, name='guides_list'),
    path('guides/<slug:slug>/', views.guide_detail_view, name='guide_detail'),
    path('tutorials/', views.guides_list_view, name='tutorials_list'),

    # ATS 90+ Score Resume Generator & Enterprise Project Matcher
    path('resume/', views.resume_builder_view, name='resume_builder'),
    path('resume-builder/', views.resume_builder_view, name='resume_builder_alias'),
    path('api/resume/download-pdf/', views.api_download_resume_pdf, name='api_download_resume_pdf'),
    path('api/resume/download-docx/', views.api_download_resume_docx, name='api_download_resume_docx'),
    path('api/resume/template/<slug:role>/', views.api_resume_template, name='api_resume_template'),
    path('api/resume/evaluate/', views.api_ats_score_eval, name='api_ats_score_eval'),
    path('api/resume/score-project/', views.api_score_project_ats, name='api_score_project_ats'),
    path('api/resume/bengaluru-projects/', views.api_bengaluru_projects, name='api_bengaluru_projects'),
    path('api/projects/indian-demo/', views.api_indian_demo_projects, name='api_indian_demo_projects'),
    path('api/projects/indian-demo/match/', views.api_match_indian_projects_for_job, name='api_match_indian_projects_for_job'),
    path('api/resume/attach-indian-project/', views.api_resume_attach_indian_project, name='api_resume_attach_indian_project'),
    path('api/resume/upload/', views.api_resume_upload, name='api_resume_upload'),
    
    # Job-Specific AI Resume Generation & GitHub Project Discovery Pipeline
    path('api/resume/generations/', views.api_resume_generation_create, name='api_resume_generation_create'),
    path('api/resume/generations/<uuid:job_uuid>/', views.api_resume_generation_status, name='api_resume_generation_status'),
    path('api/resume/generations/<uuid:job_uuid>/projects/', views.api_resume_generation_projects, name='api_resume_generation_projects'),
    path('api/resume/generations/<uuid:job_uuid>/projects/select/', views.api_resume_generation_select_projects, name='api_resume_generation_select_projects'),
    path('api/resume/generations/<uuid:job_uuid>/generate/', views.api_resume_generation_finalize, name='api_resume_generation_finalize'),
    path('api/resume/github-discovery/', views.api_resume_github_discovery_direct, name='api_resume_github_discovery_direct'),

    # India-Wide Multi-Source Job Aggregation & Last-Hour Discovery Endpoints
    path('api/jobs/feed/', views.api_jobs_list, name='api_jobs_feed'),
    path('api/jobs/search/', views.api_jobs_list, name='api_jobs_search'),
    path('api/jobs/last-hour/', views.api_jobs_last_hour, name='api_jobs_last_hour'),
    path('api/jobs/ingest/', views.api_jobs_ingest_trigger, name='api_jobs_ingest_trigger'),
    path('api/jobs/ingestion-status/', views.api_jobs_ingestion_status, name='api_jobs_ingestion_status'),
    path('api/jobs/deduplicate/', views.api_jobs_deduplicate, name='api_jobs_deduplicate'),

    # AI Job Description Generator & Career Suite
    path('tools/job-description-generator/', views.job_description_generator_view, name='job_description_generator'),
    path('jd-generator/', views.job_description_generator_view, name='jd_generator_alias'),
    path('ai-job-description/', views.job_description_generator_view, name='ai_jd_alias'),
    path('api/ai/generate-jd/', views.api_ai_generate_jd, name='api_ai_generate_jd'),
    path('api/ai/polish-bullet/', views.api_ai_polish_bullet, name='api_ai_polish_bullet'),
    path('api/ai/tailor-resume/', views.api_ai_tailor_resume, name='api_ai_tailor_resume'),
    path('api/ai/alter-resume/', views.api_ai_alter_resume, name='api_ai_alter_resume'),
    path('api/ai/generate-summary/', views.api_ai_generate_summary, name='api_ai_generate_summary'),
    path('api/ai/github-project/', views.api_ai_github_project, name='api_ai_github_project'),

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
    path('job/<uuid:uuid>/apply/', views.job_apply_redirect_view, name='job_apply_redirect'),
    path('apply/<uuid:uuid>/', views.job_apply_redirect_view, name='direct_apply_redirect'),
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
    path('api/owner/verify-links/', views.api_owner_verify_links, name='api_owner_verify_links'),
    path('api/owner/backup/trigger/', views.api_owner_trigger_backup, name='api_owner_trigger_backup'),
]

