"""
Script de Migração de Dados do Sistema Original para DRH
Copia dados de: db.sqlite3 (original) -> db_drh.sqlite3 (DRH)
"""
import os
import sys
import django
import sqlite3
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DRH.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Provincia, Distrito
from candidaturas.models import Candidato, Vaga, PerfilUtilizador

# Caminho para o banco original
ORIGINAL_DB = Path(__file__).parent.parent / 'db.sqlite3'

def conectar_db_original():
    """Conecta ao banco de dados original"""
    if not ORIGINAL_DB.exists():
        print(f"❌ Erro: Base de dados original não encontrada em {ORIGINAL_DB}")
        sys.exit(1)
    return sqlite3.connect(str(ORIGINAL_DB))

def migrar_provincias(conn_original):
    """Migra províncias do sistema original"""
    print("\n📍 Migrando Províncias...")
    cursor = conn_original.cursor()
    cursor.execute("SELECT id, nome, latitude, longitude FROM candidaturas_provincia")
    
    count = 0
    for row in cursor.fetchall():
        provincia, created = Provincia.objects.get_or_create(
            id=row[0],
            defaults={
                'nome': row[1],
                'latitude': row[2],
                'longitude': row[3]
            }
        )
        if created:
            count += 1
            print(f"  ✅ {provincia.nome}")
    
    print(f"✅ {count} províncias migradas")
    return count

def migrar_distritos(conn_original):
    """Migra distritos do sistema original"""
    print("\n🏘️  Migrando Distritos...")
    cursor = conn_original.cursor()
    cursor.execute("SELECT id, nome, provincia_id FROM candidaturas_distrito")
    
    count = 0
    for row in cursor.fetchall():
        try:
            provincia = Provincia.objects.get(id=row[2])
            distrito, created = Distrito.objects.get_or_create(
                id=row[0],
                defaults={
                    'nome': row[1],
                    'provincia': provincia
                }
            )
            if created:
                count += 1
        except Provincia.DoesNotExist:
            print(f"  ⚠️  Província {row[2]} não encontrada para distrito {row[1]}")
    
    print(f"✅ {count} distritos migrados")
    return count

def migrar_vagas(conn_original):
    """Migra vagas do sistema original"""
    from datetime import date
    print("\n💼 Migrando Vagas...")
    cursor = conn_original.cursor()
    cursor.execute("""
        SELECT id, titulo, descricao, ativa
        FROM candidaturas_vaga
    """)
    
    count = 0
    for row in cursor.fetchall():
        vaga, created = Vaga.objects.get_or_create(
            id=row[0],
            defaults={
                'titulo': row[1],
                'descricao': row[2] or '',
                'ativa': bool(row[3]) if row[3] is not None else True,
                'data_inicio': date(2024, 1, 1),  # Data padrão
                'data_fim': date(2024, 12, 31),   # Data padrão
            }
        )
        if created:
            count += 1
            print(f"  ✅ {vaga.titulo}")
    
    print(f"✅ {count} vagas migradas")
    return count

def migrar_candidatos(conn_original):
    """Migra candidatos do sistema original"""
    print("\n👥 Migrando Candidatos...")
    cursor = conn_original.cursor()
    cursor.execute("""
        SELECT id, codigo_candidato, nome_completo, genero, data_nascimento,
               numero_bi, numero_telefone, provincia_id, distrito_id, endereco,
               vaga_id, estado, arquivo_cv, arquivo_bi, arquivo_certificado, foto,
               validacao_cv, validacao_bi, validacao_certificado, validacao_foto,
               observacoes, data_criacao, data_atualizacao,
               enviado_defc, data_envio_defc, id_defc
        FROM candidaturas_candidato
    """)
    
    count = 0
    erros = 0
    
    # Mapeamento de estados antigos para novos
    ESTADO_MAP = {
        'PENDENTE': 'PENDENTE',
        'DOCS_APROVADOS': 'DOCS_APROVADOS',
        'DOCS_REJEITADOS': 'DOCS_REJEITADOS',
        'ENTREVISTA_AGENDADA': 'ENTREVISTA_AGENDADA',
        'ENTREVISTA_APROVADA': 'ENTREVISTA_APROVADA',
        'ENTREVISTA_REPROVADA': 'ENTREVISTA_REPROVADA',
        'EM_FORMACAO': 'ENVIADO_DEFC',  # Candidatos em formação foram enviados para DEFC
        'FORMADOR_CERTIFICADO': 'ENVIADO_DEFC',
        'BRIGADISTA_CERTIFICADO': 'ENVIADO_DEFC',
        'CONTRATADO': 'ENVIADO_DEFC',
        'EM_FORMACAO_FORMADOR': 'ENVIADO_DEFC',
        'EM_FORMACAO_BRIGADISTA': 'ENVIADO_DEFC',
        'CANDIDATO_A_FORMADOR': 'ENTREVISTA_APROVADA',
    }
    
    for row in cursor.fetchall():
        try:
            # Mapear estado
            estado_original = row[11]
            estado_novo = ESTADO_MAP.get(estado_original, 'PENDENTE')
            
            # Verificar se já existe
            if Candidato.objects.filter(numero_bi=row[5]).exists():
                continue
            
            candidato = Candidato.objects.create(
                id=row[0],
                codigo_candidato=row[1],
                nome_completo=row[2],
                genero=row[3],
                data_nascimento=row[4],
                numero_bi=row[5],
                numero_telefone=row[6],
                provincia_id=row[7],
                distrito_id=row[8],
                endereco=row[9] or '',
                vaga_id=row[10],
                estado=estado_novo,
                arquivo_cv=row[12] or '',
                arquivo_bi=row[13] or '',
                arquivo_certificado=row[14] or '',
                foto=row[15] or '',
                validacao_cv=bool(row[16]) if row[16] is not None else False,
                validacao_bi=bool(row[17]) if row[17] is not None else False,
                validacao_certificado=bool(row[18]) if row[18] is not None else False,
                validacao_foto=bool(row[19]) if row[19] is not None else False,
                observacoes=row[20] or '',
                enviado_defc=bool(row[22]) if row[22] is not None else (estado_novo == 'ENVIADO_DEFC'),
                data_envio_defc=row[23],
                id_defc=row[24] or '',
            )
            count += 1
            
            if count % 50 == 0:
                print(f"  ⏳ {count} candidatos migrados...")
                
        except Exception as e:
            erros += 1
            print(f"  ❌ Erro ao migrar candidato {row[2]}: {str(e)}")
    
    print(f"✅ {count} candidatos migrados ({erros} erros)")
    return count

def migrar_usuarios(conn_original):
    """Migra usuários e perfis do sistema original"""
    print("\n👤 Migrando Usuários...")
    cursor = conn_original.cursor()
    
    # Migrar usuários do Django
    cursor.execute("""
        SELECT id, password, last_login, is_superuser, username, first_name,
               last_name, email, is_staff, is_active, date_joined
        FROM auth_user
    """)
    
    count_users = 0
    for row in cursor.fetchall():
        if not User.objects.filter(username=row[4]).exists():
            User.objects.create(
                id=row[0],
                password=row[1],
                last_login=row[2],
                is_superuser=bool(row[3]),
                username=row[4],
                first_name=row[5] or '',
                last_name=row[6] or '',
                email=row[7] or '',
                is_staff=bool(row[8]),
                is_active=bool(row[9]),
                date_joined=row[10]
            )
            count_users += 1
    
    print(f"✅ {count_users} usuários migrados")
    
    # Migrar perfis
    cursor.execute("""
        SELECT id, usuario_id, nivel, provincia_id, distrito_id
        FROM candidaturas_perfilutilizador
    """)
    
    count_perfis = 0
    for row in cursor.fetchall():
        try:
            if not PerfilUtilizador.objects.filter(usuario_id=row[1]).exists():
                PerfilUtilizador.objects.create(
                    id=row[0],
                    usuario_id=row[1],
                    nivel=row[2],
                    provincia_id=row[3],
                    distrito_id=row[4]
                )
                count_perfis += 1
        except Exception as e:
            print(f"  ⚠️  Erro ao migrar perfil: {str(e)}")
    
    print(f"✅ {count_perfis} perfis migrados")
    return count_users + count_perfis

def main():
    """Função principal de migração"""
    print("=" * 60)
    print("🔄 MIGRAÇÃO DE DADOS: ORIGINAL → DRH")
    print("=" * 60)
    
    # Conectar ao banco original
    conn_original = conectar_db_original()
    
    try:
        # Executar migrações em ordem
        total = 0
        total += migrar_provincias(conn_original)
        total += migrar_distritos(conn_original)
        total += migrar_vagas(conn_original)
        total += migrar_usuarios(conn_original)
        total += migrar_candidatos(conn_original)
        
        print("\n" + "=" * 60)
        print(f"✅ MIGRAÇÃO CONCLUÍDA: {total} registros migrados")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn_original.close()

if __name__ == '__main__':
    main()
