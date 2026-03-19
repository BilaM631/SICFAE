from django.contrib import admin
from .models import Provincia, Distrito, CandidatoFormacao, ConfiguracaoSistema

@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):
    list_display = ('periodo_ativo', 'data_atualizacao')
    
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'latitude', 'longitude')
    search_fields = ('nome',)
    ordering = ('nome',)


@admin.register(Distrito)
class DistritoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'provincia')
    list_filter = ('provincia',)
    search_fields = ('nome', 'provincia__nome')
    ordering = ('provincia__nome', 'nome')


@admin.register(CandidatoFormacao)
class CandidatoFormacaoAdmin(admin.ModelAdmin):
    list_display = ('codigo_candidato', 'nome_completo', 'tipo_agente', 'provincia', 'distrito', 'ativo', 'data_recepcao')
    list_filter = ('tipo_agente', 'genero', 'provincia', 'ativo')
    search_fields = ('nome_completo', 'codigo_candidato', 'numero_bi')
    readonly_fields = ('id_drh', 'codigo_candidato', 'data_recepcao')
    ordering = ('-data_recepcao',)
    
    fieldsets = (
        ('Identificação DRH', {
            'fields': ('id_drh', 'codigo_candidato', 'data_recepcao')
        }),
        ('Dados Pessoais', {
            'fields': ('nome_completo', 'genero', 'data_nascimento', 'numero_bi', 'numero_telefone', 'foto')
        }),
        ('Localização', {
            'fields': ('provincia', 'distrito', 'endereco')
        }),
        ('Formação', {
            'fields': ('tipo_agente', 'ativo', 'observacoes')
        }),
    )
