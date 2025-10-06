# 📄 PDF FILES NEEDED

## Quick Setup Guide

### Step 1: Prepare Your PDF Files
Ensure you have these two PDF documents ready:
1. **ETL Dashboard Documentation**
2. **Power BI Dashboard Documentation**

### Step 2: Rename Files (EXACT NAMES REQUIRED)
```
Report_etl_dashboard.pdf
Report_powerbi_dashboard.pdf
```

⚠️ **Important**: File names are case-sensitive and must match exactly!

### Step 3: Copy to Static Folder
```
Copy PDFs to:
frontend/static/docs/

Final location:
frontend/
  └── static/
      └── docs/
          ├── Report_etl_dashboard.pdf
          └── Report_powerbi_dashboard.pdf
```

### Step 4: Verify Access
After copying, the PDFs will be available at:
```
http://localhost:5000/docs/Report_etl_dashboard.pdf
http://localhost:5000/docs/Report_powerbi_dashboard.pdf
```

### Step 5: Test the Guidelines Page
```
Navigate to: http://localhost:5000/guidelines
Click: "View / Download PDF" buttons
Verify: PDFs open in new browser tabs
```

---

## File Specifications

### Report_etl_dashboard.pdf
**Recommended Content:**
- Excel file upload instructions
- Sheet selection workflow
- Data preview features
- Profile analysis interpretation
- Transformation options
- Output format selection (CSV/Parquet/SQLite)
- Power BI connector setup
- Troubleshooting common issues

### Report_powerbi_dashboard.pdf
**Recommended Content:**
- Dashboard overview and navigation
- KPI definitions and calculations
- Chart types and interpretations
- Master BOM page walkthrough
- Status tracking explanations
- Filter and slicer usage
- Export and sharing options
- Best practices for analysis

---

## Troubleshooting

### PDF Not Loading?
1. **Check file name**: Must be exactly `Report_etl_dashboard.pdf` or `Report_powerbi_dashboard.pdf`
2. **Check location**: Files must be in `frontend/static/docs/`
3. **Restart server**: `Ctrl+C` then `python run_dev.py`
4. **Clear browser cache**: Hard refresh with `Ctrl+Shift+R`

### 404 Error?
- Verify Flask is serving static files
- Check `frontend/static/` folder exists
- Ensure `docs/` subfolder was created

### PDF Opens But Is Blank?
- Check PDF file is not corrupted
- Try opening PDF in Adobe Reader/browser directly
- Verify PDF is not password-protected

---

## Alternative: Placeholder PDFs

If you don't have the actual PDFs yet, you can create temporary placeholders:

### Option 1: Simple Text File (Temporary)
Create a text file explaining PDFs are coming soon, save as `.txt` temporarily:
```
ETL_Dashboard_Guide_Coming_Soon.txt
PowerBI_Dashboard_Guide_Coming_Soon.txt
```

### Option 2: Generate Basic PDFs
Use any PDF creator to make simple placeholder documents with:
- Title page
- "Documentation coming soon" message
- Contact information for questions

---

## Best Practices

1. **File Size**: Keep PDFs under 10MB for fast loading
2. **Optimization**: Compress PDFs for web viewing
3. **Accessibility**: Add PDF bookmarks for easy navigation
4. **Version Control**: Include version number and date in PDF
5. **Updates**: Replace PDFs by overwriting files with same names

---

## Ready to Go! 🚀

Once you copy the two PDF files to `frontend/static/docs/`, the Guidelines page will be fully functional!

The buttons will automatically link to your documentation, opening them in new browser tabs.
