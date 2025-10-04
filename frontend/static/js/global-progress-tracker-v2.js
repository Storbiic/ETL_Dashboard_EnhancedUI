/**
 * Global Progress Tracker - Single Horizontal Line Sticky Design
 * Fully responsive progress bar that works on all screen sizes
 * Syncs with localStorage for cross-page persistence
 */

const GlobalProgressTracker = {
    // Step definitions (4 steps matching actual workflow)
    steps: {
        1: { name: 'Upload Excel Workbook', icon: 'fa-cloud-upload-alt' },
        2: { name: 'Preview & Profile Data', icon: 'fa-chart-line' },
        3: { name: 'Transform & Export', icon: 'fa-cogs' },
        4: { name: 'Download Results', icon: 'fa-download' }
    },

    currentStep: 1,
    percentage: 0,
    stepStatus: { 1: 'current', 2: 'pending', 3: 'pending', 4: 'pending' },
    completedSteps: [],

    // Initialize the tracker
    init: function() {
        console.log('[GlobalProgressTracker] Initializing sticky progress tracker...');
        
        // Check if we're on the home/index page - reset if so
        const currentPath = window.location.pathname;
        const isHomePage = currentPath === '/' || currentPath.endsWith('index.html') || currentPath.endsWith('/');
        
        if (isHomePage) {
            console.log('[GlobalProgressTracker] On home page - resetting to initial state');
            this.resetState();
        } else {
            this.loadState();
        }
        
        this.updateUI();
        this.attachEventListeners();
        
        // Listen for storage events from other tabs
        window.addEventListener('storage', (e) => {
            if (e.key === 'etl_global_progress') {
                console.log('[GlobalProgressTracker] State updated from another tab');
                this.loadState();
                this.updateUI();
            }
        });
    },

    // Attach click and keyboard handlers
    attachEventListeners: function() {
        for (let step = 1; step <= 4; step++) {
            const stepEl = document.getElementById(`global-step-${step}`);
            if (stepEl) {
                // Click handler
                stepEl.addEventListener('click', () => this.handleStepClick(step));
                
                // Keyboard handler for accessibility
                stepEl.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this.handleStepClick(step);
                    }
                });
            }
        }
    },

    // Handle step click navigation
    handleStepClick: function(stepNumber) {
        // Only allow navigation to completed or current step
        if (this.stepStatus[stepNumber] === 'completed' || stepNumber === this.currentStep) {
            console.log(`[GlobalProgressTracker] Navigating to step ${stepNumber}`);
            // Dispatch custom event that pages can listen to
            const event = new CustomEvent('stepNavigation', { detail: { step: stepNumber } });
            window.dispatchEvent(event);
        }
    },

    // Load state from localStorage
    loadState: function() {
        try {
            const saved = localStorage.getItem('etl_global_progress');
            if (saved) {
                const state = JSON.parse(saved);
                this.currentStep = state.currentStep || 1;
                this.percentage = state.percentage || 0;
                this.stepStatus = state.stepStatus || { 1: 'current', 2: 'pending', 3: 'pending', 4: 'pending' };
                this.completedSteps = state.completedSteps || [];
                console.log('[GlobalProgressTracker] State loaded:', state);
            }
        } catch (error) {
            console.error('[GlobalProgressTracker] Error loading state:', error);
        }
    },

    // Save state to localStorage
    saveState: function() {
        const state = {
            currentStep: this.currentStep,
            percentage: this.percentage,
            stepStatus: this.stepStatus,
            completedSteps: this.completedSteps,
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
        this.completedSteps = [];
        this.saveState();
        console.log('[GlobalProgressTracker] State reset to initial');
    },

    // Update a specific step
    updateStep: function(stepNumber, status = 'current', percentage = 0) {
        console.log(`[GlobalProgressTracker] Updating step ${stepNumber} to ${status} (${percentage}%)`);
        
        // Validate inputs (4 steps)
        if (stepNumber < 1 || stepNumber > 4) return;
        
        this.currentStep = stepNumber;
        this.percentage = percentage;
        this.stepStatus[stepNumber] = status;
        
        // Mark previous steps as completed
        for (let i = 1; i < stepNumber; i++) {
            this.stepStatus[i] = 'completed';
            if (!this.completedSteps.includes(i)) {
                this.completedSteps.push(i);
            }
        }
        
        // Mark future steps as pending
        for (let i = stepNumber + 1; i <= 4; i++) {
            if (status === 'completed' && i === stepNumber + 1) {
                // Next step becomes current
                this.stepStatus[i] = 'current';
            } else {
                this.stepStatus[i] = 'pending';
            }
        }
        
        // If current step is completed, add to completed list
        if (status === 'completed' && !this.completedSteps.includes(stepNumber)) {
            this.completedSteps.push(stepNumber);
        }
        
        this.saveState();
        this.updateUI();
    },

    // Update the global UI with responsive design
    updateUI: function() {
        try {
            // Update step name (clean format without "Step X:")
            const stepNameEl = document.getElementById('global-step-name');
            if (stepNameEl && this.steps[this.currentStep]) {
                stepNameEl.textContent = this.steps[this.currentStep].name;
            }

            // Calculate overall progress (0-100% across all 4 steps)
            // Each step = 25%, current step progress adds partial
            let overallProgress = 0;
            
            // Count completed steps (each worth 25%)
            const completedCount = this.completedSteps.length;
            overallProgress += completedCount * 25;
            
            // Add current step's partial progress
            if (this.stepStatus[this.currentStep] === 'current') {
                overallProgress += (this.percentage * 0.25);
            }
            
            // Cap at 100%
            overallProgress = Math.min(100, Math.round(overallProgress));

            // Update percentage display
            const percentageEl = document.getElementById('global-step-percentage');
            if (percentageEl) {
                percentageEl.textContent = `${overallProgress}%`;
            }

            // Update progress bar with smooth animation
            const progressEl = document.getElementById('global-overall-progress');
            if (progressEl) {
                progressEl.style.width = `${overallProgress}%`;
            }

            // Update each step icon (4 steps)
            for (let step = 1; step <= 4; step++) {
                const status = this.stepStatus[step] || 'pending';
                this.updateStepIcon(step, status);
            }

            // Update connector lines
            this.updateConnectors();
        } catch (error) {
            console.error('[GlobalProgressTracker] Error updating UI:', error);
        }
    },

    // Update step icon with new responsive classes
    updateStepIcon: function(stepNumber, status) {
        const stepEl = document.getElementById(`global-step-${stepNumber}`);
        if (!stepEl) return;

        // Base classes for responsive sizing (matching base.html - 4 steps)
        stepEl.className = 'step-icon w-9 h-9 sm:w-11 sm:h-11 md:w-12 md:h-12 rounded-full flex items-center justify-center font-bold transition-all duration-300';
        
        // Remove any existing pulse ring
        const parent = stepEl.parentElement;
        const existingPulse = parent.querySelector('.animate-ping');
        if (existingPulse) existingPulse.remove();

        // Update label color
        const labelEl = parent.querySelector('span');
        
        if (status === 'completed') {
            // Completed: Light green with checkmark for emphasis
            stepEl.classList.add('text-white', 'shadow-lg');
            stepEl.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
            stepEl.innerHTML = '<i class="fas fa-check text-sm sm:text-base md:text-lg"></i>';
            stepEl.style.cursor = 'pointer';
            
            if (labelEl) {
                labelEl.className = 'hidden sm:block text-[10px] md:text-xs font-semibold mt-1.5 text-center';
                labelEl.style.color = '#10b981';
            }
        } else if (status === 'current' || status === 'active') {
            // Current: Vista blue gradient with azure ring and pulse animation
            stepEl.classList.add('text-white', 'shadow-md');
            stepEl.style.background = 'linear-gradient(135deg, #7f9ec3 0%, #5d7ea3 100%)';
            stepEl.style.boxShadow = '0 0 0 4px rgba(211, 228, 233, 0.5)';
            const icon = this.steps[stepNumber]?.icon || 'fa-circle';
            stepEl.innerHTML = `<i class="fas ${icon} text-sm sm:text-base md:text-lg"></i>`;
            stepEl.style.cursor = 'pointer';
            
            // Add pulsing ring for current step with azure color
            const pulseDiv = document.createElement('div');
            pulseDiv.className = 'absolute inset-0 rounded-full animate-ping opacity-20';
            pulseDiv.style.background = '#d3e4e9';
            parent.style.position = 'relative';
            parent.insertBefore(pulseDiv, stepEl);
            
            if (labelEl) {
                labelEl.className = 'hidden sm:block text-[10px] md:text-xs font-semibold mt-1.5 text-center';
                labelEl.style.color = '#7f9ec3';
            }
        } else {
            // Pending: Gray with border
            stepEl.classList.add('bg-gray-200', 'text-gray-400', 'border-2', 'border-gray-300');
            const icon = this.steps[stepNumber]?.icon || 'fa-circle';
            stepEl.innerHTML = `<i class="fas ${icon} text-sm sm:text-base md:text-lg"></i>`;
            stepEl.style.cursor = 'not-allowed';
            
            if (labelEl) {
                labelEl.className = 'hidden sm:block text-[10px] md:text-xs font-medium text-gray-400 mt-1.5 text-center';
            }
        }

        // Update mobile label (numbers on mobile for 4 steps)
        const mobileLabel = parent.querySelector('.sm\\:hidden');
        if (mobileLabel) {
            if (status === 'completed') {
                mobileLabel.className = 'sm:hidden text-[8px] font-semibold mt-1';
                mobileLabel.style.color = '#10b981';
            } else if (status === 'current' || status === 'active') {
                mobileLabel.className = 'sm:hidden text-[8px] font-semibold mt-1';
                mobileLabel.style.color = '#7f9ec3';
            } else {
                mobileLabel.className = 'sm:hidden text-[8px] font-medium text-gray-400 mt-1';
            }
        }
    },

    // Update connector lines with scale animation
    updateConnectors: function() {
        for (let i = 1; i <= 3; i++) {
            const connectorEl = document.getElementById(`global-connector-${i}`);
            if (!connectorEl) continue;

            const prevStepStatus = this.stepStatus[i];
            
            if (prevStepStatus === 'completed') {
                // Animate to full width with scale effect
                connectorEl.style.width = '100%';
                connectorEl.style.transform = 'scaleX(1)';
                connectorEl.style.opacity = '1';
            } else {
                // Reset to 0
                connectorEl.style.width = '0%';
                connectorEl.style.transform = 'scaleX(0)';
                connectorEl.style.opacity = '0';
            }
        }
    },

    // Complete current step and move to next
    completeCurrentStep: function() {
        if (this.currentStep < 4) {
            this.updateStep(this.currentStep, 'completed', 100);
            this.updateStep(this.currentStep + 1, 'current', 0);
        } else {
            this.updateStep(4, 'completed', 100);
        }
    },

    // Mark a step as having an error
    markStepError: function(stepNumber) {
        console.log(`[GlobalProgressTracker] Step ${stepNumber} encountered an error`);
        this.updateStep(stepNumber, 'error', 0);
    },

    // Reset entire workflow
    reset: function() {
        console.log('[GlobalProgressTracker] Resetting workflow');
        this.resetState();
        this.updateUI();
    },

    // Get current state for debugging
    getState: function() {
        return {
            currentStep: this.currentStep,
            percentage: this.percentage,
            stepStatus: this.stepStatus,
            completedSteps: this.completedSteps
        };
    }
};

// Initialize on page load with multiple fallbacks
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

// Export to window for global access and debugging
if (typeof window !== 'undefined') {
    window.GlobalProgressTracker = GlobalProgressTracker;
}
