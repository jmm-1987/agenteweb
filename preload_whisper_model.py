"""
Script para pre-cargar el modelo Whisper durante el build
Esto evita que el primer usuario tenga que esperar la descarga del modelo
"""
import logging
import sys
import config

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Pre-cargando modelo Whisper...")
        logger.info(f"Modelo: {config.WHISPER_MODEL}")
        
        import whisper
        whisper.load_model(config.WHISPER_MODEL)
        
        logger.info("✅ Modelo pre-cargado correctamente")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error pre-cargando modelo: {e}")
        logger.warning("El modelo se cargará en el primer uso")
        # No fallar el build si no se puede pre-cargar
        return 0

if __name__ == '__main__':
    sys.exit(main())

