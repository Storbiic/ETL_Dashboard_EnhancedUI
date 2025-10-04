// ========================================
// PROGRESS TRACKER - QUICK RESET & TEST
// ========================================

// Copy and paste this entire block into your browser console (F12)

console.log('%c🔄 RESETTING PROGRESS TRACKER...', 'color: #2563eb; font-size: 16px; font-weight: bold;');

// 1. Clear localStorage
localStorage.removeItem('etl_global_progress');
console.log('%c✅ localStorage cleared', 'color: #10b981;');

// 2. Reset the tracker object
if (window.GlobalProgressTracker) {
    window.GlobalProgressTracker.resetState();
    window.GlobalProgressTracker.updateUI();
    console.log('%c✅ Tracker reset to initial state', 'color: #10b981;');
} else {
    console.log('%c⚠️ GlobalProgressTracker not found - page needs reload', 'color: #f59e0b;');
}

// 3. Show current state
setTimeout(() => {
    const state = window.GlobalProgressTracker ? window.GlobalProgressTracker.getState() : null;
    if (state) {
        console.log('%c📊 CURRENT STATE:', 'color: #2563eb; font-weight: bold;');
        console.table(state);
        
        console.log('\n%c🎯 EXPECTED:', 'color: #059669; font-weight: bold;');
        console.log('  currentStep: 1');
        console.log('  percentage: 0');
        console.log('  stepStatus: {1: "current", 2: "pending", 3: "pending"}');
        console.log('  completedSteps: []');
        
        // Verify
        if (state.currentStep === 1 && state.percentage === 0) {
            console.log('\n%c✅ RESET SUCCESSFUL!', 'color: #10b981; font-size: 18px; font-weight: bold;');
            console.log('%cProgress tracker is now at 0% on Step 1', 'color: #10b981;');
        } else {
            console.log('\n%c❌ Reset may have failed', 'color: #ef4444; font-weight: bold;');
            console.log('%cTry refreshing the page: location.reload()', 'color: #f59e0b;');
        }
    }
}, 100);

console.log('\n%c💡 TIP: If still showing 100%, try refreshing the page:', 'color: #6366f1; font-weight: bold;');
console.log('%clocation.reload();', 'background: #1e293b; color: #fbbf24; padding: 4px 8px; border-radius: 4px;');
