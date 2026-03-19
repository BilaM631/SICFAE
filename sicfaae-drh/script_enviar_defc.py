import os
import django
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DRH.settings')
django.setup()

from candidaturas.models import Candidato, Vaga

def enviar_candidatos(titulo_vaga, quantidade):
    vaga = Vaga.objects.filter(titulo__icontains=titulo_vaga).first()
    if not vaga:
        print(f"Vaga não encontrada para: {titulo_vaga}")
        return
    
    # Pegar candidatos que ainda não foram enviados
    candidatos = Candidato.objects.filter(vaga=vaga, enviado_defc=False)[:quantidade]
    candidatos_ids = list(candidatos.values_list('id', flat=True))
    
    # Se não houver suficientes que não foram enviados, pegar qualquer um (mesmo os já marcados, forçar)
    if len(candidatos_ids) < quantidade:
        candidatos_ids = list(Candidato.objects.filter(vaga=vaga)[:quantidade].values_list('id', flat=True))
        
    print(f"Preparando para enviar {len(candidatos_ids)} candidatos da vaga '{titulo_vaga}'...")
    
    # Atualizar em massa
    Candidato.objects.filter(id__in=candidatos_ids).update(
        estado=Candidato.Estado.ENVIADO_DEFC,
        enviado_defc=True,
        data_envio_defc=timezone.now()
    )
    print(f"Sucesso: {len(candidatos_ids)} candidatos de '{titulo_vaga}' marcados como ENVIADO_DEFC.")

if __name__ == '__main__':
    enviar_candidatos('Formador Nacional', 75)
    enviar_candidatos('Formador Provincial', 75)
    enviar_candidatos('Brigadistas Nacionais', 1850)
    print("Concluído!")
