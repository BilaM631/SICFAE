from django.core.management.base import BaseCommand
from core.models import Provincia, Distrito, CandidatoFormacao
from formacao.models import Turma, Local, TipoFormacao
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Popula a base de dados com dados de teste para Províncias, Distritos, Candidatos, Locais e Turmas'

    def handle(self, *args, **kwargs):
        self.stdout.write("A iniciar a população da base de dados...")

        # 1. Províncias
        provincias_nomes = ['Maputo Cidade', 'Maputo Província', 'Gaza', 'Inhambane', 'Sofala', 'Manica', 'Tete', 'Zambézia', 'Nampula', 'Cabo Delgado', 'Niassa']
        provincias = []
        for nome in provincias_nomes:
            prov, created = Provincia.objects.get_or_create(nome=nome)
            provincias.append(prov)
        self.stdout.write(f"{len(provincias)} Províncias criadas ou já existentes.")

        # 2. Distritos
        distritos_nomes = {
            'Maputo Cidade': ['KaMpfumo', 'KaMaxakeni', 'KaMavota', 'KaMubukwana'],
            'Maputo Província': ['Matola', 'Boane', 'Marracuene'],
            'Gaza': ['Xai-Xai', 'Chibuto', 'Chókwè'],
            'Inhambane': ['Inhambane Cidade', 'Maxixe', 'Massinga'],
            'Sofala': ['Beira', 'Dondo', 'Nhamatanda'],
            'Zambézia': ['Quelimane', 'Mocuba', 'Gurúè'],
            'Nampula': ['Nampula Cidade', 'Nacala', 'Angoche'],
        }
        distritos = []
        for prov_nome, dists in distritos_nomes.items():
            prov = Provincia.objects.get(nome=prov_nome)
            for d_nome in dists:
                dist, created = Distrito.objects.get_or_create(provincia=prov, nome=d_nome)
                distritos.append(dist)
        
        # Add basic distritos for other provinces if missing so they have at least one
        for prov in provincias:
            if not Distrito.objects.filter(provincia=prov).exists():
                dist, updated = Distrito.objects.get_or_create(provincia=prov, nome=f"D. {prov.nome} Sede")
                distritos.append(dist)
        
        distritos = list(Distrito.objects.all())
        self.stdout.write(f"{len(distritos)} Distritos na base de dados.")

        # 3. Locais
        locais = []
        for dist in distritos:
            for i in range(1, 3):
                local, created = Local.objects.get_or_create(
                    nome=f"Escola Secundária {dist.nome} - Sala {i}",
                    distrito=dist,
                    defaults={'capacidade': 30 + random.randint(0, 20), 'descricao': f'Sala número {i} do centro'}
                )
                locais.append(local)
        self.stdout.write(f"Vários locais criados. Total: {Local.objects.count()}")

        # 4. Candidatos (Formadores e Alunos)
        tipos_agentes = CandidatoFormacao.TipoAgente.choices
        primeiros_nomes = ['João', 'Maria', 'Pedro', 'Ana', 'Carlos', 'Margarida', 'António', 'Helena', 'Luís', 'Sofia', 'José', 'Catarina']
        apelidos = ['Silva', 'Santos', 'Ferreira', 'Pereira', 'Oliveira', 'Costa', 'Rodrigues', 'Martins', 'Jesus', 'Sousa', 'Fernandes']
        
        self.stdout.write("A gerar 100 candidatos aleatórios...")
        for i in range(1, 101):
            codigo = f"CAND{i:05d}"
            if CandidatoFormacao.objects.filter(codigo_candidato=codigo).exists():
                continue
            
            nome = f"{random.choice(primeiros_nomes)} {random.choice(apelidos)}"
            gen = CandidatoFormacao.Genero.MASCULINO if random.random() > 0.5 else CandidatoFormacao.Genero.FEMININO
            prov = random.choice(provincias)
            dist = random.choice(list(Distrito.objects.filter(provincia=prov)))
            tipo = random.choice([CandidatoFormacao.TipoAgente.FORMADOR, CandidatoFormacao.TipoAgente.BRIGADISTA, CandidatoFormacao.TipoAgente.MMV, CandidatoFormacao.TipoAgente.AGENTE_CIVICO])
            
            CandidatoFormacao.objects.create(
                id_drh=10000 + i,
                codigo_candidato=codigo,
                nome_completo=nome,
                genero=gen,
                data_nascimento=date.today() - timedelta(days=365*random.randint(20, 50)),
                numero_bi=f"12345{i}6M",
                numero_telefone=f"84000{i:04d}",
                provincia=prov,
                distrito=dist,
                tipo_agente=tipo
            )
        self.stdout.write(f"Candidatos inseridos. Total: {CandidatoFormacao.objects.count()}")

        # 5. Turmas
        self.stdout.write("A criar turmas...")
        
        formadores = list(CandidatoFormacao.objects.filter(tipo_agente=CandidatoFormacao.TipoAgente.FORMADOR))
        outros_candidatos = list(CandidatoFormacao.objects.exclude(tipo_agente=CandidatoFormacao.TipoAgente.FORMADOR))

        for dist in distritos[:10]: # Apenas para alguns distritos para evitar sobrecarga
            locais_dist = Local.objects.filter(distrito=dist)
            if not locais_dist.exists():
                continue
                
            for tipo_formacao, nome_tipo in TipoFormacao.choices:
                if tipo_formacao == TipoFormacao.FORMADORES_NACIONAIS:
                    continue # Requer provincia em vez de distrito
                    
                numero = random.randint(1, 10)
                
                # Para evitar turmas duplicadas (unique_together = ('distrito', 'numero', 'tipo_formacao'))
                if Turma.objects.filter(distrito=dist, numero=numero, tipo_formacao=tipo_formacao).exists():
                    continue

                local = random.choice(locais_dist)
                
                turma = Turma.objects.create(
                    nome=f"Turma {numero} - {nome_tipo[:15]}",
                    distrito=dist,
                    local=local,
                    tipo_formacao=tipo_formacao,
                    numero=numero,
                    data_inicio=date.today() + timedelta(days=random.randint(1, 30)),
                    data_fim=date.today() + timedelta(days=random.randint(31, 60)),
                    carga_horaria_prevista=40,
                )
                
                # Adicionar 2 formadores
                if len(formadores) >= 2:
                    figs = random.sample(formadores, 2)
                    turma.formadores.add(*figs)
                
                # Adicionar 5 a 15 alunos
                qtd_alunos = random.randint(5, 15)
                if len(outros_candidatos) >= qtd_alunos:
                    alunos = random.sample(outros_candidatos, qtd_alunos)
                    turma.alunos.add(*alunos)
                    
        self.stdout.write(self.style.SUCCESS(f"População da BD concluída com sucesso! Total Turmas: {Turma.objects.count()}"))
