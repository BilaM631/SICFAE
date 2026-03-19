from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'formacao'

urlpatterns = [
    # Turmas — Formadores
    path('turmas/formadores/', views.ListaTurmasFormadoresView.as_view(), name='lista_turmas_formadores'),
    path('turmas/formadores/nacionais/', views.ListaTurmasFormadoresNacionaisView.as_view(), name='lista_turmas_formadores_nacionais'),
    path('turmas/formadores/provinciais/', views.ListaTurmasFormadoresProvinciaisView.as_view(), name='lista_turmas_formadores_provinciais'),
    path('turmas/formadores/gerar/', views.GerarTurmasFormadoresView.as_view(), name='gerar_turmas_formadores'),

    # Turmas — Campo
    path('turmas/mmv/', views.ListaTurmasMMVView.as_view(), name='lista_turmas_mmv'),
    path('turmas/agentes-educacao/', views.ListaTurmasAgentesEducacaoView.as_view(), name='lista_turmas_agentes_educacao'),
    path('turmas/brigadistas/', views.ListaTurmasBrigadistasView.as_view(), name='lista_turmas_brigadistas'),
    path('turmas/', views.ListaTurmasView.as_view(), name='lista_turmas'),
    path('turmas/criar/', views.CriarTurmaView.as_view(), name='criar_turma'),
    path('turmas/<int:pk>/', views.DetalheTurmaView.as_view(), name='detalhe_turma'),
    path('turmas/<int:pk>/editar/', views.EditarTurmaView.as_view(), name='editar_turma'),
    path('turmas/<int:pk>/apagar/', views.ApagarTurmaView.as_view(), name='apagar_turma'),
    path('turmas/<int:pk>/notas/', views.LancarNotasTurmaView.as_view(), name='lancar_notas_turma'),
    path('turmas/<int:pk>/exportar/excel/', views.ExportarTurmaExcelView.as_view(), name='exportar_turma_excel'),
    path('turmas/<int:pk>/exportar/pdf/', views.ExportarTurmaPDFView.as_view(), name='exportar_turma_pdf'),
    path('turmas/gerar-auto/', views.GerarTurmasView.as_view(), name='gerar_turmas_auto'),
    path('api/formadores-disponiveis/', views.ObterFormadoresDisponiveisView.as_view(), name='api_formadores_disponiveis'),


    # Certificações
    path('turmas/<int:pk>/certificacoes/', views.ProcessarCertificacoesView.as_view(), name='processar_certificacoes'),
    path('certificacoes/', views.ListaCertificacoesView.as_view(), name='lista_certificacoes'),

    # Plano de Formação por Distrito
    path('plano/', views.PlanoFormacaoDistritoListView.as_view(), name='plano_lista'),
    path('plano/novo/', views.PlanoFormacaoDistritoCreateView.as_view(), name='plano_criar'),
    path('plano/distrito/<int:distrito_pk>/novo/', views.PlanoFormacaoDistritoCreateView.as_view(), name='plano_criar_distrito'),
    path('plano/<int:pk>/editar/', views.PlanoFormacaoDistritoUpdateView.as_view(), name='plano_editar'),
    path('plano/provincia/<int:provincia_id>/submeter/', views.SubmeterPlanosProvinciaView.as_view(), name='submeter_planos_provincia'),

    # Dashboard e Formadores
    path('dashboard/', views.DashboardGeralView.as_view(), name='dashboard_geral'),
    path('formadores/registar/', views.RegistarFormadorView.as_view(), name='registar_formador'),
    path('formadores/nacionais/', views.ListaFormadoresNacionaisCRUDView.as_view(), name='lista_formadores_nacionais_crud'),
    path('formadores/nacionais/cadastrar/', views.CadastrarFormadorNacionalView.as_view(), name='cadastrar_formador_nacional'),
    path('formadores/nacionais/<int:pk>/editar/', views.EditarFormadorNacionalView.as_view(), name='editar_formador_nacional'),
    path('formadores/nacionais/<int:pk>/apagar/', views.ApagarFormadorNacionalView.as_view(), name='apagar_formador_nacional'),

    # Locais
    path('locais/', views.ListaLocaisView.as_view(), name='lista_locais'),
    path('locais/criar/', views.CriarLocalView.as_view(), name='criar_local'),
    path('locais/<int:pk>/editar/', views.EditarLocalView.as_view(), name='editar_local'),

    # Gestão de Utilizadores
    path('utilizadores/', views.GerirUtilizadoresView.as_view(), name='gestao_utilizadores'),

    # Gestão de Brigadas
    path('brigadas/', views.BrigadaListView.as_view(), name='lista_brigadas'),
    path('brigadas/criar/', views.BrigadaCreateView.as_view(), name='criar_brigada'),
    path('brigadas/<int:pk>/editar/', views.BrigadaUpdateView.as_view(), name='editar_brigada'),
    path('brigadas/<int:pk>/apagar/', views.BrigadaDeleteView.as_view(), name='apagar_brigada'),
    path('api/brigadistas-disponiveis/', views.ObterBrigadistasDisponiveisView.as_view(), name='api_brigadistas_disponiveis'),

    # Configurações do Sistema
    path('configuracoes/', views.ConfiguracaoSistemaUpdateView.as_view(), name='configuracoes'),

    # Alteração de senha obrigatória (primeiro login / reset)
    path('alterar-senha/', views.AlterarSenhaObrigatoriaView.as_view(), name='alterar_senha_obrigatoria'),
    path('utilizadores/<int:pk>/resetar-senha/', views.ResetarSenhaUtilizadorView.as_view(), name='resetar_senha_utilizador'),

    # Redirecionamentos para compatibilidade
    path('formadores/', RedirectView.as_view(url='/formacao/dashboard/', permanent=False)),
]
