from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from requirements.views import (
    ads_txt_verification_view,
    ads_txt_view,
    randstad_svg_view,
    api_ping,
    sitemap_xml_view,
    robots_txt_view,
    rss_feed_view,
    indexnow_key_view,
)
from api.ninja_api import api as ninja_api

urlpatterns = [
    path('admin/', admin.site.urls),

    # Job Listing SVG Sprite Assets
    path('jobs-app/src/assets/img/randstad.svg', randstad_svg_view, name='randstad_svg'),

    # Keep-Alive & Healthcheck Endpoint
    path('api/ping', api_ping, name='api_ping'),
    path('api/ping/', api_ping, name='api_ping_slash'),

    # Search Engine & Crawler Discovery Root Routes
    path('sitemap.xml', sitemap_xml_view, name='sitemap_xml_root'),
    path('robots.txt', robots_txt_view, name='robots_txt_root'),
    path('rss.xml', rss_feed_view, name='rss_xml_root'),
    path('feed.xml', rss_feed_view, name='feed_xml_root'),
    path('feed/', rss_feed_view, name='feed_slash_root'),
    path('7e4c3a9d2b1f8e5a0c6d7b8a9e1f2c3d.txt', indexnow_key_view, name='indexnow_key_root'),
    path('indexnow.txt', indexnow_key_view, name='indexnow_key_alias_root'),

    # Verification / Ads Text File Root Routes
    path('ads.txt', ads_txt_view, name='ads_txt'),
    path('ads.txt/', ads_txt_view, name='ads_txt_slash'),
    path('app-ads.txt', ads_txt_view, name='app_ads_txt'),
    path('app-ads.txt/', ads_txt_view, name='app_ads_txt_slash'),
    path('c1a8fc4a2f71995dfc59.txt', ads_txt_verification_view, name='ads_verification_file'),

    # Direct Learning Academy Routes (Cleanly redirected to home)
    path('learn/', RedirectView.as_view(url='/', permanent=False), name='learn_root'),
    path('learn/<path:subpath>/', RedirectView.as_view(url='/', permanent=False)),

    # JWT Authentication Endpoints (Admin / User Login)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('debugger/', include(('debugger.urls', 'debugger'), namespace='debugger')),
    path('debug/', RedirectView.as_view(url='/debugger/', permanent=False)),
    path('debuger/', RedirectView.as_view(url='/debugger/', permanent=False)),
    path('DEBUGER/', RedirectView.as_view(url='/debugger/', permanent=False)),
    path('code-editor/', RedirectView.as_view(url='/debugger/', permanent=True)),
    path('online-compiler/', RedirectView.as_view(url='/debugger/', permanent=True)),
    path('python-compiler/', RedirectView.as_view(url='/debugger/', permanent=True)),
    path('compiler/', RedirectView.as_view(url='/debugger/', permanent=True)),
    path('jobs/', RedirectView.as_view(url='/', permanent=True)),
    path('careers/', RedirectView.as_view(url='/', permanent=True)),
    path('internships/', RedirectView.as_view(url='/', permanent=True)),
    path('sql/', include(('sqlsandbox.urls', 'sqlsandbox'), namespace='sqlsandbox')),
    path('sql-sandbox/', RedirectView.as_view(url='/sql/', permanent=False)),
    path('sqlsandbox/', RedirectView.as_view(url='/sql/', permanent=False)),
    path('blog/', RedirectView.as_view(url='/', permanent=False)),
    path('blog/<path:subpath>/', RedirectView.as_view(url='/', permanent=False)),
    path('api/v1/', ninja_api.urls),
    path('', include('requirements.urls')),
]

handler404 = 'requirements.views.custom_404_view'

