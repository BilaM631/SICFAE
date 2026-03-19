"""
Management command to populate database with realistic candidate data
Usage: python manage.py popular_base_dados --quantidade 1000
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from candidaturas.models import Candidato, Provincia, Distrito, Vaga
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Popula a base de dados com candidatos realistas de Moçambique'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quantidade',
            type=int,
            default=500,
            help='Quantidade de candidatos a criar (padrão: 500)'
        )
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Limpar candidatos existentes antes de popular'
        )

    def handle(self, *args, **options):
        quantidade = options['quantidade']
        limpar = options['limpar']
        
        self.stdout.write(self.style.SUCCESS('\n🚀 Iniciando população da base de dados...'))
        
        # Verificar se existem províncias e distritos
        if not Provincia.objects.exists() or not Distrito.objects.exists():
            self.stdout.write(self.style.ERROR('❌ Erro: Não existem províncias ou distritos na base de dados!'))
            self.stdout.write('   Execute primeiro: python manage.py loaddata provincias_distritos')
            return
        
        # Verificar se existem vagas
        if not Vaga.objects.exists():
            self.stdout.write(self.style.WARNING('⚠️  Não existem vagas. Criando vaga padrão...'))
            hoje = date.today()
            vaga = Vaga.objects.create(
                titulo='Agente Eleitoral',
                descricao='Recrutamento de Agentes Eleitorais para as eleições',
                data_inicio=hoje,
                data_fim=hoje + timedelta(days=90),
                ativa=True
            )
            self.stdout.write(self.style.SUCCESS(f'   ✅ Vaga criada: {vaga.titulo}'))
        
        # Limpar se solicitado
        if limpar:
            total_existentes = Candidato.objects.count()
            if total_existentes > 0:
                confirmar = input(f'⚠️  Isto irá apagar {total_existentes} candidatos existentes. Confirmar? (s/N): ')
                if confirmar.lower() == 's':
                    Candidato.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS(f'✅ {total_existentes} candidatos removidos.'))
                else:
                    self.stdout.write(self.style.ERROR('❌ Operação cancelada.'))
                    return
        
        self.stdout.write(f'\n📊 Criando {quantidade} candidatos...\n')
        
        # Nomes moçambicanos realistas
        primeiros_nomes_m = [
            'João', 'António', 'Manuel', 'José', 'Carlos', 'Francisco', 'Pedro', 'Armando',
            'Alberto', 'Fernando', 'Joaquim', 'Alfredo', 'Domingos', 'Sebastião', 'Tomás',
            'Alexandre', 'Augusto', 'Eduardo', 'Felisberto', 'Gabriel', 'Hélder', 'Isac',
            'Jaime', 'Lucas', 'Mário', 'Nelson', 'Orlando', 'Paulo', 'Raul', 'Samuel'
        ]
        
        primeiros_nomes_f = [
            'Maria', 'Ana', 'Isabel', 'Rosa', 'Teresa', 'Luísa', 'Beatriz', 'Carla',
            'Diana', 'Elisa', 'Fernanda', 'Graça', 'Helena', 'Inês', 'Joana', 'Laura',
            'Mariana', 'Natália', 'Olívia', 'Paula', 'Raquel', 'Sara', 'Sónia', 'Vera',
            'Alice', 'Célia', 'Fátima', 'Júlia', 'Mónica', 'Patrícia'
        ]
        
        apelidos = [
            'Silva', 'Santos', 'Machado', 'Pereira', 'Fernandes', 'Rodrigues', 'Alves',
            'Gomes', 'Martins', 'Costa', 'Ribeiro', 'Carvalho', 'Ferreira', 'Sousa',
            'Lopes', 'Marques', 'Pinto', 'Castro', 'Teixeira', 'Correia', 'Mendes',
            'Nunes', 'Gonçalves', 'Cardoso', 'Ramos', 'Dias', 'Monteiro', 'Barbosa',
            'Moreira', 'Araújo', 'Oliveira', 'Soares', 'Maia', 'Fonseca', 'Coelho',
            'Simões', 'Pires', 'Antunes', 'Baptista', 'Reis', 'Tavares', 'Freitas'
        ]
        
        # Obter dados
        provincias = list(Provincia.objects.all())
        vagas = list(Vaga.objects.filter(ativa=True))
        
        if not vagas:
            vagas = list(Vaga.objects.all())
        
        criados = 0
        erros = 0
        hoje = date.today()
        
        # Distribuição de gênero (55% mulheres, 45% homens - realista para Moçambique)
        generos = ['F'] * 55 + ['M'] * 45
        
        for i in range(quantidade):
            try:
                # Gênero
                genero = random.choice(generos)
                
                # Nome
                if genero == 'M':
                    primeiro_nome = random.choice(primeiros_nomes_m)
                else:
                    primeiro_nome = random.choice(primeiros_nomes_f)
                
                # Adicionar segundo nome às vezes
                if random.random() > 0.3:
                    if genero == 'M':
                        segundo_nome = random.choice(primeiros_nomes_m)
                    else:
                        segundo_nome = random.choice(primeiros_nomes_f)
                    nome_completo = f"{primeiro_nome} {segundo_nome} {random.choice(apelidos)}"
                else:
                    nome_completo = f"{primeiro_nome} {random.choice(apelidos)}"
                
                # Província e distrito
                provincia = random.choice(provincias)
                distritos_provincia = list(Distrito.objects.filter(provincia=provincia))
                
                if not distritos_provincia:
                    continue
                
                distrito = random.choice(distritos_provincia)
                
                # BI único
                numero_bi = f"{random.randint(100000000000, 999999999999)}M"
                
                # Verificar se BI já existe
                while Candidato.objects.filter(numero_bi=numero_bi).exists():
                    numero_bi = f"{random.randint(100000000000, 999999999999)}M"
                
                # Telefone
                prefixos = ['82', '83', '84', '85', '86', '87']
                numero_telefone = f"{random.choice(prefixos)}{random.randint(1000000, 9999999)}"
                
                # Idade (distribuição realista)
                faixas = [(18, 25)] * 40 + [(26, 35)] * 35 + [(36, 50)] * 20 + [(51, 65)] * 5
                faixa = random.choice(faixas)
                idade = random.randint(faixa[0], faixa[1])
                dias_extras = random.randint(0, 364)
                data_nascimento = hoje - timedelta(days=idade * 365 + dias_extras)
                
                # Vaga
                vaga = random.choice(vagas)
                
                # Estado (maioria pendente, alguns aprovados)
                estados_dist = (
                    [Candidato.Estado.PENDENTE] * 70 +
                    [Candidato.Estado.DOCS_APROVADOS] * 15 +
                    [Candidato.Estado.ENTREVISTA_AGENDADA] * 8 +
                    [Candidato.Estado.ENTREVISTA_APROVADA] * 5 +
                    [Candidato.Estado.DOCS_REJEITADOS] * 2
                )
                estado = random.choice(estados_dist)
                
                # Endereço
                bairros = ['Central', 'Militar', 'Cimento', 'Munhuana', 'Maxaquene', 'Polana',
                          'Sommerschield', 'Alto Maé', 'Malhangalene', 'Chamanculo']
                ruas = ['Av. Julius Nyerere', 'Av. Eduardo Mondlane', 'Av. 24 de Julho',
                       'Rua da Resistência', 'Rua do Bagamoyo', 'Av. Mao Tse Tung']
                endereco = f"{random.choice(ruas)}, Bairro {random.choice(bairros)}, Q{random.randint(1,50)}"
                
                # Criar candidato
                candidato = Candidato.objects.create(
                    vaga=vaga,
                    nome_completo=nome_completo,
                    genero=genero,
                    data_nascimento=data_nascimento,
                    numero_bi=numero_bi,
                    numero_telefone=numero_telefone,
                    provincia=provincia,
                    distrito=distrito,
                    endereco=endereco,
                    estado=estado
                )
                
                criados += 1
                if criados % 100 == 0:
                    self.stdout.write(f'  ⏳ Criados: {criados}/{quantidade}')
                    
            except Exception as e:
                erros += 1
                if erros < 10:  # Mostrar apenas primeiros 10 erros
                    self.stdout.write(self.style.ERROR(f'  ❌ Erro: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Concluído!'))
        self.stdout.write(f'  - Candidatos criados: {criados}')
        self.stdout.write(f'  - Erros: {erros}')
        
        # Estatísticas
        self.stdout.write(self.style.SUCCESS(f'\n📊 Estatísticas da Base de Dados:'))
        
        total = Candidato.objects.count()
        self.stdout.write(f'  - Total de candidatos: {total}')
        
        # Por gênero
        homens = Candidato.objects.filter(genero='M').count()
        mulheres = Candidato.objects.filter(genero='F').count()
        self.stdout.write(f'  - Homens: {homens} ({homens/total*100:.1f}%)')
        self.stdout.write(f'  - Mulheres: {mulheres} ({mulheres/total*100:.1f}%)')
        
        # Por estado
        for estado_choice in Candidato.Estado.choices[:5]:
            count = Candidato.objects.filter(estado=estado_choice[0]).count()
            if count > 0:
                self.stdout.write(f'  - {estado_choice[1]}: {count}')
        
        # Por província (top 5)
        self.stdout.write(f'\n📍 Top 5 Províncias:')
        from django.db.models import Count
        top_provincias = Candidato.objects.values('provincia__nome').annotate(
            total=Count('id')
        ).order_by('-total')[:5]
        
        for p in top_provincias:
            self.stdout.write(f'  - {p["provincia__nome"]}: {p["total"]}')
