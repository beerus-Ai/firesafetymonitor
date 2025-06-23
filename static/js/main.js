/**
 * Fire Response and Monitoring System - Main JavaScript
 * Handles real-time updates, notifications, and user interactions
 */

class FireResponseSystem {
    constructor() {
        this.updateInterval = null;
        this.notificationQueue = [];
        this.isUpdating = false;
        this.lastUpdateTime = new Date();
        
        this.init();
    }
    
    init() {
        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }
    
    setup() {
        this.setupEventListeners();
        this.startRealTimeUpdates();
        this.setupNotifications();
        this.setupKeyboardShortcuts();
        this.restoreUserPreferences();
        
        console.log('Fire Response System initialized');
    }
    
    setupEventListeners() {
        // Navigation events
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action]')) {
                this.handleAction(e.target.dataset.action, e.target);
            }
        });
        
        // Form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.fire-form')) {
                this.handleFormSubmission(e);
            }
        });
        
        // Window events
        window.addEventListener('beforeunload', () => this.cleanup());
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
        
        // Visibility change for battery optimization
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });
    }
    
    startRealTimeUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        // Update every 30 seconds
        this.updateInterval = setInterval(() => {
            this.performRealTimeUpdate();
        }, 30000);
        
        // Initial update
        this.performRealTimeUpdate();
    }
    
    async performRealTimeUpdate() {
        if (this.isUpdating) return;
        
        this.isUpdating = true;
        this.showUpdateIndicator();
        
        try {
            // Update sensors
            await this.updateSensorData();
            
            // Update alerts
            await this.updateAlertData();
            
            // Update system status
            this.updateSystemStatus();
            
            this.lastUpdateTime = new Date();
            this.updateLastUpdateTime();
            
        } catch (error) {
            console.error('Real-time update failed:', error);
            this.showNotification('Connection issue - retrying...', 'warning');
        } finally {
            this.isUpdating = false;
            this.hideUpdateIndicator();
        }
    }
    
    async updateSensorData() {
        try {
            const response = await fetch('/api/sensors');
            if (!response.ok) throw new Error('Failed to fetch sensor data');
            
            const sensors = await response.json();
            this.processSensorUpdates(sensors);
            
        } catch (error) {
            console.error('Sensor update failed:', error);
        }
    }
    
    processSensorUpdates(sensors) {
        let onlineCount = 0;
        
        sensors.forEach(sensor => {
            const statusElement = document.querySelector(`#sensor-status-${sensor.id}`);
            const readingElement = document.querySelector(`#sensor-reading-${sensor.id}`);
            const cardElement = document.querySelector(`[data-sensor-id="${sensor.id}"]`);
            
            if (statusElement) {
                const wasOnline = statusElement.classList.contains('bg-success');
                const isOnline = sensor.is_online;
                
                if (isOnline !== wasOnline) {
                    // Status changed - animate
                    this.animateStatusChange(statusElement, isOnline);
                }
                
                statusElement.textContent = isOnline ? 'Online' : 'Offline';
                statusElement.className = `badge bg-${isOnline ? 'success' : 'danger'}`;
                
                if (isOnline) onlineCount++;
            }
            
            if (readingElement && sensor.last_reading !== null) {
                const oldValue = parseFloat(readingElement.textContent) || 0;
                const newValue = sensor.last_reading;
                
                if (Math.abs(oldValue - newValue) > 0.1) {
                    this.animateValueChange(readingElement, oldValue, newValue);
                }
                
                readingElement.textContent = newValue.toFixed(2);
                
                // Check threshold
                if (newValue > sensor.threshold) {
                    readingElement.className = 'text-danger fw-bold';
                } else {
                    readingElement.className = '';
                }
            }
            
            if (cardElement) {
                // Update card appearance based on sensor status
                if (sensor.is_online) {
                    cardElement.classList.remove('border-danger');
                    cardElement.classList.add('border-success');
                } else {
                    cardElement.classList.remove('border-success');
                    cardElement.classList.add('border-danger');
                }
            }
        });
        
        // Update global online sensor count
        const onlineSensorsElement = document.querySelector('#online-sensors');
        if (onlineSensorsElement) {
            onlineSensorsElement.textContent = onlineCount;
        }
    }
    
    async updateAlertData() {
        try {
            const response = await fetch('/api/alerts?limit=10');
            if (!response.ok) throw new Error('Failed to fetch alert data');
            
            const alerts = await response.json();
            this.processAlertUpdates(alerts);
            
        } catch (error) {
            console.error('Alert update failed:', error);
        }
    }
    
    processAlertUpdates(alerts) {
        const activeAlerts = alerts.filter(alert => alert.status === 'active');
        const activeAlertsElement = document.querySelector('#active-alerts-count');
        
        if (activeAlertsElement) {
            const currentCount = parseInt(activeAlertsElement.textContent) || 0;
            const newCount = activeAlerts.length;
            
            if (newCount > currentCount) {
                // New alert detected
                this.showNotification(`${newCount - currentCount} new fire alert(s) detected!`, 'danger');
                this.playAlertSound();
            }
            
            activeAlertsElement.textContent = newCount;
        }
        
        // Update recent alerts list if present
        this.updateRecentAlertsList(alerts.slice(0, 5));
    }
    
    updateRecentAlertsList(alerts) {
        const alertsList = document.querySelector('#recent-alerts-list');
        if (!alertsList) return;
        
        if (alerts.length === 0) {
            alertsList.innerHTML = `
                <div class="text-center py-4">
                    <i data-feather="check-circle" width="48" height="48" class="text-success mb-3"></i>
                    <h5>No Active Alerts</h5>
                    <p class="text-muted">All systems are operating normally.</p>
                </div>
            `;
            feather.replace();
            return;
        }
        
        const alertsHTML = alerts.map(alert => this.generateAlertHTML(alert)).join('');
        alertsList.innerHTML = alertsHTML;
        feather.replace();
    }
    
    generateAlertHTML(alert) {
        const severityClass = this.getSeverityClass(alert.severity);
        const statusClass = alert.status === 'active' ? 'danger' : 'success';
        
        return `
            <div class="list-group-item d-flex justify-content-between align-items-start alert-${alert.severity}">
                <div class="ms-2 me-auto">
                    <div class="fw-bold">${this.escapeHtml(alert.title)}</div>
                    <small class="text-muted">
                        ${new Date(alert.created_at).toLocaleString()}
                        ${alert.address ? '| ' + this.escapeHtml(alert.address) : ''}
                    </small>
                    ${alert.description ? `<p class="mb-1 small">${this.escapeHtml(alert.description.substring(0, 100))}${alert.description.length > 100 ? '...' : ''}</p>` : ''}
                </div>
                <div class="text-end">
                    <span class="badge bg-${severityClass} mb-1">
                        ${alert.severity.charAt(0).toUpperCase() + alert.severity.slice(1)}
                    </span>
                    <br>
                    ${alert.status === 'active' ? `
                        <button class="btn btn-success btn-sm" onclick="fireSystem.resolveAlert(${alert.id})" title="Resolve Alert">
                            <i data-feather="check" width="16" height="16"></i>
                        </button>
                        <button class="btn btn-primary btn-sm" onclick="fireSystem.getNavigation(${alert.id})" title="Get Navigation">
                            <i data-feather="navigation" width="16" height="16"></i>
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    updateSystemStatus() {
        const statusElements = {
            sensors: document.querySelector('#sensor-status'),
            sms: document.querySelector('#sms-status'),
            email: document.querySelector('#email-status')
        };
        
        // Update based on last successful operations
        Object.entries(statusElements).forEach(([key, element]) => {
            if (element) {
                element.className = 'fs-4 text-success';
            }
        });
    }
    
    setupNotifications() {
        // Create notification container if it doesn't exist
        if (!document.querySelector('.toast-container')) {
            const container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
    
    showNotification(message, type = 'info', duration = 5000) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${this.escapeHtml(message)}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        // Add to container
        document.querySelector('.toast-container').appendChild(toast);
        
        // Initialize and show
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();
        
        // Clean up after hide
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
        
        // Browser notification for critical alerts
        if (type === 'danger' && 'Notification' in window && Notification.permission === 'granted') {
            new Notification('Fire Alert', {
                body: message,
                icon: '/static/favicon.ico',
                tag: 'fire-alert'
            });
        }
    }
    
    showUpdateIndicator() {
        let indicator = document.querySelector('.update-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'update-indicator';
            indicator.innerHTML = '<i data-feather="refresh-cw" width="16" height="16" class="me-2"></i>Updating...';
            document.body.appendChild(indicator);
            feather.replace();
        }
        
        indicator.classList.add('show');
    }
    
    hideUpdateIndicator() {
        const indicator = document.querySelector('.update-indicator');
        if (indicator) {
            indicator.classList.remove('show');
        }
    }
    
    updateLastUpdateTime() {
        const timeElement = document.querySelector('#last-update');
        if (timeElement) {
            timeElement.textContent = this.lastUpdateTime.toLocaleTimeString();
        }
    }
    
    animateStatusChange(element, isOnline) {
        element.style.transform = 'scale(1.2)';
        element.style.transition = 'transform 0.3s ease';
        
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 300);
    }
    
    animateValueChange(element, oldValue, newValue) {
        element.style.transform = 'scale(1.1)';
        element.style.transition = 'transform 0.2s ease';
        
        if (newValue > oldValue) {
            element.style.color = 'var(--fire-danger)';
        } else {
            element.style.color = 'var(--fire-success)';
        }
        
        setTimeout(() => {
            element.style.transform = 'scale(1)';
            element.style.color = '';
        }, 200);
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + R: Refresh data
            if ((e.ctrlKey || e.metaKey) && e.key === 'r' && !e.shiftKey) {
                e.preventDefault();
                this.performRealTimeUpdate();
            }
            
            // Escape: Close modals
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.modal.show');
                modals.forEach(modal => {
                    bootstrap.Modal.getInstance(modal)?.hide();
                });
            }
        });
    }
    
    restoreUserPreferences() {
        // Restore notification preferences
        const notificationPref = localStorage.getItem('fire-system-notifications');
        if (notificationPref === 'disabled') {
            this.notificationsEnabled = false;
        }
        
        // Restore update interval preference
        const updateInterval = localStorage.getItem('fire-system-update-interval');
        if (updateInterval) {
            this.setUpdateInterval(parseInt(updateInterval));
        }
    }
    
    setUpdateInterval(seconds) {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        this.updateInterval = setInterval(() => {
            this.performRealTimeUpdate();
        }, seconds * 1000);
        
        localStorage.setItem('fire-system-update-interval', seconds.toString());
    }
    
    pauseUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    resumeUpdates() {
        if (!this.updateInterval) {
            this.startRealTimeUpdates();
        }
    }
    
    handleOnline() {
        this.showNotification('Connection restored', 'success');
        this.resumeUpdates();
    }
    
    handleOffline() {
        this.showNotification('Connection lost - working offline', 'warning');
        this.pauseUpdates();
    }
    
    async resolveAlert(alertId) {
        if (!confirm('Are you sure you want to resolve this alert?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/alerts/${alertId}/resolve`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Alert resolved successfully', 'success');
                this.performRealTimeUpdate();
            } else {
                this.showNotification('Failed to resolve alert: ' + data.error, 'danger');
            }
        } catch (error) {
            this.showNotification('Error resolving alert', 'danger');
        }
    }
    
    getNavigation(alertId) {
        if (!navigator.geolocation) {
            this.showNotification('Geolocation is not supported by this browser', 'warning');
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const location = `${position.coords.latitude},${position.coords.longitude}`;
                
                try {
                    const response = await fetch(`/api/alerts/${alertId}/navigation?location=${location}`);
                    const data = await response.json();
                    
                    if (data.route_to_alert) {
                        this.showNavigationModal(data);
                    } else {
                        this.showNotification('Navigation information not available', 'warning');
                    }
                } catch (error) {
                    this.showNotification('Error getting navigation', 'danger');
                }
            },
            () => {
                this.showNotification('Unable to get your location for navigation', 'warning');
            }
        );
    }
    
    showNavigationModal(navigationData) {
        const { alert, route_to_alert, nearest_fire_stations } = navigationData;
        
        const modalHTML = `
            <div class="modal fade" id="navigationModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Navigation to Alert</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Alert Details</h6>
                                    <p><strong>${alert.title}</strong></p>
                                    <p class="text-muted">${alert.address}</p>
                                    <span class="badge bg-${this.getSeverityClass(alert.severity)}">${alert.severity}</span>
                                </div>
                                <div class="col-md-6">
                                    <h6>Route Information</h6>
                                    <p><strong>Distance:</strong> ${route_to_alert.distance}</p>
                                    <p><strong>Duration:</strong> ${route_to_alert.duration}</p>
                                    ${route_to_alert.duration_in_traffic ? `<p><strong>With Traffic:</strong> ${route_to_alert.duration_in_traffic}</p>` : ''}
                                </div>
                            </div>
                            ${nearest_fire_stations && nearest_fire_stations.length > 0 ? `
                                <hr>
                                <h6>Nearest Fire Station</h6>
                                <p><strong>${nearest_fire_stations[0].name}</strong></p>
                                <p class="text-muted">${nearest_fire_stations[0].address}</p>
                            ` : ''}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="fireSystem.openInMaps(${alert.latitude}, ${alert.longitude})">
                                Open in Maps
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = document.querySelector('#navigationModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Show modal
        const modal = new bootstrap.Modal(document.querySelector('#navigationModal'));
        modal.show();
    }
    
    openInMaps(latitude, longitude) {
        const mapsUrl = `https://www.google.com/maps/dir//${latitude},${longitude}`;
        window.open(mapsUrl, '_blank');
    }
    
    playAlertSound() {
        // Create audio context for alert sound
        if (typeof AudioContext !== 'undefined' || typeof webkitAudioContext !== 'undefined') {
            try {
                const audioContext = new (AudioContext || webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2);
                
                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.3);
            } catch (error) {
                console.warn('Could not play alert sound:', error);
            }
        }
    }
    
    getSeverityClass(severity) {
        const classes = {
            critical: 'danger',
            high: 'warning',
            medium: 'info',
            low: 'success'
        };
        return classes[severity] || 'secondary';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    cleanup() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Global utility functions for backward compatibility
window.showAlert = function(message, type = 'info') {
    if (window.fireSystem) {
        window.fireSystem.showNotification(message, type);
    }
};

window.testNotifications = function() {
    fetch('/api/test-notifications')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Test notifications sent successfully!', 'success');
            } else {
                showAlert('Failed to send test notifications: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            showAlert('Error testing notifications', 'danger');
        });
};

// Initialize the system
window.fireSystem = new FireResponseSystem();

// Service Worker registration for offline support
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
        .then(() => console.log('Service Worker registered'))
        .catch(error => console.warn('Service Worker registration failed:', error));
}
