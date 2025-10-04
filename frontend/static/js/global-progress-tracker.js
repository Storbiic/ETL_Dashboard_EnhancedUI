/**
 * Global Progress Tracker - Single Horizontal Line Design
 * Sticky progress bar that works on all screen sizes
 * Syncs with localStorage for cross-page persistence
 */

const GlobalProgressTracker = {
    // Step definitions
    steps: {
        1: { name: 'Upload Excel Workbook', icon: 'fa-cloud-upload-alt' },
        2: { name: 'Select & Preview Sheets', icon: 'fa-table' },
        3: { name: 'Profile Data Quality', icon: 'fa-chart-bar' },
        4: { name: 'Transform Data', icon: 'fa-cogs' }
    },

    currentStep: 1,
    percentage: 0,
    stepStatus: { 1: 'current', 2: 'pending', 3: 'pending', 4: 'pending' },
    completedSteps: [],

    // Initialize the tracker
    init: function() {
        console.log('[GlobalProgressTracker] Initializing...');
        this.loadState();
        this.updateUI();
        
        // Listen for storage events from other tabs
        window.addEventListener('storage', (e) => {
            if (e.key === 'etl_global_progress') {
                console.log('[GlobalProgressTracker] State updated from another tab');
                this.loadState();
                this.updateUI();
            }
        });
        
        console.log('[GlobalProgressTracker] Initialized successfully');
    },

    // Load state from localStorage
    loadState: function() {
        const saved = localStorage.getItem('etl_global_progress');
        if (saved) {
            try {
                const state = JSON.parse(saved);
                this.currentStep = state.currentStep || 1;
                this.percentage = state.percentage || 0;
                this.stepStatus = state.stepStatus || { 1: 'current', 2: 'pending', 3: 'pending', 4: 'pending' };
                console.log('[GlobalProgressTracker] State loaded:', state);
            } catch (e) {
                console.error('[GlobalProgressTracker] Error loading state:', e);
                this.resetState();
            }
        } else {
            this.resetState();
        }
    },

    // Save state to localStorage
    saveState: function() {
        const state = {
            currentStep: this.currentStep,
            percentage: this.percentage,
            stepStatus: this.stepStatus,
            timestamp: new Date().toISOString()
        };
        localStorage.setItem('etl_global_progress', JSON.stringify(state));
        console.log('[GlobalProgressTracker] State saved:', state);
    },

    // Reset to initial state
    resetState: function() {
        this.currentStep = 1;
        this.percentage = 0;
        this.stepStatus = { 1: 'current', 2: 'pending', 3: 'pending', 4: 'pending' };
        this.saveState();
    },

    // Update a specific step
    updateStep: function(stepNumber, status = 'current', percentage = 0) {
        console.log(`[GlobalProgressTracker] Updating step ${stepNumber} to ${status} (${percentage}%)`);
        
        this.currentStep = stepNumber;
        this.stepStatus[stepNumber] = status;
        
        // Calculate overall percentage: each step is 25%
        const basePercentage = (stepNumber - 1) * 25;
        const stepPercentage = percentage * 0.25;
        this.percentage = Math.round(basePercentage + stepPercentage);
        
        // Update previous steps to completed
        for (let i = 1; i < stepNumber; i++) {
            this.stepStatus[i] = 'completed';
        }
        
        // Update future steps to pending
        for (let i = stepNumber + 1; i <= 4; i++) {
            this.stepStatus[i] = 'pending';
        }
        
        this.saveState();
        this.updateUI();
    },

    // Update the global UI
    updateUI: function() {
        try {
            // Update step name
            const stepNameEl = document.getElementById('global-step-name');
            if (stepNameEl && this.steps[this.currentStep]) {
                stepNameEl.textContent = `Step ${this.currentStep}: ${this.steps[this.currentStep].name}`;
            }

            // Update percentage
            const percentageEl = document.getElementById('global-step-percentage');
            if (percentageEl) {
                percentageEl.textContent = `${this.percentage}% Complete`;
            }

            // Update progress bar
            const progressEl = document.getElementById('global-overall-progress');
            if (progressEl) {
                progressEl.style.width = `${this.percentage}%`;
            }

            // Update each step
            for (let step = 1; step <= 4; step++) {
                const status = this.stepStatus[step] || 'pending';
                this.updateStepIcon(step, status);
            }

            // Update connectors
            this.updateConnectors();
        } catch (error) {
            console.error('[GlobalProgressTracker] Error updating UI:', error);
        }
    },

    // Update a single step icon
    updateStepIcon: function(stepNumber, status) {
        const stepEl = document.getElementById(`global-step-${stepNumber}`);
        if (!stepEl) return;

        // Clear existing classes
        stepEl.className = 'flex items-center justify-center w-10 h-10 rounded-full font-bold text-xs transition-all duration-300';

        // Apply status-specific styling
        switch(status) {
            case 'completed':
                stepEl.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
                stepEl.style.color = 'white';
                stepEl.classList.add('shadow-md');
                stepEl.innerHTML = '<i class="fas fa-check"></i>';
                break;
                
            case 'current':
                stepEl.style.background = 'linear-gradient(135deg, #7f9ec3 0%, #5d9bad 100%)';
                stepEl.style.color = 'white';
                stepEl.classList.add('shadow-md', 'animate-pulse');
                stepEl.innerHTML = `<i class="fas ${this.steps[stepNumber].icon}"></i>`;
                break;
                
            case 'error':
                stepEl.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
                stepEl.style.color = 'white';
                stepEl.classList.add('shadow-md');
                stepEl.innerHTML = '<i class="fas fa-exclamation"></i>';
                break;
                
            default: // pending
                stepEl.style.background = '';
                stepEl.style.color = '';
                stepEl.classList.add('bg-gray-200', 'text-gray-500');
                stepEl.innerHTML = `<i class="fas ${this.steps[stepNumber].icon}"></i>`;
                break;
        }
    },

    // Update connector lines between steps
    updateConnectors: function() {
        for (let i = 1; i <= 3; i++) {
            const connectorEl = document.getElementById(`global-connector-${i}`);
            if (!connectorEl) continue;

            // Connector is filled if the previous step is completed
            if (this.stepStatus[i] === 'completed') {
                connectorEl.style.width = '100%';
            } else if (this.stepStatus[i] === 'current' && i === this.currentStep) {
                // Partial fill based on current step progress
                const stepProgress = (this.percentage - (i - 1) * 25) / 25 * 100;
                connectorEl.style.width = `${Math.max(0, Math.min(100, stepProgress))}%`;
            } else {
                connectorEl.style.width = '0%';
            }
        }
    },

    // Complete a step
    completeStep: function(stepNumber) {
        this.updateStep(stepNumber, 'completed', 100);
        
        // Auto-advance to next step if not at the end
        if (stepNumber < 4) {
            setTimeout(() => {
                this.updateStep(stepNumber + 1, 'current', 0);
            }, 300);
        }
    },

    // Mark a step as having an error
    errorStep: function(stepNumber) {
        this.updateStep(stepNumber, 'error', 0);
    },

    // Reset entire workflow
    reset: function() {
        console.log('[GlobalProgressTracker] Resetting workflow');
        this.resetState();
        this.updateUI();
    }
};

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        try {
            GlobalProgressTracker.init();
        } catch (error) {
            console.error('[GlobalProgressTracker] Initialization error:', error);
        }
    });
} else {
    // DOM already loaded
    try {
        GlobalProgressTracker.init();
    } catch (error) {
        console.error('[GlobalProgressTracker] Initialization error:', error);
    }
}

// Export to window for global access
if (typeof window !== 'undefined') {
    window.GlobalProgressTracker = GlobalProgressTracker;
}

// Export for use in other scripts
window.GlobalProgressTracker = GlobalProgressTracker;
