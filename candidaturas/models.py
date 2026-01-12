from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from simple_history.models import HistoricalRecords


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
        # ordering = ['provincia__nome', 'nome']


class Vaga(models.Model):
    """Modelo para gestão dinâmica de vagas de emprego/funções."""
    titulo = models.CharField(_("Título da Vaga"), max_length=100)
    descricao = models.TextField(_("Descrição"), blank=True)
    data_inicio = models.DateField(_("Data de Início"))
    data_fim = models.DateField(_("Data de Fim"))
    ativa = models.BooleanField(_("Vaga Ativa"), default=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = _("Vaga")
        verbose_name_plural = _("Vagas")
        ordering = ['-data_criacao']


class Candidato(models.Model):
    class Estado(models.TextChoices):
        PENDENTE = 'PENDENTE', _('Pendente')
        DOCS_APROVADOS = 'DOCS_APROVADOS', _('Documentos Aprovados')
        DOCS_REJEITADOS = 'DOCS_REJEITADOS', _('Documentos Rejeitados')
        ENTREVISTA_AGENDADA = 'ENTREVISTA_AGENDADA', _('Entrevista Agendada')
        ENTREVISTA_APROVADA = 'ENTREVISTA_APROVADA', _('Aprovado na Entrevista')
        ENTREVISTA_REPROVADA = 'ENTREVISTA_REPROVADA', _('Reprovado na Entrevista')
        CONTRATADO = 'CONTRATADO', _('Contratado/Credenciais Geradas')

    class Genero(models.TextChoices):
        MASCULINO = 'M', _('Masculino')
        FEMININO = 'F', _('Feminino')

    vaga = models.ForeignKey(
        'Vaga',
        on_delete=models.PROTECT,
        verbose_name=_("Vaga a Candidatar"),
        related_name='candidatos',
        null=True,
        blank=True
    )

    nome_completo = models.CharField(_("Nome Completo"), max_length=255)
    
    genero = models.CharField(
        _("Género"),
        max_length=1,
        choices=Genero.choices,
        default=Genero.MASCULINO
    )

    numero_bi = models.CharField(_("Número de BI"), max_length=20, unique=True)
    numero_telefone = models.CharField(_("Número de Telefone"), max_length=15)
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.PROTECT,
        verbose_name=_("Província"),
        related_name='candidatos',
        null=True,
        blank=True
    )
    distrito = models.ForeignKey(
        Distrito,
        on_delete=models.PROTECT,
        verbose_name=_("Distrito"),
        related_name='candidatos',
        null=True,
        blank=True
    )
    endereco = models.TextField(_("Endereço (Bairro/Rua)"), blank=True)
    
    # Documents
    arquivo_cv = models.FileField(_("Curriculum Vitae (CV)"), upload_to='candidatos/cv/', null=True, blank=True)
    arquivo_bi = models.FileField(_("Cópia do BI"), upload_to='candidatos/bi/', null=True, blank=True)
    arquivo_certificado = models.FileField(_("Certificado de Habilitações"), upload_to='candidatos/certificados/', null=True, blank=True)
    foto = models.ImageField(_("Foto"), upload_to='candidatos/fotos/', blank=True, null=True)

    estado = models.CharField(
        _("Estado da Candidatura"),
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDENTE
    )

    observacoes = models.TextField(_("Observações"), blank=True, null=True)
    
    # Identificação & Habilitações (Validação Física)
    validacao_bi = models.BooleanField(_("BI Válido"), default=False)
    validacao_cv = models.BooleanField(_("CV Válido"), default=False)
    validacao_certificado = models.BooleanField(_("Certificado Válido"), default=False)
    validacao_nuit = models.BooleanField(_("NUIT (Se aplicável)"), default=False)
    validacao_registo_criminal = models.BooleanField(_("Registo Criminal"), default=False)
    validacao_atestado_medico = models.BooleanField(_("Atestado Médico"), default=False)
    validacao_requerimento = models.BooleanField(_("Requerimento Assinado"), default=False)

    # Interview Details (Optional/Simple)
    data_entrevista = models.DateTimeField(_("Data da Entrevista"), null=True, blank=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.nome_completo} ({self.estado})"


    class Meta:
        verbose_name = _("Candidato")
        verbose_name_plural = _("Candidatos")


class PerfilUtilizador(models.Model):
    """
    Perfil de utilizador para controlo hierárquico de acesso.
    Define o nível administrativo e a área geográfica de responsabilidade.
    """
    class Nivel(models.TextChoices):
        CENTRAL = 'CENTRAL', _('STAE Central')
        PROVINCIAL = 'PROVINCIAL', _('STAE Provincial')
        DISTRITAL = 'DISTRITAL', _('STAE Distrital')
    
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
        related_name='admins_provinciais',
        blank=True,
        null=True,
        help_text=_("Província de responsabilidade (obrigatório para Provincial e Distrital)")
    )
    distrito = models.ForeignKey(
        Distrito,
        on_delete=models.SET_NULL,
        verbose_name=_("Distrito"),
        related_name='admins_distritais',
        blank=True,
        null=True,
        help_text=_("Distrito de responsabilidade (obrigatório para Distrital)")
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()
    
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
