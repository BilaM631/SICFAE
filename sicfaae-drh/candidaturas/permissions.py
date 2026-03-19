from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Candidato, PerfilUtilizador

def obter_perfil_usuario(usuario):
    """
    Obtém o perfil do utilizador. Retorna None para superusers.
    """
    if not usuario.is_authenticated:
        return None

    if usuario.is_superuser:
        return None
    
    # Cria perfil se não existir
    perfil, criado = PerfilUtilizador.objects.get_or_create(usuario=usuario)
    return perfil


def obter_candidatos_acessiveis(usuario):
    """
    Retorna queryset de candidatos acessíveis ao utilizador baseado no seu nível.
    
    - Superuser: Todos os candidatos
    - Central: Todos os candidatos
    - Provincial: Candidatos da sua província
    - Distrital: Candidatos do seu distrito
    """
    if usuario.is_superuser:
        return Candidato.objects.all()
    
    perfil = obter_perfil_usuario(usuario)
    
    if not perfil:
        return Candidato.objects.none()
    
    if perfil.nivel == PerfilUtilizador.Nivel.CENTRAL:
        return Candidato.objects.all()
    
    elif perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
        if not perfil.provincia:
            return Candidato.objects.none()
        return Candidato.objects.filter(provincia=perfil.provincia)
    
    elif perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
        # Strict checking: must have district AND province assigned
        if not perfil.distrito:
            return Candidato.objects.none()
        return Candidato.objects.filter(
            distrito=perfil.distrito
        )
    
    return Candidato.objects.none()


def pode_ver_candidato(usuario, candidato):
    """
    Verifica se o utilizador pode VER um candidato.
    """
    if usuario.is_superuser:
        return True
    
    perfil = obter_perfil_usuario(usuario)
    
    if not perfil:
        return False
    
    if perfil.nivel == PerfilUtilizador.Nivel.CENTRAL:
        return True
    
    elif perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
        # Pode ver se for da sua província
        return candidato.provincia == perfil.provincia
    
    elif perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
        # Pode ver se for do seu distrito
        return candidato.distrito == perfil.distrito
    
    return False


def pode_gerir_candidato(usuario, candidato):
    """
    Verifica se o utilizador pode GERIR (aprovar/rejeitar/editar) um candidato.
    AGORA: Apenas DISTRITAL pode gerir.
    """
    if usuario.is_superuser:
        return False # Superuser vê tudo mas não gere (política definida)
    
    perfil = obter_perfil_usuario(usuario)
    
    if not perfil:
        return False
    
    # Central e Provincial: Apenas visualizam (retorna False para gestão)
    if perfil.nivel in [PerfilUtilizador.Nivel.CENTRAL, PerfilUtilizador.Nivel.PROVINCIAL]:
        return False
    
    # Distrital: Pode gerir se for do seu distrito
    elif perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
        return candidato.distrito == perfil.distrito
        
    # Provincial: Pode gerir se for da sua província
    elif perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
        return candidato.provincia == perfil.provincia
    
    return False


def filtrar_candidatos_por_provincia(queryset, provincia):
    """
    Filtra candidatos por província (usado por utilizadores Central).
    """
    if provincia and provincia != 'ALL':
        return queryset.filter(provincia=provincia)
    return queryset


class MixinFiltroNivelUsuario:
    """
    Mixin para views que filtra automaticamente querysets baseado no nível do utilizador.
    """
    
    def get_queryset(self):
        """Sobrescreve get_queryset para aplicar filtros de permissão."""
        queryset = super().get_queryset()
        
        if not self.request.user.is_authenticated:
            return queryset.none()
        
        return obter_candidatos_acessiveis(self.request.user)
    
    def get_object(self, queryset=None):
        """Verifica permissões ao obter um objeto específico."""
        obj = super().get_object(queryset)
        
        if not pode_gerir_candidato(self.request.user, obj):
            raise PermissionDenied("Não tem permissão para aceder a este candidato.")
        
        return obj


def obter_lista_provincias():
    """
    Retorna lista de províncias de Moçambique.
    """
    return [
        'Maputo Cidade',
        'Maputo Província',
        'Gaza',
        'Inhambane',
        'Sofala',
        'Manica',
        'Tete',
        'Zambézia',
        'Nampula',
        'Niassa',
        'Cabo Delgado',
    ]


def obter_exibicao_nivel_usuario(usuario):
    """
    Retorna uma string formatada com o nível e área do utilizador.
    """
    if usuario.is_superuser:
        return "Superusuário"
    
    perfil = obter_perfil_usuario(usuario)
    
    if not perfil:
        return "Sem Perfil"
    
    if perfil.nivel == PerfilUtilizador.Nivel.CENTRAL:
        return "STAE Central"
    elif perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
        nome_prov = perfil.provincia.nome if perfil.provincia else 'Não Atribuída'
        return f"STAE Provincial - {nome_prov}"
    else:
        nome_dist = perfil.distrito.nome if perfil.distrito else 'Não Atribuído'
        return f"STAE Distrital - {nome_dist}"
