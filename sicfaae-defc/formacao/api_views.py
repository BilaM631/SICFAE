from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import CandidatoFormacao
from .serializers import CandidatoRecepcaoSerializer, CandidatoFormacaoSerializer


class CandidatoFormacaoAPIViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet para gestão de candidatos em formação.
    """
    queryset = CandidatoFormacao.objects.all()
    serializer_class = CandidatoFormacaoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        tipo_agente = self.request.query_params.get('tipo_agente')
        if tipo_agente:
            queryset = queryset.filter(tipo_agente=tipo_agente)
        
        ativo = self.request.query_params.get('ativo')
        if ativo is not None:
            queryset = queryset.filter(ativo=ativo.lower() == 'true')
        
        return queryset.order_by('-data_recepcao')
    
    @action(detail=False, methods=['post'])
    def receber(self, request):
        """
        Endpoint para receber candidato do sistema DRH.
        Cria um novo CandidatoFormacao com os dados recebidos.
        """
        serializer = CandidatoRecepcaoSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Dados inválidos',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            candidato = serializer.save()
            
            response_serializer = CandidatoFormacaoSerializer(candidato)
            
            return Response({
                'success': True,
                'message': f'Candidato {candidato.nome_completo} recebido com sucesso',
                'candidato': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': 'Erro ao criar candidato',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
