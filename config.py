"""
Configuración del sistema de gestión de tareas
"""
import os
from pathlib import Path

# Telegram (ya no necesario, pero mantenemos por compatibilidad)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL', '')
TELEGRAM_WEBHOOK_SECRET = os.getenv('TELEGRAM_WEBHOOK_SECRET', '')

# Aplicación
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Base de datos
# En Render, usar Persistent Disk montado en /opt/render/project/src/data
DATA_DIR = Path(os.getenv('DATA_DIR', '/opt/render/project/src/data'))
if not DATA_DIR.exists():
    # Fallback a directorio local si no existe el de Render
    DATA_DIR = Path(__file__).parent / 'data'
    DATA_DIR.mkdir(exist_ok=True)

SQLITE_PATH = os.getenv('SQLITE_PATH', str(DATA_DIR / 'app.db'))

# Audio
AUDIO_MAX_DURATION_SECONDS = int(os.getenv('AUDIO_MAX_DURATION_SECONDS', '60'))
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')  # tiny, base, small, medium
WHISPER_DEVICE = os.getenv('WHISPER_DEVICE', 'cpu')
WHISPER_COMPUTE_TYPE = os.getenv('WHISPER_COMPUTE_TYPE', 'int8')

# Google Calendar (Opcional)
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REFRESH_TOKEN = os.getenv('GOOGLE_REFRESH_TOKEN', '')
GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', '')

# Parser
FUZZY_MATCH_THRESHOLD_AUTO = float(os.getenv('FUZZY_MATCH_THRESHOLD_AUTO', '0.85'))
FUZZY_MATCH_THRESHOLD_CONFIRM = float(os.getenv('FUZZY_MATCH_THRESHOLD_CONFIRM', '0.70'))

# Uploads
UPLOAD_FOLDER = DATA_DIR / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB máximo

