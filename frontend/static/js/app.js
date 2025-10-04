// ETL Dashboard JavaScript Application

// Global variables
let currentFileId = null;
let currentStep = 1;
let uploadedSheets = [];
let logEntries = [];
let logPanelOpen = false;
let startTime = null;

// API base URL (will be set from template)
// Use the FASTAPI_URL set by the template in window.FASTAPI_URL
const FASTAPI_URL = window.FASTAPI_URL || 'http://127.0.0.1:8000';
console.log('FASTAPI_URL set to:', FASTAPI_URL);

// Step configuration
const STEPS = {
    1: { name: 'Upload Excel Workbook', description: 'Select and upload your Excel file' },
    2: { name: 'Select & Preview Sheets', description: 'Choose MasterBOM and Status sheets' },
    3: { name: 'Profile Data Quality', description: 'Analyze data structure and quality' },
    4: { name: 'Transform & Export', description: 'Run ETL process and generate outputs' },
    5: { name: 'Download Results', description: 'Download transformed data and reports' }
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Initializing application...');
    
    // Only initialize upload functionality if upload area exists (main page)
    const uploadArea = document.getElementById('upload-area');
    if (uploadArea) {
        initializeUpload();
    }
    
    // Only initialize sheet selection if sheet selection exists (main page)
    const sheetSelection = document.getElementById('sheet-selection');
    if (sheetSelection) {
        initializeSheetSelection();
    }
    
    // Initialize log panel if it exists (available on all pages)
    const logPanel = document.getElementById('log-panel');
    if (logPanel) {
        initializeLogPanel();
    }
    
    // Initialize progress tracking if elements exist
    const progressTracking = document.querySelector('.progress-tracker');
    if (progressTracking) {
        initializeProgressTracking();
    }
    
    console.log('Application initialized for current page');
});

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showLoading(message = 'Loading...') {
    // Implementation for loading state
    console.log('Loading:', message);
}

// Global functions for template access
window.toggleLogPanel = toggleLogPanel;
window.ETLDashboard = {
    toggleLogPanel: toggleLogPanel,
    addLogEntry: addLogEntry,
    clearLogs: clearLogs,
    showToast: showToast,
    updateStepProgress: updateStepProgress,
    runTransform: runTransform,
    formatFileSize: formatFileSize
};

// ETL Transform Function
async function runTransform() {
    const transformBtn = document.getElementById('run-transform-btn');
    const transformProgress = document.getElementById('transform-progress');
    const progressBar = document.getElementById('transform-progress-bar');
    const statusText = document.getElementById('transform-status');
    const percentageText = document.getElementById('transform-percentage');

    // Get selected sheets from URL params or stored values
    const urlParams = new URLSearchParams(window.location.search);
    const masterSheet = urlParams.get('master_sheet') || localStorage.getItem('selectedMasterSheet');
    const statusSheet = urlParams.get('status_sheet') || localStorage.getItem('selectedStatusSheet');
    const fileId = urlParams.get('file_id') || currentFileId;

    if (!fileId || !masterSheet || !statusSheet) {
        addLogEntry('ERROR', 'Missing required parameters for ETL transformation');
        showToast('Missing file or sheet information. Please start over.', 'error');
        return;
    }

    // Disable button and show progress
    transformBtn.disabled = true;
    transformBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
    transformProgress.classList.remove('hidden');

    updateStepProgress(4, 0, 'current');
    addLogEntry('INFO', 'Starting ETL transformation process...');

    try {
        // Prepare transform request
        const transformData = {
            file_id: fileId,
            master_sheet: masterSheet,
            status_sheet: statusSheet,
            options: getDateColumnOptions() // Use our centralized date column options
        };

        addLogEntry('INFO', `Transform request: MasterBOM="${masterSheet}", Status="${statusSheet}"`);
        updateStepProgress(4, 10, 'current');

        if (statusText) statusText.textContent = 'Sending transform request...';
        if (percentageText) percentageText.textContent = '10%';
        if (progressBar) progressBar.style.width = '10%';

        // Send transform request
        const response = await fetch(`${FASTAPI_URL}/api/transform`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(transformData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Transform failed');
        }

        // Simulate progress updates for better UX
        const progressStages = [
            { progress: 25, status: 'Reading Excel sheets...' },
            { progress: 40, status: 'Cleaning data...' },
            { progress: 55, status: 'Applying business rules...' },
            { progress: 70, status: 'Creating normalized tables...' },
            { progress: 85, status: 'Generating outputs...' },
            { progress: 95, status: 'Finalizing...' }
        ];

        for (const stage of progressStages) {
            await new Promise(resolve => setTimeout(resolve, 800));
            updateStepProgress(4, stage.progress, 'current');
            if (statusText) statusText.textContent = stage.status;
            if (percentageText) percentageText.textContent = `${stage.progress}%`;
            if (progressBar) progressBar.style.width = `${stage.progress}%`;
            addLogEntry('INFO', stage.status);
        }

        const result = await response.json();

        // Complete the transformation
        updateStepProgress(4, 100, 'completed');

        if (statusText) statusText.textContent = 'Transform completed successfully!';
        if (percentageText) percentageText.textContent = '100%';
        if (progressBar) progressBar.style.width = '100%';

        addLogEntry('SUCCESS', `ETL transformation completed successfully!`);
        addLogEntry('INFO', `Generated ${result.artifacts?.length || 0} output files`);

        // Show success message and redirect to results
        showToast('ETL transformation completed successfully!', 'success');

        setTimeout(() => {
            window.location.href = `/results?file_id=${fileId}&master_sheet=${encodeURIComponent(masterSheet)}&status_sheet=${encodeURIComponent(statusSheet)}`;
        }, 2000);

    } catch (error) {
        console.error('Transform error:', error);

        updateStepProgress(4, 0, 'error');
        addLogEntry('ERROR', `Transform failed: ${error.message}`);

        if (statusText) statusText.textContent = 'Transform failed';
        if (percentageText) percentageText.textContent = 'Error';
        if (progressBar) {
            progressBar.style.width = '100%';
            progressBar.className = progressBar.className.replace('from-green-500 to-blue-500', 'from-red-500 to-red-600');
        }

        showToast(`Transform failed: ${error.message}`, 'error');

        // Re-enable button
        transformBtn.disabled = false;
        transformBtn.innerHTML = '<i class="fas fa-play mr-2"></i>Retry Transform';
    }
}

// Log Panel Management
function initializeLogPanel() {
    const toggleBtn = document.getElementById('toggle-log-panel');
    const showBtn = document.getElementById('show-log-panel');
    const clearBtn = document.getElementById('clear-logs');

    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleLogPanel);
    }

    if (showBtn) {
        showBtn.addEventListener('click', toggleLogPanel);
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', clearLogs);
    }
}

function toggleLogPanel() {
    const panel = document.getElementById('log-panel');
    const showBtn = document.getElementById('show-log-panel');
    const toggleBtn = document.getElementById('toggle-log-panel');

    logPanelOpen = !logPanelOpen;

    if (logPanelOpen) {
        panel.classList.add('open');
        panel.style.transform = 'translateX(0)';
        showBtn.style.transform = 'translateX(100%)';

        // Update main content margin
        const mainContent = document.getElementById('main-content');
        mainContent.style.marginRight = '24rem';

        // Update toggle button icon
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="fas fa-times"></i>';
        }
    } else {
        panel.classList.remove('open');
        panel.style.transform = 'translateX(100%)';
        showBtn.style.transform = 'translateX(0)';

        // Reset main content margin
        const mainContent = document.getElementById('main-content');
        mainContent.style.marginRight = '0';

        // Update toggle button icon
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="fas fa-terminal"></i>';
        }
    }
}

function addLogEntry(level, message, timestamp = null) {
    const logContainer = document.getElementById('log-entries');
    const logCount = document.getElementById('log-count');
    const logNotification = document.getElementById('log-notification');

    if (!timestamp) {
        timestamp = new Date().toLocaleTimeString();
    }

    const entry = {
        level: level.toLowerCase(),
        message,
        timestamp,
        id: Date.now()
    };

    logEntries.push(entry);

    // Only manipulate DOM if log container exists (on logs page)
    if (logContainer) {
        // Create log entry element
        const entryElement = document.createElement('div');
        entryElement.className = `log-entry ${entry.level}`;
        entryElement.innerHTML = `
            <div class="flex-shrink-0 mr-3">
                <div class="log-level ${entry.level}">${level.toUpperCase()}</div>
            </div>
            <div class="flex-1">
                <div class="text-sm font-medium">${message}</div>
                <div class="log-timestamp mt-1">${timestamp}</div>
            </div>
        `;

        // Remove placeholder if it exists
        const placeholder = logContainer.querySelector('.text-center');
        if (placeholder) {
            placeholder.remove();
        }

        // Add new entry
        logContainer.appendChild(entryElement);

        // Auto-scroll if enabled
        const autoScroll = document.getElementById('auto-scroll-logs');
        if (autoScroll && autoScroll.checked) {
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        // Animate entry
        entryElement.style.opacity = '0';
        entryElement.style.transform = 'translateX(20px)';
        setTimeout(() => {
            entryElement.style.transition = 'all 0.3s ease-out';
            entryElement.style.opacity = '1';
            entryElement.style.transform = 'translateX(0)';
        }, 10);
    }

    // Update log count if element exists
    if (logCount) {
        logCount.textContent = `${logEntries.length} entries`;
    }

    // Update notification badge if element exists
    if (logNotification && !logPanelOpen) {
        logNotification.textContent = logEntries.length;
        logNotification.classList.remove('hidden');
    }

    // Console log for debugging when DOM elements don't exist
    console.log(`[${level}] ${message}`);
}

function clearLogs() {
    const logContainer = document.getElementById('log-entries');
    const logCount = document.getElementById('log-count');
    const logNotification = document.getElementById('log-notification');

    logEntries = [];
    logContainer.innerHTML = `
        <div class="text-center text-gray-500 text-sm py-8">
            <i class="fas fa-info-circle mb-2"></i>
            <p>No logs yet. Start an ETL process to see real-time updates.</p>
        </div>
    `;

    if (logCount) {
        logCount.textContent = '0 entries';
    }

    if (logNotification) {
        logNotification.classList.add('hidden');
    }
}

// Progress Tracking
function initializeProgressTracking() {
    startTime = new Date();
}

function updateStepProgress(step, percentage = 0, status = 'pending') {
    const stepElement = document.getElementById(`step-${step}`);
    const stepCheckElement = document.getElementById(`step-${step}-check`);
    const stepStatusElement = document.getElementById(`step-${step}-status`);
    const stepNameElement = document.getElementById('current-step-name');
    const stepPercentageElement = document.getElementById('step-percentage');
    const overallProgressElement = document.getElementById('overall-progress');

    // Update current step name
    if (stepNameElement && STEPS[step]) {
        stepNameElement.textContent = `Step ${step}: ${STEPS[step].name}`;
    }

    // Update step status
    if (stepStatusElement) {
        const statusText = {
            'pending': 'Pending',
            'current': 'In Progress',
            'completed': 'Completed',
            'error': 'Error'
        };
        stepStatusElement.textContent = statusText[status] || status;
        stepStatusElement.className = `text-xs font-medium mt-1 ${
            status === 'completed' ? 'text-green-600' :
            status === 'current' ? 'text-blue-600' :
            status === 'error' ? 'text-red-600' :
            'text-gray-400'
        }`;
    }

    // Update step indicator
    if (stepElement) {
        stepElement.className = `flex items-center justify-center w-12 h-12 rounded-full font-semibold transition-all duration-300 ${
            status === 'completed' ? 'bg-green-600 text-white shadow-lg' :
            status === 'current' ? 'bg-blue-600 text-white shadow-lg' :
            status === 'error' ? 'bg-red-600 text-white shadow-lg' :
            'bg-gray-300 text-gray-600'
        }`;
    }

    // Show/hide check mark
    if (stepCheckElement) {
        if (status === 'completed') {
            stepCheckElement.style.opacity = '1';
            stepCheckElement.style.transform = 'scale(1)';
        } else {
            stepCheckElement.style.opacity = '0';
            stepCheckElement.style.transform = 'scale(0)';
        }
    }

    // Update overall progress
    const overallPercentage = ((step - 1) * 25) + (percentage * 0.25);
    if (overallProgressElement) {
        overallProgressElement.style.width = `${overallPercentage}%`;
    }

    if (stepPercentageElement) {
        stepPercentageElement.textContent = `${Math.round(overallPercentage)}% Complete`;
    }

    // Update progress between steps
    if (step > 1) {
        const prevProgressElement = document.getElementById(`progress-${step-1}-${step}`);
        if (prevProgressElement) {
            prevProgressElement.style.width = '100%';
        }
    }

    if (percentage > 0 && step < 4) {
        const currentProgressElement = document.getElementById(`progress-${step}-${step+1}`);
        if (currentProgressElement) {
            currentProgressElement.style.width = `${percentage}%`;
        }
    }
}

// File Upload Functions
function initializeUpload() {
    console.log('Initializing upload functionality...');

    const fileInput = document.getElementById('file-input');
    const uploadArea = document.getElementById('upload-area');
    const fileInfo = document.getElementById('file-info');
    const removeFileBtn = document.getElementById('remove-file');

    console.log('Elements found:', {
        fileInput: !!fileInput,
        uploadArea: !!uploadArea,
        fileInfo: !!fileInfo,
        removeFileBtn: !!removeFileBtn
    });

    if (!uploadArea || !fileInput) {
        console.log('Upload elements not found - skipping upload initialization');
        return;
    }
    
    // Click to upload
    uploadArea.addEventListener('click', () => {
        console.log('Upload area clicked');
        fileInput.click();
    });
    
    // File selection
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleFileDrop);
    
    // Remove file
    if (removeFileBtn) {
        removeFileBtn.addEventListener('click', removeFile);
    }
    
    console.log('Upload functionality initialized successfully');
}

function handleFileSelect(event) {
    console.log('File selected:', event.target.files);
    const file = event.target.files[0];
    if (file) {
        console.log('File details:', file.name, file.size, file.type);
        uploadFile(file);
    } else {
        console.log('No file selected');
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add('dragover');
}

function handleDragLeave(event) {
    event.currentTarget.classList.remove('dragover');
}

function handleFileDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

async function uploadFile(file) {
    console.log('uploadFile called with:', file.name, file.size);
    console.log('Using FASTAPI_URL:', FASTAPI_URL);

    // Validate file type
    if (!file.name.toLowerCase().endsWith('.xlsx') && !file.name.toLowerCase().endsWith('.xls')) {
        addLogEntry('ERROR', 'Invalid file type. Please select an Excel file (.xlsx or .xls)');
        showToast('Please select an Excel file (.xlsx or .xls)', 'error');
        return;
    }

    // Validate file size (50MB limit)
    const maxSize = 50 * 1024 * 1024; // 50MB in bytes
    if (file.size > maxSize) {
        addLogEntry('ERROR', `File too large: ${formatFileSize(file.size)}. Maximum size is 50MB.`);
        showToast('File too large. Maximum size is 50MB.', 'error');
        return;
    }

    addLogEntry('INFO', `Starting upload: ${file.name} (${formatFileSize(file.size)})`);
    updateStepProgress(1, 10, 'current');

    // Show upload progress
    showUploadProgress();

    try {
        const formData = new FormData();
        formData.append('file', file);

        console.log('Sending request to:', '/api/upload');
        addLogEntry('INFO', 'Uploading file to server...');

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        console.log('Response status:', response.status);
        updateStepProgress(1, 70, 'current');

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();
        console.log('Upload response:', result);

        addLogEntry('SUCCESS', `File uploaded successfully. Found ${result.sheet_names.length} sheets.`);
        updateStepProgress(1, 90, 'current');

        // Store file info
        currentFileId = result.file_id;
        uploadedSheets = result.sheet_names;
        window.lastDetectedSheets = result.detected_sheets; // Store for override detection
        console.log('Stored file info:', { currentFileId, uploadedSheets, detectedSheets: result.detected_sheets });

        // Show processing state
        showProcessingState();

        // Simulate processing time for better UX
        setTimeout(() => {
            // Show file info
            showFileInfo(result);

            // Complete step 1
            updateStepProgress(1, 100, 'completed');

            // Enable next step
            enableStep(2);
            populateSheetSelectors(result.sheet_names, result.detected_sheets);

            addLogEntry('INFO', 'Ready for sheet selection. Please choose MasterBOM and Status sheets.');
            showToast('File uploaded successfully!', 'success');
        }, 1000);

    } catch (error) {
        console.error('Upload error:', error);
        addLogEntry('ERROR', `Upload failed: ${error.message}`);
        updateStepProgress(1, 0, 'error');
        showToast(`Upload failed: ${error.message}`, 'error');
        hideUploadProgress();
    }
}

function showUploadProgress() {
    const uploadArea = document.getElementById('upload-area');
    const uploadProgress = document.getElementById('upload-progress');
    const processingState = document.getElementById('processing-state');

    uploadArea.classList.add('hidden');
    uploadProgress.classList.remove('hidden');
    processingState.classList.add('hidden');

    // Enhanced progress simulation with realistic stages
    let progress = 0;
    const progressBar = document.getElementById('upload-progress-bar');
    const statusText = document.getElementById('upload-status');
    const percentageText = document.getElementById('upload-percentage');

    const stages = [
        { progress: 20, status: 'Preparing upload...' },
        { progress: 40, status: 'Uploading file...' },
        { progress: 60, status: 'Validating file...' },
        { progress: 80, status: 'Processing sheets...' },
        { progress: 95, status: 'Almost done...' }
    ];

    let stageIndex = 0;

    const interval = setInterval(() => {
        progress += Math.random() * 8 + 2; // More realistic progress increments

        // Update stage status
        if (stageIndex < stages.length && progress >= stages[stageIndex].progress) {
            if (statusText) statusText.textContent = stages[stageIndex].status;
            stageIndex++;
        }

        if (progress >= 95) {
            progress = 95; // Stop at 95% until actual completion
            clearInterval(interval);
        }

        if (progressBar) progressBar.style.width = `${progress}%`;
        if (percentageText) percentageText.textContent = `${Math.round(progress)}%`;
    }, 150);
}

function showProcessingState() {
    const uploadProgress = document.getElementById('upload-progress');
    const processingState = document.getElementById('processing-state');

    uploadProgress.classList.add('hidden');
    processingState.classList.remove('hidden');
}

function hideUploadProgress() {
    const uploadArea = document.getElementById('upload-area');
    const uploadProgress = document.getElementById('upload-progress');
    const processingState = document.getElementById('processing-state');
    const progressBar = document.getElementById('upload-progress-bar');
    const statusText = document.getElementById('upload-status');
    const percentageText = document.getElementById('upload-percentage');

    uploadArea.classList.remove('hidden');
    uploadProgress.classList.add('hidden');
    processingState.classList.add('hidden');

    if (progressBar) progressBar.style.width = '0%';
    if (statusText) statusText.textContent = 'Preparing upload...';
    if (percentageText) percentageText.textContent = '0%';
}

function showFileInfo(fileInfo) {
    console.log('showFileInfo called with:', fileInfo);
    hideUploadProgress();

    const fileNameEl = document.getElementById('file-name');
    const fileDetailsEl = document.getElementById('file-details');
    const fileInfoEl = document.getElementById('file-info');

    console.log('Elements found:', {
        fileNameEl: !!fileNameEl,
        fileDetailsEl: !!fileDetailsEl,
        fileInfoEl: !!fileInfoEl
    });

    if (fileNameEl) fileNameEl.textContent = fileInfo.filename;
    if (fileDetailsEl) {
        fileDetailsEl.textContent =
            `${formatFileSize(fileInfo.file_size)} • ${fileInfo.sheet_names.length} sheets`;
    }

    if (fileInfoEl) fileInfoEl.classList.remove('hidden');
}

function removeFile() {
    if (currentFileId) {
        // Optionally delete file from server
        fetch(`${FASTAPI_URL}/api/upload/${currentFileId}`, {
            method: 'DELETE'
        }).catch(console.error);
    }
    
    // Reset UI
    currentFileId = null;
    uploadedSheets = [];
    document.getElementById('file-info').classList.add('hidden');
    document.getElementById('file-input').value = '';
    
    // Reset steps
    resetSteps();
    
    showToast('File removed', 'info');
}

// Sheet Selection Functions
function initializeSheetSelection() {
    const previewBtn = document.getElementById('preview-btn');
    const masterSelect = document.getElementById('master-sheet-select');
    const statusSelect = document.getElementById('status-sheet-select');
    
    if (!previewBtn) return;
    
    previewBtn.addEventListener('click', previewSheets);
    
    // Enable preview button when both sheets are selected
    [masterSelect, statusSelect].forEach(select => {
        if (select) {
            select.addEventListener('change', checkSheetSelection);
        }
    });
}

function populateSheetSelectors(sheetNames, detectedSheets = null) {
    const masterSelect = document.getElementById('master-sheet-select');
    const statusSelect = document.getElementById('status-sheet-select');

    if (!masterSelect || !statusSelect) {
        console.error('Sheet selector elements not found:', {
            masterSelect: !!masterSelect,
            statusSelect: !!statusSelect
        });
        return;
    }

    // Clear existing options
    masterSelect.innerHTML = '<option value="">Select MasterBOM sheet...</option>';
    statusSelect.innerHTML = '<option value="">Select Status sheet...</option>';

    // Log sheet detection results
    if (detectedSheets) {
        addLogEntry('INFO', `Analyzing ${sheetNames.length} sheets for intelligent filtering...`);

        if (detectedSheets.masterbom) {
            const confidence = Math.round((detectedSheets.confidence?.masterbom || 0) * 100);
            addLogEntry('SUCCESS', `MasterBOM sheet detected: "${detectedSheets.masterbom}" (${confidence}% confidence)`);
        } else {
            addLogEntry('WARNING', 'No MasterBOM sheet auto-detected. Manual selection required.');
        }

        if (detectedSheets.status) {
            const confidence = Math.round((detectedSheets.confidence?.status || 0) * 100);
            addLogEntry('SUCCESS', `Status sheet detected: "${detectedSheets.status}" (${confidence}% confidence)`);
        } else {
            addLogEntry('WARNING', 'No Status sheet auto-detected. Manual selection required.');
        }
    }

    // Apply intelligent filtering
    const filteredSheets = applyIntelligentSheetFiltering(sheetNames, detectedSheets);
    
    // Populate MasterBOM dropdown with ONLY BOM-related sheets
    populateMasterBOMDropdown(masterSelect, filteredSheets.masterBomSheets, detectedSheets);
    
    // Populate Status dropdown with ONLY status-related sheets
    populateStatusDropdown(statusSelect, filteredSheets.statusSheets, detectedSheets);

    // Handle auto-detection and auto-selection
    if (detectedSheets) {
        showAutoDetectionResults(detectedSheets);
        autoSelectDetectedSheets(masterSelect, statusSelect, detectedSheets);
    }

    // Show sheet selection section with animation
    const sheetSection = document.getElementById('sheet-selection');
    sheetSection.classList.remove('hidden');
    sheetSection.classList.add('fade-in');
}

/**
 * Apply intelligent sheet filtering based on sheet names and backend detection
 */
function applyIntelligentSheetFiltering(sheetNames, detectedSheets) {
    // Get backend suggestions if available
    const masterBomCandidates = detectedSheets?.suggestions?.masterbom_candidates || [];
    const statusCandidates = detectedSheets?.suggestions?.status_candidates || [];
    
    // Create sets for backend-detected sheets
    const backendMasterBomSheets = new Set(masterBomCandidates.map(([sheet, score]) => sheet));
    const backendStatusSheets = new Set(statusCandidates.map(([sheet, score]) => sheet));
    
    // Frontend keyword-based detection patterns
    const bomKeywords = [
        'masterbom', 'master_bom', 'master-bom',
        'bom', 'bill', 'parts', 'components', 'materials',
        'inventory', 'item', 'product', 'assembly'
    ];
    
    const statusKeywords = [
        'status', 'project', 'summary', 'management', 'tracking',
        'progress', 'timeline', 'schedule', 'plan', 'overview',
        'dashboard', 'report', 'metrics', 'kpi'
    ];
    
    // Apply frontend keyword filtering
    const frontendMasterBomSheets = sheetNames.filter(sheet => 
        bomKeywords.some(keyword => 
            sheet.toLowerCase().includes(keyword.toLowerCase())
        )
    );
    
    const frontendStatusSheets = sheetNames.filter(sheet => 
        statusKeywords.some(keyword => 
            sheet.toLowerCase().includes(keyword.toLowerCase())
        )
    );
    
    // Combine backend and frontend detection (union)
    const masterBomSheets = [...new Set([
        ...Array.from(backendMasterBomSheets),
        ...frontendMasterBomSheets
    ])];
    
    const statusSheets = [...new Set([
        ...Array.from(backendStatusSheets),
        ...frontendStatusSheets
    ])];
    
    // If no sheets detected for a category, use all sheets as fallback
    const finalMasterBomSheets = masterBomSheets.length > 0 ? masterBomSheets : sheetNames;
    const finalStatusSheets = statusSheets.length > 0 ? statusSheets : sheetNames;
    
    return {
        masterBomSheets: finalMasterBomSheets,
        statusSheets: finalStatusSheets,
        usedFallback: {
            masterBom: masterBomSheets.length === 0,
            status: statusSheets.length === 0
        },
        detectionStats: {
            backendMasterBom: backendMasterBomSheets.size,
            frontendMasterBom: frontendMasterBomSheets.length,
            backendStatus: backendStatusSheets.size,
            frontendStatus: frontendStatusSheets.length
        }
    };
}

/**
 * Populate MasterBOM dropdown with intelligent filtering
 */
function populateMasterBOMDropdown(masterSelect, sheets, detectedSheets) {
    const masterBomCandidates = detectedSheets?.suggestions?.masterbom_candidates || [];
    const usedFallback = sheets.length === masterBomCandidates.length && masterBomCandidates.length === 0;
    
    // Add fallback warning if needed
    if (usedFallback) {
        const warningOption = new Option('⚠️ No BOM sheets detected. Showing all sheets.', '');
        warningOption.disabled = true;
        warningOption.style.color = '#ef4444';
        warningOption.style.fontStyle = 'italic';
        masterSelect.add(warningOption);
        
        addLogEntry('WARNING', 'No BOM sheets detected. Showing all sheets as fallback.');
    } else {
        // Add info header for filtered results
        const infoOption = new Option('');
        infoOption.disabled = true;
        infoOption.style.color = '#059669';
        infoOption.style.fontStyle = 'italic';
        masterSelect.add(infoOption);
        
        addLogEntry('INFO', `Filtered to ${sheets.length} BOM-related sheets.`);
    }
    
    // Populate with filtered sheets
    sheets.forEach(sheet => {
        const candidate = masterBomCandidates.find(([s]) => s === sheet);
        const option = new Option(sheet, sheet);
        
        if (candidate) {
            const [, score] = candidate;
            const confidence = Math.round(score * 100);
            const isDetected = detectedSheets?.masterbom === sheet;
            
            if (isDetected) {
                option.text = `${sheet} ✨ (Auto-detected - ${confidence}%)`;
                option.style.fontWeight = 'bold';
                option.style.color = confidence >= 70 ? '#059669' : '#d97706';
            } else if (confidence >= 40) {
                option.text = `${sheet} (${confidence}% match)`;
                option.style.color = '#6b7280';
            }
        }
        
        masterSelect.add(option);
    });
}

/**
 * Populate Status dropdown with intelligent filtering
 */
function populateStatusDropdown(statusSelect, sheets, detectedSheets) {
    const statusCandidates = detectedSheets?.suggestions?.status_candidates || [];
    const usedFallback = sheets.length === statusCandidates.length && statusCandidates.length === 0;
    
    // Add fallback warning if needed
    if (usedFallback) {
        const warningOption = new Option('⚠️ No Status sheets detected. Showing all sheets.', '');
        warningOption.disabled = true;
        warningOption.style.color = '#ef4444';
        warningOption.style.fontStyle = 'italic';
        statusSelect.add(warningOption);
        
        addLogEntry('WARNING', 'No Status sheets detected. Showing all sheets as fallback.');
    } else {
        // Add info header for filtered results
        const infoOption = new Option('');
        infoOption.disabled = true;
        infoOption.style.color = '#059669';
        infoOption.style.fontStyle = 'italic';
        statusSelect.add(infoOption);
        
        addLogEntry('INFO', `Filtered to ${sheets.length} Status-related sheets.`);
    }
    
    // Populate with filtered sheets
    sheets.forEach(sheet => {
        const candidate = statusCandidates.find(([s]) => s === sheet);
        const option = new Option(sheet, sheet);
        
        if (candidate) {
            const [, score] = candidate;
            const confidence = Math.round(score * 100);
            const isDetected = detectedSheets?.status === sheet;
            
            if (isDetected) {
                option.text = `${sheet} ✨ (Auto-detected - ${confidence}%)`;
                option.style.fontWeight = 'bold';
                option.style.color = confidence >= 70 ? '#059669' : '#d97706';
            } else if (confidence >= 40) {
                option.text = `${sheet} (${confidence}% match)`;
                option.style.color = '#6b7280';
            }
        }
        
        statusSelect.add(option);
    });
}

/**
 * Handle auto-selection of detected sheets
 */
function autoSelectDetectedSheets(masterSelect, statusSelect, detectedSheets) {
    let autoSelectedCount = 0;

    if (detectedSheets.masterbom && detectedSheets.confidence?.masterbom >= 0.5) {
        masterSelect.value = detectedSheets.masterbom;
        autoSelectedCount++;
        addLogEntry('INFO', `Auto-selected MasterBOM sheet: "${detectedSheets.masterbom}"`);
    }

    if (detectedSheets.status && detectedSheets.confidence?.status >= 0.5) {
        statusSelect.value = detectedSheets.status;
        autoSelectedCount++;
        addLogEntry('INFO', `Auto-selected Status sheet: "${detectedSheets.status}"`);
    }

    // Update progress based on auto-selection success
    if (autoSelectedCount === 2) {
        updateStepProgress(2, 80, 'current');
        addLogEntry('SUCCESS', 'Both sheets auto-selected successfully! Review and proceed or modify if needed.');
        showToast('Sheets auto-detected and selected!', 'success');
    } else if (autoSelectedCount === 1) {
        updateStepProgress(2, 40, 'current');
        addLogEntry('INFO', 'One sheet auto-selected. Please select the remaining sheet manually.');
        showToast('One sheet auto-detected. Please select the other manually.', 'info');
    } else {
        updateStepProgress(2, 20, 'current');
        addLogEntry('INFO', 'No sheets auto-selected. Please make manual selections.');
        showToast('Please select sheets manually.', 'info');
    }

    // Check if both sheets are selected (auto or manual)
    checkSheetSelection();
}

function showAutoDetectionResults(detectedSheets) {
    // Create or update auto-detection info panel
    let infoPanel = document.getElementById('auto-detection-info');
    if (!infoPanel) {
        infoPanel = document.createElement('div');
        infoPanel.id = 'auto-detection-info';
        infoPanel.className = 'bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-6 shadow-sm';

        const sheetSelection = document.getElementById('sheet-selection');
        const title = sheetSelection.querySelector('h2');
        title.parentNode.insertBefore(infoPanel, title.nextSibling);
    }

    // Determine overall detection status
    const masterDetected = detectedSheets.masterbom && detectedSheets.confidence?.masterbom >= 0.5;
    const statusDetected = detectedSheets.status && detectedSheets.confidence?.status >= 0.5;
    const bothDetected = masterDetected && statusDetected;

    let headerIcon, headerText, headerColor;
    if (bothDetected) {
        headerIcon = 'fas fa-check-circle';
        headerText = 'Auto-Detection Successful';
        headerColor = 'text-green-700';
    } else if (masterDetected || statusDetected) {
        headerIcon = 'fas fa-exclamation-circle';
        headerText = 'Partial Auto-Detection';
        headerColor = 'text-yellow-700';
    } else {
        headerIcon = 'fas fa-info-circle';
        headerText = 'Manual Selection Required';
        headerColor = 'text-blue-700';
    }

    let html = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <i class="${headerIcon} ${headerColor} text-xl"></i>
            </div>
            <div class="ml-3 flex-1">
                <h4 class="text-sm font-semibold ${headerColor} mb-3">${headerText}</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    `;

    // MasterBOM Detection Card
    html += '<div class="bg-white rounded-lg p-3 border border-gray-200">';
    if (detectedSheets.masterbom) {
        const confidence = Math.round((detectedSheets.confidence?.masterbom || 0) * 100);
        const confidenceColor = confidence >= 70 ? 'text-green-600' : confidence >= 50 ? 'text-yellow-600' : 'text-orange-600';
        const confidenceBg = confidence >= 70 ? 'bg-green-100' : confidence >= 50 ? 'bg-yellow-100' : 'bg-orange-100';

        html += `
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center">
                    <i class="fas fa-cogs text-blue-600 mr-2"></i>
                    <span class="font-medium text-gray-900">MasterBOM Sheet</span>
                </div>
                <span class="px-2 py-1 rounded-full text-xs font-medium ${confidenceBg} ${confidenceColor}">
                    ${confidence}%
                </span>
            </div>
            <div class="text-sm text-gray-700 font-medium">${detectedSheets.masterbom}</div>
            <div class="text-xs text-gray-500 mt-1">
                <i class="fas fa-magic mr-1"></i>Auto-detected and pre-selected
            </div>
        `;
    } else {
        html += `
            <div class="flex items-center mb-2">
                <i class="fas fa-cogs text-gray-400 mr-2"></i>
                <span class="font-medium text-gray-600">MasterBOM Sheet</span>
            </div>
            <div class="text-sm text-gray-500">Not detected</div>
            <div class="text-xs text-gray-400 mt-1">
                <i class="fas fa-hand-pointer mr-1"></i>Manual selection required
            </div>
        `;
    }
    html += '</div>';

    // Status Detection Card
    html += '<div class="bg-white rounded-lg p-3 border border-gray-200">';
    if (detectedSheets.status) {
        const confidence = Math.round((detectedSheets.confidence?.status || 0) * 100);
        const confidenceColor = confidence >= 70 ? 'text-green-600' : confidence >= 50 ? 'text-yellow-600' : 'text-orange-600';
        const confidenceBg = confidence >= 70 ? 'bg-green-100' : confidence >= 50 ? 'bg-yellow-100' : 'bg-orange-100';

        html += `
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center">
                    <i class="fas fa-chart-bar text-purple-600 mr-2"></i>
                    <span class="font-medium text-gray-900">Status Sheet</span>
                </div>
                <span class="px-2 py-1 rounded-full text-xs font-medium ${confidenceBg} ${confidenceColor}">
                    ${confidence}%
                </span>
            </div>
            <div class="text-sm text-gray-700 font-medium">${detectedSheets.status}</div>
            <div class="text-xs text-gray-500 mt-1">
                <i class="fas fa-magic mr-1"></i>Auto-detected and pre-selected
            </div>
        `;
    } else {
        html += `
            <div class="flex items-center mb-2">
                <i class="fas fa-chart-bar text-gray-400 mr-2"></i>
                <span class="font-medium text-gray-600">Status Sheet</span>
            </div>
            <div class="text-sm text-gray-500">Not detected</div>
            <div class="text-xs text-gray-400 mt-1">
                <i class="fas fa-hand-pointer mr-1"></i>Manual selection required
            </div>
        `;
    }
    html += '</div>';

    html += `
                </div>
                <div class="mt-4 p-3 bg-blue-100 rounded-lg">
                    <div class="flex items-start">
                        <i class="fas fa-lightbulb text-blue-600 mt-0.5 mr-2"></i>
                        <div class="text-xs text-blue-800">
                            <strong>Tip:</strong> Auto-detected sheets are pre-selected in the dropdowns below.
                            You can change the selections if the detection is incorrect.
                            ${bothDetected ? 'Both sheets detected - you can proceed directly!' : 'Please review and complete your selections.'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    infoPanel.innerHTML = html;

    // Add animation
    infoPanel.style.opacity = '0';
    infoPanel.style.transform = 'translateY(-10px)';
    setTimeout(() => {
        infoPanel.style.transition = 'all 0.3s ease-out';
        infoPanel.style.opacity = '1';
        infoPanel.style.transform = 'translateY(0)';
    }, 100);
}

function checkSheetSelection() {
    const masterSheet = document.getElementById('master-sheet-select').value;
    const statusSheet = document.getElementById('status-sheet-select').value;
    const previewBtn = document.getElementById('preview-btn');

    // Check for valid selection
    if (masterSheet && statusSheet && masterSheet !== statusSheet) {
        previewBtn.disabled = false;
        previewBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        previewBtn.classList.add('glass-btn');
        updateStepProgress(2, 80, 'current');

        // Check if user overrode auto-detection
        const detectedSheets = window.lastDetectedSheets;
        if (detectedSheets) {
            const masterOverridden = detectedSheets.masterbom && detectedSheets.masterbom !== masterSheet;
            const statusOverridden = detectedSheets.status && detectedSheets.status !== statusSheet;

            if (masterOverridden || statusOverridden) {
                let overrideMsg = 'User override detected: ';
                if (masterOverridden) overrideMsg += `MasterBOM changed from "${detectedSheets.masterbom}" to "${masterSheet}"`;
                if (masterOverridden && statusOverridden) overrideMsg += ', ';
                if (statusOverridden) overrideMsg += `Status changed from "${detectedSheets.status}" to "${statusSheet}"`;

                addLogEntry('INFO', overrideMsg);
                showToast('Sheet selection updated', 'info');
            }
        }

        addLogEntry('SUCCESS', `Final selection: MasterBOM="${masterSheet}", Status="${statusSheet}"`);

        // Update preview button text to show readiness
        previewBtn.innerHTML = '<i class="fas fa-eye mr-2"></i>Preview Selected Sheets';

        // Show selection status indicator
        showSelectionStatus(true);

    } else if (masterSheet && statusSheet && masterSheet === statusSheet) {
        previewBtn.disabled = true;
        previewBtn.classList.add('opacity-50', 'cursor-not-allowed');
        previewBtn.classList.remove('glass-btn');
        updateStepProgress(2, 30, 'current');
        addLogEntry('WARNING', 'Same sheet selected for both MasterBOM and Status - please choose different sheets');

        previewBtn.innerHTML = '<i class="fas fa-exclamation-triangle mr-2"></i>Select Different Sheets';

    } else {
        previewBtn.disabled = true;
        previewBtn.classList.add('opacity-50', 'cursor-not-allowed');
        previewBtn.classList.remove('glass-btn');
        updateStepProgress(2, 20, 'current');

        if (!masterSheet && !statusSheet) {
            addLogEntry('INFO', 'Please select both MasterBOM and Status sheets');
        } else if (!masterSheet) {
            addLogEntry('INFO', 'Please select a MasterBOM sheet');
        } else if (!statusSheet) {
            addLogEntry('INFO', 'Please select a Status sheet');
        }

        previewBtn.innerHTML = '<i class="fas fa-eye mr-2"></i>Preview Sheets';
        previewBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
        previewBtn.classList.add('bg-gray-400');

        // Hide selection status indicator
        showSelectionStatus(false);
    }

    // Update selection indicators
    updateSelectionIndicators(masterSheet, statusSheet);
}

function showSelectionStatus(show) {
    const statusElement = document.getElementById('selection-status');
    if (!statusElement) return;

    if (show) {
        statusElement.classList.remove('hidden');
        statusElement.classList.add('selection-status');
    } else {
        statusElement.classList.add('hidden');
        statusElement.classList.remove('selection-status');
    }
}

function updateSelectionIndicators(masterSheet, statusSheet) {
    const masterSelect = document.getElementById('master-sheet-select');
    const statusSelect = document.getElementById('status-sheet-select');

    // Add visual feedback to the select elements
    if (masterSheet) {
        masterSelect.classList.remove('border-gray-300');
        masterSelect.classList.add('border-green-400', 'bg-green-50');
    } else {
        masterSelect.classList.remove('border-green-400', 'bg-green-50');
        masterSelect.classList.add('border-gray-300');
    }

    if (statusSheet) {
        statusSelect.classList.remove('border-gray-300');
        statusSelect.classList.add('border-green-400', 'bg-green-50');
    } else {
        statusSelect.classList.remove('border-green-400', 'bg-green-50');
        statusSelect.classList.add('border-gray-300');
    }
}

function previewSheets() {
    const masterSheet = document.getElementById('master-sheet-select').value;
    const statusSheet = document.getElementById('status-sheet-select').value;

    if (!masterSheet || !statusSheet) {
        addLogEntry('ERROR', 'Both MasterBOM and Status sheets must be selected');
        showToast('Please select both sheets', 'error');
        return;
    }

    if (masterSheet === statusSheet) {
        addLogEntry('ERROR', 'MasterBOM and Status must be different sheets');
        showToast('Please select different sheets', 'error');
        return;
    }

    addLogEntry('INFO', 'Navigating to sheet preview and data profiling...');
    updateStepProgress(2, 100, 'completed');

    // Show loading state
    showLoading('Loading sheet preview...');

    // Navigate to profile page with both sheets
    window.location.href = `/profile?file_id=${currentFileId}&master_sheet=${encodeURIComponent(masterSheet)}&status_sheet=${encodeURIComponent(statusSheet)}`;
}

// Step Management Functions
function enableStep(stepNumber) {
    // Mark previous step as completed
    if (stepNumber > 1) {
        updateStepProgress(stepNumber - 1, 100, 'completed');
    }

    // Set current step as active
    updateStepProgress(stepNumber, 0, 'current');

    currentStep = stepNumber;

    // Show/hide sections based on step
    showStepSection(stepNumber);

    // Add log entry for step transition
    if (STEPS[stepNumber]) {
        addLogEntry('INFO', `Starting ${STEPS[stepNumber].name}: ${STEPS[stepNumber].description}`);
    }
}

function showStepSection(stepNumber) {
    // Hide all sections first
    const sections = ['sheet-selection', 'preview-section', 'profile-section', 'transform-section'];
    sections.forEach(sectionId => {
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.add('hidden');
        }
    });

    // Show the appropriate section
    let sectionToShow = '';
    switch(stepNumber) {
        case 2:
            sectionToShow = 'sheet-selection';
            break;
        case 3:
            sectionToShow = 'preview-section';
            break;
        case 4:
            sectionToShow = 'transform-section';
            updateTransformSection();
            break;
    }

    if (sectionToShow) {
        const section = document.getElementById(sectionToShow);
        if (section) {
            section.classList.remove('hidden');
        }
    }
}

function updateTransformSection() {
    const masterSelect = document.getElementById('master-sheet-select');
    const statusSelect = document.getElementById('status-sheet-select');

    const masterSheetDisplay = document.getElementById('selected-master-sheet');
    const statusSheetDisplay = document.getElementById('selected-status-sheet');

    if (masterSelect && masterSheetDisplay) {
        masterSheetDisplay.textContent = masterSelect.value || 'Not selected';
    }

    if (statusSelect && statusSheetDisplay) {
        statusSheetDisplay.textContent = statusSelect.value || 'Not selected';
    }
}

function resetSteps() {
    for (let i = 1; i <= 4; i++) {
        const stepElement = document.getElementById(`step-${i}`);
        if (stepElement) {
            stepElement.classList.remove('bg-blue-600', 'bg-green-600', 'text-white');
            stepElement.classList.add('bg-gray-300', 'text-gray-600');
            stepElement.textContent = i;
            
            // Reset text colors
            const stepContainer = stepElement.parentElement.parentElement;
            const title = stepContainer.querySelector('h3');
            const subtitle = stepContainer.querySelector('p');
            
            if (title) {
                title.classList.remove('text-gray-900');
                title.classList.add('text-gray-500');
            }
            if (subtitle) {
                subtitle.classList.remove('text-gray-500');
                subtitle.classList.add('text-gray-400');
            }
        }
        
        // Reset progress bars
        if (i < 4) {
            const progressBar = document.getElementById(`progress-${i}-${i + 1}`);
            if (progressBar) {
                progressBar.style.width = '0%';
            }
        }
    }
    
    // Enable first step
    enableStep(1);
    
    // Hide sections
    const sections = ['sheet-selection', 'preview-section', 'profile-section', 'transform-section'];
    sections.forEach(sectionId => {
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.add('hidden');
        }
    });
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Enhanced Toast Notification System
function showToast(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    }[type] || 'fas fa-info-circle';

    const bgColor = {
        'success': 'bg-green-50 border-green-400 text-green-800',
        'error': 'bg-red-50 border-red-400 text-red-800',
        'warning': 'bg-yellow-50 border-yellow-400 text-yellow-800',
        'info': 'bg-blue-50 border-blue-400 text-blue-800'
    }[type] || 'bg-blue-50 border-blue-400 text-blue-800';

    toast.className = `fixed top-4 right-4 p-4 rounded-lg shadow-xl z-50 transform transition-all duration-300 border-l-4 ${bgColor}`;

    toast.innerHTML = `
        <div class="flex items-center">
            <div class="flex-shrink-0">
                <i class="${icon} text-lg"></i>
            </div>
            <div class="ml-3 flex-1">
                <p class="text-sm font-medium">${escapeHtml(message)}</p>
            </div>
            <div class="ml-4">
                <button class="text-gray-400 hover:text-gray-600 transition-colors" onclick="removeToast(this.closest('.toast'))">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;

    // Initial state for animation
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';

    container.appendChild(toast);

    // Trigger animation
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 10);

    // Auto-remove after duration
    setTimeout(() => {
        removeToast(toast);
    }, duration);

    // Also add to log panel
    addLogEntry(type.toUpperCase(), message);
}

function removeToast(toast) {
    if (!toast || !toast.parentElement) return;

    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';

    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 300);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'fixed top-4 right-4 z-50 space-y-2';
    document.body.appendChild(container);
    return container;
}

// Loading Overlay
function showLoading(message = 'Processing...') {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.querySelector('span').textContent = message;
        overlay.classList.remove('hidden');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
    }
}

// Transform Functions
async function runTransform() {
    console.log('🔧 Starting ETL Transform...');

    // Get file ID and sheet names from URL parameters or stored values
    const urlParams = new URLSearchParams(window.location.search);
    const fileId = urlParams.get('file_id') || currentFileId;
    const masterSheet = urlParams.get('master_sheet') || localStorage.getItem('selectedMasterSheet');
    const statusSheet = urlParams.get('status_sheet') || localStorage.getItem('selectedStatusSheet');

    console.log('Transform parameters from URL:', {
        fileId,
        masterSheet,
        statusSheet,
        currentURL: window.location.href
    });

    if (!fileId) {
        showToast('No file ID found. Please upload a file first.', 'error');
        console.error('Missing file ID - URL params:', Object.fromEntries(urlParams));
        return;
    }

    if (!masterSheet || !statusSheet) {
        showToast('Missing sheet information. Please select sheets first.', 'error');
        console.error('Missing sheets - master:', masterSheet, 'status:', statusSheet);
        return;
    }

    // Store in global variable for future use
    currentFileId = fileId;

    console.log('Transform parameters confirmed:', {
        fileId,
        masterSheet,
        statusSheet,
        url: window.location.href
    });

    // Show progress modal
    showProgressModal();

    try {
        const transformRequest = {
            file_id: fileId,
            master_sheet: masterSheet,
            status_sheet: statusSheet,
            options: {
                id_col: "Part ID",  // Default ID column
                date_cols: []       // Will be auto-detected
            }
        };

        console.log('Sending transform request:', transformRequest);

        // Start progress simulation
        startProgressSimulation();

        const response = await fetch('/api/transform', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(transformRequest)
        });

        console.log('Transform response status:', response.status);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || error.error || 'Transform failed');
        }

        const result = await response.json();
        console.log('Transform result:', result);

        if (result.success) {
            // Complete progress
            completeProgress();

            // Store result in sessionStorage for results page
            sessionStorage.setItem(`transform_result_${fileId}`, JSON.stringify(result));

            showToast('ETL transformation completed successfully!', 'success');

            // Redirect to results page after a short delay
            setTimeout(() => {
                hideProgressModal();
                window.location.href = `/results?file_id=${fileId}`;
            }, 2000);
        } else {
            throw new Error(result.error || 'Transform failed');
        }

    } catch (error) {
        console.error('Transform error:', error);
        hideProgressModal();
        showToast(`Transform failed: ${error.message}`, 'error');
    }
}

// Progress Modal Functions
let progressTimer = null;
let progressStartTime = null;
let currentProgressStep = 0;

const progressSteps = [
    { title: "Initializing transformation", description: "Setting up processing environment and validating input files..." },
    { title: "Reading Excel sheets", description: "Loading MasterBOM and Status sheets from uploaded file..." },
    { title: "Cleaning column headers", description: "Standardizing column names and removing special characters..." },
    { title: "Validating data structure", description: "Checking data integrity and identifying key columns..." },
    { title: "Processing MasterBOM data", description: "Cleaning part numbers and standardizing item descriptions..." },
    { title: "Calculating plant-item-status", description: "Creating normalized plant-item-status relationships..." },
    { title: "Resolving duplicates", description: "Applying Morocco supplier prioritization rules..." },
    { title: "Merging data tables", description: "Combining MasterBOM and Status data with proper joins..." },
    { title: "Generating fact tables", description: "Creating fact_parts table with dimensional relationships..." },
    { title: "Creating dimension tables", description: "Building date dimensions and lookup tables..." },
    { title: "Exporting processed files", description: "Saving CSV and Parquet files for analysis..." },
    { title: "Finalizing transformation", description: "Completing data validation and generating summary..." }
];

function showProgressModal() {
    const modal = document.getElementById('progress-modal');
    if (modal) {
        modal.classList.remove('hidden');
        progressStartTime = Date.now();
        currentProgressStep = 0;

        // Start timer
        progressTimer = setInterval(updateProgressTimer, 1000);

        // Initialize progress display
        updateProgressDisplay(0);
        initializeProgressSteps();
    }
}

function hideProgressModal() {
    const modal = document.getElementById('progress-modal');
    if (modal) {
        modal.classList.add('hidden');

        // Clear timer
        if (progressTimer) {
            clearInterval(progressTimer);
            progressTimer = null;
        }
    }
}

function updateProgressTimer() {
    if (!progressStartTime) return;

    const elapsed = Math.floor((Date.now() - progressStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;

    const timerElement = document.getElementById('progress-timer');
    if (timerElement) {
        timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

function updateProgressDisplay(percentage) {
    const progressBar = document.getElementById('progress-bar');
    const progressPercentage = document.getElementById('progress-percentage');

    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
    }

    if (progressPercentage) {
        progressPercentage.textContent = `${Math.round(percentage)}%`;
    }
}

function initializeProgressSteps() {
    const stepsContainer = document.getElementById('progress-steps');
    if (!stepsContainer) return;

    stepsContainer.innerHTML = '';

    progressSteps.forEach((step, index) => {
        const stepElement = document.createElement('div');
        stepElement.id = `progress-step-${index}`;
        stepElement.className = 'flex items-start space-x-3 p-3 rounded-lg transition-all duration-300';

        stepElement.innerHTML = `
            <div class="flex-shrink-0 mt-1">
                <div class="w-6 h-6 rounded-full border-2 border-gray-300 flex items-center justify-center">
                    <i class="fas fa-circle text-gray-300 text-xs"></i>
                </div>
            </div>
            <div class="flex-1 min-w-0">
                <div class="text-sm font-medium text-gray-900">${step.title}</div>
                <div class="text-xs text-gray-500 mt-1">${step.description}</div>
            </div>
        `;

        stepsContainer.appendChild(stepElement);
    });
}

function startProgressSimulation() {
    let progress = 0;
    const totalSteps = progressSteps.length;
    const stepDuration = 2000; // 2 seconds per step

    const progressInterval = setInterval(() => {
        if (currentProgressStep < totalSteps) {
            // Update current step
            updateProgressStep(currentProgressStep, 'active');

            // Calculate progress
            progress = ((currentProgressStep + 1) / totalSteps) * 90; // Leave 10% for completion
            updateProgressDisplay(progress);

            currentProgressStep++;
        } else {
            clearInterval(progressInterval);
        }
    }, stepDuration);
}

function updateProgressStep(stepIndex, status) {
    const stepElement = document.getElementById(`progress-step-${stepIndex}`);
    if (!stepElement) return;

    const icon = stepElement.querySelector('i');
    const circle = stepElement.querySelector('.w-6');

    switch (status) {
        case 'active':
            stepElement.className = 'flex items-start space-x-3 p-3 rounded-lg bg-blue-50 border border-blue-200 transition-all duration-300';
            circle.className = 'w-6 h-6 rounded-full border-2 border-blue-500 bg-blue-500 flex items-center justify-center';
            icon.className = 'fas fa-spinner fa-spin text-white text-xs';
            break;
        case 'completed':
            stepElement.className = 'flex items-start space-x-3 p-3 rounded-lg bg-green-50 border border-green-200 transition-all duration-300';
            circle.className = 'w-6 h-6 rounded-full border-2 border-green-500 bg-green-500 flex items-center justify-center';
            icon.className = 'fas fa-check text-white text-xs';
            break;
        case 'pending':
        default:
            stepElement.className = 'flex items-start space-x-3 p-3 rounded-lg transition-all duration-300';
            circle.className = 'w-6 h-6 rounded-full border-2 border-gray-300 flex items-center justify-center';
            icon.className = 'fas fa-circle text-gray-300 text-xs';
            break;
    }
}

function completeProgress() {
    // Mark all steps as completed
    for (let i = 0; i < progressSteps.length; i++) {
        updateProgressStep(i, 'completed');
    }

    // Set progress to 100%
    updateProgressDisplay(100);

    // Update modal header
    const header = document.querySelector('#progress-modal h3');
    if (header) {
        header.innerHTML = '<i class="fas fa-check-circle mr-2 text-green-400"></i>ETL Transformation Complete';
    }
}

// Enhanced Progress Monitoring for Results Page
let progressPollingInterval = null;

function initializeDetailedProgress() {
    const progressSteps = document.getElementById('progress-steps');
    if (!progressSteps) return;

    // Start polling for progress updates
    startProgressPolling();
}

function startProgressPolling() {
    if (progressPollingInterval) {
        clearInterval(progressPollingInterval);
    }

    progressPollingInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/progress/status');
            const progressData = await response.json();

            if (progressData && progressData.status) {
                updateDetailedProgressDisplay(progressData);
            }
        } catch (error) {
            console.error('Error polling progress:', error);
        }
    }, 1000); // Poll every second
}

function updateDetailedProgressDisplay(progressData) {
    const { status, operation, description, progress, last_activity } = progressData;

    // Update step based on current operation
    if (operation.includes('MasterBOM')) {
        updateStepStatus('masterbom', progress, description, 'in-progress');
    } else if (operation.includes('Status')) {
        updateStepStatus('masterbom', 100, 'MasterBOM processing complete', 'completed');
        updateStepStatus('status', progress, description, 'in-progress');
    } else if (operation.includes('Date')) {
        updateStepStatus('masterbom', 100, 'MasterBOM processing complete', 'completed');
        updateStepStatus('status', 100, 'Status sheet processing complete', 'completed');
        updateStepStatus('dates', progress, description, 'in-progress');
    } else if (operation.includes('File') || operation.includes('Complete')) {
        updateStepStatus('masterbom', 100, 'MasterBOM processing complete', 'completed');
        updateStepStatus('status', 100, 'Status sheet processing complete', 'completed');
        updateStepStatus('dates', 100, 'Date dimension creation complete', 'completed');
        updateStepStatus('files', progress, description, progress >= 100 ? 'completed' : 'in-progress');

        if (progress >= 100) {
            stopProgressPolling();
        }
    }
}

function updateStepStatus(stepId, progress, statusText, state) {
    const stepElement = document.getElementById(`step-${stepId}`);
    const iconElement = document.getElementById(`${stepId}-icon`);
    const statusElement = document.getElementById(`${stepId}-status`);
    const progressElement = document.getElementById(`${stepId}-progress`);
    const barElement = document.getElementById(`${stepId}-bar`);

    if (!stepElement) return;

    // Update status text
    if (statusElement) {
        statusElement.textContent = statusText;
    }

    // Update progress percentage
    if (progressElement) {
        progressElement.textContent = `${Math.round(progress)}%`;
    }

    // Update progress bar
    if (barElement) {
        barElement.style.width = `${progress}%`;
    }

    // Update visual state
    if (state === 'completed') {
        stepElement.classList.remove('border-gray-300');
        stepElement.classList.add('border-green-400', 'bg-green-50');

        if (iconElement) {
            iconElement.innerHTML = '<i class="fas fa-check text-green-600 text-sm"></i>';
            iconElement.classList.remove('bg-gray-300');
            iconElement.classList.add('bg-green-500');
        }
    } else if (state === 'in-progress') {
        stepElement.classList.remove('border-gray-300');
        stepElement.classList.add('border-blue-400', 'bg-blue-50');

        if (iconElement) {
            iconElement.innerHTML = '<i class="fas fa-spinner fa-spin text-blue-600 text-sm"></i>';
            iconElement.classList.remove('bg-gray-300');
            iconElement.classList.add('bg-blue-500');
        }
    }
}

function stopProgressPolling() {
    if (progressPollingInterval) {
        clearInterval(progressPollingInterval);
        progressPollingInterval = null;
    }
}

// Download Functions for Organized Files
function downloadPowerBIPackage() {
    const fileId = getCurrentFileId();
    if (!fileId) {
        showToast('No file ID available for download', 'error');
        return;
    }

    window.location.href = `/download/powerbi/${fileId}`;
    showToast('Downloading Power BI package...', 'success');
}

function downloadCSVPackage() {
    const fileId = getCurrentFileId();
    if (!fileId) {
        showToast('No file ID available for download', 'error');
        return;
    }

    window.location.href = `/download/csv/${fileId}`;
    showToast('Downloading CSV package...', 'success');
}

function downloadDAXMeasures() {
    const fileId = getCurrentFileId();
    if (!fileId) {
        showToast('No file ID available for download', 'error');
        return;
    }

    window.location.href = `/download/dax/${fileId}`;
    showToast('Downloading DAX measures file...', 'success');
}

function getCurrentFileId() {
    // Extract file ID from URL parameters or global variable
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('file_id') || window.currentFileId;
}

/**
 * Toggle showing all sheets in dropdowns (manual override for smart filtering)
 */
function toggleShowAllSheets() {
    const btn = document.getElementById('show-all-sheets-btn');
    const isShowingAll = btn.textContent.includes('Hide');
    
    if (isShowingAll) {
        // Return to smart filtering
        if (window.lastDetectedSheets && uploadedSheets) {
            populateSheetSelectors(uploadedSheets, window.lastDetectedSheets);
            btn.innerHTML = '<i class="fas fa-eye mr-2"></i>Show All Sheets';
            addLogEntry('INFO', 'Returned to smart filtering mode.');
            showToast('Smart filtering restored', 'info');
        }
    } else {
        // Show all sheets
        if (uploadedSheets) {
            populateAllSheets(uploadedSheets, window.lastDetectedSheets);
            btn.innerHTML = '<i class="fas fa-eye-slash mr-2"></i>Hide Filtered View';
            addLogEntry('WARNING', 'Manual override: Showing all sheets in both dropdowns.');
            showToast('Showing all sheets (filtering disabled)', 'warning');
        }
    }
}

/**
 * Populate dropdowns with all sheets (override smart filtering)
 */
function populateAllSheets(sheetNames, detectedSheets) {
    const masterSelect = document.getElementById('master-sheet-select');
    const statusSelect = document.getElementById('status-sheet-select');

    if (!masterSelect || !statusSelect) return;

    // Clear and repopulate with all sheets
    masterSelect.innerHTML = '<option value=""></option>';
    statusSelect.innerHTML = '<option value=""></option>';

    // Add warning headers
    const masterWarning = new Option('⚠️ Manual Override: Showing ALL sheets', '');
    masterWarning.disabled = true;
    masterWarning.style.color = '#dc2626';
    masterWarning.style.fontStyle = 'italic';
    masterSelect.add(masterWarning);

    const statusWarning = new Option('⚠️ Manual Override: Showing ALL sheets', '');
    statusWarning.disabled = true;
    statusWarning.style.color = '#dc2626';
    statusWarning.style.fontStyle = 'italic';
    statusSelect.add(statusWarning);

    // Get detection data for styling
    const masterBomCandidates = detectedSheets?.suggestions?.masterbom_candidates || [];
    const statusCandidates = detectedSheets?.suggestions?.status_candidates || [];

    // Add all sheets to both dropdowns
    sheetNames.forEach(sheet => {
        // Master dropdown
        const masterOption = new Option(sheet, sheet);
        const masterCandidate = masterBomCandidates.find(([s]) => s === sheet);
        
        if (masterCandidate) {
            const [, score] = masterCandidate;
            const confidence = Math.round(score * 100);
            const isDetected = detectedSheets?.masterbom === sheet;
            
            if (isDetected) {
                masterOption.text = `${sheet} ✨ (Auto-detected - ${confidence}%)`;
                masterOption.style.fontWeight = 'bold';
                masterOption.style.color = '#059669';
            } else {
                masterOption.text = `${sheet} (${confidence}% BOM match)`;
                masterOption.style.color = '#6b7280';
            }
        }
        
        masterSelect.add(masterOption);

        // Status dropdown
        const statusOption = new Option(sheet, sheet);
        const statusCandidate = statusCandidates.find(([s]) => s === sheet);
        
        if (statusCandidate) {
            const [, score] = statusCandidate;
            const confidence = Math.round(score * 100);
            const isDetected = detectedSheets?.status === sheet;
            
            if (isDetected) {
                statusOption.text = `${sheet} ✨ (Auto-detected - ${confidence}%)`;
                statusOption.style.fontWeight = 'bold';
                statusOption.style.color = '#059669';
            } else {
                statusOption.text = `${sheet} (${confidence}% Status match)`;
                statusOption.style.color = '#6b7280';
            }
        }
        
        statusSelect.add(statusOption);
    });

    // Auto-select if previously detected
    if (detectedSheets?.masterbom) {
        masterSelect.value = detectedSheets.masterbom;
    }
    if (detectedSheets?.status) {
        statusSelect.value = detectedSheets.status;
    }
}

// Export functions for global access
window.toggleShowAllSheets = toggleShowAllSheets;

// Export functions for use in templates
window.ETLDashboard = {
    showToast,
    showLoading,
    hideLoading,
    formatFileSize,
    escapeHtml,
    enableStep,
    resetSteps,
    runTransform,
    showProgressModal,
    hideProgressModal,
    initializeDetailedProgress,
    downloadPowerBIPackage,
    downloadCSVPackage,
    downloadDAXMeasures
};
