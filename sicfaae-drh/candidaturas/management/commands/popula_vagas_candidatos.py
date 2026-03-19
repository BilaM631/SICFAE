import random
import string
import urllib.request
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from candidaturas.models import Vaga, Candidato, Provincia, Distrito

class Command(BaseCommand):
    help = 'Popula a base de dados do DRH com vagas e candidatos para testes'

    def gerar_bi(self):
        numeros = ''.join(random.choices(string.digits, k=12))
        letra = random.choice(string.ascii_uppercase)
        return f"{numeros}{letra}"

    def gerar_telefone(self):
        prefixo = random.choice(['84', '85', '82', '83', '86', '87'])
        sufixo = ''.join(random.choices(string.digits, k=7))
        return f"{prefixo}{sufixo}"

    def get_dummy_file_path(self, folder, filename, content):
        import os
        from django.conf import settings
        from django.core.files.storage import default_storage
        
        rel_path = f'candidatos/{folder}/{filename}'
        if not default_storage.exists(rel_path):
            default_storage.save(rel_path, ContentFile(content))
        return rel_path

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando população de vagas e candidatos...'))
        
        # Limpar Dados Anteriores das Vagas de Teste
        Candidato.objects.all().delete()
        Vaga.objects.filter(titulo__in=['Formador Nacional', 'Formador Provincial - Maputo', 'Brigadistas Nacionais', 'Agentes de Educação Cívica']).delete()

        # Download Dummy PDF Content
        self.stdout.write('Preparando ficheiros de modelo (Isto ocorre apenas uma vez)...')
        try:
            req_pdf = urllib.request.Request('https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf', headers={'User-Agent': 'Mozilla/5.0'})
            dummy_pdf_content = urllib.request.urlopen(req_pdf, timeout=10).read()
        except Exception:
            dummy_pdf_content = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF'
            
        dummy_cv_path = self.get_dummy_file_path('cv', 'dummy_cv.pdf', dummy_pdf_content)
        dummy_bi_path = self.get_dummy_file_path('bi', 'dummy_bi.pdf', dummy_pdf_content)
        dummy_cert_path = self.get_dummy_file_path('certificados', 'dummy_cert.pdf', dummy_pdf_content)
        
        # Download some photos to reuse
        self.stdout.write('A preparar fotos de perfil...')
        dummy_fotos_paths = []
        for i in range(5):
            try:
                img_req = urllib.request.Request(f'https://randomuser.me/api/portraits/lego/{i}.jpg', headers={'User-Agent': 'Mozilla/5.0'})
                foto_content = urllib.request.urlopen(img_req, timeout=5).read()
                path = self.get_dummy_file_path('fotos', f'dummy_foto_{i}.jpg', foto_content)
                dummy_fotos_paths.append(path)
            except Exception:
                # Se falhar criar um conteúdo de imagem vazio simples
                pass
        
        if not dummy_fotos_paths:
            dummy_fotos_paths = [None]

        # Obter províncias e distritos (assumindo que já existem da base de dados)
        provincias = list(Provincia.objects.all())
        distritos = list(Distrito.objects.all())
        
        if not provincias or not distritos:
            self.stdout.write(self.style.ERROR('Erro: Não existem Províncias ou Distritos na Base de Dados. Popula o DEFC/core primeiro.'))
            return

        maputo_prov = Provincia.objects.filter(nome__icontains='Maputo').first() or provincias[0]
        
        now = timezone.now().date()
        futuro = now + timedelta(days=30)
        passado = now - timedelta(days=10)

        # 1. Criar Vagas
        vagas_dados = [
            {
                'titulo': 'Formador Nacional',
                'descricao': 'Vaga para selecionar Formadores Nacionais para as Eleições.',
                'nivel_aprovacao': Vaga.NivelAprovacao.CENTRAL,
                'requer_formacao': True,
                'ativa': True,
                'data_inicio': passado,
                'data_fim': futuro,
                'provincia': None,
                'distrito': None
            },
            {
                'titulo': 'Formador Provincial - Maputo',
                'descricao': 'Vaga para Formadores Provinciais focados na Província de Maputo.',
                'nivel_aprovacao': Vaga.NivelAprovacao.PROVINCIAL,
                'requer_formacao': True,
                'ativa': True,
                'data_inicio': passado,
                'data_fim': futuro,
                'provincia': maputo_prov,
                'distrito': None
            },
            {
                'titulo': 'Brigadistas Nacionais',
                'descricao': 'Recrutamento Nacional de Brigadistas de Recenseamento Eleitoral.',
                'nivel_aprovacao': Vaga.NivelAprovacao.DISTRITAL,
                'requer_formacao': True,
                'ativa': True,
                'data_inicio': now,
                'data_fim': futuro,
                'provincia': None,
                'distrito': None
            },
            {
                'titulo': 'Agentes de Educação Cívica',
                'descricao': 'Campanha nacional de mobilização e educação cívica.',
                'nivel_aprovacao': Vaga.NivelAprovacao.DISTRITAL,
                'requer_formacao': False,
                'ativa': True,
                'data_inicio': now,
                'data_fim': futuro,
                'provincia': None,
                'distrito': None
            }
        ]

        vagas_criadas = []
        for v_data in vagas_dados:
            vaga, created = Vaga.objects.get_or_create(
                titulo=v_data['titulo'],
                defaults=v_data
            )
            vagas_criadas.append(vaga)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Vaga "{vaga.titulo}" criada com sucesso!'))
            else:
                self.stdout.write(f'Vaga "{vaga.titulo}" já existia.')

        # 2. Criar Candidatos
        estados_possiveis = [
            Candidato.Estado.PENDENTE,
            Candidato.Estado.DOCS_APROVADOS,
            Candidato.Estado.DOCS_REJEITADOS,
            Candidato.Estado.ENTREVISTA_AGENDADA,
            Candidato.Estado.ENTREVISTA_APROVADA,
            Candidato.Estado.ENTREVISTA_REPROVADA,
            Candidato.Estado.ENVIADO_DEFC,
        ]

        nomes = ['João', 'Maria', 'Pedro', 'Ana', 'Carlos', 'Fatima', 'Rui', 'Marta', 'Luis', 'Sofia', 'José', 'Isabel', 'Antonio', 'Teresa', 'Manuel', 'Fernando', 'Carla', 'Helena', 'Ricardo', 'Paulo']
        apelidos = ['Silva', 'Santos', 'Ferreira', 'Pereira', 'Oliveira', 'Costa', 'Rodrigues', 'Martins', 'Jesus', 'Sousa', 'Fernandes', 'Gomes', 'Lopes', 'Marques', 'Alves', 'Monteiro']

        num_candidatos_gerados = 0
        
        # Para garantir BIs únicos, vamos usar um set temporário
        bis_usados = set()
        
        self.stdout.write(self.style.WARNING('A gerar mais de 12.000 candidatos (O processo demora alguns segundos)...'))

        for vaga in vagas_criadas:
            # Gerar 3050 candidatos por vaga, totalizando ~12200 candidatos
            candidatos_batch = []
            
            for i in range(3050):
                nome_completo = f"{random.choice(nomes)} {random.choice(apelidos)} {random.choice(apelidos)}"
                genero = 'M' if nome_completo.split()[0] in ['João', 'Pedro', 'Carlos', 'Rui', 'Luis', 'José', 'Antonio', 'Manuel', 'Fernando', 'Ricardo', 'Paulo'] else 'F'
                
                # Definir geografia do candidato baseado na vaga ou aleatório
                candidato_prov = vaga.provincia if vaga.provincia else random.choice(provincias)
                
                if vaga.distrito:
                    candidato_dist = vaga.distrito
                else:
                    distritos_prov = Distrito.objects.filter(provincia=candidato_prov)
                    candidato_dist = random.choice(distritos_prov) if distritos_prov.exists() else random.choice(distritos)

                novo_bi = self.gerar_bi()
                while novo_bi in bis_usados:
                    novo_bi = self.gerar_bi()
                bis_usados.add(novo_bi)

                candidato = Candidato(
                    nome_completo=nome_completo,
                    genero=genero,
                    vaga=vaga,
                    numero_bi=novo_bi,
                    numero_telefone=self.gerar_telefone(),
                    provincia=candidato_prov,
                    distrito=candidato_dist,
                    endereco=f"Bairro {random.choice(['Central', 'Triunfo', 'Agosto', 'Matola', 'Zimpeto'])}, Rua {random.randint(1, 100)}",
                    estado=random.choice(estados_possiveis),
                    foto=random.choice(dummy_fotos_paths),
                    arquivo_cv=dummy_cv_path,
                    arquivo_bi=dummy_bi_path,
                    arquivo_certificado=dummy_cert_path,
                    codigo_candidato=f"TESTE-{novo_bi}"
                )
                
                candidatos_batch.append(candidato)
                
                # Inserir em lotes de 1000 para não estourar a memória
                if len(candidatos_batch) >= 1000:
                    Candidato.objects.bulk_create(candidatos_batch, ignore_conflicts=True)
                    num_candidatos_gerados += len(candidatos_batch)
                    candidatos_batch = []
                    self.stdout.write(f'Inseridos {num_candidatos_gerados} candidatos até o momento...')
            
            # Inserir remanescentes
            if candidatos_batch:
                Candidato.objects.bulk_create(candidatos_batch, ignore_conflicts=True)
                num_candidatos_gerados += len(candidatos_batch)

        self.stdout.write(self.style.SUCCESS(f'Base de Dados do DRH populada com {len(vagas_criadas)} vagas e {num_candidatos_gerados} candidatos com sucesso!'))
