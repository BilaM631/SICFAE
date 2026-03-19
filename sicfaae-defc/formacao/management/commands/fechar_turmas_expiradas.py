from django.core.management.base import BaseCommand
from formacao.models import Turma
from datetime import date

class Command(BaseCommand):
    help = 'Fecha automaticamente as turmas cuja data_fim já passou e que atingiram a carga horária.'

    def handle(self, *args, **options):
        hoje = date.today()
        # Encontrar turmas pendentes que já passaram da data_fim
        turmas_expiradas = Turma.objects.filter(
            concluida=False,
            data_fim__lt=hoje
        )
        
        fechadas = 0
        ignoradas = 0

        for turma in turmas_expiradas:
            turma.atualizar_carga_horaria()
            
            # Se a turma atingiu a carga horaria ou tem 100% de presencas/sessoes, fechar
            # Critério: percentual >= 100 (ou seja, horas reais >= previstas)
            percentual = turma.percentual_carga_horaria()
            
            if percentual >= 100:
                turma.concluida = True
                turma.save()
                fechadas += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Turma {turma.numero} ({turma.distrito.nome}) fechada com sucesso.')
                )
            else:
                ignoradas += 1
                self.stdout.write(
                    self.style.WARNING(f'Turma {turma.numero} ignorada. Carga horária incompleta ({percentual}%).')
                )

        self.stdout.write(self.style.SUCCESS(f'Processo concluído: {fechadas} fechadas, {ignoradas} ignoradas.'))
