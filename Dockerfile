# Dockerfile para Render
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update -qq && \
    apt-get install -y -qq \
    ffmpeg \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Pre-cargar modelo Whisper
RUN python preload_whisper_model.py || echo "Advertencia: No se pudo pre-cargar el modelo"

# Exponer puerto (Render inyecta PORT como variable de entorno)
EXPOSE 5000

# Comando de inicio (Render inyecta PORT automáticamente)
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 --timeout 300

