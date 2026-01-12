from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Candidato, PerfilUtilizador, Provincia, Distrito, Vaga
from .permissions import obter_candidatos_acessiveis, pode_gerir_candidato
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(Distrito)
class DistritoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'provincia')
    list_filter = ('provincia',)
    search_fields = ('nome', 'provincia__nome')

@admin.register(Vaga)
class VagaAdmin(SimpleHistoryAdmin):
    list_display = ('titulo', 'ativa', 'data_inicio', 'data_fim', 'data_criacao')
    list_filter = ('ativa', 'data_inicio', 'data_fim')
    search_fields = ('titulo', 'descricao')
    ordering = ('titulo',)

@admin.register(Candidato)
class CandidatoAdmin(SimpleHistoryAdmin):
    list_display = ('nome_completo', 'vaga', 'numero_bi', 'provincia', 'distrito', 'estado', 'data_criacao')
    list_filter = ('vaga', 'estado', 'provincia', 'distrito', 'data_criacao')
    search_fields = ('nome_completo', 'numero_bi', 'provincia__nome', 'distrito__nome')
    readonly_fields = ('data_criacao', 'data_atualizacao')
    actions = ['enviar_whatsapp_massivo']
    change_list_template = "admin/candidaturas/candidate/change_list.html" # Note: template path might need update later if I rename folder
    
    def get_queryset(self, request):
        """Filtra candidatos baseado no nível do utilizador."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return obter_candidatos_acessiveis(request.user) # Will need to rename permissions function

    def has_change_permission(self, request, obj=None):
        if obj:
            return pode_gerir_candidato(request.user, obj) # Will rename
        return True
    
    def has_delete_permission(self, request, obj=None):
        if obj:
            return pode_gerir_candidato(request.user, obj)
        return True

    @admin.action(description='Enviar WhatsApp Massivo (Automático)')
    def enviar_whatsapp_massivo(self, request, queryset):
        from .services import ServicoWhatsApp # Will rename
        from django.contrib import messages
        
        msg_template = "Olá {name}, a sua candidatura no SICFAAE foi analisada. Por favor verifique o seu email/status para mais detalhes."
        results = ServicoWhatsApp.enviar_mensagens_massa(queryset, msg_template) # Will rename
        
        self.message_user(
            request, 
            f"Processo concluído. Sucesso: {results['sucesso']}, Falhas: {results['falhas']}", 
            messages.SUCCESS
        )

    
    def changelist_view(self, request, extra_context=None):
        # ... logic for excel import needs update to new field names ...
        # I will simplify for now to focus on structure
        return super().changelist_view(request, extra_context=extra_context)


# PerfilUtilizador Admin
@admin.register(PerfilUtilizador)
class PerfilUtilizadorAdmin(SimpleHistoryAdmin):
    list_display = ('usuario', 'nivel', 'provincia', 'distrito', 'data_criacao')
    list_filter = ('nivel', 'provincia', 'distrito')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'provincia__nome', 'distrito__nome')
    readonly_fields = ('data_criacao', 'data_atualizacao')
    
    fieldsets = (
        ('Utilizador', {
            'fields': ('usuario',)
        }),
        ('Nível Administrativo', {
            'fields': ('nivel',)
        }),
        ('Área Geográfica', {
            'fields': ('provincia', 'distrito'),
            'description': 'Defina a província para utilizadores Provincial e Distrital. Defina o distrito apenas para Distrital.'
        }),
        ('Informação do Sistema', {
            'fields': ('data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )


# Inline PerfilUtilizador in User Admin
class PerfilUtilizadorInline(admin.StackedInline):
    model = PerfilUtilizador
    can_delete = False
    verbose_name_plural = 'Perfil Administrativo'
    fk_name = 'usuario'
    fields = ('nivel', 'provincia', 'distrito')


# Extend User Admin
class CustomUserAdmin(BaseUserAdmin):
    inlines = (PerfilUtilizadorInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
