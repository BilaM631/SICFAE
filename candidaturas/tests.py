from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch
from .models import Candidato, Provincia, Distrito, PerfilUtilizador
from .managers import GestorEstatisticas

class TesteFluxoCandidatura(TestCase):
    def setUp(self):
        # Criar Província e Distrito
        self.provincia = Provincia.objects.create(nome="Maputo Província")
        self.distrito = Distrito.objects.create(provincia=self.provincia, nome="Matola")

        # Criar Utilizador Júri
        self.user = User.objects.create_user(username='juri', password='password')
        
        # O signal post_save já cria o perfil, então apenas atualizamos
        self.perfil = self.user.perfil
        self.perfil.nivel = PerfilUtilizador.Nivel.DISTRITAL
        self.perfil.provincia = self.provincia
        self.perfil.distrito = self.distrito
        self.perfil.save()

        self.client = Client()
        self.client.force_login(self.user)
        
        # Criar Candidato
        self.candidato = Candidato.objects.create(
            nome_completo="João Teste",
            numero_bi="1100110011B",
            numero_telefone="841234567",
            estado=Candidato.Estado.PENDENTE,
            provincia=self.provincia,
            distrito=self.distrito,
            funcao=Candidato.Funcao.AGENTE_CIVICO
        )

    @patch('candidaturas.views.render_to_pdf')
    def test_fluxo_completo(self, mock_render):
        # Mock PDF generation
        mock_render.return_value = b'%PDF-1.4 mock'

        # 1. Aprovar Documentos
        url = reverse('candidaturas:verificar_candidato', args=[self.candidato.pk, 'aprovar'])
        response = self.client.get(url, follow=True)
        self.candidato.refresh_from_db()
        self.assertEqual(self.candidato.estado, Candidato.Estado.DOCS_APROVADOS)

        # 2. Gerar PDF
        url_pdf = reverse('candidaturas:gerar_pdf', args=[self.candidato.pk])
        response_pdf = self.client.get(url_pdf)
        self.assertEqual(response_pdf.status_code, 200)

        # 3. Enviar SMS (Muda para Entrevista Agendada)
        url_sms = reverse('candidaturas:enviar_sms', args=[self.candidato.pk])
        self.client.get(url_sms, follow=True)
        self.candidato.refresh_from_db()
        self.assertEqual(self.candidato.estado, Candidato.Estado.ENTREVISTA_AGENDADA)

        # 4. Aprovar na Entrevista
        url_entrevista = reverse('candidaturas:registar_entrevista', args=[self.candidato.pk, 'passou'])
        self.client.get(url_entrevista, follow=True)
        self.candidato.refresh_from_db()
        self.assertEqual(self.candidato.estado, Candidato.Estado.ENTREVISTA_APROVADA)

class TesteGestorEstatisticas(TestCase):
    def setUp(self):
        self.provincia = Provincia.objects.create(nome="Maputo")
        self.distrito = Distrito.objects.create(provincia=self.provincia, nome="KaMpfumo")
        
        # Criar 3 candidatos
        Candidato.objects.create(
            nome_completo="C1", numero_bi="1", numero_telefone="1",
            provincia=self.provincia, distrito=self.distrito,
            funcao=Candidato.Funcao.BRIGADISTA, estado=Candidato.Estado.PENDENTE
        )
        Candidato.objects.create(
            nome_completo="C2", numero_bi="2", numero_telefone="2",
            provincia=self.provincia, distrito=self.distrito,
            funcao=Candidato.Funcao.BRIGADISTA, estado=Candidato.Estado.DOCS_APROVADOS
        )
        Candidato.objects.create(
            nome_completo="C3", numero_bi="3", numero_telefone="3",
            provincia=self.provincia, distrito=self.distrito,
            funcao=Candidato.Funcao.FORMADOR, estado=Candidato.Estado.PENDENTE
        )

        self.user = User.objects.create_user('admin', 'password') # Sem perfil = Superuser logic fallback or base

    def test_estatisticas_gerais(self):
        gestor = GestorEstatisticas(self.user)
        stats = gestor.obter_estatisticas_gerais()
        
        self.assertEqual(stats['total_candidatos'], 3)
        self.assertEqual(stats['candidatos_pendentes'], 2)
        
        # Verificar contagem por função
        brigadistas = next(item for item in stats['stats_funcao'] if item['label'] == 'Brigadista')
        self.assertEqual(brigadistas['count'], 2)
        
        formadores = next(item for item in stats['stats_funcao'] if item['label'] == 'Formador')
        self.assertEqual(formadores['count'], 1)

    def test_estatisticas_estado(self):
        gestor = GestorEstatisticas(self.user)
        stats = gestor.obter_estatisticas_gerais()
        
        pendentes = next(item for item in stats['stats_estado'] if item['label'] == 'Pendente')
        self.assertEqual(pendentes['count'], 2)
