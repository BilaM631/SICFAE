import os
import django
import sqlite3
from pathlib import Path

# Configurar Django para o DRH
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DRH.settings')
django.setup()

from django.contrib.auth.models import User

# Caminho para o banco original
ORIGINAL_DB = Path(__file__).parent / 'db_drh.sqlite3'

def migrate_users():
    if not ORIGINAL_DB.exists():
        print(f"❌ Banco original não encontrado: {ORIGINAL_DB}")
        return

    print("🔄 Migrando Usuários para o DRH...")
    print(f"📂 Origem: {ORIGINAL_DB}")

    conn = sqlite3.connect(str(ORIGINAL_DB))
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, password, last_login, is_superuser, username, 
                   first_name, last_name, email, is_staff, is_active, date_joined
            FROM auth_user
        """)
        
        users = cursor.fetchall()
        count = 0
        skipped = 0
        
        for row in users:
            username = row[4]
            
            if User.objects.filter(username=username).exists():
                skipped += 1
                continue
                
            try:
                user = User(
                    username=username,
                    password=row[1],
                    last_login=row[2],
                    is_superuser=row[3],
                    first_name=row[5],
                    last_name=row[6],
                    email=row[7],
                    is_staff=row[8],
                    is_active=row[9],
                    date_joined=row[10]
                )
                user.save()
                count += 1
            except Exception as e:
                print(f"  ❌ Erro ao criar {username}: {e}")

        print("\n" + "="*40)
        print(f"✅ Migração de usuários concluída!")
        print(f"📥 Novos usuários: {count}")
        print(f"⏭️  Existentes/Pulados: {skipped}")
        print("="*40)

    except Exception as e:
        print(f"❌ Erro fatal ao ler banco original: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_users()
