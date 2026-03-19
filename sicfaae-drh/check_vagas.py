import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DRH.settings')
django.setup()

from candidaturas.models import Vaga

print("=== Relatório de Vagas ===")
hoje = timezone.now().date()
print(f"Data de Hoje: {hoje}")

vagas = Vaga.objects.all()
if not vagas.exists():
    print("Nenhuma vaga encontrada no banco de dados.")
else:
    for v in vagas:
        status_temporal = "DENTRO DO PRAZO"
        if v.data_inicio > hoje:
            status_temporal = "FUTURA"
        elif v.data_fim < hoje:
            status_temporal = "EXPIRADA"
            
        print(f"ID: {v.id} | Título: {v.titulo}")
        print(f"  - Ativa: {v.ativa}")
        print(f"  - Início: {v.data_inicio} | Fim: {v.data_fim}")
        print(f"  - Status Temporal: {status_temporal}")
        print(f"  - Deveria aparecer? {'SIM' if v.ativa and status_temporal == 'DENTRO DO PRAZO' else 'NÃO'}")
        print("-" * 30)
