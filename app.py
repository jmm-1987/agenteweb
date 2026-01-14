"""
Aplicación Flask principal - Sistema de Gestión de Tareas Web
"""
import os
import logging
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename
from pathlib import Path
import config
import database
import audio_pipeline
import parser

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = str(config.UPLOAD_FOLDER)

# Inicializar componentes
db = database.Database()
intent_parser = parser.IntentParser(db)


@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/api/audio/process', methods=['POST'])
def process_audio():
    """Procesa audio y devuelve transcripción + parseo"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No se recibió archivo de audio'}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'Archivo vacío'}), 400
        
        # Validar extensión
        allowed_extensions = {'.ogg', '.wav', '.mp3', '.m4a', '.webm'}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Formato no soportado: {file_ext}'}), 400
        
        # Guardar archivo temporal
        filename = secure_filename(file.filename)
        filepath = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(str(filepath))
        
        try:
            # Procesar audio
            logger.info(f"Procesando audio: {filename}")
            transcript = audio_pipeline.process_audio_from_file(str(filepath))
            
            if not transcript:
                return jsonify({'error': 'No se pudo transcribir el audio'}), 400
            
            # Parsear intención
            parsed = intent_parser.parse(transcript)
            
            return jsonify({
                'success': True,
                'transcript': transcript,
                'parsed': parsed
            })
            
        finally:
            # Limpiar archivo temporal
            if filepath.exists():
                filepath.unlink()
                
    except Exception as e:
        logger.error(f"Error procesando audio: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Obtiene lista de tareas"""
    try:
        status = request.args.get('status')
        client_id = request.args.get('client_id', type=int)
        due_date = request.args.get('due_date')
        
        tasks = db.get_tasks(status=status, client_id=client_id, due_date=due_date)
        return jsonify({'success': True, 'tasks': tasks})
    except Exception as e:
        logger.error(f"Error obteniendo tareas: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Crea una nueva tarea"""
    try:
        data = request.get_json()
        
        title = data.get('title')
        if not title:
            return jsonify({'error': 'Título requerido'}), 400
        
        client_id = data.get('client_id')
        due_date = data.get('due_date')
        priority = data.get('priority', 'normal')
        
        # Si se proporciona nombre de cliente, buscar o crear
        client_name = data.get('client_name')
        if client_name and not client_id:
            client = db.get_client_by_name(client_name)
            if not client:
                client_id = db.add_client(client_name)
            else:
                client_id = client['id']
        
        task_id = db.add_task(
            title=title,
            client_id=client_id,
            due_date=due_date,
            priority=priority
        )
        
        task = db.get_task_by_id(task_id)
        return jsonify({'success': True, 'task': task}), 201
        
    except Exception as e:
        logger.error(f"Error creando tarea: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Obtiene una tarea por ID"""
    try:
        task = db.get_task_by_id(task_id)
        if not task:
            return jsonify({'error': 'Tarea no encontrada'}), 404
        return jsonify({'success': True, 'task': task})
    except Exception as e:
        logger.error(f"Error obteniendo tarea: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Actualiza una tarea"""
    try:
        data = request.get_json()
        
        # Si se proporciona nombre de cliente, buscar o crear
        client_name = data.get('client_name')
        if client_name:
            client = db.get_client_by_name(client_name)
            if not client:
                client_id = db.add_client(client_name)
            else:
                client_id = client['id']
            data['client_id'] = client_id
            data.pop('client_name', None)
        
        success = db.update_task(task_id, **data)
        if not success:
            return jsonify({'error': 'Tarea no encontrada'}), 404
        
        task = db.get_task_by_id(task_id)
        return jsonify({'success': True, 'task': task})
        
    except Exception as e:
        logger.error(f"Error actualizando tarea: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Marca una tarea como completada"""
    try:
        success = db.complete_task(task_id)
        if not success:
            return jsonify({'error': 'Tarea no encontrada'}), 404
        
        task = db.get_task_by_id(task_id)
        return jsonify({'success': True, 'task': task})
        
    except Exception as e:
        logger.error(f"Error completando tarea: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks/<int:task_id>/ampliar', methods=['POST'])
def ampliar_task(task_id):
    """Añade ampliación a una tarea"""
    try:
        data = request.get_json()
        ampliacion = data.get('ampliacion')
        
        if not ampliacion:
            return jsonify({'error': 'Ampliación requerida'}), 400
        
        success = db.update_task(task_id, ampliacion=ampliacion)
        if not success:
            return jsonify({'error': 'Tarea no encontrada'}), 404
        
        task = db.get_task_by_id(task_id)
        return jsonify({'success': True, 'task': task})
        
    except Exception as e:
        logger.error(f"Error ampliando tarea: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients', methods=['GET'])
def get_clients():
    """Obtiene lista de clientes"""
    try:
        query = request.args.get('q')
        clients = db.search_clients(query=query)
        return jsonify({'success': True, 'clients': clients})
    except Exception as e:
        logger.error(f"Error obteniendo clientes: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients', methods=['POST'])
def create_client():
    """Crea un nuevo cliente"""
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'error': 'Nombre requerido'}), 400
        
        client_id = db.add_client(name)
        client = db.get_client_by_id(client_id)
        return jsonify({'success': True, 'client': client}), 201
        
    except Exception as e:
        logger.error(f"Error creando cliente: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    """Obtiene un cliente por ID"""
    try:
        client = db.get_client_by_id(client_id)
        if not client:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        return jsonify({'success': True, 'client': client})
    except Exception as e:
        logger.error(f"Error obteniendo cliente: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# Rutas de administración web (opcional, para gestión avanzada)
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login del panel de administración"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == config.ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_tasks'))
        return render_template('admin/login.html', error='Contraseña incorrecta')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    """Logout del panel de administración"""
    session.pop('admin', None)
    return redirect(url_for('index'))


@app.route('/admin/tasks')
def admin_tasks():
    """Panel de administración de tareas"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin/tasks.html')


@app.route('/admin/clients')
def admin_clients():
    """Panel de administración de clientes"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin/clients.html')


if __name__ == '__main__':
    # Pre-cargar modelo Whisper si está disponible
    try:
        logger.info("Pre-cargando modelo Whisper...")
        audio_pipeline.preload_model()
    except Exception as e:
        logger.warning(f"No se pudo pre-cargar modelo: {e}")
    
    # Ejecutar en desarrollo
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)

