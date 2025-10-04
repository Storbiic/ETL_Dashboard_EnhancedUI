# DAX Measures for ETL Dashboard

This document contains DAX measures for creating a comprehensive Power BI dashboard from the ETL Dashboard outputs.

## Part Status Measures

### Basic Counts
```dax
Active Parts = 
COUNTROWS(
    FILTER(
        plant_item_status,
        plant_item_status[status_class] = "active"
    )
)
```

```dax
Inactive Parts = 
COUNTROWS(
    FILTER(
        plant_item_status,
        plant_item_status[status_class] = "inactive"
    )
)
```

```dax
New Items = 
COUNTROWS(
    FILTER(
        plant_item_status,
        plant_item_status[status_class] = "new"
    )
)
```

```dax
Duplicate Parts = 
COUNTROWS(
    FILTER(
        plant_item_status,
        plant_item_status[status_class] = "duplicate"
    )
)
```

```dax
Total Parts = 
COUNTROWS(fact_parts)
```

### Percentage Measures
```dax
Active Parts % = 
DIVIDE(
    [Active Parts],
    [Total Parts],
    0
)
```

```dax
Inactive Parts % = 
DIVIDE(
    [Inactive Parts],
    [Total Parts],
    0
)
```

```dax
New Items % = 
DIVIDE(
    [New Items],
    [Total Parts],
    0
)
```

```dax
Duplicate Parts % = 
DIVIDE(
    [Duplicate Parts],
    [Total Parts],
    0
)
```

## Quality Measures

### PSW Measures
```dax
PSW OK Count = 
COUNTROWS(
    FILTER(
        fact_parts,
        fact_parts[psw_ok] = TRUE
    )
)
```

```dax
PSW OK % = 
DIVIDE(
    [PSW OK Count],
    [Total Parts],
    0
)
```

```dax
PSW NOT OK Count = 
COUNTROWS(
    FILTER(
        fact_parts,
        fact_parts[psw_ok] = FALSE
    )
)
```

### FAR Measures
```dax
FAR OK Count = 
COUNTROWS(
    FILTER(
        fact_parts,
        fact_parts[far_ok] = TRUE
    )
)
```

```dax
FAR OK % = 
DIVIDE(
    [FAR OK Count],
    [Total Parts],
    0
)
```

```dax
FAR NOT OK Count = 
COUNTROWS(
    FILTER(
        fact_parts,
        fact_parts[far_ok] = FALSE
    )
)
```

### IMDS Measures
```dax
IMDS OK Count = 
COUNTROWS(
    FILTER(
        fact_parts,
        fact_parts[imds_ok] = TRUE
    )
)
```

```dax
IMDS OK % = 
DIVIDE(
    [IMDS OK Count],
    [Total Parts],
    0
)
```

```dax
IMDS NOT OK Count = 
COUNTROWS(
    FILTER(
        fact_parts,
        fact_parts[imds_ok] = FALSE
    )
)
```

### Handling Manual Measures
```dax
Has Handling Manual Count = 
COUNTROWS(
    FILTER(
        fact_parts,
        fact_parts[has_handling_manual] = TRUE
    )
)
```

```dax
Has Handling Manual % = 
DIVIDE(
    [Has Handling Manual Count],
    [Total Parts],
    0
)
```

## Plant Distribution Measures

### Plant Coverage
```dax
Average Plants per Part = 
AVERAGEX(
    fact_parts,
    fact_parts[total_plants]
)
```

```dax
Max Plants per Part = 
MAXX(
    fact_parts,
    fact_parts[total_plants]
)
```

```dax
Parts in Multiple Plants = 
COUNTROWS(
    FILTER(
        fact_parts,
        fact_parts[total_plants] > 1
    )
)
```

```dax
Single Plant Parts = 
COUNTROWS(
    FILTER(
        fact_parts,
        fact_parts[total_plants] = 1
    )
)
```

## Time Intelligence Measures

### Date-based Measures
```dax
Parts Approved This Month = 
CALCULATE(
    [Total Parts],
    FILTER(
        fact_parts,
        MONTH(fact_parts[latest_approved_date]) = MONTH(TODAY()) &&
        YEAR(fact_parts[latest_approved_date]) = YEAR(TODAY())
    )
)
```

```dax
Parts Approved This Quarter = 
CALCULATE(
    [Total Parts],
    FILTER(
        fact_parts,
        QUARTER(fact_parts[latest_approved_date]) = QUARTER(TODAY()) &&
        YEAR(fact_parts[latest_approved_date]) = YEAR(TODAY())
    )
)
```

```dax
Parts Approved This Year = 
CALCULATE(
    [Total Parts],
    FILTER(
        fact_parts,
        YEAR(fact_parts[latest_approved_date]) = YEAR(TODAY())
    )
)
```

### Overdue Measures
```dax
Overdue FAR Count = 
COUNTROWS(
    FILTER(
        fact_parts,
        fact_parts[earliest_far_promised_date] < TODAY() &&
        fact_parts[far_ok] = FALSE
    )
)
```

```dax
Overdue FAR % = 
DIVIDE(
    [Overdue FAR Count],
    [FAR NOT OK Count],
    0
)
```

## Supplier Measures

### Supplier Performance
```dax
Unique Suppliers = 
DISTINCTCOUNT(fact_parts[supplier_name])
```

```dax
Parts per Supplier = 
DIVIDE(
    [Total Parts],
    [Unique Suppliers],
    0
)
```

```dax
Top Supplier Parts Count = 
CALCULATE(
    [Total Parts],
    TOPN(
        1,
        VALUES(fact_parts[supplier_name]),
        [Total Parts],
        DESC
    )
)
```

## Project/Plant Measures

### Project Coverage
```dax
Unique Projects = 
DISTINCTCOUNT(
    SELECTCOLUMNS(
        plant_item_status,
        "Project",
        LEFT(
            plant_item_status[project_plant],
            SEARCH("_", plant_item_status[project_plant] & "_") - 1
        )
    )
)
```

```dax
Unique Plants = 
DISTINCTCOUNT(plant_item_status[project_plant])
```

```dax
Parts per Project = 
DIVIDE(
    [Total Parts],
    [Unique Projects],
    0
)
```

## Conditional Formatting Measures

### Status Colors
```dax
Status Color = 
SWITCH(
    TRUE(),
    [PSW OK %] >= 0.9, "Green",
    [PSW OK %] >= 0.7, "Yellow",
    "Red"
)
```

```dax
FAR Status Color = 
SWITCH(
    TRUE(),
    [FAR OK %] >= 0.9, "Green",
    [FAR OK %] >= 0.7, "Yellow",
    "Red"
)
```

```dax
IMDS Status Color = 
SWITCH(
    TRUE(),
    [IMDS OK %] >= 0.95, "Green",
    [IMDS OK %] >= 0.8, "Yellow",
    "Red"
)
```

## Trend Measures

### Month-over-Month Growth
```dax
Parts Approved MoM = 
VAR CurrentMonth = [Parts Approved This Month]
VAR PreviousMonth = 
    CALCULATE(
        [Total Parts],
        FILTER(
            fact_parts,
            MONTH(fact_parts[latest_approved_date]) = MONTH(TODAY()) - 1 &&
            YEAR(fact_parts[latest_approved_date]) = YEAR(TODAY())
        )
    )
RETURN
    CurrentMonth - PreviousMonth
```

```dax
Parts Approved MoM % = 
VAR CurrentMonth = [Parts Approved This Month]
VAR PreviousMonth = 
    CALCULATE(
        [Total Parts],
        FILTER(
            fact_parts,
            MONTH(fact_parts[latest_approved_date]) = MONTH(TODAY()) - 1 &&
            YEAR(fact_parts[latest_approved_date]) = YEAR(TODAY())
        )
    )
RETURN
    DIVIDE(
        CurrentMonth - PreviousMonth,
        PreviousMonth,
        0
    )
```

## Enhanced Duplicate Analysis Measures

### Duplicate Part Counts
```dax
Total Duplicate Parts =
COUNTROWS(
    FILTER(
        masterbom_clean,
        masterbom_clean[is_duplicate_entry] = TRUE
    )
)
```

```dax
Duplicate Rate % =
DIVIDE(
    [Total Duplicate Parts],
    COUNTROWS(masterbom_clean),
    0
)
```

```dax
Unique Parts (Excluding Duplicates) =
COUNTROWS(
    FILTER(
        masterbom_clean,
        masterbom_clean[is_duplicate_entry] = FALSE
    )
)
```

```dax
Duplicate Parts by Supplier =
CALCULATE(
    [Total Duplicate Parts],
    ALLEXCEPT(masterbom_clean, masterbom_clean[supplier_name])
)
```

### Duplicate Analysis by Category
```dax
Duplicates with Different Suppliers =
VAR DuplicateParts =
    FILTER(
        SUMMARIZE(
            masterbom_clean,
            masterbom_clean[part_id_std],
            "SupplierCount", DISTINCTCOUNT(masterbom_clean[supplier_name])
        ),
        [SupplierCount] > 1
    )
RETURN
    COUNTROWS(DuplicateParts)
```

```dax
Duplicates with Same Supplier =
VAR DuplicateParts =
    FILTER(
        SUMMARIZE(
            masterbom_clean,
            masterbom_clean[part_id_std],
            "SupplierCount", DISTINCTCOUNT(masterbom_clean[supplier_name])
        ),
        [SupplierCount] = 1
    )
RETURN
    COUNTROWS(DuplicateParts)
```

## Project Completion Tracking Measures

### Overall Project Completion
```dax
Average Project Completion % =
AVERAGEX(
    project_completion_by_plant,
    project_completion_by_plant[overall_completion_pct]
)
```

```dax
Projects Complete Count =
COUNTROWS(
    FILTER(
        project_completion_by_plant,
        project_completion_by_plant[completion_status] = "Complete"
    )
)
```

```dax
Projects In Progress Count =
COUNTROWS(
    FILTER(
        project_completion_by_plant,
        project_completion_by_plant[completion_status] = "In Progress"
    )
)
```

### Plant-Specific Completion
```dax
Plant Completion Average =
CALCULATE(
    AVERAGE(project_completion_by_plant[overall_completion_pct]),
    ALLEXCEPT(project_completion_by_plant, project_completion_by_plant[plant_id])
)
```

```dax
Best Performing Plant =
TOPN(
    1,
    SUMMARIZE(
        project_completion_by_plant,
        project_completion_by_plant[plant_id],
        "AvgCompletion", AVERAGE(project_completion_by_plant[overall_completion_pct])
    ),
    [AvgCompletion],
    DESC
)
```

```dax
Worst Performing Plant =
TOPN(
    1,
    SUMMARIZE(
        project_completion_by_plant,
        project_completion_by_plant[plant_id],
        "AvgCompletion", AVERAGE(project_completion_by_plant[overall_completion_pct])
    ),
    [AvgCompletion],
    ASC
)
```

### PSW and Drawing Completion
```dax
PSW Completion Average =
AVERAGE(project_completion_by_plant[psw_completion_pct])
```

```dax
Drawing Completion Average =
AVERAGE(project_completion_by_plant[drawing_completion_pct])
```

```dax
PPAP Completion Average =
AVERAGE(project_completion_by_plant[ppap_completion_pct])
```

### Cross-Plant Comparisons
```dax
Plant Completion Variance =
VAR MaxCompletion = MAXX(project_completion_by_plant, project_completion_by_plant[overall_completion_pct])
VAR MinCompletion = MINX(project_completion_by_plant, project_completion_by_plant[overall_completion_pct])
RETURN
    MaxCompletion - MinCompletion
```

```dax
Plants Above Average =
VAR OverallAvg = [Average Project Completion %]
RETURN
    COUNTROWS(
        FILTER(
            SUMMARIZE(
                project_completion_by_plant,
                project_completion_by_plant[plant_id],
                "PlantAvg", AVERAGE(project_completion_by_plant[overall_completion_pct])
            ),
            [PlantAvg] > OverallAvg
        )
    )
```

```dax
Plants Below Average =
VAR OverallAvg = [Average Project Completion %]
RETURN
    COUNTROWS(
        FILTER(
            SUMMARIZE(
                project_completion_by_plant,
                project_completion_by_plant[plant_id],
                "PlantAvg", AVERAGE(project_completion_by_plant[overall_completion_pct])
            ),
            [PlantAvg] < OverallAvg
        )
    )
```

## Time-Based Completion Tracking

### Milestone Analysis
```dax
Overdue Milestones =
COUNTROWS(
    FILTER(
        project_completion_by_plant,
        project_completion_by_plant[milestone_date] < TODAY() &&
        project_completion_by_plant[completion_status] <> "Complete"
    )
)
```

```dax
Upcoming Milestones (30 Days) =
COUNTROWS(
    FILTER(
        project_completion_by_plant,
        project_completion_by_plant[milestone_date] >= TODAY() &&
        project_completion_by_plant[milestone_date] <= TODAY() + 30 &&
        project_completion_by_plant[completion_status] <> "Complete"
    )
)
```

```dax
Average Days to Milestone =
AVERAGEX(
    FILTER(
        project_completion_by_plant,
        project_completion_by_plant[milestone_date] >= TODAY()
    ),
    project_completion_by_plant[milestone_date] - TODAY()
)
```

### Completion Trend Analysis
```dax
Completion Trend (MoM) =
VAR CurrentMonth = [Average Project Completion %]
VAR PreviousMonth =
    CALCULATE(
        [Average Project Completion %],
        DATEADD(dim_dates[date_value], -1, MONTH)
    )
RETURN
    CurrentMonth - PreviousMonth
```

```dax
Projects Completed This Month =
COUNTROWS(
    FILTER(
        project_completion_by_plant,
        project_completion_by_plant[completion_status] = "Complete" &&
        MONTH(project_completion_by_plant[milestone_date]) = MONTH(TODAY()) &&
        YEAR(project_completion_by_plant[milestone_date]) = YEAR(TODAY())
    )
)
```

## Enhanced Duplicate-Aware Measures

### Part Analysis with Duplicates
```dax
Total Parts (Including Duplicates) =
COUNTROWS(masterbom_clean)
```

```dax
Unique Part IDs =
DISTINCTCOUNT(masterbom_clean[part_id_std])
```

```dax
Average Duplicates per Part =
DIVIDE(
    COUNTROWS(masterbom_clean),
    DISTINCTCOUNT(masterbom_clean[part_id_std]),
    1
) - 1
```

```dax
Parts with Multiple Entries =
COUNTROWS(
    FILTER(
        SUMMARIZE(
            masterbom_clean,
            masterbom_clean[part_id_std],
            "EntryCount", COUNTROWS(masterbom_clean)
        ),
        [EntryCount] > 1
    )
)
```

### Quality Metrics with Duplicate Awareness
```dax
PSW OK % (Duplicate Aware) =
VAR UniquePartsWithPSW =
    COUNTROWS(
        FILTER(
            SUMMARIZE(
                masterbom_clean,
                masterbom_clean[part_id_std],
                "HasPSW", MAX(masterbom_clean[psw_ok])
            ),
            [HasPSW] = TRUE
        )
    )
RETURN
    DIVIDE(
        UniquePartsWithPSW,
        [Unique Part IDs],
        0
    )
```

```dax
FAR OK % (Duplicate Aware) =
VAR UniquePartsWithFAR =
    COUNTROWS(
        FILTER(
            SUMMARIZE(
                masterbom_clean,
                masterbom_clean[part_id_std],
                "HasFAR", MAX(masterbom_clean[far_ok])
            ),
            [HasFAR] = TRUE
        )
    )
RETURN
    DIVIDE(
        UniquePartsWithFAR,
        [Unique Part IDs],
        0
    )
```

## Usage Notes

1. **Relationships**: Ensure proper relationships are established between tables:
   - fact_parts[part_id_std] ↔ plant_item_status[part_id_std]
   - fact_parts[part_id_std] ↔ masterbom_clean[part_id_std]
   - project_completion_by_plant[project_name] ↔ status_clean[project]
   - Date columns ↔ dim_dates[date_value]

2. **Duplicate Handling**: The new measures account for the `is_duplicate_entry` flag in masterbom_clean

3. **Project Completion**: Use project_completion_by_plant table for plant-specific completion analysis

4. **Filters**: These measures respect any filters applied to visuals or pages

5. **Performance**: For large datasets, consider using SUMMARIZE or ADDCOLUMNS for complex calculations

6. **Formatting**: Apply appropriate number formatting (percentage, currency, etc.) to measures in the model

7. **Tooltips**: Use these measures in tooltips for enhanced user experience

8. **Duplicate Analysis**: Use duplicate-aware measures when you want to analyze unique parts vs. all entries
