import os
import django
from django.template import Template, TemplateSyntaxError

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SICFAAE.settings')
django.setup()

def validate_template(path):
    print(f"Validating {os.path.basename(path)}...")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        Template(source)
        print("  [OK] Valid syntax")
    except TemplateSyntaxError as e:
        print(f"  [ERROR] {e}")
    except Exception as e:
        print(f"  [EXCEPTION] {e}")

# Paths
base_dir = r"c:\Users\vagne\OneDrive\Desktop\sicfaae\templates\candidaturas"
files = [
    "painel_controlo.html",
    "lista_candidatos.html"
]

for f in files:
    validate_template(os.path.join(base_dir, f))
