// ============================================================================
// CLOUD FILE MANAGER - CLIENT-SIDE JAVASCRIPT
// ============================================================================

// ============================================================================
// Modal Management
// ============================================================================

/**
 * Open a modal by ID
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        modal.style.display = 'flex';
        
        // Focus first input if exists
        const firstInput = modal.querySelector('input:not([type="hidden"])');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
}

/**
 * Close a modal by ID
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
}

/**
 * Close all open modals
 */
function closeAllModals() {
    document.querySelectorAll('.modal.active').forEach(modal => {
        modal.classList.remove('active');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    });
}

// Close modal when clicking on backdrop
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal') && e.target.classList.contains('active')) {
        closeModal(e.target.id);
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeAllModals();
    }
});

// ============================================================================
// Toast Notifications
// ============================================================================

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showToast(message, type = 'success', duration = 3000) {
    const toast = document.getElementById('toast');
    if (!toast) {
        console.warn('Toast element not found');
        return;
    }
    
    // Remove existing classes
    toast.className = 'toast';
    
    // Set message and type
    toast.textContent = message;
    toast.classList.add('show', type);
    
    // Auto-hide after duration
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

/**
 * Show success toast
 */
function showSuccess(message) {
    showToast(message, 'success');
}

/**
 * Show error toast
 */
function showError(message) {
    showToast(message, 'error', 4000);
}

/**
 * Show warning toast
 */
function showWarning(message) {
    showToast(message, 'warning');
}

/**
 * Show info toast
 */
function showInfo(message) {
    showToast(message, 'info');
}

// ============================================================================
// Password Strength Checker (Signup Page)
// ============================================================================

const passwordInput = document.getElementById('password');
if (passwordInput) {
    passwordInput.addEventListener('input', (e) => {
        const password = e.target.value;
        
        // Check length (at least 8 characters)
        const lengthReq = document.getElementById('req-length');
        if (lengthReq) {
            if (password.length >= 8) {
                lengthReq.classList.add('valid');
                lengthReq.classList.remove('invalid');
                lengthReq.style.color = 'var(--success)';
            } else {
                lengthReq.classList.remove('valid');
                lengthReq.classList.add('invalid');
                lengthReq.style.color = 'var(--text-muted)';
            }
        }
        
        // Check for uppercase letter
        const uppercaseReq = document.getElementById('req-uppercase');
        if (uppercaseReq) {
            if (/[A-Z]/.test(password)) {
                uppercaseReq.classList.add('valid');
                uppercaseReq.classList.remove('invalid');
                uppercaseReq.style.color = 'var(--success)';
            } else {
                uppercaseReq.classList.remove('valid');
                uppercaseReq.classList.add('invalid');
                uppercaseReq.style.color = 'var(--text-muted)';
            }
        }
        
        // Check for lowercase letter
        const lowercaseReq = document.getElementById('req-lowercase');
        if (lowercaseReq) {
            if (/[a-z]/.test(password)) {
                lowercaseReq.classList.add('valid');
                lowercaseReq.classList.remove('invalid');
                lowercaseReq.style.color = 'var(--success)';
            } else {
                lowercaseReq.classList.remove('valid');
                lowercaseReq.classList.add('invalid');
                lowercaseReq.style.color = 'var(--text-muted)';
            }
        }
        
        // Check for number
        const numberReq = document.getElementById('req-number');
        if (numberReq) {
            if (/[0-9]/.test(password)) {
                numberReq.classList.add('valid');
                numberReq.classList.remove('invalid');
                numberReq.style.color = 'var(--success)';
            } else {
                numberReq.classList.remove('valid');
                numberReq.classList.add('invalid');
                numberReq.style.color = 'var(--text-muted)';
            }
        }
    });
}

// ============================================================================
// Form Validation
// ============================================================================

/**
 * Validate form before submission
 */
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    let firstInvalidField = null;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.style.borderColor = 'var(--danger)';
            if (!firstInvalidField) {
                firstInvalidField = field;
            }
        } else {
            field.style.borderColor = '';
        }
    });
    
    if (!isValid && firstInvalidField) {
        firstInvalidField.focus();
        showError('Please fill in all required fields');
    }
    
    return isValid;
}

// Add validation to all forms
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', (e) => {
        if (!validateForm(form)) {
            e.preventDefault();
        }
    });
    
    // Remove error border on input
    form.querySelectorAll('input, textarea, select').forEach(field => {
        field.addEventListener('input', () => {
            field.style.borderColor = '';
        });
    });
});

// ============================================================================
// Theme Management
// ============================================================================

/**
 * Apply theme
 */
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

/**
 * Toggle theme between light and dark
 */
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
}

/**
 * Preview theme (for settings page)
 */
function previewTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    const currentTheme = document.documentElement.getAttribute('data-theme');
    
    if (savedTheme && !currentTheme) {
        applyTheme(savedTheme);
    }
});

// ============================================================================
// File Upload with Progress
// ============================================================================

/**
 * Handle file upload with visual feedback
 */
async function uploadFilesWithProgress(files, folderId, onProgress, onComplete) {
    const formData = new FormData();
    formData.append('folder_id', folderId);
    
    for (let file of files) {
        formData.append('files', file);
    }
    
    try {
        const xhr = new XMLHttpRequest();
        
        // Progress tracking
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                if (onProgress) onProgress(percent);
            }
        });
        
        // Completion
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                if (onComplete) onComplete(response);
            } else {
                showError('Upload failed');
            }
        });
        
        // Error handling
        xhr.addEventListener('error', () => {
            showError('Network error during upload');
        });
        
        xhr.open('POST', '/upload');
        xhr.send(formData);
        
    } catch (error) {
        console.error('Upload error:', error);
        showError('Error uploading files');
    }
}

// ============================================================================
// Drag and Drop File Upload
// ============================================================================

/**
 * Setup drag and drop for file upload
 */
function setupDragAndDrop(dropZone, onFilesDropped) {
    if (!dropZone) return;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });
    
    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('drag-over');
        });
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('drag-over');
        });
    });
    
    // Handle dropped files
    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0 && onFilesDropped) {
            onFilesDropped(files);
        }
    });
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Format bytes to human readable size
 */
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format date to readable string
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showSuccess('Copied to clipboard');
    } catch (err) {
        console.error('Failed to copy:', err);
        showError('Failed to copy to clipboard');
    }
}

/**
 * Confirm dialog with custom message
 */
function confirmAction(message, onConfirm, onCancel) {
    if (confirm(message)) {
        if (onConfirm) onConfirm();
    } else {
        if (onCancel) onCancel();
    }
}

// ============================================================================
// Auto-hide Alerts
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.3s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

// ============================================================================
// Loading Indicator
// ============================================================================

/**
 * Show loading indicator
 */
function showLoading(message = 'Loading...') {
    let loader = document.getElementById('loading-indicator');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'loading-indicator';
        loader.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: var(--bg-secondary);
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 10px 40px var(--shadow-lg);
            z-index: 9999;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1rem;
        `;
        document.body.appendChild(loader);
    }
    
    loader.innerHTML = `
        <div style="border: 4px solid var(--border-color); border-top: 4px solid var(--primary); border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite;"></div>
        <div style="color: var(--text-primary);">${message}</div>
    `;
    loader.style.display = 'flex';
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    const loader = document.getElementById('loading-indicator');
    if (loader) {
        loader.style.display = 'none';
    }
}

// Add spinner animation
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K: Focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-input');
        if (searchInput) searchInput.focus();
    }
    
    // Ctrl/Cmd + U: Upload files
    if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
        e.preventDefault();
        const fileInput = document.getElementById('fileInput');
        if (fileInput) fileInput.click();
    }
    
    // Ctrl/Cmd + N: New folder
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        const newFolderBtn = document.querySelector('[onclick*="newFolder"]');
        if (newFolderBtn) newFolderBtn.click();
    }
});

// ============================================================================
// API Helper Functions
// ============================================================================

/**
 * Make authenticated API request
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                ...options.headers,
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// ============================================================================
// Console Welcome Message
// ============================================================================

console.log('%c☁️ Cloud File Manager', 'font-size: 24px; font-weight: bold; color: #3b82f6; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);');
console.log('%c🔒 Secure. Private. Zero-Knowledge.', 'font-size: 14px; color: #94a3b8;');
console.log('%c📁 Your files are encrypted end-to-end', 'font-size: 12px; color: #64748b;');
console.log('%c\nKeyboard Shortcuts:', 'font-size: 12px; font-weight: bold; color: #3b82f6; margin-top: 10px;');
console.log('%c  Ctrl/Cmd + K: Focus search', 'font-size: 11px; color: #94a3b8;');
console.log('%c  Ctrl/Cmd + U: Upload files', 'font-size: 11px; color: #94a3b8;');
console.log('%c  Ctrl/Cmd + N: New folder', 'font-size: 11px; color: #94a3b8;');
console.log('%c  ESC: Close modal', 'font-size: 11px; color: #94a3b8;');

// ============================================================================
// Export functions for global use
// ============================================================================

window.cloudApp = {
    openModal,
    closeModal,
    closeAllModals,
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showLoading,
    hideLoading,
    formatBytes,
    formatDate,
    copyToClipboard,
    confirmAction,
    apiRequest,
    debounce,
    applyTheme,
    toggleTheme,
    previewTheme
};