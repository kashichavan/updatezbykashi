from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from requirements.views import custom_404_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT Authentication Endpoints (Admin / User Login)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('instagram/', include(('instaautomation.urls', 'instaautomation'), namespace='instaautomation')),
    path('debugger/', include(('debugger.urls', 'debugger'), namespace='debugger')),
    path('debug/', RedirectView.as_view(url='/debugger/', permanent=False)),
    path('debuger/', RedirectView.as_view(url='/debugger/', permanent=False)),
    path('DEBUGER/', RedirectView.as_view(url='/debugger/', permanent=False)),
    path('', include('requirements.urls')),
]

handler404 = 'requirements.views.custom_404_view'
