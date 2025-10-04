# ETL Transform Workflow: Deep Technical Documentation

## Overview

This document provides a comprehensive explanation of the ETL (Extract, Transform, Load) workflow in the ETL Dashboard application, covering the complete journey from uploading Excel sheets (MasterBOM and Status) to generating processed Parquet/CSV/DAX files.

## Workflow Architecture

The ETL transformation process follows a structured pipeline with the following main components:

```
File Upload → Validation → Excel Reading → Sheet Processing → Data Transformation → Output Generation
     ↓             ↓           ↓               ↓                    ↓                  ↓
  Frontend     Backend API   ExcelReader   MasterBOM/Status    Cleaning &         Multi-format
   Upload      Endpoint      Service       Processors          Enrichment         Storage
```

## Detailed Workflow Steps

### 1. File Upload and Initial Validation (`routes_transform.py`)

**Entry Point**: `POST /api/transform`

**Process**:
1. **Request Validation**: Validates the incoming `TransformRequest` containing:
   - `file_id`: UUID of the uploaded Excel file
   - `masterbom_sheet`: Name of the MasterBOM sheet
   - `status_sheet`: Name of the Status sheet
   - Optional parameters for date columns and ID column

2. **UUID Validation**: Ensures the file_id is a valid UUID format
   ```python
   try:
       uuid.UUID(request.file_id)
   except ValueError:
       raise HTTPException(status_code=400, detail="Invalid file ID format")
   ```

3. **File Existence Check**: Verifies the uploaded file exists in the uploads directory
   ```python
   file_path = settings.uploads_folder_path / f"{request.file_id}.xlsx"
   if not file_path.exists():
       raise HTTPException(status_code=404, detail="File not found")
   ```

### 2. Excel Reading and Sheet Validation (`excel_reader.py`)

**Process**:
1. **Excel File Opening**: Uses `openpyxl` to open the Excel file safely
2. **Sheet Name Validation**: Validates that the specified MasterBOM and Status sheets exist
3. **Sheet Reading**: Reads both sheets into pandas DataFrames with error handling

**Key Features**:
- Multi-row header detection and handling
- Automatic data type inference
- Memory-efficient reading for large files

### 3. MasterBOM Processing (`masterbom_rules.py`)

The `MasterBOMProcessor` class handles the complex business logic for processing MasterBOM sheets.

#### 3.1 Header Detection and Cleaning
```python
def _detect_and_fix_headers(self):
    """Detect and fix multi-row headers in Excel data."""
```
- Identifies the actual data start row (skipping merged header rows)
- Handles Excel formatting artifacts
- Standardizes column names

#### 3.2 Column Identification
```python
def _identify_columns(self, id_col: str):
    """Identify ID column and project columns."""
```
- Locates the primary ID column (typically "YAZAKI PN")
- Identifies project/plant columns (columns containing plant codes)
- Maps column relationships for downstream processing

#### 3.3 Data Cleaning and Standardization
- **ID Column Cleaning**: Standardizes part numbers using `clean_id()` function
- **Date Processing**: Detects and parses date columns with multiple format support
- **Text Standardization**: Applies consistent text formatting across string columns

#### 3.4 Derived Table Creation

**Plant-Item-Status Table**:
```python
def _create_plant_item_status(self):
    """Create normalized plant-item-status table."""
```
- Unpivots project columns into a normalized structure
- Creates relationships between parts, plants, and statuses
- Applies status classification rules (active/inactive/new/duplicate)

**Fact Parts Table**:
```python
def _create_fact_parts(self):
    """Create fact parts table."""
```
- Aggregates part information across plants
- Calculates summary metrics
- Maintains dimensional relationships

### 4. Status Sheet Processing (`status_processor_v2.py`)

The `StatusProcessorV2` class processes project status information with exact specification requirements.

#### 4.1 Data Cleaning and Preparation
```python
def _clean_and_prepare_data(self):
    """Clean and prepare data according to specification."""
```
- Removes unnamed and blank columns
- Truncates at first fully empty row
- Handles Excel formatting artifacts

#### 4.2 Header Normalization and Schema Mapping
```python
def _normalize_headers_and_map_schema(self):
    """Normalize headers and map to canonical schema."""
```

**Column Mapping Specification**:
- `project` → `plant_id`
- `oem` → `oem`
- `managed by` → `sqe`
- `1st ppap milestone` → `milestone_date`
- `total part numbers` → `total_parts`
- `psw available` → `psw_available`
- `% psw` → `psw_completion_pct`
- `drawing available` → `drawing_available`
- `%.1 drawing` → `drawing_completion_pct`
- `imds` → `imds_total`
- `% imds` → `imds_completion_pct`
- `m2 parts` → `m2_parts`
- `m2 parts psw ok` → `m2_parts_psw_ok`
- `project status` → `completion_status`
- `bom file date` → `bom_file_date`

#### 4.3 Type Coercion and Derived Fields
- Converts percentage strings to numeric values
- Calculates derived completion metrics
- Handles date parsing with multiple format support

### 5. Date Dimension Creation (`cleaning.py`)

**Date Column Detection**:
```python
def detect_date_columns(df: pd.DataFrame) -> List[str]:
    """Automatically detect date columns in DataFrame."""
```

**Date Dimension Table Creation**:
```python
def create_dim_dates(df: pd.DataFrame, date_columns: List[str]) -> pd.DataFrame:
    """Create date dimension table from date columns."""
```

**Features**:
- Extracts unique dates from all date columns
- Creates comprehensive date attributes (year, month, quarter, etc.)
- Handles multiple date formats automatically

### 6. Data Storage and Output Generation (`storage.py`)

The `DataStorage` class handles multi-format output generation.

#### 6.1 Format-Specific Optimizations

**CSV Storage**:
```python
def _save_csv(self, table_name: str, df: pd.DataFrame) -> List[ArtifactInfo]:
```
- Converts datetime columns to string format for compatibility
- Uses chunking for large datasets (>50,000 rows)
- Optimized encoding (UTF-8)

**Parquet Storage**:
```python
def _save_parquet(self, table_name: str, df: pd.DataFrame) -> List[ArtifactInfo]:
```
- Preserves data types for efficient storage
- Columnar compression for better performance
- Handles complex data types

**SQLite Database**:
```python
def _save_sqlite(self, dataframes: Dict[str, pd.DataFrame]) -> List[ArtifactInfo]:
```
- Creates relational database with all tables
- Optimized indexes for query performance
- ACID compliance for data integrity

#### 6.2 Data Dictionary Generation
```python
def create_data_dictionary(self, dataframes: Dict[str, pd.DataFrame]) -> Optional[str]:
```
- Automatically generates comprehensive metadata documentation
- Includes column descriptions, data types, and sample values
- Markdown format for easy reading and version control

### 7. DAX File Generation (`dax_generator.py`)

**Power BI Integration**:
```python
def generate_dax_file(self, output_path: str) -> str:
```

**Features**:
- Extracts DAX measures from markdown documentation
- Generates importable .dax file for Power BI
- Includes all business logic measures and calculations

## Output Artifacts

The ETL process generates the following artifacts:

### Core Data Tables
1. **masterbom_clean.csv/parquet**: Cleaned and standardized MasterBOM data
2. **plant_item_status.csv/parquet**: Normalized plant-item-status relationships
3. **fact_parts.csv/parquet**: Aggregated part facts for analysis
4. **status_clean.csv/parquet**: Processed project status data
5. **project_completion_by_plant.csv/parquet**: Plant-level completion metrics
6. **dim_dates.csv/parquet**: Date dimension table
7. **date_role_bridge.csv/parquet**: Date role relationships

### Supporting Files
8. **etl.sqlite**: Relational database containing all tables
9. **data_dictionary.md**: Comprehensive metadata documentation
10. **ETL_Dashboard_Measures.dax**: Power BI DAX measures file

## Error Handling and Logging

### Comprehensive Error Management
- **HTTP Exceptions**: Proper status codes for different error types
- **Data Validation**: Input validation at multiple levels
- **Graceful Degradation**: Continues processing when possible
- **Detailed Error Messages**: Specific error information for debugging

### ETL Logging System
```python
class ETLLogger:
    """Structured logging for ETL operations."""
```

**Features**:
- Structured logging with contextual information
- Processing time tracking
- Data quality metrics
- Error categorization and reporting

## Summary Statistics

The workflow generates comprehensive summary statistics:

```python
class TransformSummary:
    total_parts: int
    active_parts: int
    inactive_parts: int
    new_parts: int
    duplicate_parts: int
    plants_detected: int
    duplicates_removed: int
    date_columns_processed: List[str]
    processing_time_seconds: float
```

## Performance Optimizations

1. **Memory Management**: Efficient DataFrame operations and memory cleanup
2. **Chunked Processing**: Large dataset handling with configurable chunk sizes
3. **Parallel Processing**: Multi-format output generation where applicable
4. **Optimized I/O**: Format-specific optimizations for read/write operations
5. **Connection Pooling**: Database connection management for SQLite operations

## Data Quality Assurance

1. **Input Validation**: Multi-level validation of input data
2. **Data Type Enforcement**: Consistent data type handling
3. **Duplicate Detection**: Automatic duplicate identification and flagging
4. **Missing Data Handling**: Configurable strategies for missing values
5. **Business Rule Validation**: Domain-specific validation rules

## API Response Structure

```python
class TransformResponse:
    success: bool
    artifacts: List[ArtifactInfo]
    summary: TransformSummary
    messages: List[str]
    error: Optional[str] = None
```

This comprehensive workflow ensures reliable, scalable, and maintainable ETL processing from raw Excel data to analysis-ready outputs suitable for Power BI integration and business intelligence workflows.