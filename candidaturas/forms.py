from django import forms
from django.utils import timezone
from .models import Candidato, Provincia, Distrito, PerfilUtilizador, Vaga

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
        else:
            pass

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
