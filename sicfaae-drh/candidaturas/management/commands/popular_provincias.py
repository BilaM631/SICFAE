from django.core.management.base import BaseCommand
from candidaturas.models import Provincia, Distrito

class Command(BaseCommand):
    help = 'Popula a base de dados com Províncias e Distritos de Moçambique'

    def handle(self, *args, **kwargs):
        data = {
            "Maputo Cidade": [
                "KaMpfumo", "Nlhamankulu", "KaMaxaquene", "KaMavota", 
                "KaMubukwana", "KaTembe", "KaNyaka"
            ],
            "Maputo Província": [
                "Cidade da Matola", "Boane", "Magude", "Manhiça", 
                "Marracuene", "Matutuíne", "Moamba", "Namaacha"
            ],
            "Gaza": [
                "Xai-Xai", "Bilene", "Chibuto", "Chicualacuala", "Chigubo", 
                "Chókwè", "Guijá", "Mabalane", "Manjacaze", "Massangena", 
                "Massingir", "Limpopo"
            ],
            "Inhambane": [
                "Cidade de Inhambane", "Maxixe", "Funhalouro", "Govuro", 
                "Homoíne", "Inharrime", "Inhassoro", "Jangamo", "Mabote", 
                "Massinga", "Morrumbene", "Panda", "Vilankulo", "Zavala"
            ],
            "Sofala": [
                "Beira", "Búzi", "Caia", "Chemba", "Cheringoma", "Chibabava", 
                "Dondo", "Gorongosa", "Machanga", "Maringué", "Marromeu", 
                "Muanza", "Nhamatanda"
            ],
            "Manica": [
                "Chimoio", "Bárue", "Gondola", "Guro", "Macate", "Machaze", 
                "Macossa", "Manica", "Mossurize", "Sussundenga", "Tambara", 
                "Vanduzi"
            ],
            "Tete": [
                "Cidade de Tete", "Angónia", "Cahora-Bassa", "Changara", 
                "Chifunde", "Chiuta", "Dôa", "Macanga", "Magoé", "Marara", 
                "Marávia", "Moatize", "Mutarara", "Tsangano", "Zumbo"
            ],
            "Zambézia": [
                "Quelimane", "Alto Molócuè", "Chinde", "Derre", "Gilé", 
                "Gurué", "Ile", "Inhassunge", "Luabo", "Lugela", "Maganja da Costa", 
                "Milange", "Mocuba", "Mocubela", "Molumbo", "Mopeia", 
                "Morrumbala", "Mulevala", "Namacurra", "Namarroi", "Nicoadala", 
                "Pebane"
            ],
            "Nampula": [
                "Cidade de Nampula", "Angoche", "Eráti", "Ilha de Moçambique", 
                "Lalaua", "Larde", "Liúpo", "Malema", "Meconta", "Mecubúri", 
                "Memba", "Mogincual", "Mogovolas", "Moma", "Monapo", 
                "Mossuril", "Muecate", "Murrupula", "Nacala-a-Velha", "Nacala-Porto", 
                "Nacarôa", "Rapale", "Ribáuè"
            ],
            "Niassa": [
                "Lichinga", "Chimbonila", "Cuamba", "Lago", "Majune", 
                "Mandimba", "Marrupa", "Maúa", "Mavago", "Mecanhelas", 
                "Mecula", "Metarica", "Muembe", "N'gauma", "Sanga"
            ],
            "Cabo Delgado": [
                "Pemba", "Ancuabe", "Balama", "Chiúre", "Ibo", "Macomia", 
                "Mecúfi", "Meluco", "Metuge", "Mocímboa da Praia", "Montepuez", 
                "Mueda", "Muidumbe", "Namuno", "Nangade", "Palma", "Quissanga"
            ]
        }

        self.stdout.write("A iniciar povoamento de províncias e distritos...")

        total_prov = 0
        total_dist = 0

        for nome_provincia, distritos in data.items():
            provincia, created = Provincia.objects.get_or_create(nome=nome_provincia)
            if created:
                total_prov += 1
            
            for nome_distrito in distritos:
                _, d_created = Distrito.objects.get_or_create(provincia=provincia, nome=nome_distrito)
                if d_created:
                    total_dist += 1
        
        self.stdout.write(self.style.SUCCESS(f'Concluído! {total_prov} Províncias e {total_dist} Distritos criados.'))
