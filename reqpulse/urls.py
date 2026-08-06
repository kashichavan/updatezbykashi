from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('debugger/', include(('debugger.urls', 'debugger'), namespace='debugger')),
    path('debug/', RedirectView.as_view(url='/debugger/', permanent=False)),
    path('debuger/', RedirectView.as_view(url='/debugger/', permanent=False)),
    path('DEBUGER/', RedirectView.as_view(url='/debugger/', permanent=False)),
    path('', include('requirements.urls')),
]
