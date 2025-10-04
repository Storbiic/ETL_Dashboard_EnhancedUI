"""Tests for data cleaning utilities."""

import pandas as pd

from backend.services.cleaning import (
    clean_id,
    create_dim_dates,
    create_row_hash,
    detect_date_columns,
    parse_date_column,
    remove_duplicate_rows,
    standardize_text,
)


class TestCleanId:
    """Test the clean_id function."""

    def test_basic_cleaning(self):
        """Test basic ID cleaning functionality."""
        assert clean_id("7009-6933") == "7009-6933"
        assert clean_id("7116-4101-02") == "7116-4101-02"
        assert clean_id("  ABC123  ") == "ABC123"

    def test_special_characters(self):
        """Test removal of special characters."""
        assert clean_id("7009@6933#") == "70096933"
        assert clean_id("ABC!@#123") == "ABC123"
        assert clean_id("7009/6933\\") == "70096933"

    def test_spaces_and_underscores(self):
        """Test space and underscore handling."""
        assert clean_id("7009   6933") == "7009 6933"
        assert clean_id("7009___6933") == "7009 6933"
        assert clean_id("7009 _ _ 6933") == "7009 6933"

    def test_case_conversion(self):
        """Test uppercase conversion."""
        assert clean_id("abc123") == "ABC123"
        assert clean_id("MiXeD123") == "MIXED123"

    def test_empty_and_null(self):
        """Test empty and null inputs."""
        assert clean_id("") == ""
        assert clean_id(None) == ""
        assert clean_id(pd.NA) == ""

    def test_numeric_input(self):
        """Test numeric inputs."""
        assert clean_id(123) == "123"
        assert clean_id(7009.6933) == "70096933"


class TestParseDateColumn:
    """Test date parsing functionality."""

    def test_valid_dates(self):
        """Test parsing of valid date strings."""
        dates = pd.Series(["2024-01-15", "2024-02-20", "2024-03-25"])
        result = parse_date_column(dates, "test_date")

        assert "test_date" in result.columns
        assert "test_date_date" in result.columns
        assert "test_date_year" in result.columns
        assert "test_date_month" in result.columns
        assert "test_date_day" in result.columns
        assert "test_date_qtr" in result.columns
        assert "test_date_week" in result.columns

        # Check specific values
        assert result["test_date_year"].iloc[0] == 2024
        assert result["test_date_month"].iloc[0] == 1
        assert result["test_date_day"].iloc[0] == 15
        assert result["test_date_qtr"].iloc[0] == 1

    def test_invalid_dates(self):
        """Test handling of invalid dates."""
        dates = pd.Series(["invalid", "2024-13-45", "not-a-date"])
        result = parse_date_column(dates, "test_date")

        # Should still create columns but with null values
        assert "test_date_date" in result.columns
        assert pd.isna(result["test_date_date"]).all()

    def test_mixed_dates(self):
        """Test mix of valid and invalid dates."""
        dates = pd.Series(["2024-01-15", "invalid", "2024-03-25"])
        result = parse_date_column(dates, "test_date")

        # First and third should be valid
        assert result["test_date_year"].iloc[0] == 2024
        assert pd.isna(result["test_date_year"].iloc[1])
        assert result["test_date_year"].iloc[2] == 2024

    def test_different_date_formats(self):
        """Test different date formats."""
        dates = pd.Series(["01/15/2024", "15-Jan-2024", "2024.01.15"])
        result = parse_date_column(dates, "test_date")

        # Should parse at least some formats
        valid_dates = result["test_date_date"].notna().sum()
        assert valid_dates > 0


class TestCreateDimDates:
    """Test date dimension creation."""

    def test_single_date_column(self):
        """Test with single date column."""
        dates = [pd.Series(["2024-01-15", "2024-02-20"])]
        names = ["approved_date"]

        result = create_dim_dates(dates, names)

        assert len(result) == 2
        assert "date" in result.columns
        assert "role" in result.columns
        assert "year" in result.columns
        assert "month" in result.columns
        assert "quarter" in result.columns

        # Check role assignment
        assert all(result["role"] == "approved_date")

    def test_multiple_date_columns(self):
        """Test with multiple date columns."""
        dates = [
            pd.Series(["2024-01-15", "2024-02-20"]),
            pd.Series(["2024-01-10", "2024-02-15"]),
        ]
        names = ["approved_date", "promised_date"]

        result = create_dim_dates(dates, names)

        # Should have entries for both roles
        roles = result["role"].unique()
        assert "approved_date" in roles
        assert "promised_date" in roles

    def test_duplicate_dates(self):
        """Test handling of duplicate dates."""
        dates = [pd.Series(["2024-01-15", "2024-01-15", "2024-02-20"])]
        names = ["test_date"]

        result = create_dim_dates(dates, names)

        # Should deduplicate by date and role
        unique_dates = result["date"].nunique()
        assert unique_dates == 2

    def test_empty_dates(self):
        """Test with empty date series."""
        dates = [pd.Series([])]
        names = ["empty_date"]

        result = create_dim_dates(dates, names)

        assert len(result) == 0


class TestStandardizeText:
    """Test text standardization."""

    def test_basic_standardization(self):
        """Test basic text cleaning."""
        text = pd.Series(["  supplier name  ", "ANOTHER SUPPLIER", "mixed Case"])
        result = standardize_text(text)

        assert result.iloc[0] == "Supplier Name"
        assert result.iloc[1] == "Another Supplier"
        assert result.iloc[2] == "Mixed Case"

    def test_newline_handling(self):
        """Test newline character handling."""
        text = pd.Series(["line1\\nline2", "normal text"])
        result = standardize_text(text)

        assert "line1\nline2" in result.iloc[0]

    def test_null_handling(self):
        """Test null value handling."""
        text = pd.Series(["valid text", None, pd.NA])
        result = standardize_text(text)

        assert result.iloc[0] == "Valid Text"
        assert pd.isna(result.iloc[1])
        assert pd.isna(result.iloc[2])


class TestCreateRowHash:
    """Test row hashing functionality."""

    def test_basic_hashing(self):
        """Test basic row hashing."""
        df = pd.DataFrame(
            {"col1": ["A", "B", "C"], "col2": [1, 2, 3], "col3": ["X", "Y", "Z"]}
        )

        hashes = create_row_hash(df)

        assert len(hashes) == 3
        assert len(hashes.unique()) == 3  # All different
        assert all(isinstance(h, str) for h in hashes)

    def test_identical_rows(self):
        """Test hashing of identical rows."""
        df = pd.DataFrame({"col1": ["A", "A", "B"], "col2": [1, 1, 2]})

        hashes = create_row_hash(df)

        # First two should be identical
        assert hashes.iloc[0] == hashes.iloc[1]
        assert hashes.iloc[0] != hashes.iloc[2]

    def test_subset_columns(self):
        """Test hashing with subset of columns."""
        df = pd.DataFrame(
            {"col1": ["A", "A", "B"], "col2": [1, 2, 1], "col3": ["X", "X", "Y"]}
        )

        hashes = create_row_hash(df, columns=["col1", "col3"])

        # First two should be identical (ignoring col2)
        assert hashes.iloc[0] == hashes.iloc[1]


class TestRemoveDuplicateRows:
    """Test duplicate row removal."""

    def test_no_duplicates(self):
        """Test DataFrame with no duplicates."""
        df = pd.DataFrame({"col1": ["A", "B", "C"], "col2": [1, 2, 3]})

        cleaned, count = remove_duplicate_rows(df)

        assert len(cleaned) == 3
        assert count == 0

    def test_with_duplicates(self):
        """Test DataFrame with duplicates."""
        df = pd.DataFrame({"col1": ["A", "B", "A", "C"], "col2": [1, 2, 1, 3]})

        cleaned, count = remove_duplicate_rows(df)

        assert len(cleaned) == 3
        assert count == 1

    def test_subset_duplicates(self):
        """Test duplicate detection on subset of columns."""
        df = pd.DataFrame(
            {
                "col1": ["A", "B", "A", "C"],
                "col2": [1, 2, 3, 4],  # Different values
                "col3": ["X", "Y", "X", "Z"],
            }
        )

        cleaned, count = remove_duplicate_rows(df, subset=["col1", "col3"])

        assert len(cleaned) == 3
        assert count == 1


class TestDetectDateColumns:
    """Test automatic date column detection."""

    def test_obvious_date_columns(self):
        """Test detection of obvious date columns."""
        df = pd.DataFrame(
            {
                "part_id": ["A", "B", "C"],
                "approved_date": ["2024-01-15", "2024-02-20", "2024-03-25"],
                "promised_date": ["2024-02-01", "2024-03-01", "2024-04-01"],
                "description": ["Part A", "Part B", "Part C"],
            }
        )

        date_cols = detect_date_columns(df)

        assert "approved_date" in date_cols
        assert "promised_date" in date_cols
        assert "part_id" not in date_cols
        assert "description" not in date_cols

    def test_mixed_content_columns(self):
        """Test columns with mixed date/non-date content."""
        df = pd.DataFrame(
            {
                "maybe_date": ["2024-01-15", "not-a-date", "2024-03-25"],
                "definitely_not": ["text", "more text", "even more text"],
            }
        )

        date_cols = detect_date_columns(df)

        # Should detect maybe_date if >50% are valid dates
        assert "maybe_date" in date_cols
        assert "definitely_not" not in date_cols

    def test_no_date_columns(self):
        """Test DataFrame with no date columns."""
        df = pd.DataFrame(
            {
                "part_id": ["A", "B", "C"],
                "description": ["Part A", "Part B", "Part C"],
                "quantity": [1, 2, 3],
            }
        )

        date_cols = detect_date_columns(df)

        assert len(date_cols) == 0


# Integration tests
class TestCleaningIntegration:
    """Integration tests for cleaning functions."""

    def test_full_cleaning_pipeline(self):
        """Test complete cleaning pipeline."""
        # Create sample data
        df = pd.DataFrame(
            {
                "part_id": ["  7009-6933  ", "7116@4101#02", "ABC_123"],
                "supplier": ["  supplier one  ", "SUPPLIER TWO", "supplier three"],
                "approved_date": ["2024-01-15", "2024-02-20", "invalid"],
                "description": ["Part A", "Part B", "Part A"],  # Duplicate
            }
        )

        # Clean IDs
        df["part_id_clean"] = df["part_id"].apply(clean_id)

        # Standardize text
        df["supplier_clean"] = standardize_text(df["supplier"])

        # Parse dates
        date_df = parse_date_column(df["approved_date"], "approved_date")
        df = pd.concat([df, date_df.drop("approved_date", axis=1)], axis=1)

        # Remove duplicates
        df_clean, dup_count = remove_duplicate_rows(df)

        # Verify results
        assert df_clean["part_id_clean"].iloc[0] == "7009-6933"
        assert df_clean["part_id_clean"].iloc[1] == "711641010"
        assert df_clean["supplier_clean"].iloc[0] == "Supplier One"
        assert df_clean["approved_date_year"].iloc[0] == 2024
        assert dup_count == 1  # One duplicate removed
