from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .api_views import CandidatoFormacaoAPIViewSet

app_name = 'formacao_api'

router = DefaultRouter()
router.register(r'candidatos', CandidatoFormacaoAPIViewSet, basename='candidato_formacao')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
]
