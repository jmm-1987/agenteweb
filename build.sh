#!/bin/bash
set -e

echo "🔧 Instalando dependencias del sistema..."
apt-get update -qq
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
    pkg-config

echo "📦 Actualizando pip..."
pip install --upgrade pip

echo "📥 Instalando dependencias de Python..."
pip install -r requirements.txt

echo "🤖 Pre-cargando modelo Whisper..."
python preload_whisper_model.py || echo "⚠️  Advertencia: No se pudo pre-cargar el modelo"

echo "✅ Build completado"

