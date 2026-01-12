import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SICFAAE.settings')
django.setup()

from django.contrib.auth.models import User

try:
    if User.objects.filter(username='admin').exists():
        user = User.objects.get(username='admin')
        user.set_password('admin123')
        user.save()
        print("Senha do utilizador 'admin' atualizada com sucesso para 'admin123'.")
    else:
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Utilizador 'admin' criado com sucesso com a senha 'admin123'.")
except Exception as e:
    print(f"Erro: {e}")
