"""
Script de Migração de Dados - ORIGINAL → DEFC
Migra dados de formação completos
"""
import os
import sys
import django
import sqlite3
from pathlib import Path
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DEFC.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Provincia, Distrito, CandidatoFormacao
from formacao.models import Turma, Local

ORIGINAL_DB = Path(__file__).parent.parent / 'sicfaae-drh' / 'db_drh.sqlite3'

def main():
    print("=" * 60)
    print("🔄 MIGRAÇÃO DE DADOS: ORIGINAL → DEFC")
    print("=" * 60)
    
    if not ORIGINAL_DB.exists():
        print(f"❌ Base de dados original não encontrada: {ORIGINAL_DB}")
        return
    
    conn = sqlite3.connect(str(ORIGINAL_DB))
    cursor = conn.cursor()
    
    # 1. PROVÍNCIAS
    print("\n📍 Migrando Províncias...")
    cursor.execute("SELECT id, nome FROM core_provincia")
    for row in cursor.fetchall():
        Provincia.objects.get_or_create(id=row[0], defaults={'nome': row[1]})
    print(f"✅ Províncias migradas")
    
    # 2. DISTRITOS
    print("\n🏘️  Migrando Distritos...")
    cursor.execute("SELECT id, nome, provincia_id FROM core_distrito")
    primeiro_distrito = None
    for row in cursor.fetchall():
        try:
            d, _ = Distrito.objects.get_or_create(id=row[0], defaults={'nome': row[1], 'provincia_id': row[2]})
            if not primeiro_distrito: primeiro_distrito = d
        except: pass
    print(f"✅ Distritos migrados")
    
    if not primeiro_distrito:
        print("⚠️  Nenhum distrito encontrado. Criando um padrão.")
        prov, _ = Provincia.objects.get_or_create(nome="Maputo")
        primeiro_distrito = Distrito.objects.create(nome="Distrito Geral", provincia=prov)

    # 3. LOCAIS
    print("\n🏫 Criando Local Padrão...")
    local_padrao, _ = Local.objects.get_or_create(
        nome="Sede STAE (Migrado)",
        distrito=primeiro_distrito,
        defaults={'capacidade': 50}
    )
    
    # 4. CANDIDATOS FORMACAO
    print("\n👥 Migrando Candidatos para Formação...")
    
    # Buscar formadores e alunos da tabela antiga
    cursor.execute("""
        SELECT c.id, c.codigo_candidato, c.nome_completo, c.genero, c.data_nascimento,
               c.numero_bi, c.numero_telefone, c.provincia_id, c.distrito_id, c.endereco,
               c.foto, v.titulo
        FROM candidaturas_candidato c
        LEFT JOIN candidaturas_vaga v ON c.vaga_id = v.id
        WHERE c.estado IN ('ENVIADO_DEFC', 'EM_FORMACAO', 'FORMADOR_CERTIFICADO', 'BRIGADISTA_CERTIFICADO', 'CONTRATADO')
    """)
    
    count_c = 0
    erros_c = 0
    for row in cursor.fetchall():
        try:
            # Garantir existência de provincia e distrito
            prov_id = row[7]
            dist_id = row[8]
            titulo_vaga = row[11] or ''
            
            tipo_agente = CandidatoFormacao.TipoAgente.BRIGADISTA
            vaga_str = titulo_vaga.upper()
            if 'FORMADOR' in vaga_str:
                tipo_agente = CandidatoFormacao.TipoAgente.FORMADOR
            elif 'AGENTE' in vaga_str or 'CIVICO' in vaga_str or 'CÍVICO' in vaga_str:
                tipo_agente = CandidatoFormacao.TipoAgente.AGENTE_CIVICO
            elif 'MMV' in vaga_str or 'MESA' in vaga_str:
                tipo_agente = CandidatoFormacao.TipoAgente.MMV
            
            if not Provincia.objects.filter(id=prov_id).exists():
                prov_id = primeiro_distrito.provincia.id
                
            if not Distrito.objects.filter(id=dist_id).exists():
                dist_id = primeiro_distrito.id

            CandidatoFormacao.objects.update_or_create(
                id_drh=row[0],
                defaults={
                    'codigo_candidato': row[1] or f'C{row[0]}',
                    'nome_completo': row[2],
                    'genero': row[3] or 'M',
                    'data_nascimento': row[4],
                    'numero_bi': row[5],
                    'numero_telefone': row[6] or '',
                    'provincia_id': prov_id,
                    'distrito_id': dist_id,
                    'endereco': row[9] or '',
                    'foto': row[10] or '',
                    'tipo_agente': tipo_agente
                }
            )
            count_c += 1
        except Exception as e:
            erros_c += 1
            # print(f"  ❌ Erro no candidato {row[2]}: {e}")
            
    print(f"✅ {count_c} candidatos importados para formação ({erros_c} erros)")
    
    # 5. TURMAS
    print("\n📚 Migrando Turmas... (Ignorado: tabelas não existem no ambiente DRH)")
    # A tabela formacao_turma não existe no DRH, é específica do DEFC.

    conn.close()
    print("\n" + "=" * 60)
    print(f"✅ MIGRAÇÃO DEFC CONCLUÍDA")
    print("=" * 60)

if __name__ == '__main__':
    main()
