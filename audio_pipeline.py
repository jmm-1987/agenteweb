"""
Pipeline de procesamiento de audio
Convierte y transcribe audio usando faster-whisper
"""
import logging
import os
import subprocess
import threading
from pathlib import Path
import config

logger = logging.getLogger(__name__)

# Modelo Whisper global (carga única)
_whisper_model = None
_model_lock = threading.Lock()


def _get_whisper_model():
    """Obtiene el modelo Whisper (carga única, thread-safe)"""
    global _whisper_model
    if _whisper_model is None:
        with _model_lock:
            if _whisper_model is None:
                try:
                    import whisper
                    logger.info(f"Cargando modelo Whisper: {config.WHISPER_MODEL}")
                    _whisper_model = whisper.load_model(config.WHISPER_MODEL)
                    logger.info("Modelo Whisper cargado correctamente")
                except Exception as e:
                    logger.error(f"Error cargando modelo Whisper: {e}")
                    raise
    return _whisper_model


def convert_to_wav(input_path: str, output_path: str = None) -> str:
    """
    Convierte audio a WAV 16kHz mono usando ffmpeg
    
    Args:
        input_path: Ruta del archivo de entrada
        output_path: Ruta del archivo de salida (opcional)
    
    Returns:
        Ruta del archivo WAV generado
    """
    if output_path is None:
        output_path = str(Path(input_path).with_suffix('.wav'))
    
    try:
        # Comando ffmpeg con filtros para mejorar calidad
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ar', '16000',  # Sample rate 16kHz
            '-ac', '1',      # Mono
            '-f', 'wav',
            '-y',            # Sobrescribir si existe
            '-af', 'highpass=f=80,acompressor=threshold=0.089:ratio=9:attack=200:release=1000',
            output_path
        ]
        
        logger.info(f"Convirtiendo audio: {input_path} -> {output_path}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"Error en ffmpeg: {result.stderr}")
            raise Exception(f"Error de conversión: {result.stderr}")
        
        if not Path(output_path).exists():
            raise Exception("Archivo WAV no generado")
        
        logger.info(f"Conversión completada: {output_path}")
        return output_path
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout en conversión de audio")
        raise Exception("Timeout en conversión de audio")
    except Exception as e:
        logger.error(f"Error convirtiendo audio: {e}")
        raise


def transcribe_audio(audio_path: str, language: str = 'es') -> str:
    """
    Transcribe audio usando openai-whisper
    
    Args:
        audio_path: Ruta del archivo de audio (WAV)
        language: Código de idioma (default: 'es')
    
    Returns:
        Texto transcrito
    """
    try:
        model = _get_whisper_model()
        logger.info(f"Iniciando transcripción: {audio_path}")
        
        result = model.transcribe(
            audio_path,
            language=language,
            fp16=False  # Usar float32 para compatibilidad
        )
        
        transcript = result["text"].strip()
        logger.info(f"Transcripción completada: {len(transcript)} caracteres")
        
        if not transcript:
            logger.warning("Transcripción vacía")
            return ""
        
        return transcript
        
    except Exception as e:
        logger.error(f"Error en transcripción: {e}")
        raise


def process_audio_from_file(file_path: str, language: str = 'es') -> str:
    """
    Pipeline completo: convierte y transcribe audio
    
    Args:
        file_path: Ruta del archivo de audio original
        language: Código de idioma (default: 'es')
    
    Returns:
        Texto transcrito
    """
    wav_path = None
    try:
        # Convertir a WAV
        wav_path = convert_to_wav(file_path)
        
        # Transcribir
        transcript = transcribe_audio(wav_path, language)
        
        return transcript
        
    finally:
        # Limpiar archivo temporal WAV
        if wav_path and Path(wav_path).exists():
            try:
                os.remove(wav_path)
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal: {e}")


def preload_model():
    """Pre-carga el modelo Whisper (útil para build en Render)"""
    try:
        logger.info("Pre-cargando modelo Whisper...")
        import whisper
        whisper.load_model(config.WHISPER_MODEL)
        logger.info("Modelo pre-cargado correctamente")
    except Exception as e:
        logger.error(f"Error pre-cargando modelo: {e}")
        raise

