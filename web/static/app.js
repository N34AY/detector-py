/**
 * Person Detection Web Interface
 * Clean, modular JavaScript for camera feed and ROI management
 */

class DetectorWebUI {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.roiCanvas = null;
        this.roiCanvasCtx = null;
        this.currentROIs = [];
        this.roiDrawing = false;
        this.roiStart = { x: 0, y: 0 };
        this.roiEnd = { x: 0, y: 0 };
        
        // Sound settings
        this.soundEnabled = true;
        this.motionSoundVolume = 0.5;
        this.lastDetectionTime = 0;
        this.soundCooldown = 2000; // 2 seconds between sounds
        
        this.init();
    }
    
    init() {
        document.addEventListener('DOMContentLoaded', () => {
            console.log('DetectorWebUI initializing...');
            this.initializeSocket();
            this.setupCameraInteraction();
            this.initializeROICanvas();
            this.initializeSoundSettings();
            this.loadMotionConfig();
            this.refreshData();
            
            // Auto-refresh data
            setInterval(() => this.refreshStatus(), 5000);
            setInterval(() => this.refreshROIs(), 10000);
            
            // Check if system needs initialization
            setTimeout(() => {
                const cameraStatus = document.getElementById('cameraStatus');
                if (cameraStatus && cameraStatus.textContent === 'Disconnected') {
                    console.log('System appears to need initialization');
                    this.showAlert('Click "Initialize System" to start the detection system', 'info');
                }
            }, 2000);
        });
    }
    
    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.isConnected = true;
            this.updateConnectionStatus(true);
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.isConnected = false;
            this.updateConnectionStatus(false);
        });
        
        this.socket.on('frame_update', (data) => {
            console.log('Frame update received', {
                hasFrame: !!data.frame,
                frameSize: data.frame ? data.frame.length : 0,
                stats: data.stats
            });
            this.updateCameraFeed(data.frame);
            this.updateStats(data.stats);
            this.updateRainStatus(data.stats);
        });
    }
    
    initializeROICanvas() {
        this.roiCanvas = document.getElementById('roiCanvas');
        if (this.roiCanvas) {
            this.roiCanvasCtx = this.roiCanvas.getContext('2d');
            console.log('ROI Canvas initialized');
            
            // Ensure canvas is positioned correctly
            this.roiCanvas.style.position = 'absolute';
            this.roiCanvas.style.top = '0';
            this.roiCanvas.style.left = '0';
            this.roiCanvas.style.pointerEvents = 'none';
            this.roiCanvas.style.zIndex = '10';
        } else {
            console.error('ROI Canvas not found');
        }
    }
    
    setupCameraInteraction() {
        const cameraContainer = document.getElementById('cameraContainer');
        if (!cameraContainer) {
            console.error('Camera container not found');
            return;
        }
        
        let isDrawing = false;
        let startX, startY;
        
        cameraContainer.addEventListener('mousedown', (e) => {
            const img = document.getElementById('cameraFeed');
            if (!img || e.target.id !== 'cameraFeed') return;
            
            // Ensure image is loaded
            if (!img.naturalWidth || !img.naturalHeight) {
                console.log('Image not fully loaded yet');
                return;
            }
            
            isDrawing = true;
            const rect = img.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
            
            // Convert to image coordinates
            const scaleX = img.naturalWidth / rect.width;
            const scaleY = img.naturalHeight / rect.height;
            
            this.roiStart = {
                x: Math.round(startX * scaleX),
                y: Math.round(startY * scaleY)
            };
            
            console.log('ROI start:', this.roiStart);
            e.preventDefault();
        });
        
        cameraContainer.addEventListener('mousemove', (e) => {
            if (!isDrawing) return;
            
            const img = document.getElementById('cameraFeed');
            if (!img) return;
            
            const rect = img.getBoundingClientRect();
            const currentX = e.clientX - rect.left;
            const currentY = e.clientY - rect.top;
            
            // Convert to image coordinates
            const scaleX = img.naturalWidth / rect.width;
            const scaleY = img.naturalHeight / rect.height;
            
            this.roiEnd = {
                x: Math.round(currentX * scaleX),
                y: Math.round(currentY * scaleY)
            };
            
            this.drawTemporaryROI();
        });
        
        cameraContainer.addEventListener('mouseup', (e) => {
            if (!isDrawing) return;
            
            isDrawing = false;
            
            console.log('ROI end:', this.roiEnd);
            
            // Create ROI if valid size
            const width = Math.abs(this.roiEnd.x - this.roiStart.x);
            const height = Math.abs(this.roiEnd.y - this.roiStart.y);
            
            console.log('ROI dimensions:', width, 'x', height);
            
            if (width > 50 && height > 50) {
                const x1 = Math.min(this.roiStart.x, this.roiEnd.x);
                const y1 = Math.min(this.roiStart.y, this.roiEnd.y);
                const x2 = Math.max(this.roiStart.x, this.roiEnd.x);
                const y2 = Math.max(this.roiStart.y, this.roiEnd.y);
                
                console.log('Creating ROI:', x1, y1, x2, y2);
                this.addROI(x1, y1, x2, y2);
            } else {
                console.log('ROI too small, not creating');
            }
            
            this.clearTemporaryROI();
        });
        
        // Prevent context menu on right click
        cameraContainer.addEventListener('contextmenu', (e) => {
            e.preventDefault();
        });
        
        console.log('Camera interaction setup complete');
    }
    
    drawTemporaryROI() {
        if (!this.roiCanvasCtx) {
            console.log('No canvas context available');
            return;
        }
        
        this.clearTemporaryROI();
        
        const canvas = this.roiCanvas;
        const img = document.getElementById('cameraFeed');
        
        if (!img || !img.naturalWidth || !img.naturalHeight) {
            console.log('Image not loaded yet');
            return;
        }
        
        // Set canvas size to match image display size
        const rect = img.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        
        // Calculate scale from image coordinates to display coordinates
        const scaleX = rect.width / img.naturalWidth;
        const scaleY = rect.height / img.naturalHeight;
        
        const x1 = this.roiStart.x * scaleX;
        const y1 = this.roiStart.y * scaleY;
        const x2 = this.roiEnd.x * scaleX;
        const y2 = this.roiEnd.y * scaleY;
        
        this.roiCanvasCtx.strokeStyle = '#00ff00';
        this.roiCanvasCtx.lineWidth = 3;
        this.roiCanvasCtx.setLineDash([5, 5]);
        this.roiCanvasCtx.strokeRect(
            Math.min(x1, x2),
            Math.min(y1, y2),
            Math.abs(x2 - x1),
            Math.abs(y2 - y1)
        );
        
        // Add temporary label
        this.roiCanvasCtx.fillStyle = '#00ff00';
        this.roiCanvasCtx.font = '14px Arial';
        this.roiCanvasCtx.fillText('New ROI', Math.min(x1, x2), Math.min(y1, y2) - 5);
    }
    
    clearTemporaryROI() {
        if (this.roiCanvasCtx) {
            this.roiCanvasCtx.clearRect(0, 0, this.roiCanvas.width, this.roiCanvas.height);
        }
    }
    
    drawAllROIs() {
        if (!this.roiCanvasCtx || !this.currentROIs.length) {
            return;
        }
        
        const canvas = this.roiCanvas;
        const img = document.getElementById('cameraFeed');
        
        if (!img || !img.naturalWidth || !img.naturalHeight) {
            return;
        }
        
        // Clear canvas first
        this.roiCanvasCtx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Set canvas size to match image display size
        const rect = img.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        
        // Calculate scale from image coordinates to display coordinates
        const scaleX = rect.width / img.naturalWidth;
        const scaleY = rect.height / img.naturalHeight;
        
        // Draw each ROI
        this.currentROIs.forEach(roi => {
            const x1 = roi.x1 * scaleX;
            const y1 = roi.y1 * scaleY;
            const x2 = roi.x2 * scaleX;
            const y2 = roi.y2 * scaleY;
            
            // Color based on motion detection
            if (roi.motion_detected) {
                this.roiCanvasCtx.strokeStyle = '#ff0000'; // Red for motion
                this.roiCanvasCtx.lineWidth = 3;
                this.roiCanvasCtx.setLineDash([]);
            } else {
                this.roiCanvasCtx.strokeStyle = '#ffff00'; // Yellow for monitoring
                this.roiCanvasCtx.lineWidth = 2;
                this.roiCanvasCtx.setLineDash([]);
            }
            
            // Draw rectangle
            this.roiCanvasCtx.strokeRect(
                Math.min(x1, x2),
                Math.min(y1, y2),
                Math.abs(x2 - x1),
                Math.abs(y2 - y1)
            );
            
            // Add label with background
            const label = roi.motion_detected ? `ROI ${roi.id} - MOTION!` : `ROI ${roi.id}`;
            this.roiCanvasCtx.fillStyle = roi.motion_detected ? '#ff0000' : '#ffff00';
            this.roiCanvasCtx.font = '14px Arial';
            
            // Measure text and draw background
            const textMetrics = this.roiCanvasCtx.measureText(label);
            const textX = Math.min(x1, x2);
            const textY = Math.min(y1, y2) - 5;
            
            this.roiCanvasCtx.fillRect(textX, textY - 18, textMetrics.width + 10, 20);
            
            // Draw text
            this.roiCanvasCtx.fillStyle = '#000000';
            this.roiCanvasCtx.fillText(label, textX + 5, textY - 5);
        });
    }
    
    updateCameraFeed(frameData) {
        const img = document.getElementById('cameraFeed');
        if (img && frameData) {
            img.src = 'data:image/jpeg;base64,' + frameData;
            
            // Ensure canvas is sized correctly when image loads and draw ROIs
            img.onload = () => {
                if (this.roiCanvas) {
                    const rect = img.getBoundingClientRect();
                    this.roiCanvas.width = rect.width;
                    this.roiCanvas.height = rect.height;
                    console.log('Canvas resized to:', rect.width, 'x', rect.height);
                    
                    // Draw all ROIs on the canvas
                    this.drawAllROIs();
                }
            };
        }
    }
    
    updateStats(stats) {
        if (!stats) return;
        
        this.updateElement('cameraStatus', 
            stats.camera_status.charAt(0).toUpperCase() + stats.camera_status.slice(1));
        this.updateElement('fpsCounter', Math.round(stats.fps || 0));
        this.updateElement('detectionCount', stats.total_detections || 0);
        
        // Check for detections and play sounds
        this.checkForDetectionSounds(stats);
        
        // Update ROI motion status
        if (stats.motion_detected_rois && this.currentROIs.length > 0) {
            // Update motion status for each ROI
            this.currentROIs.forEach(roi => {
                roi.motion_detected = stats.motion_detected_rois.includes(roi.id);
            });
            
            // Redraw ROIs with updated motion status
            this.drawAllROIs();
        }
        
        // Update ROI status with motion/rain indication
        const roiCount = stats.active_rois || 0;
        const motionRois = stats.motion_detected_rois || [];
        const roiElement = document.getElementById('roiCount');
        
        if (roiElement) {
            let display = roiCount.toString();
            let color = '';
            
            if (stats.rain_detected) {
                display += ' (Rain)';
                color = '#ffc107';
            } else if (motionRois.length > 0) {
                display += ` (${motionRois.length} motion)`;
                color = '#dc3545';
            }
            
            roiElement.textContent = display;
            roiElement.style.color = color;
            roiElement.style.fontWeight = color ? 'bold' : '';
        }
    }
    
    updateRainStatus(stats) {
        const rainStatus = document.getElementById('rainStatus');
        if (rainStatus) {
            rainStatus.style.display = stats?.rain_detected ? 'block' : 'none';
        }
    }
    
    updateConnectionStatus(connected) {
        // Update the main connection status in navbar
        const connectionStatus = document.getElementById('connectionStatus');
        if (connectionStatus) {
            const icon = connectionStatus.querySelector('i');
            const text = connectionStatus.querySelector('span') || connectionStatus;
            
            if (connected) {
                icon.className = 'fas fa-circle status-connected';
                text.textContent = connected ? 'Connected' : 'Disconnected';
                connectionStatus.innerHTML = `<i class="fas fa-circle status-connected"></i> Connected`;
            } else {
                icon.className = 'fas fa-circle status-disconnected';
                connectionStatus.innerHTML = `<i class="fas fa-circle status-disconnected"></i> Disconnected`;
            }
        }
        
        // Also update any elements with connection-status class
        const statusElements = document.querySelectorAll('.connection-status');
        statusElements.forEach(el => {
            el.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
            el.textContent = connected ? 'Connected' : 'Disconnected';
        });
    }
    
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    // API Methods
    async apiCall(endpoint, method = 'GET', data = null) {
        try {
            const options = {
                method,
                headers: { 'Content-Type': 'application/json' }
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            const response = await fetch(endpoint, options);
            return await response.json();
        } catch (error) {
            console.error(`API call failed: ${endpoint}`, error);
            this.showAlert(`API Error: ${error.message}`, 'danger');
            return { success: false, error: error.message };
        }
    }
    
    async initializeSystem() {
        this.showLoading('Initializing system...');
        console.log('Initializing detection system...');
        
        const result = await this.apiCall('/api/initialize', 'POST', { camera_source: 0 });
        
        console.log('Initialize result:', result);
        
        if (result.success) {
            this.showAlert('System initialized successfully!', 'success');
            // Auto-refresh status after initialization
            setTimeout(() => this.refreshData(), 1000);
        } else {
            this.showAlert(`Initialization failed: ${result.error || 'Unknown error'}`, 'danger');
            console.error('Initialization error:', result.error);
        }
        
        this.hideLoading();
    }
    
    async startCamera() {
        this.showLoading('Starting camera...');
        console.log('Starting camera feed...');
        
        const result = await this.apiCall('/api/camera/start', 'POST', { source: 0 });
        
        console.log('Camera start result:', result);
        
        if (result.success) {
            this.showAlert('Camera started successfully!', 'success');
            // Auto-refresh to get camera status
            setTimeout(() => {
                this.refreshStatus();
                // Check if we're getting frame updates
                setTimeout(() => {
                    if (!this.isConnected) {
                        console.warn('No frame updates received, checking connection');
                    }
                }, 3000);
            }, 1000);
        } else {
            this.showAlert(`Failed to start camera: ${result.error || 'Unknown error'}`, 'danger');
            console.error('Camera start error:', result.error);
        }
        
        this.hideLoading();
    }
    
    async stopCamera() {
        const result = await this.apiCall('/api/camera/stop', 'POST');
        
        if (result.success) {
            this.showAlert('Camera stopped', 'warning');
        } else {
            this.showAlert(`Failed to stop camera: ${result.error}`, 'danger');
        }
    }
    
    async addROI(x1, y1, x2, y2) {
        const result = await this.apiCall('/api/rois/add', 'POST', { x1, y1, x2, y2 });
        
        if (result.success) {
            this.showAlert('ROI added successfully', 'success');
            this.refreshROIs();
        } else {
            this.showAlert(`Failed to add ROI: ${result.error}`, 'danger');
        }
    }
    
    async deleteROI(roiId) {
        const result = await this.apiCall(`/api/rois/delete/${roiId}`, 'DELETE');
        
        if (result.success) {
            this.showAlert(`ROI ${roiId} deleted`, 'success');
            this.refreshROIs();
        } else {
            this.showAlert(`Failed to delete ROI: ${result.error}`, 'danger');
        }
    }
    
    async clearROIs() {
        if (!confirm('Are you sure you want to clear all ROIs?')) return;
        
        const result = await this.apiCall('/api/rois/clear', 'POST');
        
        if (result.success) {
            this.showAlert('All ROIs cleared', 'warning');
            this.refreshROIs();
        } else {
            this.showAlert(`Failed to clear ROIs: ${result.error}`, 'danger');
        }
    }
    
    async refreshStatus() {
        const result = await this.apiCall('/api/camera/status');
        if (result.stats) {
            this.updateStats(result.stats);
        }
    }
    
    async refreshROIs() {
        const result = await this.apiCall('/api/rois');
        if (result.rois) {
            this.updateROITable(result.rois);
            this.currentROIs = result.rois;
            
            // Redraw ROIs on canvas
            this.drawAllROIs();
        }
    }
    
    async refreshData() {
        await this.refreshStatus();
        await this.refreshROIs();
    }
    
    updateROITable(rois) {
        const container = document.getElementById('roiList');
        if (!container) return;
        
        if (rois.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i> No ROIs defined. Use the camera feed to create detection zones.
                </div>
            `;
            return;
        }
        
        const table = `
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Position</th>
                            <th>Size</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rois.map(roi => `
                            <tr class="${roi.motion_detected ? 'table-danger' : ''}">
                                <td><strong>${roi.id}</strong></td>
                                <td>${roi.x1},${roi.y1}</td>
                                <td>${roi.width}×${roi.height}</td>
                                <td>
                                    <span class="badge ${roi.motion_detected ? 'bg-danger' : 'bg-success'}">
                                        ${roi.motion_detected ? 'Motion Detected' : 'Monitoring'}
                                    </span>
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-danger" onclick="detectorUI.deleteROI(${roi.id})">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = table;
    }
    
    // Motion Configuration
    async loadMotionConfig() {
        const result = await this.apiCall('/api/config/motion');
        if (result.motion_threshold !== undefined) {
            this.updateSlider('motionThreshold', result.motion_threshold);
        }
        if (result.max_small_contours !== undefined) {
            this.updateSlider('rainFilter', result.max_small_contours);
        }
    }
    
    async updateMotionConfig() {
        const motionThreshold = parseInt(document.getElementById('motionThreshold').value);
        const rainFilter = parseInt(document.getElementById('rainFilter').value);
        
        // Update display values
        document.getElementById('motionThresholdValue').textContent = motionThreshold;
        document.getElementById('rainFilterValue').textContent = rainFilter;
        
        // Send to server
        await this.apiCall('/api/config/motion', 'POST', {
            motion_threshold: motionThreshold,
            min_contour_area: motionThreshold * 2,
            max_small_contours: rainFilter
        });
    }
    
    updateSlider(id, value) {
        const slider = document.getElementById(id);
        const valueDisplay = document.getElementById(id + 'Value');
        
        if (slider) slider.value = value;
        if (valueDisplay) valueDisplay.textContent = value;
    }
    
    // UI Helpers
    showAlert(message, type = 'info') {
        // Remove existing alerts
        document.querySelectorAll('.alert-dismissible').forEach(alert => alert.remove());
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    showLoading(message = 'Loading...') {
        this.hideLoading();
        
        this.loadingElement = document.createElement('div');
        this.loadingElement.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center';
        this.loadingElement.style.cssText = 'background: rgba(0,0,0,0.5); z-index: 9999;';
        this.loadingElement.innerHTML = `
            <div class="bg-white p-4 rounded shadow">
                <div class="d-flex align-items-center">
                    <div class="spinner-border text-primary me-3"></div>
                    <span>${message}</span>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.loadingElement);
    }
    
    hideLoading() {
        if (this.loadingElement) {
            this.loadingElement.remove();
            this.loadingElement = null;
        }
    }
    
    // Sound Management Methods
    initializeSoundSettings() {
        // Load settings from localStorage if available
        const savedSettings = localStorage.getItem('detectionSoundSettings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            this.soundEnabled = settings.soundEnabled ?? true;
            this.motionSoundVolume = settings.motionSoundVolume ?? 0.5;
            
            // Update UI controls
            document.getElementById('soundEnabled').checked = this.soundEnabled;
            document.getElementById('motionVolume').value = this.motionSoundVolume;
            document.getElementById('motionVolumeValue').textContent = this.motionSoundVolume;
        }
        
        console.log('Sound settings initialized:', {
            enabled: this.soundEnabled,
            motionVolume: this.motionSoundVolume
        });
    }
    
    updateSoundSettings() {
        this.soundEnabled = document.getElementById('soundEnabled').checked;
        this.motionSoundVolume = parseFloat(document.getElementById('motionVolume').value);
        
        // Update display values
        document.getElementById('motionVolumeValue').textContent = this.motionSoundVolume;
        
        // Save to localStorage
        localStorage.setItem('detectionSoundSettings', JSON.stringify({
            soundEnabled: this.soundEnabled,
            motionSoundVolume: this.motionSoundVolume
        }));
        
        console.log('Sound settings updated:', {
            enabled: this.soundEnabled,
            motionVolume: this.motionSoundVolume
        });
    }
    
    checkForDetectionSounds(stats) {
        if (!this.soundEnabled) return;
        
        const now = Date.now();
        if (now - this.lastDetectionTime < this.soundCooldown) return;
        
        // Check for motion detection in ROIs (excluding rain)
        const motionRois = stats.motion_detected_rois || [];
        if (motionRois.length > 0 && !stats.rain_detected) {
            this.playMotionDetectionSound();
            this.lastDetectionTime = now;
        }
    }
    
    playMotionDetectionSound() {
        if (!this.soundEnabled) return;
        
        const audio = document.getElementById('motionSound');
        if (audio) {
            audio.volume = this.motionSoundVolume;
            audio.currentTime = 0;
            audio.play().catch(e => {
                console.log('Motion sound playback failed:', e.message);
            });
            console.log('Playing motion detection sound');
        }
    }
    
    testSounds() {
        console.log('Testing motion detection sound...');
        this.showAlert('Testing motion detection sound...', 'info');
        this.playMotionDetectionSound();
    }
}

// Global instance
const detectorUI = new DetectorWebUI();

// Manual ROI creation function
function addROIManually() {
    const x1 = prompt('Enter X1 coordinate:', '100');
    const y1 = prompt('Enter Y1 coordinate:', '100');
    const x2 = prompt('Enter X2 coordinate:', '300');
    const y2 = prompt('Enter Y2 coordinate:', '200');
    
    if (x1 && y1 && x2 && y2) {
        detectorUI.addROI(parseInt(x1), parseInt(y1), parseInt(x2), parseInt(y2));
    }
}

// Test ROI function
function addTestROI() {
    // Add a test ROI in the center of a 640x480 image
    detectorUI.addROI(200, 150, 400, 300);
}

// Global functions for backwards compatibility
function initializeSystem() { return detectorUI.initializeSystem(); }
function startCamera() { return detectorUI.startCamera(); }
function stopCamera() { return detectorUI.stopCamera(); }
function clearROIs() { return detectorUI.clearROIs(); }
function updateMotionSensitivity() { return detectorUI.updateMotionConfig(); }
function updateSoundSettings() { return detectorUI.updateSoundSettings(); }
function testSounds() { return detectorUI.testSounds(); }
function refreshStatus() { return detectorUI.refreshStatus(); }
function refreshROIs() { return detectorUI.refreshROIs(); }
function saveROIs() { 
    detectorUI.showAlert('ROIs are auto-saved when created/modified', 'info');
    return detectorUI.refreshROIs();
}
function loadROIs() { 
    return detectorUI.refreshROIs();
}