from django.urls import path
from . import views

app_name = 'candidaturas'

urlpatterns = [
    path('', views.PaginaInicialView.as_view(), name='inicio'),
    path('gestao/', views.PainelControloView.as_view(), name='painel_controlo'),
    path('gestao/lista/', views.ListaVerificacaoView.as_view(), name='lista_verificacao'),
    path('gestao/relatorios/', views.RelatoriosView.as_view(), name='relatorios'),
    path('gestao/exportar-excel/<str:tipo_relatorio>/', views.ExportarExcelView.as_view(), name='exportar_excel'),
    path('gestao/relatorios/pdf/<str:tipo_relatorio>/', views.relatorio_pdf, name='relatorio_pdf'),
    path('gestao/utilizadores/', views.GerirUtilizadoresView.as_view(), name='gestao_utilizadores'),
    path('registar/', views.RegistarCandidaturaView.as_view(), name='registar_candidatura'),
    path('sucesso/', views.sucesso_candidatura, name='sucesso_candidatura'),
    path('candidato/<int:pk>/', views.DetalheCandidatoView.as_view(), name='detalhe_candidato'),
    path('verificar-candidato/<int:pk>/<str:acao>/', views.verificar_candidato, name='verificar_candidato'),
    path('gerar_pdf/<int:pk>/', views.gerar_pdf, name='gerar_pdf'),
    path('importar_excel/', views.ImportarExcelView.as_view(), name='importar_excel'),
    path('ajax/carregar-distritos/', views.carregar_distritos, name='ajax_carregar_distritos'),
    path('entrevista/<int:pk>/<str:resultado>/', views.registar_entrevista, name='registar_entrevista'),
    path('candidato/<int:pk>/validar-docs/', views.ValidarDocumentosView.as_view(), name='validar_documentos'),
    path('candidatura-manual/', views.RegistarCandidaturaManualView.as_view(), name='registar_candidatura_manual'), # [CHANGED]

    path('enviar-sms/<int:pk>/', views.enviar_sms, name='enviar_sms'),
    
    # Despachante
    path('dispatch/', views.despachante_auth, name='despachante_auth'),
    
    # Painel do Candidato
    path('candidato/entrar/', views.LoginCandidatoView.as_view(), name='login_candidato'),
    path('candidato/painel/', views.PainelCandidatoView.as_view(), name='painel_candidato'),
    path('candidato/sair/', views.logout_candidato, name='logout_candidato'),
]
