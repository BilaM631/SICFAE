# Usar imagem oficial leve do Python
FROM python:3.11-slim

# Definir variáveis de ambiente para evitar arquivos .pyc e logs em buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias para compilar pacotes Python
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivo de requerimentos e instalar
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar o restante do código
COPY . /app/

# Expor a porta 8000
EXPOSE 8000

# Comando padrão (pode ser sobrescrito pelo docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
