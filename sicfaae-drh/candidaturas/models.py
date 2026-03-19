from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from simple_history.models import HistoricalRecords
from core.models import Provincia, Distrito


class Vaga(models.Model):
    """Modelo para gestão dinâmica de vagas de emprego/funções."""
    titulo = models.CharField(_("Título da Vaga"), max_length=100)
    descricao = models.TextField(_("Descrição"), blank=True)
    data_inicio = models.DateField(_("Data de Início"))
    data_fim = models.DateField(_("Data de Fim"))
    ativa = models.BooleanField(_("Vaga Ativa"), default=True)
    requer_formacao = models.BooleanField(
        _("Requer Formação"),
        default=True,
        help_text=_("Se marcado, candidatos aprovados serão enviados para formação no DEFC. Caso contrário, são contratados diretamente.")
    )
    documentos_necessarios = models.JSONField(
        _("Documentos Necessários"),
        default=list,
        blank=True,
        help_text=_("Lista de documentos que os candidatos devem submeter para esta vaga")
    )
    
    concurso_aberto = models.BooleanField(_("Concurso Aberto"), default=False)
    numero_vagas = models.PositiveIntegerField(
        _("Número de Vagas"), 
        null=True, 
        blank=True,
        help_text=_("Quantidade de vagas disponíveis especificadas na abertura do concurso.")
    )
    documento_concurso = models.FileField(
        _("Documento do Concurso"), 
        upload_to='vagas/concursos/', 
        null=True, 
        blank=True,
        help_text=_("PDF oficial gerado aquando da abertura do concurso.")
    )

    
    class NivelAprovacao(models.TextChoices):
        CENTRAL = 'CENTRAL', _('STAE Central')
        PROVINCIAL = 'PROVINCIAL', _('STAE Provincial')
        DISTRITAL = 'DISTRITAL', _('STAE Distrital')

    nivel_aprovacao = models.CharField(
        _("Destino da Vaga"),
        max_length=20,
        choices=NivelAprovacao.choices,
        default=NivelAprovacao.DISTRITAL,
        help_text=_("Define para onde é a vaga (STAE Central, Provincial ou Distrital).")
    )

    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Província",
        help_text=_("Selecione a província, caso seja uma vaga Provincial ou Distrital.")
    )

    distrito = models.ForeignKey(
        Distrito,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Distrito",
        help_text=_("Selecione o distrito, caso seja uma vaga Distrital.")
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = _("Vaga")
        verbose_name_plural = _("Vagas")
        ordering = ['-data_criacao']


class EntrevistadorVaga(models.Model):
    """
    Representa um entrevistador que é alocado especificamente a uma Vaga.
    Eles acedem apenas com Nome e Código de Acesso.
    """
    vaga = models.ForeignKey(
        Vaga,
        on_delete=models.CASCADE,
        related_name='entrevistadores',
        verbose_name=_("Vaga Alocada")
    )
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='entrevistador_vaga',
        verbose_name=_("Utilizador do Sistema")
    )
    nome = models.CharField(_("Nome do Entrevistador"), max_length=255)
    codigo_acesso = models.CharField(
        _("Código de Acesso"), 
        max_length=20, 
        unique=True,
        help_text=_("O código gerado automaticamente que o entrevistador usará como senha.")
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Entrevistador da Vaga")
        verbose_name_plural = _("Entrevistadores da Vaga")
        ordering = ['-data_criacao']

    def __str__(self):
        return f"{self.nome} - {self.vaga.titulo}"


class Candidato(models.Model):
    class Estado(models.TextChoices):
        PENDENTE = 'PENDENTE', _('Pendente')
        ENTREVISTA_AGENDADA = 'ENTREVISTA_AGENDADA', _('Entrevista Agendada')
        ENTREVISTA_APROVADA = 'ENTREVISTA_APROVADA', _('Aprovado na Entrevista')
        ENTREVISTA_REPROVADA = 'ENTREVISTA_REPROVADA', _('Reprovado na Entrevista')
        ENVIADO_DEFC = 'ENVIADO_DEFC', _('Enviado para Formação (DEFC)')

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

    enviado_defc = models.BooleanField(
        _("Enviado para DEFC"),
        default=False,
        help_text=_("Indica se candidato foi transferido para sistema DEFC")
    )
    data_envio_defc = models.DateTimeField(
        _("Data de Envio para DEFC"),
        null=True,
        blank=True
    )
    id_defc = models.CharField(
        _("ID no Sistema DEFC"),
        max_length=50,
        blank=True,
        help_text=_("ID do candidato no sistema DEFC após transferência")
    )

    nome_completo = models.CharField(_("Nome Completo"), max_length=255)
    
    genero = models.CharField(
        _("Género"),
        max_length=1,
        choices=Genero.choices,
        default=Genero.MASCULINO
    )
    
    data_nascimento = models.DateField(_("Data de Nascimento"), null=True, blank=True)

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
    
    # Código Único do Candidato
    codigo_candidato = models.CharField(
        _("Código do Candidato"),
        max_length=20,
        unique=True,
        blank=True,
        help_text=_("Formato: A-B-12345678-C (Província-Bloco-Sequencial-Distrito)")
    )
    
    # Documents
    arquivo_cv = models.FileField(_("Curriculum Vitae (CV)"), upload_to='candidatos/cv/', null=True, blank=True)
    arquivo_bi = models.FileField(_("Cópia do BI"), upload_to='candidatos/bi/', null=True, blank=True)
    arquivo_certificado = models.FileField(_("Certificado de Habilitações"), upload_to='candidatos/certificados/', null=True, blank=True)
    foto = models.ImageField(_("Foto"), upload_to='candidatos/fotos/', blank=True, null=True)

    estado = models.CharField(
        _("Estado da Candidatura"),
        max_length=30,
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
    
    def _obter_bloco_distrito(self):
        """Obtém bloco automático baseado no ID do distrito.
        
        Usa conversão base-36 para gerar blocos únicos (0-9, A-Z, 10, 11, ...).
        Isso garante que cada distrito tenha seu próprio bloco sem configuração manual,
        mesmo com IDs maiores que 35.
        
        Exemplos:
        - ID 0 -> '0'
        - ID 9 -> '9'
        - ID 10 -> 'A'
        - ID 35 -> 'Z'
        - ID 36 -> '10' (1*36 + 0)
        - ID 37 -> '11' (1*36 + 1)
        - ID 71 -> '1Z' (1*36 + 35)
        - ID 72 -> '20' (2*36 + 0)
        """
        if not self.distrito:
            return '0'
        
        # Converter ID do distrito para base 36
        distrito_id = self.distrito.id
        
        if distrito_id == 0:
            return '0'
        
        # Conversão base 36: 0-9, A-Z
        base36_chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        result = ''
        
        while distrito_id > 0:
            result = base36_chars[distrito_id % 36] + result
            distrito_id //= 36
        
        return result
    
    def _obter_inicial_distrito(self):
        """Obtém inicial(is) do distrito, evitando conflitos."""
        if not self.distrito:
            return 'X'
        
        primeira_letra = self.distrito.nome[0].upper()
        
        # Verificar se há outros distritos na mesma província com mesma inicial
        conflitos = Distrito.objects.filter(
            provincia=self.provincia,
            nome__istartswith=primeira_letra
        ).exclude(id=self.distrito.id).exists()
        
        if conflitos:
            # Usar 2 letras
            return self.distrito.nome[:2].upper()
        else:
            # Usar 1 letra
            return primeira_letra
    
    def gerar_codigo_candidato(self):
        """Gera código único no formato: Província-Bloco-Sequencial-Distrito
        
        Formato: A-B-12345678-C
        - A: Inicial da província
        - B: Bloco automático (baseado no ID do distrito)
        - 12345678: Número sequencial (8 dígitos)
        - C: Inicial(is) do distrito
        
        Exemplo: M-5-00000042-Ma (Maputo, Bloco 5, #42, Matola)
        
        Sistema híbrido que funciona offline e online:
        - Cada distrito tem bloco único automático
        - Suporta sincronização de múltiplas instalações
        - Usa transações atômicas para evitar duplicação
        """
        if self.codigo_candidato:
            return self.codigo_candidato
        
        if not self.provincia or not self.distrito:
            return ''
        
        from django.db import transaction
        
        inicial_provincia = self.provincia.nome[0].upper()
        bloco = self._obter_bloco_distrito()
        inicial_distrito = self._obter_inicial_distrito()
        
        # Usar transação atômica para evitar race conditions
        with transaction.atomic():
            # Buscar último candidato DESTE BLOCO e distrito
            ultimo_candidato = Candidato.objects.filter(
                distrito=self.distrito,
                codigo_candidato__contains=f"-{bloco}-"
            ).exclude(
                codigo_candidato=''
            ).select_for_update().order_by('-id').first()
            
            if ultimo_candidato and ultimo_candidato.codigo_candidato:
                try:
                    # Extrair número: M-5-00000042-Ma -> "00000042"
                    partes = ultimo_candidato.codigo_candidato.split('-')
                    if len(partes) >= 3:
                        numero_str = partes[2]
                        proximo_numero = int(numero_str) + 1
                    else:
                        proximo_numero = 1
                except (ValueError, IndexError):
                    proximo_numero = 1
            else:
                proximo_numero = 1
            
            # Formatar: 8 dígitos com zeros à esquerda
            numero_formatado = str(proximo_numero).zfill(8)
            
            # Montar código
            codigo = f"{inicial_provincia}-{bloco}-{numero_formatado}-{inicial_distrito}"
            
            # Verificação adicional: garantir unicidade
            tentativas = 0
            while Candidato.objects.filter(codigo_candidato=codigo).exists() and tentativas < 100:
                proximo_numero += 1
                numero_formatado = str(proximo_numero).zfill(8)
                codigo = f"{inicial_provincia}-{bloco}-{numero_formatado}-{inicial_distrito}"
                tentativas += 1
            
            return codigo
    
    def save(self, *args, **kwargs):
        """Sobrescreve save para gerar código automaticamente."""
        # Gerar código antes de salvar, se necessário
        if not self.codigo_candidato and self.provincia and self.distrito:
            try:
                self.codigo_candidato = self.gerar_codigo_candidato()
            except Exception as e:
                # Se falhar, deixar vazio por enquanto
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome_completo} ({self.estado})"


    class Meta:
        verbose_name = _("Candidato")
        verbose_name_plural = _("Candidatos")


class Entrevista(models.Model):
    """Registo de Agendamento e Avaliação de Entrevistas."""
    
    class Status(models.TextChoices):
        AGENDADA = 'AGENDADA', _('Agendada')
        REALIZADA = 'REALIZADA', _('Realizada')
        CANCELADA = 'CANCELADA', _('Cancelada')
        FALTOU = 'FALTOU', _('Não Compareceu')

    class Resultado(models.TextChoices):
        APROVADO = 'APROVADO', _('Aprovado')
        REPROVADO = 'REPROVADO', _('Reprovado')
        PENDENTE = 'PENDENTE', _('Pendente')

    candidato = models.OneToOneField(
        Candidato,
        on_delete=models.CASCADE,
        verbose_name=_("Candidato"),
        related_name='entrevista_detalhe'
    )
    
    entrevistador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name=_("Entrevistador"),
        null=True,
        blank=True,
        limit_choices_to={'is_staff': True}
    )

    data_hora = models.DateTimeField(_("Data e Hora"))
    local = models.CharField(_("Local"), max_length=200, help_text=_("Ex: Sala 2, STAE Central ou Link Google Meet"))
    
    # Avaliação
    nota_tecnica = models.IntegerField(_("Nota Técnica (0-20)"), default=0)
    nota_comunicacao = models.IntegerField(_("Nota Comunicação (0-20)"), default=0)
    nota_experiencia = models.IntegerField(_("Nota Experiência (0-20)"), default=0)
    
    observacoes = models.TextField(_("Observações do Entrevistador"), blank=True)
    
    status = models.CharField(
        _("Status da Entrevista"),
        max_length=20,
        choices=Status.choices,
        default=Status.AGENDADA
    )
    
    resultado = models.CharField(
        _("Resultado Final"),
        max_length=20,
        choices=Resultado.choices,
        default=Resultado.PENDENTE
    )

    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Entrevista")
        verbose_name_plural = _("Entrevistas")
        ordering = ['data_hora']

    def __str__(self):
        return f"Entrevista: {self.candidato.nome_completo} ({self.data_hora.strftime('%d/%m %H:%M')})"

    @property
    def media_final(self):
        return round((self.nota_tecnica + self.nota_comunicacao + self.nota_experiencia) / 3, 1)
    
    @property
    def pode_enviar_defc(self):
        """Verifica se candidato pode ser enviado para DEFC"""
        return (
            self.estado == self.Estado.ENTREVISTA_APROVADA and
            not self.enviado_defc and
            self.validacao_bi and
            self.validacao_cv
        )
    



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
