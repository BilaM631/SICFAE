from django.db.models import Count, Q, Prefetch
from .models import Candidato, Provincia, Distrito, PerfilUtilizador

class GestorEstatisticas:
    """
    Gestor responsável por agregar e calcular estatísticas do sistema.
    Remove a complexidade das Views.
    """

    def __init__(self, user):
        self.user = user

    def obter_queryset_base(self):
        """Retorna o queryset filtrado com base nas permissões do utilizador."""
        from .permissions import obter_candidatos_acessiveis
        return obter_candidatos_acessiveis(self.user)

    def obter_estatisticas_gerais(self):
        """Retorna estatísticas básicas (Totais, Pendentes, Gráficos)."""
        base_qs = self.obter_queryset_base()
        
        # Totais
        total = base_qs.count()
        pendentes = base_qs.filter(estado=Candidato.Estado.PENDENTE).count()

        # Gráficos de Distribuição
        stats_funcao = list(base_qs.values('vaga__titulo').annotate(count=Count('vaga')))
        for item in stats_funcao:
            item['label'] = item['vaga__titulo']

        stats_estado = list(base_qs.values('estado').annotate(count=Count('estado')))
        for item in stats_estado:
            try:
                item['label'] = Candidato.Estado(item['estado']).label
            except ValueError:
                item['label'] = item['estado']

        return {
            'total_candidatos': total,
            'candidatos_pendentes': pendentes,
            'stats_funcao': stats_funcao,
            'stats_estado': stats_estado
        }

    def obter_detalhes_admissao(self):
        """Retorna estatísticas detalhadas de admissão e género."""
        base_qs = self.obter_queryset_base()
        STATUS_ADMITIDOS = [Candidato.Estado.CONTRATADO, Candidato.Estado.ENTREVISTA_APROVADA]
        
        admitidos_qs = base_qs.filter(estado__in=STATUS_ADMITIDOS)
        
        return {
            'total_admitidos': admitidos_qs.count(),
            'admitidos_homens': admitidos_qs.filter(genero=Candidato.Genero.MASCULINO).count(),
            'admitidos_mulheres': admitidos_qs.filter(genero=Candidato.Genero.FEMININO).count()
        }

    def obter_distribuicao_geografica(self, is_central=False, is_provincial=False, perfil=None):
        """
        Retorna estatísticas complexas por Província ou Distrito.
        """
        STATUS_ADMITIDOS = [Candidato.Estado.CONTRATADO, Candidato.Estado.ENTREVISTA_APROVADA]
        
        # Filtros Comuns
        filtro_admitidos = Q(candidatos__estado__in=STATUS_ADMITIDOS)
        filtro_homem = Q(candidatos__genero=Candidato.Genero.MASCULINO)
        filtro_mulher = Q(candidatos__genero=Candidato.Genero.FEMININO)
        filtro_admitido_homem = filtro_admitidos & filtro_homem
        filtro_admitido_mulher = filtro_admitidos & filtro_mulher

        dados = {}

        # Lógica Central (Por Província)
        if is_central:
            distritos_prefetch = Prefetch(
                'distritos',
                queryset=Distrito.objects.annotate(
                    total=Count('candidatos'),
                    admitted=Count('candidatos', filter=filtro_admitidos)
                ).filter(total__gt=0).order_by('-admitted')
            )
            
            provincias = Provincia.objects.annotate(
                total=Count('candidatos'),
                admitted_total=Count('candidatos', filter=filtro_admitidos),
                gen_male=Count('candidatos', filter=filtro_homem),
                gen_female=Count('candidatos', filter=filtro_mulher),
                adm_male=Count('candidatos', filter=filtro_admitido_homem),
                adm_female=Count('candidatos', filter=filtro_admitido_mulher)
            ).filter(total__gt=0).prefetch_related(distritos_prefetch).order_by('-total')

            lista_provincias = []
            for prov in provincias:
                stats_distritos = [
                    {'name': d.nome, 'admitted': d.admitted, 'total': d.total} 
                    for d in prov.distritos.all()
                ]
                
                lista_provincias.append({
                    'id': prov.id,
                    'nome': prov.nome,
                    'lat': prov.latitude,
                    'lon': prov.longitude,
                    'total': prov.total,
                    'admitted_total': prov.admitted_total,
                    'not_admitted_total': prov.total - prov.admitted_total,
                    'gender_general': {'m': prov.gen_male, 'f': prov.gen_female},
                    'gender_admitted': {'m': prov.adm_male, 'f': prov.adm_female},
                    'districts_stats': stats_distritos
                })
            dados['detalhes_provincia'] = lista_provincias

        # Lógica Provincial (Por Distrito)
        if is_provincial and perfil and perfil.provincia:
            distritos = Distrito.objects.filter(provincia=perfil.provincia).annotate(
                total=Count('candidatos'),
                admitted_total=Count('candidatos', filter=filtro_admitidos),
                gen_male=Count('candidatos', filter=filtro_homem),
                gen_female=Count('candidatos', filter=filtro_mulher),
                adm_male=Count('candidatos', filter=filtro_admitido_homem),
                adm_female=Count('candidatos', filter=filtro_admitido_mulher)
            ).filter(total__gt=0).order_by('-total')

            lista_distritos = []
            for dist in distritos:
                lista_distritos.append({
                    'id': dist.id,
                    'nome': dist.nome,
                    'total': dist.total,
                    'admitted_total': dist.admitted_total,
                    'not_admitted_total': dist.total - dist.admitted_total,
                    'gender_general': {'m': dist.gen_male, 'f': dist.gen_female},
                    'gender_admitted': {'m': dist.adm_male, 'f': dist.adm_female},
                })
            dados['detalhes_distrito'] = lista_distritos
            
        return dados

    def obter_candidatos_recentes(self, limite=5):
        """Retorna os candidatos pendentes mais recentes."""
        return self.obter_queryset_base().filter(estado=Candidato.Estado.PENDENTE).order_by('-data_criacao')[:limite]
