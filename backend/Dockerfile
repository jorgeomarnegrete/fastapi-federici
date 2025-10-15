# Usa una imagen base ligera de Python
FROM python:3.11-slim

# Instala librerías de sistema necesarias
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

ENV PYTHONPATH=/app

# Copia e instala las dependencias primero
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# CLAVE: Copia todo el contenido de 'backend' al contenedor
COPY backend/ /app/backend/ 

# CLAVE: Cambia el WORKDIR para que apunte a la carpeta que contiene main.py
WORKDIR /app/backend 

# Puerto que usará el servidor Uvicorn
EXPOSE 8000

# Comando para iniciar el servidor (Busca ./main.py)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]