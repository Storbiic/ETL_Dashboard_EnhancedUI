"""Tests for enhanced plant_item_status processing with Morocco supplier
prioritization.
"""

from unittest.mock import Mock

import pandas as pd
import pytest

from backend.core.logging import ETLLogger
from backend.services.masterbom_rules import MasterBOMProcessor


class TestEnhancedPlantItemStatus:
    """Test enhanced plant-item-status processing logic."""

    @pytest.fixture
    def sample_data_with_duplicates(self):
        """Create sample data with duplicates and Morocco suppliers."""
        return pd.DataFrame(
            {
                "YAZAKI PN": [
                    "180AN503913",
                    "180AN503913",
                    "180AN503913",  # Triple duplicate
                    "7009-6933",
                    "7009-6933",  # Double duplicate
                    "ABC-123",  # No duplicate
                ],
                "BX726_BEV_JOB1+90_YMOK": ["X", "X", "D", "", "X", ""],
                "BX726_BEV_JOB1+90_YRL": ["", "D", "X", "X", "", "D"],
                "BX726_MCA_JOB1+90_YMOK": ["D", "", "", "D", "X", "X"],
                "Item Description": [
                    "Wire Harness A",
                    "Wire Harness A",
                    "Wire Harness A",
                    "Connector B",
                    "Connector B",
                    "Terminal C",
                ],
                "Supplier Name": [
                    "Global Supplier Inc",
                    "Morocco Automotive MA",
                    "Yazaki Maroc",
                    "Standard Supplier",
                    "Morocco Industrial MAROC",
                    "Regular Corp",
                ],
                "FAR Status": [
                    "To be Requested",
                    "OK",
                    "Pending",
                    "OK",
                    "To be Requested",
                    "OK",
                ],
            }
        )

    @pytest.fixture
    def mock_logger(self):
        """Create a mock ETL logger."""
        return Mock(spec=ETLLogger)

    def test_morocco_supplier_prioritization(
        self, sample_data_with_duplicates, mock_logger
    ):
        """Test that Morocco suppliers are prioritized in duplicate resolution."""
        processor = MasterBOMProcessor(sample_data_with_duplicates, mock_logger)
        processor.id_column = "YAZAKI PN"
        processor.project_columns = [
            "BX726_BEV_JOB1+90_YMOK",
            "BX726_BEV_JOB1+90_YRL",
            "BX726_MCA_JOB1+90_YMOK",
        ]
        processor._clean_id_column()

        # Test source duplicate handling
        deduplicated = processor._handle_source_duplicates()

        # Should have 3 unique parts (duplicates resolved)
        assert len(deduplicated) == 3
        assert deduplicated["part_id_std"].nunique() == 3

        # Check that Morocco suppliers were prioritized
        part_180AN = deduplicated[deduplicated["part_id_std"] == "180AN503913"]
        assert len(part_180AN) == 1
        # Should be one of the Morocco suppliers
        supplier_name = part_180AN.iloc[0]["Supplier Name"]
        assert any(
            pattern.lower() in supplier_name.lower()
            for pattern in ["ma", "maroc", "morocco"]
        )

        part_7009 = deduplicated[deduplicated["part_id_std"] == "7009-6933"]
        assert len(part_7009) == 1
        # Should be the Morocco supplier
        supplier_name = part_7009.iloc[0]["Supplier Name"]
        assert "maroc" in supplier_name.lower()

    def test_status_classification_enhanced(
        self, sample_data_with_duplicates, mock_logger
    ):
        """Test enhanced status classification logic."""
        processor = MasterBOMProcessor(sample_data_with_duplicates, mock_logger)

        # Test status classification
        test_cases = [
            ("X", "active"),
            ("D", "discontinued"),
            ("", "not_in_project"),
            ("0", "not_in_project"),
            ("random", "not_in_project"),
            (None, "not_in_project"),
        ]

        for raw_status, expected_class in test_cases:
            row = {"raw_status": raw_status}
            result = processor._classify_status_enhanced(row)
            assert (
                result == expected_class
            ), f"Status '{raw_status}' should be '{expected_class}', got '{result}'"

    def test_plant_item_status_creation_with_duplicates(
        self, sample_data_with_duplicates, mock_logger
    ):
        """Test complete plant-item-status creation with duplicate handling."""
        processor = MasterBOMProcessor(sample_data_with_duplicates, mock_logger)
        processor.id_column = "YAZAKI PN"
        processor.project_columns = [
            "BX726_BEV_JOB1+90_YMOK",
            "BX726_BEV_JOB1+90_YRL",
            "BX726_MCA_JOB1+90_YMOK",
        ]
        processor._clean_id_column()

        result = processor._create_plant_item_status()

        # Should have 9 records (3 unique parts × 3 projects)
        assert len(result) == 9
        assert result["part_id_std"].nunique() == 3
        assert result["project_plant"].nunique() == 3

        # Check status classes
        status_classes = result["status_class"].unique()
        expected_statuses = {"active", "discontinued", "not_in_project"}
        assert set(status_classes).issubset(expected_statuses)

        # Check that we have the expected columns
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

    def test_specific_yazaki_pn_180AN503913(
        self, sample_data_with_duplicates, mock_logger
    ):
        """Test specific case: Yazaki PN 180AN503913 with multiple FAR Status values."""
        processor = MasterBOMProcessor(sample_data_with_duplicates, mock_logger)
        processor.id_column = "YAZAKI PN"
        processor.project_columns = [
            "BX726_BEV_JOB1+90_YMOK",
            "BX726_BEV_JOB1+90_YRL",
            "BX726_MCA_JOB1+90_YMOK",
        ]
        processor._clean_id_column()

        # Test duplicate resolution for specific part
        part_records = sample_data_with_duplicates[
            sample_data_with_duplicates["YAZAKI PN"] == "180AN503913"
        ].copy()

        resolved = processor._resolve_duplicate_with_morocco_priority(
            "180AN503913", part_records
        )

        # Should return single record
        assert len(resolved) == 1

        # Should be a Morocco supplier
        supplier_name = resolved.iloc[0]["Supplier Name"]
        assert any(
            pattern.lower() in supplier_name.lower()
            for pattern in ["ma", "maroc", "morocco"]
        )

    def test_no_duplicates_case(self, mock_logger):
        """Test processing when no duplicates exist."""
        clean_data = pd.DataFrame(
            {
                "YAZAKI PN": ["ABC-123", "DEF-456", "GHI-789"],
                "BX726_BEV_JOB1+90_YMOK": ["X", "D", ""],
                "BX726_BEV_JOB1+90_YRL": ["", "X", "D"],
                "Item Description": ["Part A", "Part B", "Part C"],
                "Supplier Name": ["Supplier A", "Supplier B", "Supplier C"],
                "FAR Status": ["OK", "NG", "Pending"],
            }
        )

        processor = MasterBOMProcessor(clean_data, mock_logger)
        processor.id_column = "YAZAKI PN"
        processor.project_columns = ["BX726_BEV_JOB1+90_YMOK", "BX726_BEV_JOB1+90_YRL"]
        processor._clean_id_column()

        result = processor._create_plant_item_status()

        # Should have 6 records (3 parts × 2 projects)
        assert len(result) == 6
        assert result["part_id_std"].nunique() == 3
        assert result["project_plant"].nunique() == 2

        # No duplicates should be marked
        assert not result["is_duplicate"].any()

    def test_morocco_pattern_matching(self, mock_logger):
        """Test Morocco supplier pattern matching."""
        test_data = pd.DataFrame(
            {
                "YAZAKI PN": ["TEST-001"] * 5,
                "BX726_BEV_JOB1+90_YMOK": ["X"] * 5,
                "Supplier Name": [
                    "Morocco Automotive",
                    "Yazaki MAROC Industries",
                    "Global MA Solutions",
                    "Standard Supplier",
                    "MOROCCO Manufacturing",
                ],
                "FAR Status": ["OK"] * 5,
            }
        )

        processor = MasterBOMProcessor(test_data, mock_logger)
        processor.id_column = "YAZAKI PN"
        processor._clean_id_column()

        part_records = test_data.copy()
        resolved = processor._resolve_duplicate_with_morocco_priority(
            "TEST-001", part_records
        )

        # Should return single record with Morocco supplier
        assert len(resolved) == 1
        supplier_name = resolved.iloc[0]["Supplier Name"]
        assert any(
            pattern.lower() in supplier_name.lower()
            for pattern in ["ma", "maroc", "morocco"]
        )
