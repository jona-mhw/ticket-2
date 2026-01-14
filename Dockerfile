# Usa una imagen base de Python
FROM python:3.11-slim

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requisitos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia los archivos y directorios de la aplicación
COPY app.py .
COPY config.py .
COPY models.py .
COPY commands.py .
COPY db_indexes.py .
COPY auth_iap.py .
COPY routes ./routes
COPY services ./services
COPY repositories ./repositories
COPY dto ./dto
COPY utils ./utils
COPY validators ./validators
COPY templates ./templates
COPY static ./static
COPY migrations ./migrations
COPY startup.sh .

# Convierte a formato Unix (elimina \r) y da permisos de ejecución
RUN sed -i 's/\r$//' startup.sh && chmod +x startup.sh

# Expone el puerto en el que Cloud Run escuchará
EXPOSE 8080

# Define el script de inicio como el punto de entrada del contenedor
ENTRYPOINT ["sh", "/app/startup.sh"]
