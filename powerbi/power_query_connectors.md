# Power Query M Scripts

This document contains Power Query M scripts to connect Power BI to the ETL Dashboard outputs.

## Option 1: CSV Files from Folder

### Connect to Processed CSV Files

```m
let
    Source = Folder.Files("C:\path\to\your\etl-dashboard\data\processed"),
    FilteredRows = Table.SelectRows(Source, each Text.EndsWith([Name], ".csv")),
    TransformFiles = Table.AddColumn(FilteredRows, "Transform File from processed", each Csv.Document([Content])),
    RemovedOtherColumns = Table.SelectColumns(TransformFiles, {"Name", "Transform File from processed"}),
    ExpandedTableColumn = Table.ExpandTableColumn(RemovedOtherColumns, "Transform File from processed", {"Column1", "Column2", "Column3"}, {"Column1", "Column2", "Column3"}),
    PromotedHeaders = Table.PromoteHeaders(ExpandedTableColumn, [PromoteAllScalars=true]),
    AddedTableName = Table.AddColumn(PromotedHeaders, "TableName", each Text.BeforeDelimiter([Name], "."))
in
    AddedTableName
```

### Individual Table Connections

#### MasterBOM Clean
```m
let
    Source = Csv.Document(File.Contents("C:\path\to\your\etl-dashboard\data\processed\masterbom_clean.csv"),[Delimiter=",", Columns=25, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders,{
        {"part_id_std", type text},
        {"part_id_raw", type text},
        {"item_description", type text},
        {"supplier_name", type text},
        {"approved_date", type date},
        {"approved_date_year", Int64.Type},
        {"approved_date_month", Int64.Type},
        {"approved_date_day", Int64.Type},
        {"approved_date_qtr", Int64.Type},
        {"approved_date_week", Int64.Type},
        {"psw_date_ok", type date},
        {"far_promised_date", type date}
    })
in
    ChangedType
```

#### Plant Item Status
```m
let
    Source = Csv.Document(File.Contents("C:\path\to\your\etl-dashboard\data\processed\plant_item_status.csv"),[Delimiter=",", Columns=12, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders,{
        {"part_id_std", type text},
        {"part_id_raw", type text},
        {"project_plant", type text},
        {"raw_status", type text},
        {"status_class", type text},
        {"is_duplicate", type logical},
        {"is_new", type logical},
        {"notes", type text},
        {"n_active", Int64.Type},
        {"n_inactive", Int64.Type},
        {"n_new", Int64.Type},
        {"n_duplicate", Int64.Type}
    })
in
    ChangedType
```

#### Fact Parts
```m
let
    Source = Csv.Document(File.Contents("C:\path\to\your\etl-dashboard\data\processed\fact_parts.csv"),[Delimiter=",", Columns=15, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders,{
        {"part_id_std", type text},
        {"part_id_raw", type text},
        {"item_description", type text},
        {"supplier_name", type text},
        {"psw_ok", type logical},
        {"has_handling_manual", type logical},
        {"far_ok", type logical},
        {"imds_ok", type logical},
        {"ypn_status", type text},
        {"total_plants", Int64.Type},
        {"active_plants", Int64.Type},
        {"inactive_plants", Int64.Type},
        {"new_plants", Int64.Type},
        {"duplicate_plants", Int64.Type},
        {"latest_approved_date", type date},
        {"earliest_far_promised_date", type date}
    })
in
    ChangedType
```

#### Date Dimension
```m
let
    Source = Csv.Document(File.Contents("C:\path\to\your\etl-dashboard\data\processed\dim_dates.csv"),[Delimiter=",", Columns=15, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders,{
        {"date_value", type date},
        {"year", Int64.Type},
        {"month", Int64.Type},
        {"day", Int64.Type},
        {"quarter", Int64.Type},
        {"week", Int64.Type},
        {"day_of_week", Int64.Type},
        {"day_name", type text},
        {"month_name", type text},
        {"quarter_name", type text},
        {"role_col_name", type text},
        {"is_weekend", type logical},
        {"is_month_end", type logical},
        {"is_quarter_end", type logical},
        {"is_year_end", type logical}
    })
in
    ChangedType
```

## Option 2: Parquet Files

### MasterBOM Clean (Parquet)
```m
let
    Source = Parquet.Document(File.Contents("C:\path\to\your\etl-dashboard\data\processed\masterbom_clean.parquet"))
in
    Source
```

### Plant Item Status (Parquet)
```m
let
    Source = Parquet.Document(File.Contents("C:\path\to\your\etl-dashboard\data\processed\plant_item_status.parquet"))
in
    Source
```

### Fact Parts (Parquet)
```m
let
    Source = Parquet.Document(File.Contents("C:\path\to\your\etl-dashboard\data\processed\fact_parts.parquet"))
in
    Source
```

### Date Dimension (Parquet)
```m
let
    Source = Parquet.Document(File.Contents("C:\path\to\your\etl-dashboard\data\processed\dim_dates.parquet"))
in
    Source
```

## Option 3: SQLite Database

### Prerequisites
1. Install SQLite ODBC driver from: http://www.ch-werner.de/sqliteodbc/
2. Create a System DSN in Windows ODBC Data Source Administrator:
   - Driver: SQLite3 ODBC Driver
   - Data Source Name: ETL_Dashboard
   - Database Name: C:\path\to\your\etl-dashboard\data\processed\etl.sqlite

### Connect to SQLite Database
```m
let
    Source = Odbc.DataSource("dsn=ETL_Dashboard", [HierarchicalNavigation=true]),
    etl_Database = Source{[Name="etl",Kind="Database"]}[Data],
    Tables = etl_Database{[Name="Tables",Kind="Schema"]}[Data]
in
    Tables
```

### Individual Table from SQLite
```m
let
    Source = Odbc.Query("dsn=ETL_Dashboard", "SELECT * FROM masterbom_clean")
in
    Source
```

## Dynamic Path Configuration

### Using Parameters for File Paths
Create a parameter called `DataPath` in Power BI:

```m
// Parameter: DataPath
"C:\path\to\your\etl-dashboard\data\processed" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
```

Then use it in your queries:
```m
let
    Source = Csv.Document(File.Contents(DataPath & "\masterbom_clean.csv"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None])
in
    Source
```

## Refresh Strategy

### Automatic Refresh
1. Set up Power BI Gateway for on-premises data refresh
2. Configure scheduled refresh in Power BI Service
3. Ensure file paths are accessible from the gateway machine

### Manual Refresh
1. Run ETL Dashboard to generate new files
2. Refresh Power BI dataset manually
3. Verify data freshness in reports

## Troubleshooting

### Common Issues
1. **File not found**: Verify file paths are correct and accessible
2. **Permission denied**: Ensure Power BI has read access to the data folder
3. **Encoding issues**: Use UTF-8 encoding for CSV files
4. **Date parsing**: Verify date formats match regional settings

### Performance Tips
1. Use Parquet files for better performance with large datasets
2. Filter data early in the query to reduce memory usage
3. Use SQLite for complex joins and aggregations
4. Consider incremental refresh for large historical datasets

## Status Clean Table

### Status Clean (CSV)
```m
let
    Source = Csv.Document(File.Contents("C:\path\to\your\etl-dashboard\data\processed\status_clean.csv"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders,{
        {"oem", type text},
        {"project", type text},
        {"first_ppap_milestone", type date},
        {"total_part_numbers", Int64.Type},
        {"psw_available", Int64.Type},
        {"drawing_available", Int64.Type},
        {"psw_available_pct", type number},
        {"drawing_available_pct", type number}
    })
in
    ChangedType
```

### Status Clean (Parquet)
```m
let
    Source = Parquet.Document(File.Contents("C:\path\to\your\etl-dashboard\data\processed\status_clean.parquet"))
in
    Source
```

#### Project Completion by Plant
```m
let
    Source = Csv.Document(File.Contents("C:\path\to\your\etl-dashboard\data\processed\project_completion_by_plant.csv"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders,{
        {"project_name", type text},
        {"oem", type text},
        {"plant_id", type text},
        {"plant_name", type text},
        {"overall_completion_pct", type number},
        {"psw_completion_pct", type number},
        {"drawing_completion_pct", type number},
        {"ppap_completion_pct", type number},
        {"completion_status", type text},
        {"milestone_date", type date},
        {"total_parts", Int64.Type}
    })
in
    ChangedType
```

### Project Completion by Plant (Parquet)
```m
let
    Source = Parquet.Document(File.Contents("C:\path\to\your\etl-dashboard\data\processed\project_completion_by_plant.parquet"))
in
    Source
```
