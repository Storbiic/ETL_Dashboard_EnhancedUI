"""DAX measures file generator for Power BI import."""

import os
from pathlib import Path
from typing import Dict, List


class DAXGenerator:
    """Generate DAX measures file from markdown documentation."""

    def __init__(self):
        """Initialize DAX generator."""
        # Try multiple path resolution strategies for different environments
        self.project_root = self._find_project_root()
        self.measures_file = self.project_root / "powerbi" / "measures_dax.md"

    def _find_project_root(self) -> Path:
        """Find the project root directory in different environments."""
        # Strategy 1: Check if we're in Docker (/app)
        docker_root = Path("/app")
        if docker_root.exists() and (docker_root / "powerbi").exists():
            return docker_root
        
        # Strategy 2: Use PYTHONPATH environment variable
        pythonpath = os.getenv("PYTHONPATH")
        if pythonpath and Path(pythonpath).exists():
            pythonpath_root = Path(pythonpath)
            if (pythonpath_root / "powerbi").exists():
                return pythonpath_root
        
        # Strategy 3: Traditional relative path (for local development)
        file_root = Path(__file__).parent.parent.parent
        if (file_root / "powerbi").exists():
            return file_root
        
        # Strategy 4: Current working directory
        cwd_root = Path.cwd()
        if (cwd_root / "powerbi").exists():
            return cwd_root
        
        # Fallback to file-based resolution
        return Path(__file__).parent.parent.parent

    def generate_dax_file(self, output_path: str) -> str:
        """
        Generate a .dax file from the measures markdown.

        Args:
            output_path: Path where to save the .dax file

        Returns:
            Path to the generated .dax file
        """
        if not self.measures_file.exists():
            # Enhanced error message with debugging info
            error_msg = f"Measures file not found: {self.measures_file}\n"
            error_msg += f"Project root: {self.project_root}\n"
            error_msg += f"PowerBI directory exists: {(self.project_root / 'powerbi').exists()}\n"
            error_msg += f"PowerBI directory contents: {list((self.project_root / 'powerbi').glob('*')) if (self.project_root / 'powerbi').exists() else 'N/A'}\n"
            error_msg += f"Current working directory: {Path.cwd()}\n"
            error_msg += f"File location: {Path(__file__).parent}\n"
            raise FileNotFoundError(error_msg)

        # Read the markdown file
        with open(self.measures_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract DAX measures from markdown
        dax_measures = self._extract_dax_measures(content)

        # Generate the .dax file content
        dax_content = self._format_dax_file(dax_measures)

        # Write the .dax file
        dax_file_path = Path(output_path) / "ETL_Dashboard_Measures.dax"
        with open(dax_file_path, "w", encoding="utf-8") as f:
            f.write(dax_content)

        return str(dax_file_path)

    def _extract_dax_measures(self, content: str) -> List[Dict[str, str]]:
        """Extract DAX measures from markdown content."""
        measures = []
        lines = content.split("\n")

        current_measure = None
        in_dax_block = False
        dax_lines = []

        for line in lines:
            # Check for DAX code block start
            if line.strip() == "```dax":
                in_dax_block = True
                dax_lines = []
                continue

            # Check for code block end
            if line.strip() == "```" and in_dax_block:
                in_dax_block = False
                if dax_lines and current_measure:
                    # Join DAX lines and clean up
                    dax_code = "\n".join(dax_lines).strip()
                    measures.append(
                        {
                            "name": current_measure,
                            "dax": dax_code,
                            "category": self._determine_category(current_measure),
                        }
                    )
                current_measure = None
                continue

            # If we're in a DAX block, collect the lines
            if in_dax_block:
                dax_lines.append(line)
                # Extract measure name from first line if it contains =
                if "=" in line and not current_measure:
                    current_measure = line.split("=")[0].strip()
                continue

            # Look for measure names in headers or before code blocks
            if line.startswith("#") and not in_dax_block:
                # This might be a section header, not a measure name
                continue

        return measures

    def _determine_category(self, measure_name: str) -> str:
        """Determine the category for a measure based on its name."""
        name_lower = measure_name.lower()

        if any(keyword in name_lower for keyword in ["duplicate", "flag"]):
            return "Duplicate Analysis"
        elif any(
            keyword in name_lower for keyword in ["completion", "project", "milestone"]
        ):
            return "Project Completion"
        elif any(keyword in name_lower for keyword in ["plant", "facility"]):
            return "Plant Performance"
        elif any(
            keyword in name_lower for keyword in ["psw", "far", "ppap", "quality"]
        ):
            return "Quality Metrics"
        elif any(
            keyword in name_lower for keyword in ["time", "date", "trend", "month"]
        ):
            return "Time Analysis"
        elif any(keyword in name_lower for keyword in ["supplier", "vendor"]):
            return "Supplier Analysis"
        else:
            return "General Measures"

    def _format_dax_file(self, measures: List[Dict[str, str]]) -> str:
        """Format measures into a proper .dax file."""
        content = []

        # Add file header
        content.append("// ETL Dashboard - Power BI DAX Measures")
        content.append("// Generated automatically from ETL Dashboard")
        content.append("// Import this file into Power BI for ready-to-use measures")
        content.append("// ============================================")
        content.append("// ENHANCED DAX MEASURES FOR ETL DASHBOARD")
        content.append("// ============================================")
        content.append("")

        # Add essential measures first if not found in markdown
        essential_measures = self._get_essential_measures()

        # Group measures by category
        categories = {}
        for measure in measures:
            category = measure["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(measure)

        # Add essential measures to appropriate categories
        for measure in essential_measures:
            category = measure["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(measure)

        # Define category order for better organization
        category_order = [
            "General Measures",
            "Duplicate Analysis",
            "Project Completion",
            "Plant Performance",
            "Quality Metrics",
            "Time Analysis",
            "Supplier Analysis",
        ]

        # Add measures by category in order
        for category in category_order:
            if category in categories:
                content.append(f"// ============================================")
                content.append(f"// {category.upper()}")
                content.append(f"// ============================================")
                content.append("")

                for measure in categories[category]:
                    content.append(f"// {measure['name']}")
                    content.append(measure["dax"])
                    content.append("")
                    content.append("")

        # Add any remaining categories not in the order
        for category, category_measures in categories.items():
            if category not in category_order:
                content.append(f"// ============================================")
                content.append(f"// {category.upper()}")
                content.append(f"// ============================================")
                content.append("")

                for measure in category_measures:
                    content.append(f"// {measure['name']}")
                    content.append(measure["dax"])
                    content.append("")
                    content.append("")

        # Add footer with usage instructions
        content.append("// ============================================")
        content.append("// USAGE INSTRUCTIONS")
        content.append("// ============================================")
        content.append("// 1. Import your ETL Dashboard data files into Power BI")
        content.append("// 2. Ensure table relationships are properly configured")
        content.append("// 3. Copy and paste these measures into Power BI")
        content.append("// 4. Organize measures into appropriate display folders")
        content.append("// 5. Create visualizations using these measures")
        content.append("")
        content.append("// Required Tables:")
        content.append("// - masterbom_clean")
        content.append("// - plant_item_status")
        content.append("// - fact_parts")
        content.append("// - status_clean")
        content.append("// - project_completion_by_plant")
        content.append("// - dim_dates")
        content.append("// - date_role_bridge")
        content.append("")
        content.append("// Table Relationships:")
        content.append("// - masterbom_clean[id] -> plant_item_status[item_id]")
        content.append("// - masterbom_clean[id] -> fact_parts[item_id]")
        content.append(
            "// - project_completion_by_plant[project_name] -> status_clean[Project]"
        )
        content.append("// - dim_dates[date] -> date_role_bridge[date]")

        return "\n".join(content)

    def _get_essential_measures(self) -> List[Dict[str, str]]:
        """Get essential DAX measures that should always be included."""
        return [
            {
                "name": "Total Parts Count",
                "dax": """Total Parts Count =
COUNTROWS(masterbom_clean)""",
                "category": "General Measures",
            },
            {
                "name": "Total Duplicate Parts",
                "dax": """Total Duplicate Parts =
COUNTROWS(
    FILTER(
        masterbom_clean,
        masterbom_clean[is_duplicate_entry] = TRUE
    )
)""",
                "category": "Duplicate Analysis",
            },
            {
                "name": "Duplicate Percentage",
                "dax": """Duplicate Percentage =
DIVIDE(
    [Total Duplicate Parts],
    [Total Parts Count],
    0
) * 100""",
                "category": "Duplicate Analysis",
            },
            {
                "name": "Average Project Completion",
                "dax": """Average Project Completion =
AVERAGE(project_completion_by_plant[overall_completion_pct]) * 100""",
                "category": "Project Completion",
            },
            {
                "name": "Plant Count",
                "dax": """Plant Count =
DISTINCTCOUNT(project_completion_by_plant[plant_id])""",
                "category": "Plant Performance",
            },
            {
                "name": "Project Count",
                "dax": """Project Count =
DISTINCTCOUNT(project_completion_by_plant[project_name])""",
                "category": "Project Completion",
            },
            {
                "name": "PSW Completion Average",
                "dax": """PSW Completion Average =
AVERAGE(project_completion_by_plant[psw_completion_pct]) * 100""",
                "category": "Quality Metrics",
            },
            {
                "name": "Drawing Completion Average",
                "dax": """Drawing Completion Average =
AVERAGE(project_completion_by_plant[drawing_completion_pct]) * 100""",
                "category": "Quality Metrics",
            },
            {
                "name": "Plant Performance Score",
                "dax": """Plant Performance Score =
AVERAGEX(
    VALUES(project_completion_by_plant[plant_id]),
    AVERAGE(
        FILTER(
            project_completion_by_plant,
            project_completion_by_plant[plant_id] = EARLIER(project_completion_by_plant[plant_id])
        )[overall_completion_pct]
    )
) * 100""",
                "category": "Plant Performance",
            },
            {
                "name": "Cross Plant Comparison",
                "dax": """Cross Plant Comparison =
VAR CurrentPlantAvg =
    AVERAGE(
        FILTER(
            project_completion_by_plant,
            project_completion_by_plant[plant_id] = SELECTEDVALUE(project_completion_by_plant[plant_id])
        )[overall_completion_pct]
    )
VAR OverallAvg =
    AVERAGE(project_completion_by_plant[overall_completion_pct])
RETURN
    (CurrentPlantAvg - OverallAvg) * 100""",
                "category": "Plant Performance",
            },
        ]
