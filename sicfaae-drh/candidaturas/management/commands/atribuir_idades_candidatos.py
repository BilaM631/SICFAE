"""
Management command to assign realistic birth dates to existing candidates
Usage: python manage.py atribuir_idades_candidatos
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from candidaturas.models import Candidato
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Atribui datas de nascimento realistas a candidatos que não têm'

    def add_arguments(self, parser):
        parser.add_argument(
            '--idade-min',
            type=int,
            default=18,
            help='Idade mínima dos candidatos (padrão: 18)'
        )
        parser.add_argument(
            '--idade-max',
            type=int,
            default=65,
            help='Idade máxima dos candidatos (padrão: 65)'
        )

    def handle(self, *args, **options):
        idade_min = options['idade_min']
        idade_max = options['idade_max']
        
        self.stdout.write(self.style.SUCCESS('\n🎂 Iniciando atribuição de idades...'))
        self.stdout.write(f'   Faixa etária: {idade_min} a {idade_max} anos\n')
        
        candidatos_sem_idade = Candidato.objects.filter(
            data_nascimento__isnull=True
        )
        
        total = candidatos_sem_idade.count()
        self.stdout.write(f'📊 Encontrados {total} candidatos sem data de nascimento.\n')
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Todos os candidatos já têm data de nascimento!'))
            return
        
        # Confirmar ação
        self.stdout.write(self.style.WARNING(
            f'⚠️  Isto irá atribuir datas de nascimento aleatórias a {total} candidatos.'
        ))
        confirmar = input('Deseja continuar? (s/N): ')
        
        if confirmar.lower() != 's':
            self.stdout.write(self.style.ERROR('❌ Operação cancelada.'))
            return
        
        hoje = date.today()
        atribuidos = 0
        
        # Distribuição realista de idades (mais jovens)
        # 40% entre 18-25, 35% entre 26-35, 20% entre 36-50, 5% entre 51-65
        distribuicao = (
            [(18, 25)] * 40 +
            [(26, 35)] * 35 +
            [(36, 50)] * 20 +
            [(51, min(65, idade_max))] * 5
        )
        
        for candidato in candidatos_sem_idade:
            try:
                # Selecionar faixa etária baseada na distribuição
                faixa = random.choice(distribuicao)
                idade = random.randint(faixa[0], faixa[1])
                
                # Calcular data de nascimento
                anos_atras = idade
                # Adicionar variação de meses (0-11 meses)
                dias_extras = random.randint(0, 364)
                data_nascimento = hoje - timedelta(days=anos_atras * 365 + dias_extras)
                
                # Atualizar usando update() para evitar signals
                Candidato.objects.filter(id=candidato.id).update(
                    data_nascimento=data_nascimento
                )
                
                atribuidos += 1
                if atribuidos % 100 == 0:
                    self.stdout.write(f'  ⏳ Processados: {atribuidos}/{total}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Erro ao atribuir idade a {candidato.nome_completo}: {e}')
                )
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Concluído!'))
        self.stdout.write(f'  - Idades atribuídas: {atribuidos}')
        
        # Estatísticas
        self.stdout.write(self.style.SUCCESS(f'\n📊 Estatísticas de Idades:'))
        
        # Contar por faixa etária
        candidatos_com_idade = Candidato.objects.exclude(data_nascimento__isnull=True)
        
        faixas = [
            (18, 25, '18-25 anos'),
            (26, 35, '26-35 anos'),
            (36, 50, '36-50 anos'),
            (51, 100, '51+ anos'),
        ]
        
        for min_idade, max_idade, label in faixas:
            count = sum(1 for c in candidatos_com_idade if c.idade and min_idade <= c.idade <= max_idade)
            percentagem = (count / candidatos_com_idade.count() * 100) if candidatos_com_idade.count() > 0 else 0
            self.stdout.write(f'  - {label}: {count} ({percentagem:.1f}%)')
        
        # Mostrar exemplos
        self.stdout.write(self.style.SUCCESS(f'\n📝 Exemplos:'))
        exemplos = Candidato.objects.exclude(data_nascimento__isnull=True)[:5]
        for c in exemplos:
            self.stdout.write(f'  - {c.nome_completo}: {c.idade} anos (nascido em {c.data_nascimento.strftime("%d/%m/%Y")})')
