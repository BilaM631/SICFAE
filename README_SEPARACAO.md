# Separação do Sistema SICFAE - README

## Estrutura dos Projetos

Este diretório contém agora **TRÊS** sistemas:

### 1. **sicfaae/** (ORIGINAL - BACKUP)
Sistema monolítico original. **NÃO MODIFICAR**. Manter como backup e referência.

### 2. **sicfaae-drh/** (NOVO - Direção de Recursos Humanos)
**Responsabilidade**: Gestão de Candidaturas
- Recepção de candidaturas
- Validação de documentos
- Agendamento e realização de entrevistas
- Envio de candidatos aprovados para DEFC via API

**Porta**: 8000
**Base de Dados**: `db_drh.sqlite3`
**Login**: `/accounts/login/`

### 3. **sicfaae-defc/** (NOVO - Departamento de Educação e Formação Cívica)
**Responsabilidade**: Gestão de Formação
- Recepção de candidatos aprovados do DRH
- Criação e gestão de turmas
- Registo de sessões e presenças
- Emissão de certificações

**Porta**: 8001
**Base de Dados**: `db_defc.sqlite3`
**Login**: `/accounts/login/`

---

## Como Executar

### DRH (Porta 8000)
```bash
cd sicfaae-drh
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8000
```

Aceder: http://localhost:8000

### DEFC (Porta 8001)
```bash
cd sicfaae-defc
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8001
```

Aceder: http://localhost:8001

---

## Fluxo de Trabalho

1. **DRH**: Candidato submete candidatura
2. **DRH**: Admin valida documentos e aprova entrevista
3. **DRH**: Candidato aprovado → Clicar "Enviar para Formação"
4. **API**: DRH envia dados para DEFC via POST /api/candidatos/receber/
5. **DEFC**: Recebe candidato e cria `CandidatoFormacao`
6. **DEFC**: Admin aloca candidato a turmas
7. **DEFC**: Regista presenças e emite certificações

---

## Integração via API

### DRH → DEFC
**Endpoint**: `POST http://localhost:8001/api/candidatos/receber/`
**Autenticação**: Token (configurar em `.env`)

### Configuração de Tokens

#### No DRH (.env):
```
DEFC_API_URL=http://localhost:8001/api/
DEFC_API_TOKEN=<token_gerado_no_defc>
```

#### No DEFC (.env):
```
DRH_API_URL=http://localhost:8000/api/
DRH_API_TOKEN=<token_gerado_no_drh>
```

### Gerar Tokens
```bash
# No DRH
cd sicfaae-drh
python manage.py drf_create_token <username>

# No DEFC
cd sicfaae-defc
python manage.py drf_create_token <username>
```

---

## Migração de Dados

**IMPORTANTE**: Antes de usar os novos sistemas em produção, é necessário migrar dados do sistema original.

Scripts de migração serão criados em:
- `sicfaae/scripts/migrar_dados_drh.py`
- `sicfaae/scripts/migrar_dados_defc.py`

---

## Próximos Passos

1. ✅ Estrutura dos projetos criada
2. ✅ Modelos ajustados
3. ✅ API de integração implementada
4. ⏳ Ajustar views e templates
5. ⏳ Criar scripts de migração de dados
6. ⏳ Testes de integração
7. ⏳ Documentação completa

---

## Suporte

Para questões sobre:
- **Candidaturas**: Ver código em `sicfaae-drh/candidaturas/`
- **Formação**: Ver código em `sicfaae-defc/formacao/`
- **API**: Ver `api_views.py` e `api_urls.py` em cada projeto
