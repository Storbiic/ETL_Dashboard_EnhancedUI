/**
 * Integration script to sync existing app.js with GlobalProgressTracker
 * Now supports 4-step workflow with Downloads
 */

(function() {
    // Wait for both DOM and GlobalProgressTracker to be ready
    let originalUpdateStepProgress = null;
    
    // Step mapping: Old workflow → New workflow (4 steps)
    // Old: 1=Upload, 2=Select, 3=Profile, 4=Transform
    // New: 1=Upload, 2=Preview (Select+Profile), 3=Transform, 4=Downloads
    const stepMapping = {
        1: 1,  // Upload → Upload
        2: 2,  // Select → Preview
        3: 2,  // Profile → Preview (merged with Select)
        4: 3   // Transform → Transform (Downloads is step 4, triggered on results page)
    };
    
    function enhanceUpdateStepProgress() {
        // Find the updateStepProgress function in window scope
        if (typeof window.updateStepProgress === 'function' && !originalUpdateStepProgress) {
            console.log('[ProgressSync] Enhancing updateStepProgress function');
            originalUpdateStepProgress = window.updateStepProgress;
            
            // Override with enhanced version
            window.updateStepProgress = function(step, percentage = 0, status = 'pending') {
                console.log(`[ProgressSync] updateStepProgress called: step=${step}, percentage=${percentage}, status=${status}`);
                
                // Map old step numbers to new 4-step system
                const mappedStep = stepMapping[step] || step;
                
                // If step 3 (old Profile), treat as part of step 2 (new Preview)
                // Adjust percentage to second half (50-100%)
                let adjustedPercentage = percentage;
                if (step === 3) {
                    adjustedPercentage = 50 + (percentage / 2);
                }
                
                // Call global tracker with mapped values
                if (window.GlobalProgressTracker) {
                    window.GlobalProgressTracker.updateStep(mappedStep, status, adjustedPercentage);
                    
                    // Special handling: If transform completes (old step 4 = new step 3), prepare for Downloads
                    if (step === 4 && status === 'completed') {
                        console.log('[ProgressSync] Transform completed, preparing Downloads step');
                        // Don't auto-advance yet - let results page do it
                        // Just mark step 3 as completed at 100%
                        window.GlobalProgressTracker.updateStep(3, 'completed', 100);
                    }
                }
                
                // Call original function for backward compatibility
                return originalUpdateStepProgress(step, percentage, status);
            };
            
            console.log('[ProgressSync] Successfully enhanced updateStepProgress with 4-step mapping');
        }
    }
    
    // Try to enhance immediately
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(enhanceUpdateStepProgress, 100);
        });
    } else {
        setTimeout(enhanceUpdateStepProgress, 100);
    }
    
    // Also try again after a short delay to catch late-loaded scripts
    setTimeout(enhanceUpdateStepProgress, 500);
    setTimeout(enhanceUpdateStepProgress, 1000);
})();
