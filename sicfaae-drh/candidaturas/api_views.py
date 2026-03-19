from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.conf import settings
import requests

from .models import Candidato
from .serializers import CandidatoParaDEFCSerializer, CandidatoListSerializer


class CandidatoAPIViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet para gestão de candidatos.
    Permite consulta e envio de candidatos para DEFC.
    """
    queryset = Candidato.objects.all()
    serializer_class = CandidatoListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        enviado_defc = self.request.query_params.get('enviado_defc')
        if enviado_defc is not None:
            queryset = queryset.filter(enviado_defc=enviado_defc.lower() == 'true')
        
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset.order_by('-data_criacao')
    
    @action(detail=True, methods=['post'])
    def enviar_para_defc(self, request, pk=None):
        """
        Envia candidato aprovado para o sistema DEFC.
        """
        candidato = self.get_object()
        
        if not candidato.pode_enviar_defc:
            return Response({
                'error': 'Candidato não está apto para envio ao DEFC',
                'motivo': self._verificar_requisitos_envio(candidato)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if candidato.enviado_defc:
            return Response({
                'error': 'Candidato já foi enviado para DEFC',
                'id_defc': candidato.id_defc,
                'data_envio': candidato.data_envio_defc
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CandidatoParaDEFCSerializer(candidato)
        
        try:
            defc_api_url = settings.DEFC_API_URL
            defc_token = settings.DEFC_API_TOKEN
            
            if not defc_api_url or not defc_token:
                return Response({
                    'error': 'Configuração de API DEFC não encontrada'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            headers = {
                'Authorization': f'Token {defc_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{defc_api_url}candidatos/receber/',
                json=serializer.data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                response_data = response.json()
                
                candidato.enviado_defc = True
                candidato.data_envio_defc = timezone.now()
                candidato.id_defc = response_data.get('id', '')
                candidato.estado = Candidato.Estado.ENVIADO_DEFC
                candidato.save()
                
                return Response({
                    'success': True,
                    'message': f'Candidato {candidato.nome_completo} enviado para DEFC com sucesso',
                    'id_defc': candidato.id_defc,
                    'data_envio': candidato.data_envio_defc
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Erro ao enviar candidato para DEFC',
                    'defc_response': response.text
                }, status=status.HTTP_502_BAD_GATEWAY)
                
        except requests.exceptions.RequestException as e:
            return Response({
                'error': 'Erro de comunicação com DEFC',
                'details': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({
                'error': 'Erro interno ao processar envio',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _verificar_requisitos_envio(self, candidato):
        """Verifica e retorna motivos pelos quais candidato não pode ser enviado"""
        motivos = []
        
        if candidato.estado != Candidato.Estado.ENTREVISTA_APROVADA:
            motivos.append(f'Estado atual: {candidato.get_estado_display()}. Necessário: Aprovado na Entrevista')
        
        if not candidato.validacao_bi:
            motivos.append('BI não validado')
        
        if not candidato.validacao_cv:
            motivos.append('CV não validado')
        
        if candidato.enviado_defc:
            motivos.append('Já enviado para DEFC')
        
        return motivos
