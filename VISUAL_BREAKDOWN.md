# 📱 Responsive Progress Tracker - Visual Breakdown

## Screen Size Examples

### 📱 Extra Small Mobile (<400px)
```
┌────────────────────────────────────┐
│ Upload Excel...           [0%]     │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  ●  ─  ○  ─  ○  ─  ○              │
│  1     2     3     4               │
└────────────────────────────────────┘
```
- Icons: 32x32px
- Labels: Numbers only (8px font)
- Connectors: 2px height
- Total height: ~60px

---

### 📱 Mobile (400px - 640px)
```
┌──────────────────────────────────────────┐
│ Upload Excel Workbook         [0%]       │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│   ●   ──   ○   ──   ○   ──   ○          │
│   1        2        3        4           │
└──────────────────────────────────────────┘
```
- Icons: 32x32px
- Labels: Numbers (8px font)
- Spacing: Slightly more generous
- Total height: ~64px

---

### 📊 Tablet (640px - 768px) - `sm:` breakpoint
```
┌────────────────────────────────────────────────────┐
│ Upload Excel Workbook                   [0%]       │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│    ●    ────    ○    ────    ○    ────    ○       │
│  Upload       Select      Profile    Transform    │
└────────────────────────────────────────────────────┘
```
- Icons: 40x40px
- Labels: **Text appears** (10px font)
- Connectors: 4px height
- Total height: ~80px

---

### 💻 Desktop (>768px) - `md:` breakpoint
```
┌──────────────────────────────────────────────────────────────────┐
│ Upload Excel Workbook                              [0%]          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│     ●     ──────     ○     ──────     ○     ──────     ○         │
│   Upload           Select          Profile        Transform      │
└──────────────────────────────────────────────────────────────────┘
```
- Icons: 48x48px
- Labels: Full text (12px font)
- Connectors: 4px height, longer
- Total height: ~96px

---

## 🎨 State Visualizations

### All Steps Pending (Initial State)
```
Upload Excel Workbook                                    [0%]
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ (empty)
 ⊙ ─── ○ ─── ○ ─── ○
Blue   Gray  Gray  Gray
(pulsing)
```

### Step 1 at 50%
```
Upload Excel Workbook                                   [50%]
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ⊙ ─── ○ ─── ○ ─── ○
Blue   Gray  Gray  Gray
(pulsing)
```

### Step 1 Complete, Step 2 Active
```
Select & Preview Sheets                                 [25%]
▬▬▬▬▬▬▬▬▬▬▬▬▬━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ✓ ━━━ ⊙ ─── ○ ─── ○
Dark  Blue  Blue  Gray  Gray
Blue  Line  (pulsing)
```

### Step 2 Complete, Step 3 Active
```
Profile Data Quality                                    [50%]
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ✓ ━━━ ✓ ━━━ ⊙ ─── ○
Dark  Blue Dark Blue Blue  Gray
Blue  Line Blue Line (pulsing)
```

### All Steps Complete
```
Transform Data                                        [100%]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ✓ ━━━ ✓ ━━━ ✓ ━━━ ✓
Dark  Blue Dark Blue Dark  Blue Dark
Blue  Line Blue Line Blue  Line Blue
```

---

## 🎭 Animation Sequence

### Step Transition (Step 1 → Step 2)

**T=0ms**: User completes Step 1
```
 ⊙ ─── ○ ─── ○ ─── ○
Blue   Gray  Gray  Gray
```

**T=150ms**: Icon changes to checkmark
```
 ✓ ─── ○ ─── ○ ─── ○
Dark   Gray  Gray  Gray
Blue
```

**T=300ms**: Connector 1 starts filling (transform: scaleX)
```
 ✓ ━── ○ ─── ○ ─── ○
Dark  50%  Gray  Gray  Gray
Blue  Blue
```

**T=500ms**: Connector 1 full, Step 2 icon changes
```
 ✓ ━━━ ⊙ ─── ○ ─── ○
Dark  100% Blue  Gray  Gray
Blue  Blue (pulsing)
```

**T=700ms**: Progress bar updates, animation complete
```
 ✓ ━━━ ⊙ ─── ○ ─── ○
Dark  Blue Blue  Gray  Gray
Blue       (pulsing)
Progress bar: 0% → 25%
```

---

## 🎯 Icon Legend

### States
- `⊙` = Current step (blue gradient + pulsing ring)
- `✓` = Completed step (dark blue gradient + checkmark)
- `○` = Pending step (gray outline)

### Connectors
- `───` = Unfilled connector (gray)
- `━━━` = Filled connector (blue gradient)

### Progress Bar
- `▬▬▬` = Unfilled (gray background)
- `━━━` = Filled (blue-indigo gradient)

---

## 📐 Layout Math

### Width Distribution (Flexbox)
```
Total width: 100%

Step 1:      20%  (flex-shrink-0)
Connector 1: 18%  (flex-1, max-width)
Step 2:      20%  (flex-shrink-0)
Connector 2: 18%  (flex-1, max-width)
Step 3:      20%  (flex-shrink-0)
Connector 3: 18%  (flex-1, max-width)
Step 4:      20%  (flex-shrink-0)

(20 + 18) × 3 + 20 = 20 + 38 + 38 + 38 + 20 = 154%
But flex-1 with max-width: 18% distributes evenly
Actual: Each connector takes ~6% of remaining space
```

### Height Calculations
```
Mobile (<640px):
  Top padding:    12px (py-3)
  Info row:       20px (text + badge)
  Margin:         8px  (mb-2)
  Progress bar:   4px  (h-1)
  Margin:         12px (mb-3)
  Icons:          32px (w-8 h-8)
  Labels:         12px (text + margin)
  Bottom padding: 12px (py-3)
  ─────────────────────
  Total:          ~80px

Desktop (>640px):
  Top padding:    16px (py-4)
  Info row:       24px
  Margin:         8px
  Progress bar:   6px  (h-1.5)
  Margin:         12px
  Icons:          48px (w-12 h-12)
  Labels:         16px
  Bottom padding: 16px
  ─────────────────────
  Total:          ~96px
```

---

## 🎨 Color Palette

### Current Step (Blue)
```css
background: linear-gradient(to bottom right, #2563eb, #4f46e5);
/* from-blue-600 to-indigo-600 */
ring-color: rgba(37, 99, 235, 0.1); /* ring-blue-100 */
```

### Completed Step (Dark Blue)
```css
background: linear-gradient(to bottom right, #1d4ed8, #4338ca);
/* from-blue-700 to-indigo-700 */
```

### Pending Step (Gray)
```css
background: #e5e7eb; /* bg-gray-200 */
border: 2px solid #d1d5db; /* border-gray-300 */
color: #9ca3af; /* text-gray-400 */
```

### Progress Bar Gradient
```css
background: linear-gradient(to right, #2563eb, #4f46e5, #2563eb);
/* from-blue-600 via-indigo-600 to-blue-600 */
```

### Connectors
```css
background: linear-gradient(to right, #2563eb, #4338ca);
/* from-blue-600 to-indigo-600 */
```

---

## ♿ Accessibility Features

### Keyboard Navigation
```
Tab → Focus Step 1
Enter/Space → Click Step 1 (if allowed)
Tab → Focus Step 2
Enter/Space → Click Step 2 (if allowed)
...
```

### ARIA Labels
```html
<div role="button" 
     aria-label="Step 1: Upload Excel Workbook, Current" 
     tabindex="0">
  <i class="fas fa-cloud-upload-alt"></i>
</div>

<div role="button" 
     aria-label="Step 2: Select Sheets, Pending" 
     tabindex="0" 
     aria-disabled="true">
  <i class="fas fa-table"></i>
</div>
```

### Screen Reader Announcements
- "Step 1 of 4: Upload Excel Workbook, Current, 50% complete"
- "Step 2 of 4: Select Sheets, Not started"
- "Step 1 completed, now on Step 2: Select Sheets"

---

## 🔧 CSS Custom Properties (Optional Enhancement)

```css
:root {
  --tracker-height-mobile: 80px;
  --tracker-height-desktop: 96px;
  --tracker-icon-size-xs: 32px;
  --tracker-icon-size-sm: 40px;
  --tracker-icon-size-md: 48px;
  --tracker-connector-height-mobile: 2px;
  --tracker-connector-height-desktop: 4px;
  --tracker-blue: #2563eb;
  --tracker-indigo: #4f46e5;
  --tracker-dark-blue: #1d4ed8;
  --tracker-gray: #e5e7eb;
}
```

---

**Visual Reference Created**: October 3, 2025  
**Status**: ✅ Complete Responsive Breakdown  
**Developer**: GitHub Copilot
