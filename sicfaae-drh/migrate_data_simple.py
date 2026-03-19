"""
Script Simplificado de Migração de Dados - ORIGINAL → DRH
Migra apenas dados essenciais que existem em ambos os sistemas
"""
import os
import sys
import django
import sqlite3
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DRH.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Provincia, Distrito
from candidaturas.models import Candidato, Vaga, PerfilUtilizador
from datetime import date

ORIGINAL_DB = Path(__file__).parent.parent / 'db.sqlite3'

def main():
    print("=" * 60)
    print("🔄 MIGRAÇÃO SIMPLIFICADA: ORIGINAL → DRH")
    print("=" * 60)
    
    if not ORIGINAL_DB.exists():
        print(f"❌ Base de dados original não encontrada: {ORIGINAL_DB}")
        return
    
    conn = sqlite3.connect(str(ORIGINAL_DB))
    cursor = conn.cursor()
    
    total = 0
    
    # 1. PROVÍNCIAS
    print("\n📍 Migrando Províncias...")
    cursor.execute("SELECT id, nome, latitude, longitude FROM candidaturas_provincia")
    for row in cursor.fetchall():
        Provincia.objects.get_or_create(
            id=row[0],
            defaults={'nome': row[1], 'latitude': row[2], 'longitude': row[3]}
        )
        total += 1
    print(f"✅ Províncias migradas")
    
    # 2. DISTRITOS
    print("\n🏘️  Migrando Distritos...")
    cursor.execute("SELECT id, nome, provincia_id FROM candidaturas_distrito")
    for row in cursor.fetchall():
        try:
            Distrito.objects.get_or_create(
                id=row[0],
                defaults={'nome': row[1], 'provincia_id': row[2]}
            )
            total += 1
        except:
            pass
    print(f"✅ Distritos migrados")
    
    # 3. VAGAS
    print("\n💼 Migrando Vagas...")
    cursor.execute("SELECT id, titulo, descricao, ativa FROM candidaturas_vaga")
    for row in cursor.fetchall():
        Vaga.objects.get_or_create(
            id=row[0],
            defaults={
                'titulo': row[1],
                'descricao': row[2] or '',
                'ativa': bool(row[3]) if row[3] is not None else True,
                'data_inicio': date(2024, 1, 1),
                'data_fim': date(2024, 12, 31),
            }
        )
        total += 1
    print(f"✅ Vagas migradas")
    
    # 4. USUÁRIOS
    print("\n👤 Migrando Usuários...")
    cursor.execute("""
        SELECT id, password, username, email, is_superuser, is_staff, is_active, date_joined
        FROM auth_user
    """)
    for row in cursor.fetchall():
        if not User.objects.filter(username=row[2]).exists():
            User.objects.create(
                id=row[0],
                password=row[1],
                username=row[2],
                email=row[3] or '',
                is_superuser=bool(row[4]),
                is_staff=bool(row[5]),
                is_active=bool(row[6]),
                date_joined=row[7]
            )
            total += 1
    print(f"✅ Usuários migrados")
    
    # 5. CANDIDATOS (apenas campos essenciais)
    print("\n👥 Migrando Candidatos (pode demorar)...")
    cursor.execute("""
        SELECT id, codigo_candidato, nome_completo, genero, data_nascimento,
               numero_bi, numero_telefone, provincia_id, distrito_id, endereco,
               vaga_id, estado, foto, data_criacao
        FROM candidaturas_candidato
    """)
    
    count = 0
    ESTADO_MAP = {
        'PENDENTE': 'PENDENTE',
        'DOCS_APROVADOS': 'DOCS_APROVADOS',
        'DOCS_REJEITADOS': 'DOCS_REJEITADOS',
        'ENTREVISTA_AGENDADA': 'ENTREVISTA_AGENDADA',
        'ENTREVISTA_APROVADA': 'ENTREVISTA_APROVADA',
        'ENTREVISTA_REPROVADA': 'ENTREVISTA_REPROVADA',
    }
    
    # Estados que indicam que o candidato foi enviado para DEFC
    ESTADOS_DEFC = ['EM_FORMACAO', 'FORMADOR_CERTIFICADO', 'BRIGADISTA_CERTIFICADO', 
                    'CONTRATADO', 'EM_FORMACAO_FORMADOR', 'EM_FORMACAO_BRIGADISTA', 
                    'CANDIDATO_A_FORMADOR']
    
    for row in cursor.fetchall():
        try:
            if Candidato.objects.filter(numero_bi=row[5]).exists():
                continue
            
            estado_original = row[11]
            if estado_original in ESTADOS_DEFC:
                estado_novo = 'ENVIADO_DEFC'
                enviado_defc = True
            else:
                estado_novo = ESTADO_MAP.get(estado_original, 'PENDENTE')
                enviado_defc = False
            
            Candidato.objects.create(
                id=row[0],
                codigo_candidato=row[1] or f'CAND{row[0]:05d}',
                nome_completo=row[2],
                genero=row[3] or 'M',
                data_nascimento=row[4],
                numero_bi=row[5],
                numero_telefone=row[6] or '000000000',
                provincia_id=row[7],
                distrito_id=row[8],
                endereco=row[9] or '',
                vaga_id=row[10],
                estado=estado_novo,
                foto=row[12] or '',
                enviado_defc=enviado_defc,
            )
            count += 1
            if count % 100 == 0:
                print(f"  ⏳ {count} candidatos...")
        except Exception as e:
            print(f"  ⚠️  Erro: {str(e)[:50]}")
    
    total += count
    print(f"✅ {count} candidatos migrados")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✅ MIGRAÇÃO CONCLUÍDA: ~{total} registros")
    print("=" * 60)
    print("\n💡 Próximos passos:")
    print("  1. Verifique os dados no admin: http://localhost:8000/admin")
    print("  2. Atualize a página do DRH para ver os candidatos")
    print("=" * 60)

if __name__ == '__main__':
    main()
