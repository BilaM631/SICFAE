from django import forms
from django.utils import timezone
from .models import Candidato, Provincia, Distrito, PerfilUtilizador, Vaga, Entrevista
from .permissions import obter_perfil_usuario

class FormularioCandidatura(forms.ModelForm):
    class Meta:
        model = Candidato
        fields = [
            'nome_completo', 'genero', 'vaga', 'numero_bi', 'numero_telefone', 
            'provincia', 'distrito', 'endereco', 'arquivo_cv', 'arquivo_bi', 
            'arquivo_certificado', 'foto'
        ]
        error_messages = {
            'numero_bi': {
                'unique': "Este número de BI já se encontra registado.",
            }
        }
        widgets = {
            'vaga': forms.Select(attrs={'class': 'form-select form-select-lg bg-light border-0'}),
            'genero': forms.Select(attrs={'class': 'form-select form-select-lg bg-light border-0'}),
            'nome_completo': forms.TextInput(attrs={'class': 'form-control form-control-lg bg-light border-0', 'placeholder': 'Ex: João Manuel Silva'}),
            'numero_bi': forms.TextInput(attrs={'class': 'form-control form-control-lg bg-light border-0', 'placeholder': 'Ex: 1234567890123'}),
            'numero_telefone': forms.TextInput(attrs={'class': 'form-control form-control-lg bg-light border-0', 'placeholder': 'Ex: 841234567'}),
            'provincia': forms.Select(attrs={'class': 'form-select form-select-lg bg-light border-0 select2', 'data-placeholder': 'Selecione a Província'}),
            'distrito': forms.Select(attrs={'class': 'form-select form-select-lg bg-light border-0 select2', 'data-placeholder': 'Selecione o Distrito'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control bg-light border-0', 'rows': 2, 'placeholder': 'Sua morada completa...'}),
            'arquivo_cv': forms.FileInput(attrs={'class': 'form-control mt-2'}),
            'arquivo_bi': forms.FileInput(attrs={'class': 'form-control mt-2'}),
            'arquivo_certificado': forms.FileInput(attrs={'class': 'form-control mt-2'}),
            'foto': forms.FileInput(attrs={'class': 'form-control mt-2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['distrito'].queryset = Distrito.objects.none()
        
        # Filtrar apenas vagas ativas e dentro do prazo
        hoje = timezone.now().date()
        self.fields['vaga'].queryset = Vaga.objects.filter(
            ativa=True,
            data_inicio__lte=hoje,
            data_fim__gte=hoje
        )

        if 'provincia' in self.data:
            try:
                provincia_id = int(self.data.get('provincia'))
                self.fields['distrito'].queryset = Distrito.objects.filter(provincia_id=provincia_id).order_by('nome')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.provincia:
            self.fields['distrito'].queryset = self.instance.distrito.provincia.distritos.order_by('nome')

class FormularioCandidaturaEtapa1(forms.ModelForm):
    """Formulário para Etapa 1: Dados Pessoais (sem uploads)"""
    class Meta:
        model = Candidato
        fields = [
            'vaga', 'nome_completo', 'genero', 'data_nascimento',
            'numero_bi', 'numero_telefone', 'provincia', 'distrito', 'endereco'
        ]
        widgets = {
            'vaga': forms.Select(attrs={'class': 'form-select form-select-lg bg-light border-0'}),
            'genero': forms.Select(attrs={'class': 'form-select form-select-lg bg-light border-0'}),
            'nome_completo': forms.TextInput(attrs={'class': 'form-control form-control-lg bg-light border-0', 'placeholder': 'Ex: João Manuel Silva'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control form-control-lg bg-light border-0', 'type': 'date'}),
            'numero_bi': forms.TextInput(attrs={'class': 'form-control form-control-lg bg-light border-0', 'placeholder': 'Ex: 1234567890123'}),
            'numero_telefone': forms.TextInput(attrs={'class': 'form-control form-control-lg bg-light border-0', 'placeholder': 'Ex: 841234567'}),
            'provincia': forms.Select(attrs={'class': 'form-select form-select-lg bg-light border-0 select2', 'data-placeholder': 'Selecione a Província'}),
            'distrito': forms.Select(attrs={'class': 'form-select form-select-lg bg-light border-0 select2', 'data-placeholder': 'Selecione o Distrito'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control bg-light border-0', 'rows': 2, 'placeholder': 'Sua morada completa...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['distrito'].queryset = Distrito.objects.none()
        
        hoje = timezone.now().date()
        self.fields['vaga'].queryset = Vaga.objects.filter(
            ativa=True,
            data_inicio__lte=hoje,
            data_fim__gte=hoje
        )

        if 'provincia' in self.data:
            try:
                provincia_id = int(self.data.get('provincia'))
                self.fields['distrito'].queryset = Distrito.objects.filter(provincia_id=provincia_id).order_by('nome')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.provincia:
            self.fields['distrito'].queryset = self.instance.provincia.distritos.order_by('nome')

class FormularioCandidaturaEtapa2(forms.ModelForm):
    """Formulário para Etapa 2: Upload de Documentos"""
    class Meta:
        model = Candidato
        fields = ['arquivo_cv', 'arquivo_bi', 'arquivo_certificado', 'foto']
        widgets = {
            'arquivo_cv': forms.FileInput(attrs={'class': 'form-control mt-2', 'accept': '.pdf,.doc,.docx'}),
            'arquivo_bi': forms.FileInput(attrs={'class': 'form-control mt-2', 'accept': '.pdf,.jpg,.jpeg,.png'}),
            'arquivo_certificado': forms.FileInput(attrs={'class': 'form-control mt-2', 'accept': '.pdf,.jpg,.jpeg,.png'}),
            'foto': forms.FileInput(attrs={'class': 'form-control mt-2', 'accept': '.jpg,.jpeg,.png'}),
        }

class EntrevistaForm(forms.ModelForm):
    """Formulário para agendamento de entrevista."""
    class Meta:
        model = Entrevista
        fields = ['data_hora', 'local', 'entrevistador', 'observacoes']
        widgets = {
            'data_hora': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'local': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Sala 2 ou Link Meet'}),
            'entrevistador': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AvaliacaoEntrevistaForm(forms.ModelForm):
    """Formulário para avaliação do candidato."""
    class Meta:
        model = Entrevista
        fields = ['nota_tecnica', 'nota_comunicacao', 'nota_experiencia', 'observacoes', 'resultado']
        widgets = {
            'nota_tecnica': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 20}),
            'nota_comunicacao': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 20}),
            'nota_experiencia': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 20}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'resultado': forms.Select(attrs={'class': 'form-select'}),
        }


class FormularioAutenticacao(forms.Form):
    numero_bi = forms.CharField(
        max_length=20, 
        label="Número de BI",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite seu BI'})
    )
    numero_telefone = forms.CharField(
        max_length=15, 
        label="Número de Telefone (usado no registo)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite seu telefone'})
    )

class FormularioCriacaoUsuario(forms.ModelForm):
    """
    Formulário para criar utilizadores com perfil associado.
    Adapta-se ao nível do utilizador logado (hierarquia).
    """
    username = forms.CharField(label="Nome de Utilizador", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Senha/Password", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    nivel = forms.ChoiceField(choices=PerfilUtilizador.Nivel.choices, label="Nível de Acesso", widget=forms.Select(attrs={'class': 'form-select'}))
    provincia = forms.ModelChoiceField(queryset=Provincia.objects.all(), required=False, label="Província", widget=forms.Select(attrs={'class': 'form-select'}))
    distrito = forms.ModelChoiceField(queryset=Distrito.objects.all(), required=False, label="Distrito", widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = PerfilUtilizador
        fields = ['username', 'password', 'nivel', 'provincia', 'distrito']

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
            if perfil_criador.provincia:
                self.fields['distrito'].queryset = Distrito.objects.filter(provincia=perfil_criador.provincia)
            else:
                self.fields['distrito'].queryset = Distrito.objects.none()
        elif perfil_criador and perfil_criador.nivel == PerfilUtilizador.Nivel.DISTRITAL:
            # Distrital criando (normalmente Entrevistador)
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

    def save(self, commit=True):
        # 1. Criar User
        from django.contrib.auth.models import User
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        
        user = User.objects.create_user(username=username, password=password)
        
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


class FormularioValidacaoDocumentos(forms.ModelForm):
    class Meta:
        model = Candidato
        fields = [
            'validacao_bi',
            'validacao_cv',
            'validacao_certificado',
            'validacao_nuit',
            'validacao_registo_criminal',
            'validacao_atestado_medico',
            'validacao_requerimento'
        ]
        widgets = {
            'validacao_bi': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'validacao_cv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'validacao_certificado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'validacao_nuit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'validacao_registo_criminal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'validacao_atestado_medico': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'validacao_requerimento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class FormularioCandidaturaManual(forms.ModelForm):
    class Meta:
        model = Candidato
        fields = [
            'nome_completo', 'numero_bi', 'numero_telefone', 'vaga',
            'provincia', 'distrito',
            'validacao_bi', 'validacao_cv', 'validacao_certificado',
            'validacao_nuit', 'validacao_registo_criminal', 
            'validacao_atestado_medico', 'validacao_requerimento'
        ]
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Completo'}),
            'numero_bi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de BI'}),
            'numero_telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefone'}),
            'vaga': forms.Select(attrs={'class': 'form-select'}),
            'provincia': forms.Select(attrs={'class': 'form-select select2', 'id': 'id_provincia'}),
            'distrito': forms.Select(attrs={'class': 'form-select select2', 'id': 'id_distrito'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Checkboxes style
        for field_name in self.fields:
            if field_name.startswith('validacao_'):
                self.fields[field_name].widget.attrs['class'] = 'form-check-input'

        # Cascade Logic (same as main form)
        self.fields['distrito'].queryset = Distrito.objects.none()
        
        # Vagas Filter
        hoje = timezone.now().date()
        self.fields['vaga'].queryset = Vaga.objects.filter(
            ativa=True, data_inicio__lte=hoje, data_fim__gte=hoje
        )

        if 'provincia' in self.data:
            try:
                provincia_id = int(self.data.get('provincia'))
                self.fields['distrito'].queryset = Distrito.objects.filter(provincia_id=provincia_id).order_by('nome')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.provincia:
            self.fields['distrito'].queryset = self.instance.distrito.provincia.distritos.order_by('nome')


class VagaFormEtapa1(forms.ModelForm):
    '''Etapa 1: Dados básicos da vaga'''
    
    class Meta:
        model = Vaga
        fields = ['titulo', 'descricao', 'data_inicio', 'data_fim', 'ativa', 'requer_formacao', 'nivel_aprovacao', 'provincia', 'distrito']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nivel_aprovacao': forms.Select(attrs={'class': 'form-select'}),
            'provincia': forms.Select(attrs={'class': 'form-select'}),
            'distrito': forms.Select(attrs={'class': 'form-select'}),
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['provincia'].required = False
        self.fields['distrito'].required = False
        
        # Filtro de permissões hierárquicas
        if user and not user.is_superuser:
            perfil = obter_perfil_usuario(user)
            if perfil:
                if perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
                    self.fields['nivel_aprovacao'].choices = [(Vaga.NivelAprovacao.DISTRITAL, 'STAE Distrital')]
                    self.fields['nivel_aprovacao'].initial = Vaga.NivelAprovacao.DISTRITAL
                    if perfil.provincia:
                        self.fields['provincia'].queryset = Provincia.objects.filter(id=perfil.provincia.id)
                        self.fields['provincia'].initial = perfil.provincia.id
                    if perfil.distrito:
                        self.fields['distrito'].queryset = Distrito.objects.filter(id=perfil.distrito.id)
                        self.fields['distrito'].initial = perfil.distrito.id
                        
                elif perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
                    self.fields['nivel_aprovacao'].choices = [
                        (Vaga.NivelAprovacao.PROVINCIAL, 'STAE Provincial'),
                        (Vaga.NivelAprovacao.DISTRITAL, 'STAE Distrital')
                    ]
                    if getattr(self.instance, 'pk', None) is None:
                        self.fields['nivel_aprovacao'].initial = Vaga.NivelAprovacao.PROVINCIAL
                    if perfil.provincia:
                        self.fields['provincia'].queryset = Provincia.objects.filter(id=perfil.provincia.id)
                        self.fields['provincia'].initial = perfil.provincia.id
                        self.fields['distrito'].queryset = Distrito.objects.filter(provincia=perfil.provincia).order_by('nome')
                    else:
                        self.fields['distrito'].queryset = Distrito.objects.none()

        # Load all districts for AJAX loading on client side or filter based on form data (aplica-se a perfis Centrais ou livres)
        if 'provincia' in self.data:
            try:
                provincia_id = int(self.data.get('provincia'))
                # Apenas atualiza se não tivermos restrito a queryset antes de forma mais restritiva
                if not (user and not user.is_superuser and perfil and perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL):
                     self.fields['distrito'].queryset = Distrito.objects.filter(provincia_id=provincia_id).order_by('nome')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty Distrito queryset
        elif self.instance.pk and self.instance.provincia:
            # Também para o Central ao editar
            if not (user and not user.is_superuser and perfil and perfil.nivel in [PerfilUtilizador.Nivel.DISTRITAL, PerfilUtilizador.Nivel.PROVINCIAL]):
                self.fields['distrito'].queryset = self.instance.distrito.provincia.distritos.order_by('nome')


class VagaFormEtapa2(forms.Form):
    '''Etapa 2: Seleção de documentos necessários'''
    
    doc_bi = forms.BooleanField(
        required=False,
        initial=True,
        label='📇 Bilhete de Identidade',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input doc-checkbox'})
    )
    doc_certificado = forms.BooleanField(
        required=False,
        initial=True,
        label='🎓 Certificado de Habilitações',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input doc-checkbox'})
    )
    doc_cv = forms.BooleanField(
        required=False,
        initial=True,
        label='📋 Curriculum Vitae',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input doc-checkbox'})
    )
    doc_foto = forms.BooleanField(
        required=False,
        initial=True,
        label='📸 Fotografia',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input doc-checkbox'})
    )


# Manter VagaForm para edição
class VagaForm(forms.ModelForm):
    '''Formulário para edição de vagas (todas as informações em uma página)'''
    
    # Checkboxes para documentos
    doc_bi = forms.BooleanField(
        required=False,
        initial=True,
        label='Bilhete de Identidade',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    doc_certificado = forms.BooleanField(
        required=False,
        initial=True,
        label='Certificado de Habilitações',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    doc_cv = forms.BooleanField(
        required=False,
        initial=True,
        label='Curriculum Vitae',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    doc_foto = forms.BooleanField(
        required=False,
        initial=True,
        label='Fotografia',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Vaga
        fields = ['titulo', 'descricao', 'data_inicio', 'data_fim', 'ativa', 'requer_formacao', 'nivel_aprovacao', 'provincia', 'distrito']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nivel_aprovacao': forms.Select(attrs={'class': 'form-select'}),
            'provincia': forms.Select(attrs={'class': 'form-select'}),
            'distrito': forms.Select(attrs={'class': 'form-select'}),
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['provincia'].required = False
        self.fields['distrito'].required = False
        
        # Filtro de permissões hierárquicas
        if user and not user.is_superuser:
            perfil = obter_perfil_usuario(user)
            if perfil:
                if perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
                    self.fields['nivel_aprovacao'].choices = [(Vaga.NivelAprovacao.DISTRITAL, 'STAE Distrital')]
                    if perfil.provincia:
                        self.fields['provincia'].queryset = Provincia.objects.filter(id=perfil.provincia.id)
                    if perfil.distrito:
                        self.fields['distrito'].queryset = Distrito.objects.filter(id=perfil.distrito.id)
                        
                elif perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
                    self.fields['nivel_aprovacao'].choices = [
                        (Vaga.NivelAprovacao.PROVINCIAL, 'STAE Provincial'),
                        (Vaga.NivelAprovacao.DISTRITAL, 'STAE Distrital')
                    ]
                    if perfil.provincia:
                        self.fields['provincia'].queryset = Provincia.objects.filter(id=perfil.provincia.id)
                        self.fields['distrito'].queryset = Distrito.objects.filter(provincia=perfil.provincia).order_by('nome')
                    else:
                        self.fields['distrito'].queryset = Distrito.objects.none()

        # Pré-preencher checkboxes baseado em documentos_necessarios
        if self.instance.pk and self.instance.documentos_necessarios:
            self.fields['doc_bi'].initial = 'bi' in self.instance.documentos_necessarios
            self.fields['doc_certificado'].initial = 'certificado' in self.instance.documentos_necessarios
            self.fields['doc_cv'].initial = 'cv' in self.instance.documentos_necessarios
            self.fields['doc_foto'].initial = 'foto' in self.instance.documentos_necessarios
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Construir lista de documentos necessários
        docs = []
        if self.cleaned_data.get('doc_bi'):
            docs.append('bi')
        if self.cleaned_data.get('doc_certificado'):
            docs.append('certificado')
        if self.cleaned_data.get('doc_cv'):
            docs.append('cv')
        if self.cleaned_data.get('doc_foto'):
            docs.append('foto')
        
        instance.documentos_necessarios = docs
        
        if commit:
            instance.save()
        return instance

class AbrirConcursoForm(forms.ModelForm):
    """Formulário para abrir um concurso e definir o número de vagas."""
    class Meta:
        model = Vaga
        fields = ['numero_vagas']
        widgets = {
            'numero_vagas': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'min': 1, 'required': True}),
        }

class CriarEntrevistadorVagaForm(forms.ModelForm):
    """Formulário simplificado para cadastrar um entrevistador diretamente a uma vaga."""
    class Meta:
        from .models import EntrevistadorVaga
        model = EntrevistadorVaga
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Entrevistador'}),
        }
