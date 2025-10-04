# Upload Double-Click Bug Fix

## Issue Reported
User had to click the upload area **TWICE** to select a file:
1. First click: File selection window appears → select file → **nothing happens**
2. Second click: File selection window appears again → select file → **file uploads**

## Root Cause
The upload area had **DUPLICATE click handlers** that were conflicting:

### Handler #1 (HTML inline - BAD)
```html
<div class="upload-area" onclick="document.getElementById('file-input').click()">
```

### Handler #2 (JavaScript - GOOD)
```javascript
uploadArea.addEventListener('click', () => {
    console.log('Upload area clicked');
    fileInput.click();
});
```

## What Was Happening
```
User clicks upload area
    ↓
Inline onclick fires → Opens file dialog (1st time)
    ↓
JavaScript addEventListener fires → Opens file dialog (2nd time)
    ↓
Second dialog cancels first file selection
    ↓
User has to click again to select file
```

## Fix Applied
Removed the inline `onclick` handler from the HTML, keeping only the JavaScript event listener.

**Before:**
```html
<div class="border-2 border-dashed border-azure rounded-2xl p-16 text-center transition-all duration-300 upload-area hover:border-vista-blue hover:bg-azure/20 cursor-pointer" onclick="document.getElementById('file-input').click()">
```

**After:**
```html
<div class="border-2 border-dashed border-azure rounded-2xl p-16 text-center transition-all duration-300 upload-area hover:border-vista-blue hover:bg-azure/20 cursor-pointer">
```

## Why This Fix Works
- **Single handler**: Only the JavaScript `addEventListener` fires now
- **Clean separation**: Event handling stays in JavaScript, not mixed in HTML
- **No conflicts**: File dialog opens once, file selection works immediately

## Files Modified
1. `frontend/templates/index.html` - Removed inline `onclick` attribute from upload area div

## Testing Checklist
✅ Click upload area → File dialog opens
✅ Select file → File uploads immediately (no second click needed)
✅ Drag and drop still works
✅ Remove file button still works
✅ No console errors

## Expected Behavior Now
```
User clicks upload area (once)
    ↓
JavaScript addEventListener fires → Opens file dialog
    ↓
User selects file
    ↓
handleFileSelect() fires → uploadFile() called
    ↓
File uploads successfully ✓
```

## Additional Notes
This is a common anti-pattern to avoid:
- ❌ **Never mix** inline onclick with addEventListener for the same element
- ✅ **Always use** addEventListener for better control and debugging
- ✅ Keeps HTML clean and JavaScript separate
