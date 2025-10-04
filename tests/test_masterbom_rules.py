"""Tests for MasterBOM processing rules and transformations."""

from unittest.mock import Mock

import pandas as pd
import pytest

from backend.core.logging import ETLLogger
from backend.services.masterbom_rules import MasterBOMProcessor


class TestMasterBOMProcessor:
    """Test the MasterBOMProcessor class."""

    @pytest.fixture
    def sample_masterbom_data(self):
        """Create sample MasterBOM data for testing."""
        return pd.DataFrame(
            {
                "YAZAKI PN": [
                    "7009-6933",
                    "7116-4101-02",
                    "ABC-123",
                    "7009-6933",
                ],  # Duplicate
                "BX726_BEV_JOB1+90_YMOK": ["X", "D", "", "X"],
                "BX726_BEV_JOB1+90_YRL": ["", "X", "0", ""],
                "BX726_MCA_JOB1+90_YMOK": ["D", "", "X", "D"],
                "Item Description": [
                    "Wire Harness",
                    "Connector",
                    "Terminal",
                    "Wire Harness",
                ],
                "Supplier Name": [
                    "  yazaki corp  ",
                    "MOLEX INC",
                    "te connectivity",
                    "  yazaki corp  ",
                ],
                "PSW": ["OK", "NG", "", "OK"],
                "PSW Type": ["Type A", "Type B", "Type C", "Type A"],
                "Approved Date": ["2024-01-15", "2024-02-20", "invalid", "2024-01-15"],
                "PSW Date OK": ["2024-01-10", "2024-02-15", "", "2024-01-10"],
                "FAR Status": ["OK", "NG", "Pending", "OK"],
                "Handling Manual": ["Available", "", "Available", "Available"],
                "IMDS STATUS (Yes, No, N/A)": ["Yes", "No", "N/A", "Yes"],
            }
        )

    @pytest.fixture
    def mock_logger(self):
        """Create a mock ETL logger."""
        return Mock(spec=ETLLogger)

    def test_processor_initialization(self, sample_masterbom_data, mock_logger):
        """Test processor initialization."""
        processor = MasterBOMProcessor(sample_masterbom_data, mock_logger)

        assert processor.df is not None
        assert len(processor.df) == 4
        assert processor.logger is mock_logger
        assert processor.project_columns == []
        assert processor.id_column is None

    def test_clean_column_names(self, sample_masterbom_data, mock_logger):
        """Test column name cleaning."""
        # Add some messy column names
        sample_masterbom_data.columns = [
            "  YAZAKI PN  ",
            "BX726_BEV_JOB1+90_YMOK",
            "BX726_BEV_JOB1+90_YRL",
            "BX726_MCA_JOB1+90_YMOK",
            "  Item Description  ",
            "Supplier Name",
            "PSW",
            "PSW Type",
            "Approved Date",
            "PSW Date OK",
            "FAR Status",
            "Handling Manual",
            "IMDS STATUS (Yes, No, N/A)",
        ]

        processor = MasterBOMProcessor(sample_masterbom_data, mock_logger)
        processor._clean_column_names()

        # Check that column names are cleaned
        assert "YAZAKI PN" in processor.df.columns
        assert "Item Description" in processor.df.columns
        assert "  YAZAKI PN  " not in processor.df.columns

    def test_identify_columns(self, sample_masterbom_data, mock_logger):
        """Test ID and project column identification."""
        processor = MasterBOMProcessor(sample_masterbom_data, mock_logger)
        processor._identify_columns("YAZAKI PN")

        assert processor.id_column == "YAZAKI PN"

        # Project columns should be between ID and Item Description
        expected_projects = [
            "BX726_BEV_JOB1+90_YMOK",
            "BX726_BEV_JOB1+90_YRL",
            "BX726_MCA_JOB1+90_YMOK",
        ]
        assert processor.project_columns == expected_projects

    def test_clean_id_column(self, sample_masterbom_data, mock_logger):
        """Test ID column cleaning."""
        processor = MasterBOMProcessor(sample_masterbom_data, mock_logger)
        processor.id_column = "YAZAKI PN"
        processor._clean_id_column()

        assert "part_id_raw" in processor.df.columns
        assert "part_id_std" in processor.df.columns

        # Check cleaning results
        assert processor.df["part_id_std"].iloc[0] == "7009-6933"
        assert processor.df["part_id_std"].iloc[1] == "7116-4101-02"
        assert processor.df["part_id_std"].iloc[2] == "ABC-123"

    def test_process_date_columns(self, sample_masterbom_data, mock_logger):
        """Test date column processing."""
        processor = MasterBOMProcessor(sample_masterbom_data, mock_logger)
        date_cols = ["Approved Date", "PSW Date OK"]
        processor._process_date_columns(date_cols)

        # Check that date columns are created
        assert "Approved Date_date" in processor.df.columns
        assert "Approved Date_year" in processor.df.columns
        assert "Approved Date_month" in processor.df.columns
        assert "PSW Date OK_date" in processor.df.columns

        # Check specific values
        assert processor.df["Approved Date_year"].iloc[0] == 2024
        assert processor.df["Approved Date_month"].iloc[0] == 1

    def test_standardize_text_columns(self, sample_masterbom_data, mock_logger):
        """Test text column standardization."""
        processor = MasterBOMProcessor(sample_masterbom_data, mock_logger)
        processor._standardize_text_columns()

        # Check supplier name standardization
        assert processor.df["Supplier Name"].iloc[0] == "Yazaki Corp"
        assert processor.df["Supplier Name"].iloc[1] == "Molex Inc"
        assert processor.df["Supplier Name"].iloc[2] == "Te Connectivity"

    def test_create_plant_item_status(self, sample_masterbom_data, mock_logger):
        """Test plant-item-status table creation."""
        processor = MasterBOMProcessor(sample_masterbom_data, mock_logger)
        processor.id_column = "YAZAKI PN"
        processor.project_columns = [
            "BX726_BEV_JOB1+90_YMOK",
            "BX726_BEV_JOB1+90_YRL",
            "BX726_MCA_JOB1+90_YMOK",
        ]
        processor._clean_id_column()

        result = processor._create_plant_item_status()

        # Check structure
        expected_columns = [
            "part_id_std",
            "part_id_raw",
            "YAZAKI PN",
            "project_plant",
            "raw_status",
            "status_class",
            "is_duplicate",
            "is_new",
            "notes",
        ]
        for col in expected_columns:
            assert col in result.columns

        # Check that we have entries for all parts and projects
        assert len(result) == 4 * 3  # 4 parts × 3 projects

        # Check status classification
        x_entries = result[result["raw_status"] == "X"]
        assert all(x_entries["status_class"] == "active")

        d_entries = result[result["raw_status"] == "D"]
        assert all(d_entries["status_class"] == "inactive")

    def test_classify_status(self, sample_masterbom_data, mock_logger):
        """Test status classification logic."""
        processor = MasterBOMProcessor(sample_masterbom_data, mock_logger)

        # Test different status values
        test_row_x = pd.Series({"raw_status": "X"})
        assert processor._classify_status(test_row_x) == "active"

        test_row_d = pd.Series({"raw_status": "D"})
        assert processor._classify_status(test_row_d) == "inactive"

        test_row_0 = pd.Series({"raw_status": "0"})
        assert processor._classify_status(test_row_0) == "duplicate"

        test_row_empty = pd.Series({"raw_status": ""})
        assert processor._classify_status(test_row_empty) == "new"

        test_row_nan = pd.Series({"raw_status": None})
        assert processor._classify_status(test_row_nan) == "new"

    def test_create_fact_parts(self, sample_masterbom_data, mock_logger):
        """Test fact parts table creation."""
        processor = MasterBOMProcessor(sample_masterbom_data, mock_logger)
        processor.id_column = "YAZAKI PN"
        processor._clean_id_column()

        result = processor._create_fact_parts()

        # Check structure
        expected_columns = [
            "part_id_std",
            "part_id_raw",
            "Item Description",
            "Supplier Name",
            "PSW",
            "PSW Type",
            "FAR Status",
            "Handling Manual",
        ]
        for col in expected_columns:
            assert col in result.columns

        # Should have one row per unique part
        unique_parts = sample_masterbom_data["YAZAKI PN"].nunique()
        assert len(result) == unique_parts

        # Check derived flags
        if "psw_ok" in result.columns:
            # Parts with PSW = "OK" should have psw_ok = True
            ok_parts = result[result["PSW"] == "OK"]
            assert all(ok_parts["psw_ok"] is True)

    def test_finalize_masterbom(self, sample_masterbom_data, mock_logger):
        """Test MasterBOM finalization."""
        processor = MasterBOMProcessor(sample_masterbom_data, mock_logger)

        result = processor._finalize_masterbom()

        # Should remove duplicates
        assert len(result) <= len(sample_masterbom_data)

        # Check that it's a DataFrame
        assert isinstance(result, pd.DataFrame)

    def test_full_process(self, sample_masterbom_data, mock_logger):
        """Test complete processing pipeline."""
        processor = MasterBOMProcessor(sample_masterbom_data, mock_logger)

        result = processor.process(
            id_col="YAZAKI PN", date_cols=["Approved Date", "PSW Date OK"]
        )

        # Check that all expected tables are returned
        expected_tables = ["masterbom_clean", "plant_item_status", "fact_parts"]
        for table in expected_tables:
            assert table in result
            assert isinstance(result[table], pd.DataFrame)

        # Check masterbom_clean
        masterbom = result["masterbom_clean"]
        assert "part_id_std" in masterbom.columns
        assert "part_id_raw" in masterbom.columns
        assert "Approved Date_date" in masterbom.columns

        # Check plant_item_status
        plant_status = result["plant_item_status"]
        assert len(plant_status) > 0
        assert "status_class" in plant_status.columns

        # Check fact_parts
        fact_parts = result["fact_parts"]
        assert len(fact_parts) > 0
        assert "part_id_std" in fact_parts.columns

    def test_missing_id_column(self, sample_masterbom_data, mock_logger):
        """Test handling of missing ID column."""
        processor = MasterBOMProcessor(sample_masterbom_data, mock_logger)

        # Process with non-existent ID column
        result = processor.process(id_col="NON_EXISTENT_COLUMN")

        # Should still complete but use first column
        assert "masterbom_clean" in result
        assert "plant_item_status" in result
        assert "fact_parts" in result

    def test_no_project_columns(self, mock_logger):
        """Test handling when no project columns are detected."""
        # Create data with no clear project columns
        df = pd.DataFrame(
            {
                "YAZAKI PN": ["7009-6933", "7116-4101"],
                "Item Description": ["Wire Harness", "Connector"],
                "Supplier Name": ["Yazaki", "Molex"],
            }
        )

        processor = MasterBOMProcessor(df, mock_logger)
        result = processor.process(id_col="YAZAKI PN")

        # Should still complete
        assert "masterbom_clean" in result
        assert "plant_item_status" in result
        assert "fact_parts" in result

        # plant_item_status should be empty or minimal
        plant_status = result["plant_item_status"]
        assert len(plant_status) == 0 or len(plant_status) <= len(df)

    def test_empty_dataframe(self, mock_logger):
        """Test processing empty DataFrame."""
        df = pd.DataFrame()
        processor = MasterBOMProcessor(df, mock_logger)

        result = processor.process()

        # Should return empty tables
        for table in result.values():
            assert len(table) == 0


class TestMasterBOMEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def mock_logger(self):
        return Mock(spec=ETLLogger)

    def test_special_characters_in_ids(self, mock_logger):
        """Test handling of special characters in part IDs."""
        df = pd.DataFrame(
            {
                "YAZAKI PN": ["7009@6933#", "ABC/123\\", "XYZ*456&"],
                "Item Description": ["Part A", "Part B", "Part C"],
            }
        )

        processor = MasterBOMProcessor(df, mock_logger)
        result = processor.process(id_col="YAZAKI PN")

        masterbom = result["masterbom_clean"]

        # Check that IDs are cleaned
        assert masterbom["part_id_std"].iloc[0] == "70096933"
        assert masterbom["part_id_std"].iloc[1] == "ABC123"
        assert masterbom["part_id_std"].iloc[2] == "XYZ456"

    def test_unicode_characters(self, mock_logger):
        """Test handling of Unicode characters."""
        df = pd.DataFrame(
            {
                "YAZAKI PN": ["7009-6933", "ABC-123"],
                "Item Description": ["Café Wire", "Naïve Connector"],
                "Supplier Name": ["Zürich Corp", "Résumé Inc"],
            }
        )

        processor = MasterBOMProcessor(df, mock_logger)
        result = processor.process(id_col="YAZAKI PN")

        # Should handle Unicode without errors
        masterbom = result["masterbom_clean"]
        assert len(masterbom) == 2

    def test_very_large_dataset(self, mock_logger):
        """Test processing with large dataset."""
        # Create larger dataset
        import numpy as np

        np.random.seed(42)

        n_parts = 1000
        n_projects = 10

        data = {"YAZAKI PN": [f"PART-{i:04d}" for i in range(n_parts)]}

        # Add project columns
        for j in range(n_projects):
            project_name = f"PROJECT_{j}"
            data[project_name] = np.random.choice(["X", "D", "", "0"], n_parts)

        data["Item Description"] = [f"Description {i}" for i in range(n_parts)]

        df = pd.DataFrame(data)
        processor = MasterBOMProcessor(df, mock_logger)

        result = processor.process(id_col="YAZAKI PN")

        # Should complete successfully
        assert len(result["masterbom_clean"]) == n_parts
        assert len(result["fact_parts"]) == n_parts
        # plant_item_status should have n_parts × n_projects entries
        assert len(result["plant_item_status"]) == n_parts * n_projects
