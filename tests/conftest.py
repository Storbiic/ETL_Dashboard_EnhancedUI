"""Pytest configuration and shared fixtures."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

from backend.core.logging import ETLLogger


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_excel_data():
    """Create sample Excel-like data for testing."""
    return {
        "masterbom": pd.DataFrame(
            {
                "YAZAKI PN": ["7009-6933", "7116-4101-02", "ABC-123", "DEF-456"],
                "BX726_BEV_JOB1+90_YMOK": ["X", "D", "", "0"],
                "BX726_BEV_JOB1+90_YRL": ["", "X", "0", "X"],
                "BX726_MCA_JOB1+90_YMOK": ["D", "", "X", ""],
                "Item Description": ["Wire Harness", "Connector", "Terminal", "Fuse"],
                "Supplier Name": [
                    "Yazaki Corp",
                    "Molex Inc",
                    "TE Connectivity",
                    "Littelfuse",
                ],
                "PSW": ["OK", "NG", "", "OK"],
                "PSW Type": ["Type A", "Type B", "Type C", "Type A"],
                "Approved Date": [
                    "2024-01-15",
                    "2024-02-20",
                    "2024-03-25",
                    "2024-01-30",
                ],
                "PSW Date OK": ["2024-01-10", "2024-02-15", "", "2024-01-25"],
                "FAR Status": ["OK", "NG", "Pending", "OK"],
                "Handling Manual": ["Available", "", "Available", "Available"],
                "IMDS STATUS (Yes, No, N/A)": ["Yes", "No", "N/A", "Yes"],
            }
        ),
        "status": pd.DataFrame(
            {
                "OEM": ["Toyota", "Honda", "Ford"],
                "Project": ["BX726 BEV", "HX123 ICE", "FX456 HEV"],
                "1st PPAP milestone": ["2024-Q2", "2024-Q3", "2024-Q4"],
                "Total Part Numbers": [1250, 890, 1500],
                "PSW Available": ["85%", "92%", "78%"],
                "Drawing Available": ["90%", "88%", "85%"],
                "Managed By": ["Team A", "Team B", "Team C"],
            }
        ),
    }


@pytest.fixture
def mock_etl_logger():
    """Create a mock ETL logger for testing."""
    logger = Mock(spec=ETLLogger)
    logger.messages = []

    def mock_log(level, message, **kwargs):
        logger.messages.append({"level": level, "message": message, "data": kwargs})

    logger.info.side_effect = lambda msg, **kwargs: mock_log("info", msg, **kwargs)
    logger.warning.side_effect = lambda msg, **kwargs: mock_log(
        "warning", msg, **kwargs
    )
    logger.error.side_effect = lambda msg, **kwargs: mock_log("error", msg, **kwargs)
    logger.debug.side_effect = lambda msg, **kwargs: mock_log("debug", msg, **kwargs)
    logger.get_messages.return_value = logger.messages
    logger.clear_messages.side_effect = lambda: logger.messages.clear()

    return logger


@pytest.fixture
def sample_cleaned_data():
    """Create sample cleaned data for testing storage and output."""
    return {
        "masterbom_clean": pd.DataFrame(
            {
                "part_id_std": ["7009-6933", "7116-4101-02", "ABC-123"],
                "part_id_raw": ["7009-6933", "7116-4101-02", "ABC-123"],
                "Item Description": ["Wire Harness", "Connector", "Terminal"],
                "Supplier Name": ["Yazaki Corp", "Molex Inc", "TE Connectivity"],
                "PSW": ["OK", "NG", ""],
                "Approved Date_date": pd.to_datetime(
                    ["2024-01-15", "2024-02-20", "2024-03-25"]
                ).date,
                "Approved Date_year": [2024, 2024, 2024],
                "Approved Date_month": [1, 2, 3],
            }
        ),
        "plant_item_status": pd.DataFrame(
            {
                "part_id_std": [
                    "7009-6933",
                    "7009-6933",
                    "7116-4101-02",
                    "7116-4101-02",
                ],
                "project_plant": ["BX726_BEV", "BX726_MCA", "BX726_BEV", "BX726_MCA"],
                "raw_status": ["X", "D", "D", ""],
                "status_class": ["active", "inactive", "inactive", "new"],
                "is_duplicate": [False, False, False, False],
                "is_new": [False, False, False, True],
                "n_active": [1, 1, 0, 0],
                "n_inactive": [1, 1, 1, 1],
                "n_new": [0, 0, 1, 1],
                "n_duplicate": [0, 0, 0, 0],
            }
        ),
        "fact_parts": pd.DataFrame(
            {
                "part_id_std": ["7009-6933", "7116-4101-02", "ABC-123"],
                "part_id_raw": ["7009-6933", "7116-4101-02", "ABC-123"],
                "Item Description": ["Wire Harness", "Connector", "Terminal"],
                "Supplier Name": ["Yazaki Corp", "Molex Inc", "TE Connectivity"],
                "psw_ok": [True, False, False],
                "has_handling_manual": [True, False, True],
                "far_ok": [True, False, False],
                "imds_ok": [True, False, False],
            }
        ),
        "status_clean": pd.DataFrame(
            {
                "OEM": ["Toyota", "Honda", "Ford"],
                "Project": ["BX726 BEV", "HX123 ICE", "FX456 HEV"],
                "First_PPAP_Milestone": ["2024-Q2", "2024-Q3", "2024-Q4"],
                "Total_Part_Numbers": [1250, 890, 1500],
                "PSW_Available": [0.85, 0.92, 0.78],
                "Drawing_Available": [0.90, 0.88, 0.85],
            }
        ),
        "dim_dates": pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-15", "2024-02-20", "2024-03-25"]).date,
                "role": ["Approved Date", "Approved Date", "Approved Date"],
                "year": [2024, 2024, 2024],
                "month": [1, 2, 3],
                "day": [15, 20, 25],
                "quarter": [1, 1, 1],
                "week": [3, 8, 12],
                "weekday": [0, 1, 0],
                "month_name": ["January", "February", "March"],
                "day_name": ["Monday", "Tuesday", "Monday"],
            }
        ),
    }


@pytest.fixture
def sample_file_upload():
    """Create sample file upload data for API testing."""
    return {
        "file_id": "test-file-123",
        "filename": "test_workbook.xlsx",
        "sheet_names": ["MasterBOM", "Status", "Summary"],
        "file_size": 1024000,  # 1MB
        "upload_time": "2024-01-15T10:30:00",
    }


@pytest.fixture
def sample_transform_request():
    """Create sample transform request for API testing."""
    return {
        "file_id": "test-file-123",
        "master_sheet": "MasterBOM",
        "status_sheet": "Status",
        "options": {
            "id_col": "YAZAKI PN",
            "date_cols": ["Approved Date", "PSW Date OK"],
        },
    }


@pytest.fixture
def sample_artifacts():
    """Create sample artifact information for testing."""
    return [
        {
            "name": "masterbom_clean.csv",
            "path": "/data/processed/masterbom_clean.csv",
            "format": "CSV",
            "size_bytes": 50000,
            "row_count": 1000,
        },
        {
            "name": "masterbom_clean.parquet",
            "path": "/data/processed/masterbom_clean.parquet",
            "format": "Parquet",
            "size_bytes": 25000,
            "row_count": 1000,
        },
        {
            "name": "etl.sqlite",
            "path": "/data/processed/etl.sqlite",
            "format": "SQLite",
            "size_bytes": 100000,
            "row_count": 5000,
        },
    ]


# Test data generators
def generate_large_masterbom(n_parts=1000, n_projects=10):
    """Generate large MasterBOM dataset for performance testing."""
    import numpy as np

    np.random.seed(42)

    data = {"YAZAKI PN": [f"PART-{i:06d}" for i in range(n_parts)]}

    # Add project columns
    for j in range(n_projects):
        project_name = f"PROJECT_{j:02d}_PLANT"
        data[project_name] = np.random.choice(
            ["X", "D", "", "0"], n_parts, p=[0.4, 0.2, 0.3, 0.1]
        )

    data.update(
        {
            "Item Description": [f"Component {i}" for i in range(n_parts)],
            "Supplier Name": np.random.choice(
                ["Supplier A", "Supplier B", "Supplier C"], n_parts
            ),
            "PSW": np.random.choice(["OK", "NG", ""], n_parts, p=[0.6, 0.2, 0.2]),
            "Approved Date": pd.date_range(
                "2023-01-01", periods=n_parts, freq="D"
            ).strftime("%Y-%m-%d"),
            "FAR Status": np.random.choice(
                ["OK", "NG", "Pending"], n_parts, p=[0.5, 0.2, 0.3]
            ),
        }
    )

    return pd.DataFrame(data)


def generate_problematic_data():
    """Generate data with common problems for error testing."""
    return pd.DataFrame(
        {
            "YAZAKI PN": ["", None, "VALID-123", "7009@6933#", "  spaced  "],
            "Project_1": ["X", "invalid", "", "0", "D"],
            "Item Description": [
                "",
                "Valid Description",
                None,
                "Spéciàl Chars",
                "Normal",
            ],
            "Supplier Name": [
                None,
                "",
                "UPPERCASE SUPPLIER",
                "  spaced supplier  ",
                "Normal Supplier",
            ],
            "Approved Date": ["", "invalid-date", "2024-01-15", "2024-13-45", None],
            "PSW": ["", "UNKNOWN", "OK", "NG", None],
        }
    )


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")


# Custom assertions
def assert_dataframe_equal(df1, df2, check_dtype=True, check_index=True):
    """Custom assertion for DataFrame equality with better error messages."""
    try:
        pd.testing.assert_frame_equal(
            df1, df2, check_dtype=check_dtype, check_index=check_index
        )
    except AssertionError as e:
        # Add more context to the error
        print("DataFrame comparison failed:")
        print(f"Left shape: {df1.shape}, Right shape: {df2.shape}")
        print(f"Left columns: {list(df1.columns)}")
        print(f"Right columns: {list(df2.columns)}")
        raise e


def assert_valid_part_id(part_id):
    """Assert that a part ID is properly cleaned."""
    assert isinstance(part_id, str)
    assert part_id == part_id.upper()
    assert part_id == part_id.strip()
    # Should only contain alphanumeric, hyphens, and single spaces
    import re

    assert re.match(r"^[A-Z0-9\-\s]+$", part_id)
    # No multiple spaces
    assert "  " not in part_id
