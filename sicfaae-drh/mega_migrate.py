import os
import django
from django.apps import apps
from django.db import connections

# DRH Config
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DRH.settings')
django.setup()

def get_complete_config(db_path):
    return {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': db_path,
        'USER': '', 'PASSWORD': '', 'HOST': '', 'PORT': '',
        'CONN_MAX_AGE': 0, 'CONN_HEALTH_CHECKS': False,
        'AUTOCOMMIT': True, 'ATOMIC_REQUESTS': False,
        'OPTIONS': {}, 'TIME_ZONE': None,
    }

def mega_migrate():
    sqlite_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db_drh.sqlite3')
    connections.databases['sqlite_local'] = get_complete_config(sqlite_db_path)

    models_to_migrate = [
        'core.Provincia', 'core.Distrito', 'core.PostoAdministrativo', 
        'core.Localidade', 'core.PerfilUtilizador', 'candidaturas.Concurso', 
        'candidaturas.Vaga', 'candidaturas.Candidato', 'candidaturas.ExperienciaProfissional'
    ]

    for model_label in models_to_migrate:
        print(f"Migrating {model_label}...", flush=True)
        try:
            model = apps.get_model(model_label)
        except LookupError:
            print(f"Model {model_label} not found. Skipping.", flush=True)
            continue

        objects = list(model.objects.using('sqlite_local').all())
        count = len(objects)
        print(f"Found {count} objects.", flush=True)
        
        if count > 0:
            for obj in objects:
                obj._state.db = 'default'
            
            for i in range(0, count, 100):
                chunk = objects[i:i+100]
                model.objects.using('default').bulk_create(chunk, ignore_conflicts=True)
                print(f"Bulk Progress: {i + len(chunk)}/{count}...", flush=True)

    print("Mega Migration Finished for DRH!", flush=True)

if __name__ == '__main__':
    mega_migrate()
