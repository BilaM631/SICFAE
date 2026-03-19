from django.db import models
from django.utils.translation import gettext_lazy as _


class Provincia(models.Model):
    """Província de Moçambique"""
    nome = models.CharField(_("Nome da Província"), max_length=100, unique=True)
    latitude = models.FloatField(_("Latitude"), null=True, blank=True)
    longitude = models.FloatField(_("Longitude"), null=True, blank=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = _("Província")
        verbose_name_plural = _("Províncias")
        ordering = ['nome']


class Distrito(models.Model):
    """Distrito de Moçambique"""
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.CASCADE,
        related_name='distritos',
        verbose_name=_("Província")
    )
    nome = models.CharField(_("Nome do Distrito"), max_length=100)
    
    def __str__(self):
        return f"{self.nome} ({self.provincia.nome})"
    
    class Meta:
        verbose_name = _("Distrito")
        verbose_name_plural = _("Distritos")
        unique_together = ('provincia', 'nome')
        ordering = ['provincia__nome', 'nome']


class CandidatoFormacao(models.Model):
    """
    Modelo simplificado de Candidato para o sistema DEFC.
    Contém apenas dados essenciais recebidos do DRH.
    """
    class TipoAgente(models.TextChoices):
        MMV = 'MMV', _('Membro de Mesa de Voto')
        AGENTE_CIVICO = 'AGENTE_CIVICO', _('Agente de Educação Cívica')
        FORMADOR = 'FORMADOR', _('Formador')
        BRIGADISTA = 'BRIGADISTA', _('Brigadista')
    
    class Genero(models.TextChoices):
        MASCULINO = 'M', _('Masculino')
        FEMININO = 'F', _('Feminino')
    
    id_drh = models.IntegerField(
        _("ID no Sistema DRH"),
        unique=True,
        help_text=_("ID original do candidato no sistema DRH")
    )
    
    codigo_candidato = models.CharField(
        _("Código do Candidato"),
        max_length=20,
        unique=True,
        help_text=_("Código único gerado pelo DRH")
    )
    
    nome_completo = models.CharField(_("Nome Completo"), max_length=255)
    
    genero = models.CharField(
        _("Género"),
        max_length=1,
        choices=Genero.choices
    )
    
    data_nascimento = models.DateField(_("Data de Nascimento"), null=True, blank=True)
    numero_bi = models.CharField(_("Número de BI"), max_length=20)
    numero_telefone = models.CharField(_("Número de Telefone"), max_length=15)
    
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.PROTECT,
        verbose_name=_("Província"),
        related_name='candidatos_formacao'
    )
    
    distrito = models.ForeignKey(
        Distrito,
        on_delete=models.PROTECT,
        verbose_name=_("Distrito"),
        related_name='candidatos_formacao'
    )
    
    endereco = models.TextField(_("Endereço"), blank=True)
    
    tipo_agente = models.CharField(
        _("Tipo de Agente"),
        max_length=20,
        choices=TipoAgente.choices,
        default=TipoAgente.BRIGADISTA,
        help_text=_("Tipo de agente eleitoral para formação")
    )
    
    foto = models.ImageField(
        _("Foto"),
        upload_to='candidatos_formacao/fotos/',
        blank=True,
        null=True
    )
    
    data_recepcao = models.DateTimeField(
        _("Data de Recepção do DRH"),
        auto_now_add=True
    )
    
    ativo = models.BooleanField(_("Ativo"), default=True)
    
    observacoes = models.TextField(_("Observações"), blank=True)
    
    @property
    def idade(self):
        """Calcula a idade do candidato"""
        if not self.data_nascimento:
            return None
        from datetime import date
        hoje = date.today()
        return hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )
    
    def __str__(self):
        return f"{self.nome_completo} ({self.codigo_candidato})"
    
    class Meta:
        verbose_name = _("Candidato em Formação")
        verbose_name_plural = _("Candidatos em Formação")
        ordering = ['-data_recepcao']


class ConfiguracaoSistema(models.Model):
    """
    Modelo Singleton para configurações globais do sistema.
    Assegura que apenas existe uma linha na tabela com pk=1.
    """
    class PeriodoEleitoral(models.TextChoices):
        RECENSEAMENTO = 'RECENSEAMENTO', _('Recenseamento Eleitoral')
        VOTACAO = 'VOTACAO', _('Votação')

    periodo_ativo = models.CharField(
        _("Período Eleitoral Ativo"),
        max_length=20,
        choices=PeriodoEleitoral.choices,
        default=PeriodoEleitoral.RECENSEAMENTO,
        help_text=_("Controla os tipos de formação permitidos (ex: Brigadistas no Recenseamento, MMV na Votação)")
    )

    data_atualizacao = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Configuração do Sistema ({self.get_periodo_ativo_display()})"

    class Meta:
        verbose_name = _("Configuração Geral")
        verbose_name_plural = _("Configurações Gerais")


class PerfilUtilizador(models.Model):
    """
    Perfil de utilizador para controlo hierárquico de acesso no DEFC.
    Define o nível administrativo e a área geográfica de responsabilidade.
    """
    class Nivel(models.TextChoices):
        CENTRAL = 'CENTRAL', _('STAE Central')
        PROVINCIAL = 'PROVINCIAL', _('STAE Provincial')
        DISTRITAL = 'DISTRITAL', _('STAE Distrital')
    
    from django.contrib.auth.models import User
    
    usuario = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='perfil',
        verbose_name=_("Utilizador")
    )
    nivel = models.CharField(
        _("Nível Administrativo"),
        max_length=20,
        choices=Nivel.choices,
        default=Nivel.DISTRITAL
    )
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.SET_NULL,
        verbose_name=_("Província"),
        related_name='admins_provinciais_defc',
        blank=True,
        null=True,
        help_text=_("Província de responsabilidade (obrigatório para Provincial e Distrital)")
    )
    distrito = models.ForeignKey(
        Distrito,
        on_delete=models.SET_NULL,
        verbose_name=_("Distrito"),
        related_name='admins_distritais_defc',
        blank=True,
        null=True,
        help_text=_("Distrito de responsabilidade (obrigatório para Distrital)")
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    deve_alterar_senha = models.BooleanField(
        _("Deve Alterar Senha"),
        default=True,
        help_text=_("Se True, o utilizador é forçado a definir uma nova senha no próximo login.")
    )
    
    def __str__(self):
        if self.nivel == self.Nivel.CENTRAL:
            return f"{self.usuario.username} - Central"
        elif self.nivel == self.Nivel.PROVINCIAL:
            nome_prov = self.provincia.nome if self.provincia else "N/A"
            return f"{self.usuario.username} - {nome_prov}"
        else:
            nome_dist = self.distrito.nome if self.distrito else "N/A"
            nome_prov = self.provincia.nome if self.provincia else "N/A"
            return f"{self.usuario.username} - {nome_dist}, {nome_prov}"
    
    class Meta:
        verbose_name = _("Perfil de Utilizador")
        verbose_name_plural = _("Perfis de Utilizadores")


# Signal to auto-create UserProfile for new users
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    """Cria automaticamente um perfil para novos utilizadores."""
    if created and not instance.is_superuser:
        PerfilUtilizador.objects.create(usuario=instance)


@receiver(post_save, sender=User)
def salvar_perfil_usuario(sender, instance, **kwargs):
    """Guarda o perfil quando o utilizador é guardado."""
    if not instance.is_superuser and hasattr(instance, 'perfil'):
        instance.perfil.save()
