# Sistema de Gestión de Tareas Web

Sistema completo de gestión de tareas que funciona mediante **comandos de voz** a través de una **interfaz web móvil**. Permite crear, listar, cerrar y gestionar tareas usando comandos de voz naturales en español.

## 🚀 Características Principales

- 🎤 **Interacción por voz**: Todo se gestiona mediante grabación de audio en el navegador
- 🧠 **Transcripción local**: Usa `faster-whisper` para transcribir audio sin APIs externas
- 📝 **Parser inteligente**: Detecta intenciones y extrae información usando reglas, regex y fuzzy matching
- 👥 **Gestión de clientes**: Identificación automática de clientes con coincidencia difusa
- 📅 **Fechas inteligentes**: Reconocimiento de fechas relativas ("mañana", "el lunes", etc.)
- 🌐 **Interfaz web móvil**: Diseño responsive optimizado para móviles
- 💾 **SQLite**: Base de datos ligera y portable

## 📋 Requisitos

- Python 3.11+
- ffmpeg instalado en el sistema
- Navegador moderno con soporte para MediaRecorder API

## 🛠️ Instalación Local

1. **Clonar el repositorio**
```bash
git clone <tu-repositorio>
cd agenteweb
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Instalar ffmpeg**
- **Windows**: Descargar de https://ffmpeg.org/download.html
- **Linux**: `sudo apt-get install ffmpeg`
- **macOS**: `brew install ffmpeg`

5. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus valores
```

6. **Ejecutar aplicación**
```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

## 🚀 Despliegue en Render

### Configuración Básica

1. **Crear servicio Web en Render**
   - Conectar repositorio Git
   - Seleccionar tipo: Web Service
   - Environment: Python 3

2. **Configurar variables de entorno**
   - `ADMIN_PASSWORD`: Contraseña para panel de administración
   - `SECRET_KEY`: Clave secreta aleatoria (Render puede generarla)
   - `WHISPER_MODEL`: `base` (recomendado para free tier)
   - `DATA_DIR`: `/opt/render/project/src/data`
   - `SQLITE_PATH`: `/opt/render/project/src/data/app.db`

3. **Activar Persistent Disk** (IMPORTANTE)
   - En la configuración del servicio
   - Añadir disco persistente
   - Montar en: `/opt/render/project/src/data`
   - Tamaño mínimo: 1GB

4. **Build y Start Commands**
   - Build: Se configura automáticamente desde `render.yaml`
   - Start: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 300`

### Optimizaciones para Render Free Tier

- **Modelo Whisper**: Usar `base` (no `small` o superior)
- **Compute Type**: `int8` (menos memoria)
- **Workers**: 2 workers con 4 threads cada uno
- **Timeout**: 300 segundos (5 minutos) para procesamiento de audio

## 📱 Uso

### Crear Tarea por Voz

1. Hacer clic en el botón "🎙️ Grabar"
2. Decir algo como: *"Crear tarea llamar al cliente Alditraex mañana"*
3. Detener la grabación
4. El sistema transcribe y crea la tarea automáticamente

### Comandos de Voz Soportados

**Crear Tarea:**
- "Crear tarea llamar al cliente X mañana"
- "Tarea urgente para el cliente Y el lunes"
- "Recordar reunión con cliente Z el viernes"

**Listar Tareas:**
- "Listar tareas pendientes"
- "Mostrar tareas de hoy"
- "Tareas de mañana"

**Cerrar Tarea:**
- "Da por hecha la tarea del cliente X"
- "Completar tarea llamar cliente Y"

**Ampliar Tarea:**
- Usar el botón "📝 Ampliar Tareas" y grabar audio con más información

### Acciones Rápidas

- **📋 Ver Tareas**: Muestra todas las tareas pendientes
- **✅ Cerrar Tareas**: Permite marcar tareas como completadas
- **📝 Ampliar Tareas**: Añade información adicional a tareas existentes

## 🏗️ Arquitectura

```
Frontend (HTML/JS)
    ↓
Flask API REST (/api/*)
    ↓
┌───────────┬───────────┬───────────┐
│  Audio    │  Parser   │ Database  │
│ Pipeline  │ (parser)  │ (SQLite)  │
└───────────┴───────────┴───────────┘
```

## 📁 Estructura del Proyecto

```
agenteweb/
├── app.py                 # Aplicación Flask principal
├── config.py              # Configuración
├── database.py            # Gestión de base de datos
├── audio_pipeline.py      # Procesamiento de audio
├── parser.py              # Parser de intenciones
├── preload_whisper_model.py  # Pre-carga del modelo
├── requirements.txt       # Dependencias Python
├── render.yaml           # Configuración Render
├── .env.example          # Ejemplo de variables de entorno
├── templates/            # Templates HTML
│   ├── base.html
│   └── index.html
└── static/               # Archivos estáticos
    ├── css/
    │   └── style.css
    └── js/
        ├── main.js
        ├── audio.js
        └── tasks.js
```

## 🔧 Configuración Avanzada

### Variables de Entorno

- `ADMIN_PASSWORD`: Contraseña del panel de administración
- `SECRET_KEY`: Clave secreta para sesiones Flask
- `WHISPER_MODEL`: Modelo Whisper (`tiny`, `base`, `small`, `medium`)
- `WHISPER_DEVICE`: Dispositivo (`cpu` o `cuda`)
- `WHISPER_COMPUTE_TYPE`: Tipo de computación (`int8`, `float16`, `float32`)
- `SQLITE_PATH`: Ruta de la base de datos
- `AUDIO_MAX_DURATION_SECONDS`: Duración máxima de audio (default: 60s)

### Parser

- `FUZZY_MATCH_THRESHOLD_AUTO`: Umbral para selección automática de cliente (default: 0.85)
- `FUZZY_MATCH_THRESHOLD_CONFIRM`: Umbral para pedir confirmación (default: 0.70)

## 🐛 Troubleshooting

### Error: "No se pudo acceder al micrófono"
- Verificar permisos del navegador
- Usar HTTPS en producción (requerido para MediaRecorder)

### Error: "Out of Memory" en Render
- Reducir `WHISPER_MODEL` a `base` o `tiny`
- Verificar que se use `int8` como compute type
- Reducir número de workers

### Base de datos no persiste
- Verificar que Persistent Disk esté activado en Render
- Verificar que `DATA_DIR` y `SQLITE_PATH` apunten al disco persistente

## 📝 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.

