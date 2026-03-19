from django.core.management.base import BaseCommand
from candidaturas.models import Candidato, Provincia, Distrito, Vaga
import random
from faker import Faker
import datetime
from django.utils import timezone

class Command(BaseCommand):
    help = 'Povoa a base de dados com 50 candidatos por província para testes'

    def handle(self, *args, **kwargs):
        fake = Faker(['pt_PT']) # Usar locale português
        
        provincias = Provincia.objects.all()
        vagas = Vaga.objects.filter(ativa=True)
        
        if not vagas.exists():
            self.stdout.write(self.style.ERROR('Erro: Não existem vagas ativas. Crie pelo menos uma vaga antes de executar.'))
            return

        total_criados = 0

        self.stdout.write(f"Iniciando povoamento de dados...")

        for provincia in provincias:
            distritos = list(Distrito.objects.filter(provincia=provincia))
            if not distritos:
                self.stdout.write(self.style.WARNING(f"Aviso: Província {provincia.nome} sem distritos. Pulando."))
                continue

            self.stdout.write(f"Gerando para {provincia.nome}...")
            
            for i in range(50):
                distrito = random.choice(distritos)
                vaga = random.choice(vagas)
                genero = random.choice([Candidato.Genero.MASCULINO, Candidato.Genero.FEMININO])
                
                # Estado aleatório com pesos
                estados = [
                    Candidato.Estado.PENDENTE,
                    Candidato.Estado.DOCS_APROVADOS,
                    Candidato.Estado.DOCS_REJEITADOS,
                    Candidato.Estado.ENTREVISTA_AGENDADA,
                    Candidato.Estado.ENTREVISTA_APROVADA,
                    Candidato.Estado.CONTRATADO
                ]
                pesos = [40, 20, 10, 15, 10, 5] # Maioria pendente/aprovado docs
                estado = random.choices(estados, weights=pesos, k=1)[0]

                # Criar BI fictício mas com formato realista
                bi = f"{random.randint(100000000, 999999999)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
                
                # Garantir unicidade do BI (simples retry)
                while Candidato.objects.filter(numero_bi=bi).exists():
                     bi = f"{random.randint(100000000, 999999999)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"

                Candidato.objects.create(
                    nome_completo=fake.name(),
                    numero_bi=bi,
                    numero_telefone=f"8{random.choice(['2','4','6','7'])}{random.randint(1000000, 9999999)}",
                    genero=genero,
                    provincia=provincia,
                    distrito=distrito,
                    vaga=vaga,
                    endereco=fake.address(),
                    estado=estado,
                    data_criacao=timezone.now() - datetime.timedelta(days=random.randint(0, 30)) # Data nos últimos 30 dias
                )
                total_criados += 1
        
        self.stdout.write(self.style.SUCCESS(f'Sucesso! {total_criados} candidatos criados.'))
