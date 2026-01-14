// Utilidades generales
const API_BASE = '';

function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function showError(message) {
    alert('Error: ' + message);
}

function showSuccess(message) {
    // Podríamos usar un toast notification aquí
    console.log('Success:', message);
}

// Modal
function showModal(title, message, onConfirm, onCancel) {
    const modal = document.getElementById('confirmModal');
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalMessage').textContent = message;
    
    const confirmBtn = document.getElementById('modalConfirm');
    const cancelBtn = document.getElementById('modalCancel');
    
    // Remover listeners anteriores
    const newConfirmBtn = confirmBtn.cloneNode(true);
    const newCancelBtn = cancelBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
    
    newConfirmBtn.onclick = () => {
        if (onConfirm) onConfirm();
        hideModal();
    };
    
    newCancelBtn.onclick = () => {
        if (onCancel) onCancel();
        hideModal();
    };
    
    modal.classList.add('show');
}

function hideModal() {
    document.getElementById('confirmModal').classList.remove('show');
}

// Cerrar modal al hacer click fuera
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('confirmModal');
    const closeBtn = modal.querySelector('.close');
    
    if (closeBtn) {
        closeBtn.onclick = hideModal;
    }
    
    modal.onclick = (e) => {
        if (e.target === modal) {
            hideModal();
        }
    };
});

