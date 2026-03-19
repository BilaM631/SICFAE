"""
Management command to generate codes for existing candidates
Usage: python manage.py gerar_codigos_candidatos
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from candidaturas.models import Candidato

class Command(BaseCommand):
    help = 'Gera códigos únicos para candidatos que ainda não têm código'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🚀 Iniciando geração de códigos...'))
        
        candidatos_sem_codigo = Candidato.objects.filter(
            codigo_candidato=''
        ).exclude(
            provincia__isnull=True
        ).exclude(
            distrito__isnull=True
        ).order_by('distrito', 'id')
        
        total = candidatos_sem_codigo.count()
        self.stdout.write(f'📊 Encontrados {total} candidatos sem código.\n')
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Todos os candidatos já têm código!'))
            return
        
        gerados = 0
        erros = 0
        
        for candidato in candidatos_sem_codigo:
            try:
                # Gerar código
                codigo = candidato.gerar_codigo_candidato()
                
                # Atualizar usando queryset.update() para evitar signals
                Candidato.objects.filter(id=candidato.id).update(codigo_candidato=codigo)
                
                gerados += 1
                if gerados % 100 == 0:
                    self.stdout.write(f'  ⏳ Processados: {gerados}/{total}')
                    
            except Exception as e:
                erros += 1
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Erro ao gerar código para {candidato.nome_completo}: {e}')
                )
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Concluído!'))
        self.stdout.write(f'  - Códigos gerados: {gerados}')
        self.stdout.write(f'  - Erros: {erros}')
        
        # Mostrar exemplos
        self.stdout.write(self.style.SUCCESS(f'\n📝 Exemplos de códigos gerados:'))
        exemplos = Candidato.objects.exclude(codigo_candidato='')[:10]
        for c in exemplos:
            self.stdout.write(f'  - {c.codigo_candidato}: {c.nome_completo} ({c.distrito.nome})')
