from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from requirements.views import custom_404_view, ads_txt_verification_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # Verification / Ads Text File Root Route
    path('c1a8fc4a2f71995dfc59.txt', ads_txt_verification_view, name='ads_verification_file'),

    # JWT Authentication Endpoints (Admin / User Login)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('debugger/', include(('debugger.urls', 'debugger'), namespace='debugger')),
    path('debug/', RedirectView.as_view(url='/debugger/', permanent=False)),
    path('debuger/', RedirectView.as_view(url='/debugger/', permanent=False)),
    path('DEBUGER/', RedirectView.as_view(url='/debugger/', permanent=False)),
    path('', include('requirements.urls')),
]

handler404 = 'requirements.views.custom_404_view'
