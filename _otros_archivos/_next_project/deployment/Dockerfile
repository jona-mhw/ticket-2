# Usa una imagen base de Python
FROM python:3.11-slim

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requisitos e instala las dependencias
# Se hace por separado para aprovechar el caché de Docker si no cambian las dependencias
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia los archivos y directorios de la aplicación de forma explícita
COPY app.py .
COPY config.py .
COPY models.py .
COPY commands.py .
COPY routes ./routes
COPY templates ./templates
COPY static ./static
COPY migrations ./migrations
COPY .env.production .env
COPY auth_iap.py .


# Copia y da permisos al script de inicio
COPY startup.sh .
# Convierte line endings de Windows (CRLF) a Unix (LF) y da permisos de ejecución
RUN apt-get update && apt-get install -y dos2unix && \
    dos2unix startup.sh && \
    chmod +x startup.sh && \
    apt-get remove -y dos2unix && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Expone el puerto en el que Cloud Run escuchará
# La variable $PORT es proporcionada por el entorno de Cloud Run
EXPOSE 8080

# Define el script de inicio como el punto de entrada del contenedor
ENTRYPOINT ["/bin/bash", "/app/startup.sh"]