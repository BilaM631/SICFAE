from rest_framework import serializers
from .models import Candidato, Vaga
from core.models import Provincia, Distrito


class CandidatoParaDEFCSerializer(serializers.ModelSerializer):
    """Serializer para enviar candidato para DEFC"""
    provincia_nome = serializers.CharField(source='provincia.nome', read_only=True)
    distrito_nome = serializers.CharField(source='distrito.nome', read_only=True)
    vaga_titulo = serializers.CharField(source='vaga.titulo', read_only=True)
    
    class Meta:
        model = Candidato
        fields = [
            'id',
            'codigo_candidato',
            'nome_completo',
            'genero',
            'data_nascimento',
            'numero_bi',
            'numero_telefone',
            'provincia',
            'provincia_nome',
            'distrito',
            'distrito_nome',
            'endereco',
            'vaga',
            'vaga_titulo',
            'estado',
            'foto',
        ]
        read_only_fields = ['id', 'codigo_candidato', 'estado']


class CandidatoListSerializer(serializers.ModelSerializer):
    """Serializer para listagem de candidatos"""
    provincia_nome = serializers.CharField(source='provincia.nome', read_only=True)
    distrito_nome = serializers.CharField(source='distrito.nome', read_only=True)
    
    class Meta:
        model = Candidato
        fields = [
            'id',
            'codigo_candidato',
            'nome_completo',
            'numero_bi',
            'genero',
            'provincia_nome',
            'distrito_nome',
            'estado',
            'enviado_defc',
            'data_envio_defc',
            'id_defc',
        ]
