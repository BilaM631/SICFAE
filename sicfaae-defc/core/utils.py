from .models import PerfilUtilizador

def obter_perfil_usuario(user):
    """Obtém o perfil do utilizador ou None se não existir."""
    if not user.is_authenticated:
        return None
    try:
        return user.perfil
    except PerfilUtilizador.DoesNotExist:
        return None

def obter_exibicao_nivel_usuario(user):
    """Retorna string de exibição do nível do utilizador."""
    if user.is_superuser:
        return "Administrador do Sistema"
        
    perfil = obter_perfil_usuario(user)
    if not perfil:
        return "Utilizador (Sem Perfil)"
        
    if perfil.nivel == PerfilUtilizador.Nivel.CENTRAL:
        return "Nível Central (STAE Sede)"
    elif perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
        return f"Nível Provincial ({perfil.provincia.nome})"
    elif perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
        return f"Nível Distrital ({perfil.distrito.nome})"
    
    return str(perfil.nivel)
