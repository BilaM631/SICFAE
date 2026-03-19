from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .api_views import CandidatoAPIViewSet

app_name = 'candidaturas_api'

router = DefaultRouter()
router.register(r'candidatos', CandidatoAPIViewSet, basename='candidato')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
]
