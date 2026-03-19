from django.core.management.base import BaseCommand
from django.db import transaction
from candidaturas.models import Candidato


class Command(BaseCommand):
    help = 'Regenera os códigos de candidatos usando a nova lógica de blocos base-36'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra o que seria alterado sem fazer mudanças',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Nenhuma alteração será feita'))
        
        candidatos = Candidato.objects.select_related('provincia', 'distrito').order_by('id')
        total = candidatos.count()
        
        self.stdout.write(f'\nTotal de candidatos: {total}')
        self.stdout.write('=' * 80)
        
        alterados = 0
        mantidos = 0
        erros = 0
        
        # Agrupar por distrito para regenerar sequencialmente
        from collections import defaultdict
        por_distrito = defaultdict(list)
        
        for candidato in candidatos:
            if candidato.distrito:
                por_distrito[candidato.distrito.id].append(candidato)
        
        self.stdout.write(f'\nProcessando {len(por_distrito)} distritos...\n')
        
        for distrito_id, candidatos_distrito in sorted(por_distrito.items()):
            if not candidatos_distrito:
                continue
            
            distrito_nome = candidatos_distrito[0].distrito.nome
            provincia_nome = candidatos_distrito[0].provincia.nome
            
            self.stdout.write(f'\n{provincia_nome} - {distrito_nome} (ID {distrito_id}):')
            self.stdout.write('-' * 80)
            
            # Regenerar códigos sequencialmente para este distrito
            for idx, candidato in enumerate(candidatos_distrito, start=1):
                try:
                    codigo_antigo = candidato.codigo_candidato
                    
                    # Gerar novo código
                    candidato.codigo_candidato = ''  # Limpar para forçar regeneração
                    codigo_novo = candidato.gerar_codigo_candidato()
                    
                    if codigo_antigo != codigo_novo:
                        self.stdout.write(
                            f'  [{idx:3d}] {codigo_antigo:20s} -> {codigo_novo:20s}'
                        )
                        
                        if not dry_run:
                            # Usar update para evitar signals
                            Candidato.objects.filter(id=candidato.id).update(
                                codigo_candidato=codigo_novo
                            )
                        
                        alterados += 1
                    else:
                        mantidos += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  Erro no candidato {candidato.id}: {str(e)}')
                    )
                    erros += 1
        
        # Resumo
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('\nResumo:'))
        self.stdout.write(f'  Total de candidatos: {total}')
        self.stdout.write(f'  Códigos alterados: {alterados}')
        self.stdout.write(f'  Códigos mantidos: {mantidos}')
        self.stdout.write(f'  Erros: {erros}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nMODO DRY-RUN: Execute sem --dry-run para aplicar as mudanças')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✓ Regeneração concluída com sucesso!')
            )
