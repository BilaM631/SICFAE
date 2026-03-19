from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from core.models import Distrito, CandidatoFormacao
from datetime import timedelta
import math


class TipoFormacao(models.TextChoices):
    FORMADORES_NACIONAIS   = 'FORMADORES_NACIONAIS',   _('Formadores Nacionais')
    FORMADORES_PROVINCIAIS = 'FORMADORES_PROVINCIAIS',  _('Formadores Provinciais')
    MMV                    = 'MMV',                    _('Membros de Mesas de Voto (MMV)')
    AGENTES_EDUCACAO       = 'AGENTES_EDUCACAO',       _('Agentes de Educação Cívica')
    BRIGADISTAS            = 'BRIGADISTAS',            _('Brigadistas')
    # Mantido para retrocompatibilidade — usar FORMADORES_NACIONAIS ou FORMADORES_PROVINCIAIS
    FORMADORES             = 'FORMADORES',             _('Formadores (legado)')

    @classmethod
    def tipos_formadores(cls):
        """Retorna os tipos relacionados com formadores"""
        return [cls.FORMADORES_NACIONAIS, cls.FORMADORES_PROVINCIAIS, cls.FORMADORES]

    @classmethod
    def tipos_campo(cls):
        """Tipos que ocorrem nos distritos (Brigadistas, MMV, Educ. Cívica)"""
        return [cls.BRIGADISTAS, cls.MMV, cls.AGENTES_EDUCACAO]


class Local(models.Model):
    nome = models.CharField(max_length=100)
    distrito = models.ForeignKey(Distrito, on_delete=models.CASCADE, related_name='locais_formacao')
    capacidade = models.PositiveIntegerField(default=30)
    descricao = models.TextField(blank=True, null=True, help_text="Ex: Sala 10, Bloco A - 08:00 às 13:00")
    
    def __str__(self):
        return f"{self.nome} ({self.distrito.nome})"
    
    class Meta:
        verbose_name = _("Local de Formação")
        verbose_name_plural = _("Locais de Formação")


class Turma(models.Model):
    nome = models.CharField(max_length=100)
    distrito = models.ForeignKey(
        Distrito, on_delete=models.CASCADE, related_name='turmas',
        null=True, blank=True,
        help_text=_("Obrigatório para turmas de campo (Brigadistas, MMV, Educ. Cívica) e Formadores Provinciais")
    )
    provincia = models.ForeignKey(
        'core.Provincia', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='turmas_provinciais',
        verbose_name=_("Direção Provincial"),
        help_text=_("Obrigatório para Formadores Nacionais — indica a Direção Provincial onde ocorre a formação")
    )
    local = models.ForeignKey(Local, on_delete=models.SET_NULL, null=True, blank=True, related_name='turmas')
    formadores = models.ManyToManyField('core.CandidatoFormacao', blank=True, related_name='turmas_como_formador')
    alunos = models.ManyToManyField('core.CandidatoFormacao', blank=True, related_name='turmas_como_aluno')

    tipo_formacao = models.CharField(
        _("Tipo de Formação"),
        max_length=30,
        choices=TipoFormacao.choices,
        default=TipoFormacao.BRIGADISTAS,
        help_text=_("Formadores Nacionais: ocorrem nas Direções Provinciais. "
                    "Formadores Provinciais: ocorrem a nível da Província. "
                    "MMV, Brigadistas, Educ. Cívica: ocorrem nos Distritos.")
    )
    
    numero = models.PositiveIntegerField(help_text="Número da turma dentro do distrito (1 a 35)")
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    
    carga_horaria_prevista = models.PositiveIntegerField(
        _("Carga Horária Prevista (horas)"),
        default=40,
        help_text=_("Carga horária total prevista em horas")
    )
    carga_horaria_realizada = models.PositiveIntegerField(
        _("Carga Horária Realizada (horas)"),
        default=0,
        help_text=_("Calculado automaticamente pelas sessões realizadas")
    )
    
    percentual_presenca_minimo = models.PositiveIntegerField(
        _("Presença Mínima (%)"),
        default=75,
        help_text=_("Percentual mínimo de presença para certificação")
    )
    nota_minima_aprovacao = models.DecimalField(
        _("Nota Mínima para Aprovação"),
        max_digits=4,
        decimal_places=2,
        default=10.0,
        help_text=_("Nota mínima para aprovação (escala 0-20)")
    )
    
    concluida = models.BooleanField(_("Formação Concluída"), default=False)
    data_conclusao = models.DateField(_("Data de Conclusão"), null=True, blank=True)
    
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('distrito', 'numero', 'tipo_formacao')
        ordering = ['distrito', 'numero']
        verbose_name = _("Turma")
        verbose_name_plural = _("Turmas")

    def __str__(self):
        return f"{self.nome} - {self.get_tipo_formacao_display()} ({self.distrito.nome})"
    
    @property
    def duracao_dias(self):
        """Calcula duração em dias entre data_inicio e data_fim"""
        if self.data_inicio and self.data_fim:
            return (self.data_fim - self.data_inicio).days + 1
        return None
    
    @property
    def percentual_carga_horaria(self):
        """Calcula percentual de carga horária realizada"""
        if self.carga_horaria_prevista > 0:
            return round((self.carga_horaria_realizada / self.carga_horaria_prevista) * 100, 2)
        return 0
    

    def clean(self):
        super().clean()
        # Formadores Nacionais requerem Província, não Distrito
        if self.tipo_formacao == TipoFormacao.FORMADORES_NACIONAIS:
            if not self.provincia:
                raise ValidationError(
                    _("Formadores Nacionais requerem uma Direção Provincial seleccionada.")
                )
        else:
            # Todos os outros tipos requerem Distrito
            if not self.distrito:
                raise ValidationError(
                    _("Este tipo de formação requer um Distrito seleccionado.")
                )
                
        # Validação em Cascata (Hierarquia de Formação)
        if self.data_inicio:
            if self.tipo_formacao == TipoFormacao.FORMADORES_PROVINCIAIS and self.distrito:
                prov_id = self.distrito.provincia_id
                existe_nacional = Turma.objects.filter(
                    tipo_formacao=TipoFormacao.FORMADORES_NACIONAIS,
                    provincia_id=prov_id,
                    data_fim__lte=self.data_inicio
                ).exclude(pk=self.pk).exists()
                
                if not existe_nacional:
                    raise ValidationError(
                        _("Validação em Cascata: Na província selecionada, a formação de Formadores Provinciais só pode iniciar após uma Turma de Formadores Nacionais concluída ou com data final anterior ou igual ao início pretendido.")
                    )
                    
            elif self.tipo_formacao in [TipoFormacao.BRIGADISTAS, TipoFormacao.MMV, TipoFormacao.AGENTES_EDUCACAO] and self.distrito:
                prov_id = self.distrito.provincia_id
                existe_provincial = Turma.objects.filter(
                    tipo_formacao=TipoFormacao.FORMADORES_PROVINCIAIS,
                    distrito__provincia_id=prov_id,
                    data_fim__lte=self.data_inicio
                ).exclude(pk=self.pk).exists()
                
                if not existe_provincial:
                    tipo_nome = self.get_tipo_formacao_display() if hasattr(self, 'get_tipo_formacao_display') else dict(TipoFormacao.choices).get(self.tipo_formacao)
                    raise ValidationError(
                        _(f"Validação em Cascata: A turma de {tipo_nome} só pode iniciar após uma Turma de Formadores Provinciais concluída na mesma Província (data de fim <= data de início desta turma).")
                    )

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.distrito:
                total_turmas = Turma.objects.filter(
                    distrito=self.distrito,
                    tipo_formacao=self.tipo_formacao
                ).count()
                if total_turmas >= 35:
                    pass
        super().save(*args, **kwargs)


class PlanoFormacaoDistrito(models.Model):
    """
    Plano de formação por tipo de agente, por distrito.
    Cada tipo (Brigadistas, MMV, Agentes de Educação Cívica) tem um plano separado,
    com regras de cálculo próprias.

    - BRIGADISTAS: calculado a partir do nº de brigadas × 3 + margem de contingência
    - MMV: calculado a partir do nº directo de agentes previstos (só período eleitoral)
    - AGENTES_EDUCACAO: calculado a partir do nº directo de agentes previstos
    """

    # --- Tipos de agente que têm plano ---
    class TipoPlano(models.TextChoices):
        BRIGADISTAS    = 'BRIGADISTAS',    _('Brigadistas')
        MMV            = 'MMV',            _('Membros de Mesas de Voto (MMV)')
        AGENTES_EDUCACAO = 'AGENTES_EDUCACAO', _('Agentes de Educação Cívica')

    class EstadoPlano(models.TextChoices):
        RASCUNHO = 'RASCUNHO', _('Rascunho')
        SUBMETIDO_RH = 'SUBMETIDO_RH', _('Submetido aos RH')

    BRIGADISTAS_POR_BRIGADA = 3  # Regra de negócio fixada

    # --- Campos base ---
    distrito = models.ForeignKey(
        Distrito,
        on_delete=models.CASCADE,
        related_name='planos_formacao',
        verbose_name=_("Distrito")
    )
    tipo = models.CharField(
        _("Tipo de Plano"),
        max_length=30,
        choices=TipoPlano.choices,
        help_text=_("Tipo de agente para o qual se define este plano. "
                    "Cada tipo tem um plano separado.")
    )

    # --- Campos para BRIGADISTAS (calculado via brigadas) ---
    num_brigadas = models.PositiveIntegerField(
        _("Número de Brigadas"),
        null=True, blank=True,
        help_text=_("(Brigadistas) Total de brigadas a funcionar neste distrito. "
                    "O sistema calcula 3 brigadistas × brigada.")
    )

    # --- Campos para MMV e AGENTES_EDUCACAO (número directo) ---
    num_agentes_previstos = models.PositiveIntegerField(
        _("Nº de Agentes Previstos"),
        null=True, blank=True,
        help_text=_("(MMV / Agentes de Educ. Cívica) Número total de agentes a formar neste distrito.")
    )

    # --- Margem de contingência (aplica-se a todos os tipos) ---
    margem_contingencia = models.DecimalField(
        _("Margem de Contingência (%)"),
        max_digits=5,
        decimal_places=2,
        default=5.0,
        help_text=_("Percentagem adicional para cobrir desistências. Ex: 5 = 5%")
    )

    # --- Capacidade por turma ---
    candidatos_por_turma = models.PositiveIntegerField(
        _("Candidatos por Turma"),
        default=40,
        help_text=_("Número máximo de formandos por turma para este tipo.")
    )

    estado = models.CharField(
        _("Estado do Plano"),
        max_length=20,
        choices=EstadoPlano.choices,
        default=EstadoPlano.RASCUNHO,
        help_text=_("Indica se o plano ainda está a ser trabalhado (Rascunho) ou se já foi Submetido aos RH.")
    )

    atualizado_em = models.DateTimeField(auto_now=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    # ----------------------------------------------------------------
    # Propriedades de cálculo — adaptadas ao tipo
    # ----------------------------------------------------------------

    @property
    def total_base(self):
        """Total de agentes a formar SEM margem de contingência."""
        if self.tipo == self.TipoPlano.BRIGADISTAS:
            if self.num_brigadas:
                return self.num_brigadas * self.BRIGADISTAS_POR_BRIGADA
            return 0
        else:
            # MMV e Agentes de Educação Cívica: número directo
            return self.num_agentes_previstos or 0

    @property
    def total_com_contingencia(self):
        """Total de agentes a formar incluindo a margem de contingência."""
        fator = 1 + float(self.margem_contingencia) / 100
        return math.ceil(self.total_base * fator)

    @property
    def num_turmas_necessarias(self):
        """Número de turmas necessárias para cobrir o total com contingência."""
        if self.candidatos_por_turma > 0 and self.total_com_contingencia > 0:
            return math.ceil(self.total_com_contingencia / self.candidatos_por_turma)
        return 0

    def turmas_criadas(self):
        """Turmas já criadas neste distrito para este tipo."""
        return self.distrito.turmas.filter(tipo_formacao=self.tipo).count()

    def __str__(self):
        return f"Plano {self.get_tipo_display()} — {self.distrito.nome}"

    def clean(self):
        super().clean()
        if self.tipo == self.TipoPlano.BRIGADISTAS:
            if not self.num_brigadas:
                raise ValidationError(
                    _("Para Brigadistas, deve indicar o número de brigadas.")
                )
        else:
            if not self.num_agentes_previstos:
                raise ValidationError(
                    _("Para %(tipo)s, deve indicar o número de agentes previstos.") % {
                        'tipo': self.get_tipo_display()
                    }
                )

    class Meta:
        unique_together = ('distrito', 'tipo')
        verbose_name = _("Plano de Formação por Distrito")
        verbose_name_plural = _("Planos de Formação por Distrito")
        ordering = ['distrito__provincia__nome', 'distrito__nome', 'tipo']



class Certificacao(models.Model):
    class TipoCertificacao(models.TextChoices):
        FORMADOR = 'FORMADOR', _('Formador Certificado')
        MMV = 'MMV', _('MMV Certificado')
        AGENTE_EDUCACAO = 'AGENTE_EDUCACAO', _('Agente de Educação Cívica Certificado')
        BRIGADISTA = 'BRIGADISTA', _('Brigadista Certificado')
    
    class EstadoCertificacao(models.TextChoices):
        ATIVO = 'ATIVO', _('Ativo')
        SUSPENSO = 'SUSPENSO', _('Suspenso')
        REVOGADO = 'REVOGADO', _('Revogado')
        EXPIRADO = 'EXPIRADO', _('Expirado')
    
    candidato = models.ForeignKey(
        'core.CandidatoFormacao',
        on_delete=models.CASCADE,
        related_name='certificacoes',
        verbose_name=_("Candidato")
    )
    turma = models.ForeignKey(
        Turma,
        on_delete=models.SET_NULL,
        null=True,
        related_name='certificacoes_emitidas',
        verbose_name=_("Turma de Origem")
    )
    
    tipo = models.CharField(
        _("Tipo de Certificação"),
        max_length=20,
        choices=TipoCertificacao.choices
    )
    numero_certificado = models.CharField(
        _("Número do Certificado"),
        max_length=50,
        unique=True,
        help_text=_("Gerado automaticamente")
    )
    
    data_emissao = models.DateField(_("Data de Emissão"), auto_now_add=True)
    data_validade = models.DateField(
        _("Data de Validade"),
        null=True,
        blank=True,
        help_text=_("Deixe em branco para certificação permanente")
    )
    
    nota_final = models.DecimalField(
        _("Nota Final"),
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Escala 0-20")
    )
    percentual_presenca = models.DecimalField(
        _("Percentual de Presença"),
        max_digits=5,
        decimal_places=2,
        help_text=_("Calculado automaticamente")
    )
    
    estado = models.CharField(
        _("Estado"),
        max_length=20,
        choices=EstadoCertificacao.choices,
        default=EstadoCertificacao.ATIVO
    )
    
    documento_pdf = models.FileField(
        _("Certificado PDF"),
        upload_to='certificados/',
        null=True,
        blank=True
    )
    
    observacoes = models.TextField(_("Observações"), blank=True, null=True)
    
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Certificação")
        verbose_name_plural = _("Certificações")
        ordering = ['-data_emissao']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.candidato.nome_completo} ({self.numero_certificado})"
    
    def gerar_numero_certificado(self):
        """Gera número único de certificado no formato: TIPO-DISTRITO-ANO-SEQUENCIAL"""
        if self.numero_certificado:
            return self.numero_certificado
        
        from django.db import transaction
        from datetime import datetime
        
        ano = datetime.now().year
        tipo_codigo = 'F' if self.tipo == self.TipoCertificacao.FORMADOR else 'B'
        
        # Determinar um prefixo geográfico seguro para o certificado
        local_prefix = "0"
        if self.turma:
            if self.turma.distrito:
                local_prefix = str(self.turma.distrito.id)
            elif self.turma.provincia:
                local_prefix = f"P{self.turma.provincia.id}"
                
        with transaction.atomic():
            ultimo = Certificacao.objects.filter(
                tipo=self.tipo,
                numero_certificado__startswith=f"{tipo_codigo}-{local_prefix}-{ano}"
            ).order_by('-numero_certificado').first()
            
            if ultimo and ultimo.numero_certificado:
                try:
                    partes = ultimo.numero_certificado.split('-')
                    sequencial = int(partes[-1]) + 1
                except (ValueError, IndexError):
                    sequencial = 1
            else:
                sequencial = 1
            
            numero = f"{tipo_codigo}-{local_prefix}-{ano}-{sequencial:05d}"
            
            tentativas = 0
            while Certificacao.objects.filter(numero_certificado=numero).exists() and tentativas < 100:
                sequencial += 1
                numero = f"{tipo_codigo}-{local_prefix}-{ano}-{sequencial:05d}"
                tentativas += 1
            
            return numero
    
    def clean(self):
        if self.turma and not self.turma.concluida:
            raise ValidationError(_("A turma ainda não foi concluída."))
        
        if self.percentual_presenca < self.turma.percentual_presenca_minimo:
            raise ValidationError(
                _(f"Candidato não atingiu presença mínima ({self.percentual_presenca}% < {self.turma.percentual_presenca_minimo}%)")
            )
        
        if self.nota_final and self.nota_final < self.turma.nota_minima_aprovacao:
            raise ValidationError(
                _(f"Candidato não atingiu nota mínima ({self.nota_final} < {self.turma.nota_minima_aprovacao})")
            )
    
    def save(self, *args, **kwargs):
        if not self.numero_certificado:
            self.numero_certificado = self.gerar_numero_certificado()
        super().save(*args, **kwargs)

class Brigada(models.Model):
    """
    Representa uma Brigada de Recenseamento ou outra unidade funcional.
    Constituída por brigadistas certificados e alocados a um distrito.
    """
    nome = models.CharField(_("Nome da Brigada"), max_length=100)
    distrito = models.ForeignKey(
        Distrito,
        on_delete=models.CASCADE,
        related_name='brigadas',
        verbose_name=_("Distrito")
    )
    membros = models.ManyToManyField(
        'core.CandidatoFormacao',
        blank=True,
        related_name='brigadas_membro',
        verbose_name=_("Membros (Brigadistas)")
    )
    ativa = models.BooleanField(_("Ativa"), default=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Brigada")
        verbose_name_plural = _("Brigadas")
        ordering = ['distrito', 'nome']
        unique_together = ('distrito', 'nome')

    def __str__(self):
        return f"{self.nome} ({self.distrito.nome})"
