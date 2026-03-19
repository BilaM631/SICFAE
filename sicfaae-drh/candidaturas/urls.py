from django.urls import path
from . import views
from . import views_vagas
from . import views_entrevistador

app_name = 'candidaturas'

urlpatterns = [
    path('', views.PaginaInicialView.as_view(), name='inicio'),
    path('gestao/', views.PainelControloView.as_view(), name='painel_controlo'),
    path('gestao/lista/', views.ListaVerificacaoView.as_view(), name='lista_verificacao'),
    path('gestao/relatorios/', views.RelatoriosView.as_view(), name='relatorios'),
    path('gestao/exportar-excel/<str:tipo_relatorio>/', views.ExportarExcelView.as_view(), name='exportar_excel'),
    path('gestao/relatorios/pdf/<str:tipo_relatorio>/', views.relatorio_pdf, name='relatorio_pdf'),
    path('gestao/utilizadores/', views.GerirUtilizadoresView.as_view(), name='gestao_utilizadores'),
    
    # Gestão de Vagas
    path('gestao/vagas/', views_vagas.ListaVagasView.as_view(), name='lista_vagas'),
    path('gestao/vagas/nova/etapa1/', views_vagas.CriarVagaEtapa1View.as_view(), name='criar_vaga_etapa1'),
    path('gestao/vagas/nova/etapa2/', views_vagas.CriarVagaEtapa2View.as_view(), name='criar_vaga_etapa2'),
    path('gestao/vagas/<int:pk>/', views_vagas.DetalheVagaView.as_view(), name='detalhe_vaga'),
    path('gestao/vagas/<int:pk>/editar/', views_vagas.EditarVagaView.as_view(), name='editar_vaga'),
    path('gestao/vagas/<int:pk>/apagar/', views_vagas.ApagarVagaView.as_view(), name='apagar_vaga'),
    path('gestao/vagas/<int:pk>/alternar-status/', views_vagas.alternar_status_vaga, name='alternar_status_vaga'),
    path('gestao/vagas/<int:pk>/abrir-concurso/', views_vagas.AbrirConcursoView.as_view(), name='abrir_concurso'),
    path('gestao/vagas/<int:pk>/novo-entrevistador/', views_vagas.AdicionarEntrevistadorVagaView.as_view(), name='adicionar_entrevistador_vaga'),
    path('gestao/vagas/<int:pk>/enviar-aprovados-formacao/', views_vagas.enviar_aprovados_vaga_formacao, name='enviar_aprovados_vaga_formacao'),
    
    # Registo de Candidaturas (Duas Etapas)
    path('registar/', views.RegistarCandidaturaEtapa1View.as_view(), name='registar_candidatura'),
    path('registar/etapa1/', views.RegistarCandidaturaEtapa1View.as_view(), name='registar_etapa1'),
    path('registar/etapa2/', views.RegistarCandidaturaEtapa2View.as_view(), name='registar_etapa2'),
    path('registar/voltar/', views.voltar_etapa1, name='voltar_etapa1'),
    
    path('sucesso/', views.sucesso_candidatura, name='sucesso_candidatura'),
    path('candidato/<int:pk>/', views.DetalheCandidatoView.as_view(), name='detalhe_candidato'),
    path('gerar_pdf/<int:pk>/', views.gerar_pdf, name='gerar_pdf'),
    path('gerar_ficha_entrevista/<int:pk>/', views.gerar_ficha_entrevista, name='gerar_ficha_entrevista'),
    path('importar_excel/', views.ImportarExcelView.as_view(), name='importar_excel'),
    path('ajax/carregar-distritos/', views.carregar_distritos, name='ajax_carregar_distritos'),
    # Gestão de Entrevistas (Novo Fluxo)
    path('entrevista/candidato/<int:pk>/agendar/', views.AgendarEntrevistaView.as_view(), name='agendar_entrevista'),
    path('entrevistas/minhas/', views.MinhasEntrevistasView.as_view(), name='minhas_entrevistas'),
    path('entrevista/<int:pk>/realizar/', views.RealizarEntrevistaView.as_view(), name='realizar_entrevista'),

    path('entrevista/<int:pk>/<str:resultado>/', views.registar_entrevista, name='registar_entrevista'),
    path('formacao/<int:pk>/', views.enviar_para_formacao, name='enviar_para_formacao'),
    path('formacao/enviar-massa/lista/', views.enviar_aprovados_lista_formacao, name='enviar_aprovados_lista_formacao'),
    path('candidatura-manual/', views.RegistarCandidaturaManualView.as_view(), name='registar_candidatura_manual'), # [CHANGED]
    path('consulta/', views.consulta_publica, name='consulta_publica'),


    path('enviar-sms/<int:pk>/', views.enviar_sms, name='enviar_sms'),
    
    # Despachante
    path('dispatch/', views.despachante_auth, name='despachante_auth'),
    
    # Portal Isolado do Entrevistador de Vaga
    path('entrevistador/acesso/', views_entrevistador.LoginEntrevistadorVagaView.as_view(), name='login_entrevistador_vaga'),
    path('entrevistador/painel/', views_entrevistador.PainelEntrevistadorVagaView.as_view(), name='painel_entrevistador_vaga'),
    path('entrevistador/candidato/<int:pk>/avaliar/', views_entrevistador.AvaliarCandidatoVagaView.as_view(), name='avaliar_candidato_vaga'),
    
    # Painel do Candidato
    path('candidato/entrar/', views.LoginCandidatoView.as_view(), name='login_candidato'),
    path('candidato/painel/', views.PainelCandidatoView.as_view(), name='painel_candidato'),
    path('candidato/sair/', views.logout_candidato, name='logout_candidato'),
]
