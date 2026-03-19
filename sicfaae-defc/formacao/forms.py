from django import forms
from django.core.exceptions import ValidationError
from .models import Turma, Local, Certificacao, TipoFormacao, PlanoFormacaoDistrito, Brigada

class BrigadaForm(forms.ModelForm):
    """
    Formulário para Gestão de Brigadas.
    Filtra os membros para mostrar apenas Brigadistas Certificados no distrito.
    """
    class Meta:
        model = Brigada
        fields = ['nome', 'distrito', 'membros', 'ativa']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'distrito': forms.Select(attrs={'class': 'form-select'}),
            'membros': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import PerfilUtilizador
        from core.utils import obter_perfil_usuario
        
        # Filtrar distritos por permissão se houver user
        if user:
            perfil = obter_perfil_usuario(user)
            if perfil and not user.is_superuser:
                if perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
                    self.fields['distrito'].queryset = Distrito.objects.filter(provincia=perfil.provincia)
                elif perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
                    self.fields['distrito'].queryset = Distrito.objects.filter(pk=perfil.distrito.pk)
                    self.fields['distrito'].initial = perfil.distrito
                    self.fields['distrito'].disabled = True

        # Se ja tivermos um distrito (ou seja edição ou filtro aplicado)
        # filtramos os membros para apenas brigadistas certificados
        distrito_id = self.data.get('distrito') or (self.instance.distrito.id if self.instance.pk else None)
        
        if distrito_id:
            # Candidatos do distrito que tenham certificação de BRIGADISTA ativa
            certificados_ids = Certificacao.objects.filter(
                tipo=Certificacao.TipoCertificacao.BRIGADISTA,
                estado=Certificacao.EstadoCertificacao.ATIVO,
                turma__distrito_id=distrito_id
            ).values_list('candidato_id', flat=True)
            
            self.fields['membros'].queryset = CandidatoFormacao.objects.filter(
                id__in=certificados_ids
            ).order_by('nome_completo')
            self.fields['membros'].help_text = "Apenas brigadistas com certificação ativa neste distrito são listados."
        else:
            self.fields['membros'].queryset = CandidatoFormacao.objects.none()
            self.fields['membros'].help_text = "Seleccione um distrito para ver os brigadistas disponíveis."
from core.models import Distrito, CandidatoFormacao, Provincia, ConfiguracaoSistema

class ConfiguracaoSistemaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoSistema
        fields = ['periodo_ativo']
        widgets = {
            'periodo_ativo': forms.Select(attrs={'class': 'form-select'})
        }

class LocalForm(forms.ModelForm):
    class Meta:
        model = Local
        fields = ['nome', 'distrito', 'capacidade', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'distrito': forms.Select(attrs={'class': 'form-select'}),
            'capacidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ex: Sala 10, Horário 08:00-12:00'}),
        }

class TurmaForm(forms.ModelForm):
    # Campo extra: Província (para Formadores Nacionais)
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.all(),
        required=False,
        label="Direção Provincial",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_provincia_turma'
        }),
        help_text="Obrigatório apenas para Formadores Nacionais"
    )

    # Sobrescrever o campo local para ser uma TextBox com Autocomplete em vez de Select
    local = forms.CharField(
        required=False,
        label="Local de Formação",
        help_text="Escreva um novo local ou seleccione na lista",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': 'locais-datalist',
            'placeholder': 'Escreva o nome do local ou seleccione...'
        })
    )

    class Meta:
        model = Turma
        fields = ['nome', 'tipo_formacao', 'distrito', 'provincia', 'local', 'numero',
                  'data_inicio', 'data_fim', 'carga_horaria_prevista',
                  'percentual_presenca_minimo', 'nota_minima_aprovacao', 'formadores']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_formacao': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_tipo_formacao',
                'onchange': 'handleTipoFormacaoChange(this.value)'
            }),
            'distrito': forms.Select(attrs={'class': 'form-select', 'id': 'id_distrito_turma'}),
            'numero': forms.NumberInput(attrs={'class': 'form-control'}),
            'carga_horaria_prevista': forms.NumberInput(attrs={'class': 'form-control'}),
            'percentual_presenca_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'nota_minima_aprovacao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'formadores': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Determinar o tipo de formação (do instance, dos dados submetidos ou initial)
        tipo = None
        if self.instance and self.instance.pk:
            tipo = self.instance.tipo_formacao
        if self.data.get('tipo_formacao'):
            tipo = self.data.get('tipo_formacao')
        if not tipo and kwargs.get('initial') and kwargs['initial'].get('tipo_formacao'):
            tipo = kwargs['initial'].get('tipo_formacao')

        # Filtrar formadores pela Hierarquia de Formação
        from django.db.models import F
        
        if tipo in [TipoFormacao.BRIGADISTAS, TipoFormacao.MMV, TipoFormacao.AGENTES_EDUCACAO]:
            # Turmas base são dadas por Formadores Provinciais (que foram alunos na turma e APROVARAM)
            formadores_qs = CandidatoFormacao.objects.filter(
                ativo=True,
                certificacoes__turma__tipo_formacao=TipoFormacao.FORMADORES_PROVINCIAIS,
                certificacoes__nota_final__gte=F('certificacoes__turma__nota_minima_aprovacao'),
                certificacoes__percentual_presenca__gte=F('certificacoes__turma__percentual_presenca_minimo')
            ).distinct()
            self.fields['formadores'].help_text = "Selecione exactamente 2 formadores (Apenas Formadores Provinciais Aprovados)"
            
        elif tipo == TipoFormacao.FORMADORES_PROVINCIAIS:
            # Turmas provinciais são dadas por Formadores Nacionais (que foram alunos na turma e APROVARAM)
            formadores_qs = CandidatoFormacao.objects.filter(
                ativo=True,
                certificacoes__turma__tipo_formacao=TipoFormacao.FORMADORES_NACIONAIS,
                certificacoes__nota_final__gte=F('certificacoes__turma__nota_minima_aprovacao'),
                certificacoes__percentual_presenca__gte=F('certificacoes__turma__percentual_presenca_minimo')
            ).distinct()
            self.fields['formadores'].help_text = "Selecione exactamente 2 formadores (Apenas Formadores Nacionais Aprovados)"
            
        elif tipo == TipoFormacao.FORMADORES_NACIONAIS:
            # Turmas nacionais são dadas por Formadores de Nível 1 (cadastrados manualmente, código F1-...)
            formadores_qs = CandidatoFormacao.objects.filter(
                ativo=True,
                tipo_agente=CandidatoFormacao.TipoAgente.FORMADOR,
                codigo_candidato__startswith='F1-'
            ).distinct()
            self.fields['formadores'].help_text = "Selecione formadores (Apenas Formadores de Nível 1)"
            
        else:
            formadores_qs = CandidatoFormacao.objects.none()
            self.fields['formadores'].help_text = "Selecione o Tipo de Formação para carregar os Formadores válidos"

        self.fields['formadores'].queryset = formadores_qs

        # Pre-carregar provincia do instance
        if self.instance and self.instance.pk:
            if self.instance.provincia:
                self.fields['provincia'].initial = self.instance.provincia
            if self.instance.local:
                self.fields['local'].initial = self.instance.local.nome

        # Restrição Hierárquica por Usuário
        if user and not user.is_superuser:
            try:
                perfil = user.perfil
                from core.models import PerfilUtilizador

                if perfil:
                    if perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL and perfil.distrito:
                        self.fields['distrito'].initial = perfil.distrito
                        self.fields['distrito'].queryset = Distrito.objects.filter(pk=perfil.distrito.pk)
                        self.fields['distrito'].disabled = True
                        self.fields['local'].queryset = Local.objects.filter(distrito=perfil.distrito)
                        # Restringir província ao distrital
                        self.fields['provincia'].queryset = Provincia.objects.filter(
                            pk=perfil.distrito.provincia.pk
                        )
                    elif perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL and perfil.provincia:
                        self.fields['distrito'].queryset = Distrito.objects.filter(provincia=perfil.provincia)
                        self.fields['local'].queryset = Local.objects.filter(distrito__provincia=perfil.provincia)
                        self.fields['provincia'].queryset = Provincia.objects.filter(pk=perfil.provincia.pk)
                        self.fields['provincia'].initial = perfil.provincia
            except AttributeError:
                pass

    def clean(self):
        cleaned_data = super().clean()
        distrito = cleaned_data.get('distrito')
        tipo_formacao = cleaned_data.get('tipo_formacao')
        provincia = cleaned_data.get('provincia')
        formadores = cleaned_data.get('formadores')
        local_nome = cleaned_data.get('local')

        # Se houver nome do local válido, obter ou criar o Local respectivo
        if local_nome:
            if isinstance(local_nome, str): # Confirmar se ainda é uma string
                # Para Turmas Provinciais/Nacionais, não há distrito exigido no formulário. Usar o 1º da província como âncora
                distrito_alvo = distrito
                if not distrito_alvo and provincia:
                    distrito_alvo = Distrito.objects.filter(provincia=provincia).first()
                
                if distrito_alvo:
                    local_obj, _ = Local.objects.get_or_create(
                        nome__iexact=local_nome,
                        distrito=distrito_alvo,
                        defaults={'nome': local_nome}
                    )
                    cleaned_data['local'] = local_obj
                    self.instance.local = local_obj
                else:
                    self.add_error('local', "Não foi possível determinar o distrito para gravar este local.")
                    
        # Salvar província no campo do modelo
        if provincia:
            self.instance.provincia = provincia

        # Validação: Formadores Nacionais requerem Província
        if tipo_formacao == TipoFormacao.FORMADORES_NACIONAIS:
            if not provincia:
                self.add_error('provincia', "Seleccione a Direção Provincial para Formadores Nacionais.")
        else:
            # Todos os outros tipos requerem Distrito
            if not distrito:
                self.add_error('distrito', "Seleccione o Distrito para este tipo de formação.")

        # Validar: exactamente 2 formadores por turma (excepto Formadores Nacionais pioneiros que pode ser mais flexivel)
        if formadores is not None:
            num = len(formadores)
            if tipo_formacao != TipoFormacao.FORMADORES_NACIONAIS and num != 2:
                self.add_error(
                    'formadores',
                    f"Cada turma regular deve ter exactamente 2 formadores. Seleccionou {num}."
                )

        # Validação de Limite de 35 Turmas por tipo por distrito (apenas para turmas de delegacao)
        if distrito and tipo_formacao and tipo_formacao != TipoFormacao.FORMADORES_NACIONAIS:
            qs = Turma.objects.filter(distrito=distrito, tipo_formacao=tipo_formacao)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.count() >= 35:
                raise forms.ValidationError(
                    f"Este distrito já atingiu o limite máximo de 35 turmas de {tipo_formacao}."
                )

        return cleaned_data

class GerarTurmasForm(forms.Form):
    distrito = forms.ModelChoiceField(queryset=Distrito.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    local = forms.ModelChoiceField(queryset=Local.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    data_inicio = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    data_fim = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            try:
                perfil = user.perfil
                if perfil and perfil.distrito:
                    self.fields['distrito'].initial = perfil.distrito
                    self.fields['distrito'].disabled = True
                    self.fields['local'].queryset = Local.objects.filter(distrito=perfil.distrito)
                elif perfil and perfil.provincia:
                    self.fields['distrito'].queryset = Distrito.objects.filter(provincia=perfil.provincia)
                    self.fields['local'].queryset = Local.objects.filter(distrito__provincia=perfil.provincia)
            except:
                pass


class CertificacaoForm(forms.ModelForm):
    """Formulário para emitir certificações"""
    class Meta:
        model = Certificacao
        fields = ['candidato', 'turma', 'tipo', 'nota_final', 'percentual_presenca', 'data_validade', 'observacoes']
        widgets = {
            'candidato': forms.Select(attrs={'class': 'form-select'}),
            'turma': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'nota_final': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'percentual_presenca': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data_validade': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        turma = cleaned_data.get('turma')
        candidato = cleaned_data.get('candidato')
        percentual_presenca = cleaned_data.get('percentual_presenca')
        nota_final = cleaned_data.get('nota_final')
        
        if turma and not turma.concluida:
            raise ValidationError("A turma ainda não foi concluída.")
        
        if turma and percentual_presenca < turma.percentual_presenca_minimo:
            raise ValidationError(
                f"Candidato não atingiu presença mínima ({percentual_presenca}% < {turma.percentual_presenca_minimo}%)"
            )
        
        if turma and nota_final and nota_final < turma.nota_minima_aprovacao:
            raise ValidationError(
                f"Candidato não atingiu nota mínima ({nota_final} < {turma.nota_minima_aprovacao})"
            )
        
        return cleaned_data


class GerarTurmasFormadoresForm(forms.Form):
    provincia = forms.ChoiceField(
        choices=[], 
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Província (Filtro de Candidatos)"
    )
    local = forms.ModelChoiceField(
        queryset=Local.objects.none(), 
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Local de Formação"
    )
    data_inicio = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    data_fim = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    capacidade = forms.IntegerField(
        initial=30, 
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Candidatos por turma"
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import Provincia
        
        # Carregar províncias
        self.fields['provincia'].choices = [(p.id, p.nome) for p in Provincia.objects.all()]
        self.fields['local'].queryset = Local.objects.all().select_related('distrito')
        
        if user and not user.is_superuser:
            try:
                perfil = user.perfil
                if perfil and perfil.provincia:
                    # Fixar província para usuário provincial
                    self.fields['provincia'].choices = [(perfil.provincia.id, perfil.provincia.nome)]
                    self.fields['provincia'].initial = perfil.provincia.id
                    self.fields['provincia'].disabled = True
                    # Filtrar locais da província
                    self.fields['local'].queryset = Local.objects.filter(distrito__provincia=perfil.provincia)
            except:
                pass



class RegistarFormadorForm(forms.ModelForm):
    provincia_residencia = forms.ModelChoiceField(
        queryset=Provincia.objects.all(),
        label="Província de Residência",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = CandidatoFormacao
        fields = ['nome_completo', 'genero', 'data_nascimento', 'numero_bi', 'numero_telefone', 'endereco']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'genero': forms.Select(attrs={'class': 'form-select'}),
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'numero_bi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número do BI'}),
            'numero_telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '84/82/87...'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Bairro, Rua, Casa...'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['numero_telefone'].required = True

    def clean_numero_bi(self):
        numero_bi = self.cleaned_data['numero_bi']
        if CandidatoFormacao.objects.filter(numero_bi=numero_bi).exists():
            raise forms.ValidationError("Já existe um formador/candidato com este BI.")
        return numero_bi

class CadastrarFormadorNacionalForm(forms.ModelForm):
    """
    Formulário simplificado para o Cadastro de Formadores Nacionais
    directamente na secção do DEFC.
    """
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.all(),
        label="Província",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    distrito = forms.ModelChoiceField(
        queryset=Distrito.objects.all(),
        label="Distrito",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = CandidatoFormacao
        fields = ['nome_completo', 'genero', 'data_nascimento', 'numero_bi', 'numero_telefone', 'provincia', 'distrito', 'endereco']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'genero': forms.Select(attrs={'class': 'form-select'}),
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'numero_bi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número do BI'}),
            'numero_telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '84/82/87...'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Bairro, Rua, Casa...'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['numero_telefone'].required = True

    def clean_numero_bi(self):
        numero_bi = self.cleaned_data['numero_bi']
        qs = CandidatoFormacao.objects.filter(numero_bi=numero_bi)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Já existe um formador/candidato com este BI no sistema.")
        return numero_bi


from core.models import PerfilUtilizador
class FormularioCriacaoUsuario(forms.ModelForm):
    """
    Formulário para criar utilizadores com perfil associado no DEFC.
    Adapta-se ao nível do utilizador logado (hierarquia).
    """
    username = forms.CharField(label="Nome de Utilizador", widget=forms.TextInput(attrs={'class': 'form-control'}))
    nivel = forms.ChoiceField(choices=PerfilUtilizador.Nivel.choices, label="Nível de Acesso", widget=forms.Select(attrs={'class': 'form-select'}))
    provincia = forms.ModelChoiceField(queryset=Provincia.objects.all(), required=False, label="Província", widget=forms.Select(attrs={'class': 'form-select'}))
    distrito = forms.ModelChoiceField(queryset=Distrito.objects.all(), required=False, label="Distrito", widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = PerfilUtilizador
        fields = ['username', 'nivel', 'provincia', 'distrito']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_creator = user
        perfil_criador = getattr(user, 'perfil', None)

        # Lógica Hierárquica
        if user.is_superuser or (perfil_criador and perfil_criador.nivel == PerfilUtilizador.Nivel.CENTRAL):
            self.fields['nivel'].choices = [
                (PerfilUtilizador.Nivel.CENTRAL, 'Central'),
                (PerfilUtilizador.Nivel.PROVINCIAL, 'Provincial'),
            ]
        elif perfil_criador and perfil_criador.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
            self.fields['nivel'].choices = [
                (PerfilUtilizador.Nivel.DISTRITAL, 'Distrital'),
                (PerfilUtilizador.Nivel.PROVINCIAL, 'Provincial')
            ]
            self.fields['nivel'].initial = PerfilUtilizador.Nivel.DISTRITAL
            
            # Província fixa (a do criador)
            self.fields['provincia'].queryset = Provincia.objects.filter(pk=perfil_criador.provincia.pk)
            self.fields['provincia'].initial = perfil_criador.provincia
            self.fields['provincia'].widget.attrs['readonly'] = True
            
            # Distritos apenas desta província
            if perfil_criador.provincia:
                self.fields['distrito'].queryset = Distrito.objects.filter(provincia=perfil_criador.provincia)
            else:
                self.fields['distrito'].queryset = Distrito.objects.none()
        elif perfil_criador and perfil_criador.nivel == PerfilUtilizador.Nivel.DISTRITAL:
            # Distrital criando (normalmente Entrevistador - mas aqui seria Staff local)
            self.fields['nivel'].choices = [
                (PerfilUtilizador.Nivel.DISTRITAL, 'Distrital'),
            ]
            self.fields['nivel'].initial = PerfilUtilizador.Nivel.DISTRITAL
            
            # Província e Distrito fixos
            self.fields['provincia'].queryset = Provincia.objects.filter(pk=perfil_criador.provincia.pk)
            self.fields['provincia'].initial = perfil_criador.provincia
            self.fields['provincia'].widget.attrs['readonly'] = True
            
            self.fields['distrito'].queryset = Distrito.objects.filter(pk=perfil_criador.distrito.pk)
            self.fields['distrito'].initial = perfil_criador.distrito
            self.fields['distrito'].widget.attrs['readonly'] = True
        else:
            pass

    def clean_username(self):
        username = self.cleaned_data['username']
        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nome de utilizador já está em uso. Por favor, escolha outro.")
        return username

    def save(self, commit=True, generated_password=None):
        # 1. Criar User
        from django.contrib.auth.models import User
        username = self.cleaned_data['username']
        
        user = User.objects.create_user(username=username, password=generated_password)
        
        # 2. Atualizar Perfil
        if hasattr(user, 'perfil'):
            perfil = user.perfil
        else:
            perfil = super().save(commit=False)
            perfil.usuario = user
        
        perfil.nivel = self.cleaned_data['nivel']
        perfil.provincia = self.cleaned_data['provincia']
        perfil.distrito = self.cleaned_data['distrito']
        
        if commit:
            perfil.save()
        return perfil


class PlanoFormacaoDistritoForm(forms.ModelForm):
    """
    Formulário para o Plano de Formação por Tipo.
    - BRIGADISTAS: introduz nº de brigadas → sistema calcula 3 × brigadas + margem%
    - MMV / AGENTES_EDUCACAO: introduz directamente o nº de agentes previstos
    """
    class Meta:
        model = PlanoFormacaoDistrito
        fields = [
            'distrito',
            'tipo',
            'num_brigadas',
            'num_agentes_previstos',
            'margem_contingencia',
            'candidatos_por_turma',
        ]
        widgets = {
            'distrito': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_tipo_plano',
                'onchange': 'handleTipoPlanoChange(this.value)'
            }),
            'num_brigadas': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_num_brigadas',
                'min': '1',
                'oninput': 'calcularPlano()'
            }),
            'num_agentes_previstos': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_num_agentes',
                'min': '1',
                'oninput': 'calcularPlano()'
            }),
            'margem_contingencia': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_margem_contingencia',
                'step': '0.5',
                'min': '0',
                'max': '50',
                'oninput': 'calcularPlano()'
            }),
            'candidatos_por_turma': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_candidatos_por_turma',
                'min': '1',
                'oninput': 'calcularPlano()'
            }),
        }
        labels = {
            'num_brigadistas': 'Nº de Brigadas',
            'num_agentes_previstos': 'Nº de Agentes Previstos',
        }
        help_texts = {
            'num_brigadas': 'Total de brigadas no distrito. O sistema calcula 3 brigadistas × brigada.',
            'num_agentes_previstos': 'Número total de agentes deste tipo a recrutar neste distrito.',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtro de período eleitoral
        from core.models import ConfiguracaoSistema
        from .models import PlanoFormacaoDistrito
        config = ConfiguracaoSistema.get_config()
        
        choices_filtrados = []
        for t in self.fields['tipo'].choices:
            tipo = t[0]
            if not tipo: 
                choices_filtrados.append(t)
                continue
            if config.periodo_ativo == ConfiguracaoSistema.PeriodoEleitoral.RECENSEAMENTO and tipo == PlanoFormacaoDistrito.TipoPlano.MMV:
                continue
            if config.periodo_ativo == ConfiguracaoSistema.PeriodoEleitoral.VOTACAO and tipo == PlanoFormacaoDistrito.TipoPlano.BRIGADISTAS:
                continue
            choices_filtrados.append(t)
        
        self.fields['tipo'].choices = choices_filtrados
        
        if user and not user.is_superuser:
            try:
                perfil = user.perfil
                from core.models import PerfilUtilizador
                if perfil and perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL and perfil.provincia:
                    self.fields['distrito'].queryset = Distrito.objects.filter(provincia=perfil.provincia)
                elif perfil and perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL and perfil.distrito:
                    self.fields['distrito'].queryset = Distrito.objects.filter(pk=perfil.distrito.pk)
                    self.fields['distrito'].initial = perfil.distrito
                    self.fields['distrito'].disabled = True
            except AttributeError:
                pass

