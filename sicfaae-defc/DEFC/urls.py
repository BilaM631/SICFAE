"""
URL configuration for DEFC project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf import settings
from django.conf.urls.static import static
from formacao import views as formacao_views

admin.site.site_header = "DEFC - Departamento de Educação e Formação Cívica"
admin.site.site_title = "DEFC Admin"
admin.site.index_title = "Gestão de Formação"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('formacao/', include('formacao.urls')),
    path('api/', include('formacao.api_urls')),
    
    # Override logout to allow GET requests
    path('accounts/logout/', formacao_views.custom_logout, name='logout'),
    
    path('accounts/', include('django.contrib.auth.urls')),
    path('', RedirectView.as_view(url='/formacao/dashboard/', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
