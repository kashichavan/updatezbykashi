from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sandbox/', include(('coding_sandbox.urls', 'coding_sandbox'), namespace='sandbox')),
    path('', include('requirements.urls')),
]
