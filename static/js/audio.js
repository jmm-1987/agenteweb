// Gestión de grabación de audio
let mediaRecorder = null;
let audioChunks = [];
let audioBlob = null;
var isRecording = false; // Global para acceso desde otros scripts

const recordBtn = document.getElementById('recordBtn');
const recordingStatus = document.getElementById('recordingStatus');
const audioPlayback = document.getElementById('audioPlayback');
const transcriptSection = document.getElementById('transcriptSection');
const transcriptText = document.getElementById('transcriptText');
const parsedInfo = document.getElementById('parsedInfo');

// Verificar soporte de MediaRecorder
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    recordBtn.disabled = true;
    recordBtn.innerHTML = '<span class="btn-icon">❌</span>';
    showError('Tu navegador no soporta grabación de audio');
}

// Eventos para mantener pulsado (soporta mouse y touch)
recordBtn.addEventListener('mousedown', startRecording);
recordBtn.addEventListener('touchstart', (e) => {
    e.preventDefault();
    startRecording();
});

recordBtn.addEventListener('mouseup', stopRecording);
recordBtn.addEventListener('mouseleave', stopRecording); // Si suelta fuera del botón
recordBtn.addEventListener('touchend', (e) => {
    e.preventDefault();
    stopRecording();
});
recordBtn.addEventListener('touchcancel', (e) => {
    e.preventDefault();
    stopRecording();
});

async function startRecording() {
    if (isRecording) return; // Evitar múltiples inicios
    
    try {
        isRecording = true;
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            } 
        });
        
        // Configurar MediaRecorder para OGG (mejor compresión)
        const options = {
            mimeType: 'audio/ogg;codecs=opus'
        };
        
        // Fallback si OGG no está disponible
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            options.mimeType = 'audio/webm;codecs=opus';
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = 'audio/webm';
            }
        }
        
        mediaRecorder = new MediaRecorder(stream, options);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
            audioPlayback.src = URL.createObjectURL(audioBlob);
            audioPlayback.style.display = 'block';
            
            // Procesar audio automáticamente
            processAudio();
        };
        
        mediaRecorder.start();
        
        // Actualizar UI
        recordBtn.classList.add('recording');
        recordingStatus.textContent = '🔴 Grabando... Mantén pulsado';
        recordingStatus.classList.add('recording');
        recordingStatus.style.display = 'block';
        transcriptSection.style.display = 'none';
        
    } catch (error) {
        console.error('Error iniciando grabación:', error);
        isRecording = false;
        showError('No se pudo acceder al micrófono. Verifica los permisos.');
    }
}

function stopRecording() {
    if (!isRecording || !mediaRecorder || mediaRecorder.state === 'inactive') {
        return;
    }
    
    isRecording = false;
    
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        
        // Detener stream
        if (mediaRecorder.stream) {
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        
        // Actualizar UI
        recordBtn.classList.remove('recording');
        recordingStatus.textContent = '✅ Grabación completada';
        recordingStatus.classList.remove('recording');
        
        // Ocultar después de un momento
        setTimeout(() => {
            recordingStatus.style.display = 'none';
        }, 2000);
    }
}

async function processAudio() {
    if (!audioBlob) {
        showError('No hay audio para procesar');
        return;
    }
    
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.ogg');
        
        const response = await fetch(API_BASE + '/api/audio/process', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Error procesando audio');
        }
        
        // Mostrar transcripción
        transcriptText.textContent = data.transcript || 'Sin transcripción';
        
        // Mostrar información parseada
        displayParsedInfo(data.parsed);
        
        // Mostrar sección
        transcriptSection.style.display = 'block';
        
        // Procesar intención automáticamente
        if (data.parsed && data.parsed.intent !== 'UNKNOWN') {
            handleIntent(data.parsed);
        }
        
    } catch (error) {
        console.error('Error procesando audio:', error);
        showError('Error procesando audio: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displayParsedInfo(parsed) {
    if (!parsed || parsed.intent === 'UNKNOWN') {
        parsedInfo.innerHTML = '<p>No se pudo detectar una intención clara.</p>';
        return;
    }
    
    let html = `<h4>Intención detectada: <strong>${parsed.intent}</strong></h4>`;
    
    if (parsed.entities) {
        html += '<div class="entities">';
        
        if (parsed.entities.title) {
            html += `
                <div class="entity">
                    <div class="entity-label">Título:</div>
                    <div class="entity-value">${parsed.entities.title}</div>
                </div>
            `;
        }
        
        if (parsed.entities.client) {
            const client = parsed.entities.client;
            html += `
                <div class="entity">
                    <div class="entity-label">Cliente:</div>
                    <div class="entity-value">${client.name}${client.needs_confirmation ? ' (necesita confirmación)' : ''}${client.needs_creation ? ' (nuevo cliente)' : ''}</div>
                </div>
            `;
        }
        
        if (parsed.entities.due_date) {
            html += `
                <div class="entity">
                    <div class="entity-label">Fecha:</div>
                    <div class="entity-value">${parsed.entities.due_date}</div>
                </div>
            `;
        }
        
        if (parsed.entities.priority) {
            html += `
                <div class="entity">
                    <div class="entity-label">Prioridad:</div>
                    <div class="entity-value">${parsed.entities.priority}</div>
                </div>
            `;
        }
        
        html += '</div>';
    }
    
    parsedInfo.innerHTML = html;
}

function handleIntent(parsed) {
    switch (parsed.intent) {
        case 'CREAR':
            handleCreateIntent(parsed);
            break;
        case 'LISTAR':
            handleListIntent(parsed);
            break;
        case 'CERRAR':
            handleCloseIntent(parsed);
            break;
        case 'AMPLIAR':
            handleAmpliarIntent(parsed);
            break;
        default:
            console.log('Intención no manejada:', parsed.intent);
    }
}

async function handleCreateIntent(parsed) {
    const entities = parsed.entities || {};
    
    // Verificar si necesita confirmación de cliente
    if (entities.client && entities.client.needs_confirmation) {
        showModal(
            'Confirmar Cliente',
            `¿Es correcto el cliente "${entities.client.name}"?`,
            async () => {
                await createTask(parsed);
            },
            () => {
                // Permitir edición manual
                showTaskForm(parsed);
            }
        );
        return;
    }
    
    // Si necesita crear cliente nuevo
    if (entities.client && entities.client.needs_creation) {
        showModal(
            'Nuevo Cliente',
            `¿Crear cliente "${entities.client.name}"?`,
            async () => {
                await createTask(parsed);
            },
            () => {
                showTaskForm(parsed);
            }
        );
        return;
    }
    
    // Crear directamente
    await createTask(parsed);
}

async function createTask(parsed) {
    const entities = parsed.entities || {};
    
    showLoading();
    
    try {
        const taskData = {
            title: entities.title || parsed.original_text,
            client_id: entities.client?.id,
            client_name: entities.client?.name,
            due_date: entities.due_date,
            priority: entities.priority || 'normal'
        };
        
        const response = await fetch(API_BASE + '/api/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Error creando tarea');
        }
        
        showSuccess('Tarea creada correctamente');
        
        // Recargar lista de tareas
        loadTasks();
        
    } catch (error) {
        console.error('Error creando tarea:', error);
        showError('Error creando tarea: ' + error.message);
    } finally {
        hideLoading();
    }
}

function handleListIntent(parsed) {
    loadTasks();
}

function handleCloseIntent(parsed) {
    loadTasksForClosing();
}

function handleAmpliarIntent(parsed) {
    loadTasksForAmpliar();
}

function showTaskForm(parsed) {
    // Implementar formulario de edición manual si es necesario
    console.log('Mostrar formulario de tarea:', parsed);
}

