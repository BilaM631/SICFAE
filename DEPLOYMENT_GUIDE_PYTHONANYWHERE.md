# Guia de Implantação no PythonAnywhere

Este guia descreve passo-a-passo como hospedar o projecto SICFAAE no PythonAnywhere.com.

## Pré-requisitos
1.  Conta criada no [PythonAnywhere](https://www.pythonanywhere.com/).
2.  Código do projecto pronto (já preparei o `requirements.txt` e configurações).

## Passo 1: Carregar o Código
Como não tenho acesso directo à sua conta, você precisará carregar os arquivos:

1.  **Compactar o projecto**: No seu computador, vá à pasta `sicfaae` e crie um arquivo **ZIP** contendo todos os arquivos (incluindo `manage.py`, a pasta `SICFAAE`, `candidaturas`, `requirements.txt`, etc).
2.  **Upload**:
    *   Faça login no PythonAnywhere e vá para a aba **Files**.
    *   No directório `/home/seuusuario/`, clique em "Upload a file" e carregue o seu ZIP.
3.  **Descompactar**:
    *   Vá para a aba **Consoles** e abra um **Bash** console.
    *   Execute o comando: `unzip nome_do_arquivo.zip -d sicfaae`
    *   Isso criará uma pasta `sicfaae` com o seu código.

## Passo 2: Configurar Ambiente Virtual
No mesmo console **Bash**:

1.  Crie o ambiente virtual:
    ```bash
    mkvirtualenv --python=/usr/bin/python3.10 meu-env
    # (Ou python3.9/3.11 dependendo da sua preferência)
    ```
    *Nota: Se o comando `mkvirtualenv` não funcionar, tente `python3 -m venv myenv` e ative-o.*

2.  Instale as dependências:
    ```bash
    workon meu-env
    cd ~/sicfaae
    pip install -r requirements.txt
    ```

## Passo 3: Configurar a Web App
1.  Vá para a aba **Web**.
2.  Clique em **Add a new web app**.
3.  Escolha **Manual configuration**.
4.  Escolha a versão do Python que usou no Passo 2 (ex: 3.10).
5.  **Virtualenv**:
    *   Na secção "Virtualenv", insira o caminho: `/home/seuusuario/.virtualenvs/meu-env` (ou o caminho onde criou).
6.  **Code**:
    *   Source code: `/home/seuusuario/sicfaae`
    *   Working directory: `/home/seuusuario/sicfaae`

## Passo 4: Configurar Arquivos Estáticos
Na aba **Web**, secção **Static files**:

*   **URL**: `/static/`
*   **Directory**: `/home/seuusuario/sicfaae/staticfiles`
*   **URL**: `/media/`
*   **Directory**: `/home/seuusuario/sicfaae/media`

*Nota: O directório `staticfiles` será criado quando executarmos o comando collectstatic.*

## Passo 5: Configurar o WSGI
Ainda na aba **Web**, clique no link do arquivo **WSGI configuration file** (algo como `/var/www/seuusuario_pythonanywhere_com_wsgi.py`).
Apague tudo e coloque este código:

```python
import os
import sys

# Caminho do projecto
path = '/home/seuusuario/sicfaae'
if path not in sys.path:
    sys.path.append(path)

# Carregar variáveis de ambiente (se usar .env)
from decouple import config
# Nota: python-decouple lê arquivos .env automaticamente se estiverem na raiz do projecto.
# Certifique-se de que o arquivo .env está em /home/seuusuario/sicfaae/.env

os.environ['DJANGO_SETTINGS_MODULE'] = 'SICFAAE.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```
*Substitua "seuusuario" pelo seu nome de usuário real no PythonAnywhere.*

## Passo 6: Variáveis de Ambiente e Banco de Dados
1.  **Arquivo .env**:
    *   Vá à aba **Files**.
    *   Navegue até `sicfaae`.
    *   Crie ou edite o arquivo `.env`. Certifique-se de que tem:
        ```ini
        DEBUG=False
        SECRET_KEY=sua_chave_secreta_aqui
        ALLOWED_HOSTS=.pythonanywhere.com
        ```
2.  **Banco de Dados e Static Files**:
    *   Volte ao console **Bash**.
    *   Certifique-se de que o virtualenv está ativo (`workon meu-env`).
    *   Vá para a pasta: `cd ~/sicfaae`
    *   Agrupe arquivos estáticos:
        ```bash
        python manage.py collectstatic
        ```
    *   Execute as migrações:
        ```bash
        python manage.py migrate
        ```
    *   Crie um superusuário (para acessar o admin):
        ```bash
        python manage.py createsuperuser
        ```

## Passo 7: Finalizar
1.  Vá à aba **Web**.
2.  Clique no botão verde **Reload**.
3.  Clique no link do seu site (ex: `seuusuario.pythonanywhere.com`) para testar!

Se houver erros, verifique o **Error log** na aba Web.
