// Date column management for ETL Dashboard

// List of date columns that will be excluded from auto-detection
const EXCLUDED_DATE_COLUMNS = ["Supplier PN", "Original Supplier PN"];

// Update the detected dates display
function updateDetectedDatesDisplay(detectedDates) {
    const container = document.getElementById('detected-dates');
    if (!container) return;
    
    // Filter out excluded columns
    const filteredDates = detectedDates.filter(date => !EXCLUDED_DATE_COLUMNS.includes(date));
    
    // Create badge for each date column
    let html = '';
    filteredDates.forEach(date => {
        html += `
            <div class="bg-blue-100 text-blue-800 text-xs font-medium px-3 py-1 rounded-full">
                ${date}
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Update the transform request options
function getDateColumnOptions() {
    return {
        date_cols: [], // Let backend auto-detect
        excluded_date_cols: EXCLUDED_DATE_COLUMNS,
        id_col: "YAZAKI PN"
    };
}