from rest_framework import serializers
from core.models import CandidatoFormacao, Provincia, Distrito


class CandidatoRecepcaoSerializer(serializers.Serializer):
    """Serializer para receber candidato do DRH"""
    id = serializers.IntegerField()
    codigo_candidato = serializers.CharField(max_length=20)
    nome_completo = serializers.CharField(max_length=255)
    genero = serializers.ChoiceField(choices=CandidatoFormacao.Genero.choices)
    data_nascimento = serializers.DateField(required=False, allow_null=True)
    numero_bi = serializers.CharField(max_length=20)
    numero_telefone = serializers.CharField(max_length=15)
    provincia = serializers.IntegerField()
    distrito = serializers.IntegerField()
    endereco = serializers.CharField(required=False, allow_blank=True)
    vaga_titulo = serializers.CharField(required=False, allow_blank=True)
    
    def create(self, validated_data):
        """Cria CandidatoFormacao a partir dos dados do DRH"""
        
        id_drh = validated_data['id']
        
        if CandidatoFormacao.objects.filter(id_drh=id_drh).exists():
            raise serializers.ValidationError({
                'id_drh': f'Candidato com ID DRH {id_drh} já existe no sistema DEFC'
            })
        
        provincia = Provincia.objects.get(id=validated_data['provincia'])
        distrito = Distrito.objects.get(id=validated_data['distrito'])
        
        vaga_titulo = validated_data.get('vaga_titulo', '').upper()
        tipo_agente = CandidatoFormacao.TipoAgente.BRIGADISTA
        
        if 'FORMADOR' in vaga_titulo:
            tipo_agente = CandidatoFormacao.TipoAgente.FORMADOR
        elif 'AGENTE' in vaga_titulo or 'CIVICO' in vaga_titulo or 'CÍVICO' in vaga_titulo:
            tipo_agente = CandidatoFormacao.TipoAgente.AGENTE_CIVICO
        elif 'MMV' in vaga_titulo or 'MESA' in vaga_titulo:
            tipo_agente = CandidatoFormacao.TipoAgente.MMV
        
        candidato = CandidatoFormacao.objects.create(
            id_drh=id_drh,
            codigo_candidato=validated_data['codigo_candidato'],
            nome_completo=validated_data['nome_completo'],
            genero=validated_data['genero'],
            data_nascimento=validated_data.get('data_nascimento'),
            numero_bi=validated_data['numero_bi'],
            numero_telefone=validated_data['numero_telefone'],
            provincia=provincia,
            distrito=distrito,
            endereco=validated_data.get('endereco', ''),
            tipo_agente=tipo_agente,
            ativo=True
        )
        
        return candidato


class CandidatoFormacaoSerializer(serializers.ModelSerializer):
    """Serializer para CandidatoFormacao"""
    provincia_nome = serializers.CharField(source='provincia.nome', read_only=True)
    distrito_nome = serializers.CharField(source='distrito.nome', read_only=True)
    
    class Meta:
        model = CandidatoFormacao
        fields = [
            'id',
            'id_drh',
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
            'tipo_agente',
            'ativo',
            'data_recepcao',
        ]
        read_only_fields = ['id', 'id_drh', 'codigo_candidato', 'data_recepcao']
