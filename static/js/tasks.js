// Gestión de tareas
const tasksSection = document.getElementById('tasksSection');
const tasksList = document.getElementById('tasksList');
const showTasksBtn = document.getElementById('showTasksBtn');
const closeTasksBtn = document.getElementById('closeTasksBtn');
const ampliarTasksBtn = document.getElementById('ampliarTasksBtn');

showTasksBtn.addEventListener('click', loadTasks);
closeTasksBtn.addEventListener('click', loadTasksForClosing);
ampliarTasksBtn.addEventListener('click', loadTasksForAmpliar);

async function loadTasks(status = 'pending') {
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/api/tasks?status=${status}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Error cargando tareas');
        }
        
        displayTasks(data.tasks || []);
        tasksSection.style.display = 'block';
        
        // Scroll a la sección
        tasksSection.scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('Error cargando tareas:', error);
        showError('Error cargando tareas: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displayTasks(tasks) {
    if (tasks.length === 0) {
        tasksList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <p>No hay tareas pendientes</p>
            </div>
        `;
        return;
    }
    
    tasksList.innerHTML = tasks.map(task => createTaskHTML(task)).join('');
    
    // Agregar event listeners a los botones
    tasks.forEach(task => {
        const completeBtn = document.getElementById(`complete-${task.id}`);
        if (completeBtn) {
            completeBtn.addEventListener('click', () => completeTask(task.id));
        }
        
        const ampliarBtn = document.getElementById(`ampliar-${task.id}`);
        if (ampliarBtn) {
            ampliarBtn.addEventListener('click', () => ampliarTask(task.id));
        }
    });
}

function createTaskHTML(task) {
    const dueDate = task.due_date ? formatDate(task.due_date) : 'Sin fecha';
    const clientName = task.client_name || 'Sin cliente';
    const priority = task.priority || 'normal';
    
    return `
        <div class="task-item ${task.status === 'completed' ? 'completed' : ''}">
            <div class="task-header">
                <div class="task-title">
                    ${escapeHtml(task.title)}
                    <span class="task-id">#${task.id}</span>
                </div>
            </div>
            <div class="task-meta">
                <span class="badge badge-client">👤 ${escapeHtml(clientName)}</span>
                <span class="badge badge-date">📅 ${dueDate}</span>
                <span class="badge badge-priority ${priority}">⚡ ${priority}</span>
            </div>
            ${task.ampliacion ? `<div style="margin-top: 0.75rem; padding: 0.875rem; background: #fee2e2; border-radius: 8px; border-left: 3px solid #dc2626; font-size: 0.95rem;">
                <strong style="color: #dc2626;">Ampliación:</strong> ${escapeHtml(task.ampliacion)}
            </div>` : ''}
            ${task.status === 'pending' ? `
                <div class="task-actions">
                    <button class="btn btn-primary" id="complete-${task.id}">✅ Completar</button>
                    <button class="btn btn-outline" id="ampliar-${task.id}">📝 Ampliar</button>
                </div>
            ` : ''}
        </div>
    `;
}

function formatDate(dateString) {
    if (!dateString) return 'Sin fecha';
    
    try {
        const date = new Date(dateString);
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        
        if (date.toDateString() === today.toDateString()) {
            return 'Hoy';
        } else if (date.toDateString() === tomorrow.toDateString()) {
            return 'Mañana';
        }
        
        return date.toLocaleDateString('es-ES', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric' 
        });
    } catch (e) {
        return dateString;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function completeTask(taskId) {
    showModal(
        'Confirmar',
        '¿Marcar esta tarea como completada?',
        async () => {
            showLoading();
            
            try {
                const response = await fetch(`${API_BASE}/api/tasks/${taskId}/complete`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Error completando tarea');
                }
                
                showSuccess('Tarea completada');
                loadTasks();
                
            } catch (error) {
                console.error('Error completando tarea:', error);
                showError('Error completando tarea: ' + error.message);
            } finally {
                hideLoading();
            }
        }
    );
}

async function loadTasksForClosing() {
    await loadTasks('pending');
}

async function loadTasksForAmpliar() {
    await loadTasks('pending');
}

async function ampliarTask(taskId) {
    // Pedir audio para ampliar
    showModal(
        'Ampliar Tarea',
        'Mantén pulsado el botón de micrófono y graba la ampliación de la tarea',
        async () => {
            // Mostrar mensaje de instrucciones
            showSuccess('Mantén pulsado el botón de micrófono para grabar');
            
            // Esperar a que termine la grabación y procesar
            const checkRecording = setInterval(() => {
                if (!isRecording && audioBlob) {
                    clearInterval(checkRecording);
                    processAmpliarAudio(taskId);
                }
            }, 500);
            
            // Timeout de seguridad (60 segundos)
            setTimeout(() => {
                clearInterval(checkRecording);
            }, 60000);
        }
    );
}

async function processAmpliarAudio(taskId) {
    if (!audioBlob) {
        showError('No hay audio para procesar');
        return;
    }
    
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'ampliar.ogg');
        
        const response = await fetch(API_BASE + '/api/audio/process', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Error procesando audio');
        }
        
        // Guardar ampliación
        const ampliarResponse = await fetch(`${API_BASE}/api/tasks/${taskId}/ampliar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ampliacion: data.transcript
            })
        });
        
        const ampliarData = await ampliarResponse.json();
        
        if (!ampliarResponse.ok) {
            throw new Error(ampliarData.error || 'Error guardando ampliación');
        }
        
        showSuccess('Ampliación guardada');
        loadTasks();
        
    } catch (error) {
        console.error('Error procesando ampliación:', error);
        showError('Error procesando ampliación: ' + error.message);
    } finally {
        hideLoading();
    }
}

