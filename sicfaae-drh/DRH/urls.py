"""
URL configuration for DRH project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "DRH - Direção de Recursos Humanos"
admin.site.site_title = "DRH Admin"
admin.site.index_title = "Gestão de Candidaturas"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('candidaturas/', include('candidaturas.urls')),
    path('api/', include('candidaturas.api_urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', RedirectView.as_view(url='/candidaturas/', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
