import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DRH.settings')
django.setup()

from candidaturas.models import Vaga

print("=== Detalhe de Vagas ===")
hoje = timezone.now().date()
print(f"Data de Hoje: {hoje}")

vagas = Vaga.objects.all()
for v in vagas:
    print(f"ID: {v.id}")
    print(f"Título: {v.titulo}")
    print(f"Início: {v.data_inicio} ({'ANTERIOR' if v.data_inicio <= hoje else 'FUTURO'})")
    print(f"Fim:    {v.data_fim}    ({'VÁLIDO' if v.data_fim >= hoje else 'EXPIRADO'})")
    print(f"Ativa:  {v.ativa}")
    visivel = v.ativa and v.data_inicio <= hoje and v.data_fim >= hoje
    print(f"Visível?: {visivel}")
    print("-" * 20)
