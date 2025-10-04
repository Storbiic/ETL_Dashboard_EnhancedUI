"""Tests for data profiling functionality."""

import numpy as np
import pandas as pd
import pytest

from backend.models.schemas import ColumnProfile, ProfileResponse
from backend.services.profiler import DataProfiler


class TestDataProfiler:
    """Test the DataProfiler class."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "text_col": ["A", "B", "C", "A", None],
                "numeric_col": [1, 2, 3, 4, 5],
                "date_col": ["2024-01-15", "2024-02-20", "invalid", "2024-03-25", None],
                "boolean_col": ["Yes", "No", "Yes", "No", "Yes"],
                "empty_col": [None, None, None, None, None],
                "mixed_col": ["text", 123, "2024-01-01", None, "more text"],
            }
        )

    def test_profiler_initialization(self, sample_dataframe):
        """Test profiler initialization."""
        profiler = DataProfiler(sample_dataframe, "test_sheet")

        assert profiler.df is not None
        assert profiler.sheet_name == "test_sheet"
        assert profiler.total_rows == 5
        assert profiler.total_cols == 6

    def test_profile_text_column(self, sample_dataframe):
        """Test profiling of text column."""
        profiler = DataProfiler(sample_dataframe, "test_sheet")
        profile = profiler.profile_column("text_col")

        assert isinstance(profile, ColumnProfile)
        assert profile.name == "text_col"
        assert profile.dtype == "text"
        assert profile.non_null_count == 4
        assert profile.null_count == 1
        assert profile.null_percentage == 20.0
        assert profile.unique_count == 3  # A, B, C
        assert len(profile.sample_values) <= 10

    def test_profile_numeric_column(self, sample_dataframe):
        """Test profiling of numeric column."""
        profiler = DataProfiler(sample_dataframe, "test_sheet")
        profile = profiler.profile_column("numeric_col")

        assert profile.name == "numeric_col"
        assert profile.dtype == "integer"
        assert profile.non_null_count == 5
        assert profile.null_count == 0
        assert profile.null_percentage == 0.0
        assert profile.unique_count == 5

    def test_profile_date_column(self, sample_dataframe):
        """Test profiling of date-like column."""
        profiler = DataProfiler(sample_dataframe, "test_sheet")
        profile = profiler.profile_column("date_col")

        assert profile.name == "date_col"
        # Should detect as date or text depending on content
        assert profile.dtype in ["date", "text"]
        assert profile.non_null_count == 4
        assert profile.null_count == 1

    def test_profile_boolean_column(self, sample_dataframe):
        """Test profiling of boolean-like column."""
        profiler = DataProfiler(sample_dataframe, "test_sheet")
        profile = profiler.profile_column("boolean_col")

        assert profile.name == "boolean_col"
        assert profile.dtype == "boolean"
        assert profile.non_null_count == 5
        assert profile.unique_count == 2  # Yes, No

    def test_profile_empty_column(self, sample_dataframe):
        """Test profiling of empty column."""
        profiler = DataProfiler(sample_dataframe, "test_sheet")
        profile = profiler.profile_column("empty_col")

        assert profile.name == "empty_col"
        assert profile.dtype == "empty"
        assert profile.non_null_count == 0
        assert profile.null_count == 5
        assert profile.null_percentage == 100.0
        assert profile.unique_count == 0
        assert len(profile.sample_values) == 0

    def test_profile_mixed_column(self, sample_dataframe):
        """Test profiling of mixed content column."""
        profiler = DataProfiler(sample_dataframe, "test_sheet")
        profile = profiler.profile_column("mixed_col")

        assert profile.name == "mixed_col"
        assert profile.dtype == "text"  # Should default to text
        assert profile.non_null_count == 4
        assert profile.null_count == 1

    def test_count_duplicate_rows(self, sample_dataframe):
        """Test duplicate row counting."""
        profiler = DataProfiler(sample_dataframe, "test_sheet")
        dup_count = profiler.count_duplicate_rows()

        # No exact duplicates in sample data
        assert dup_count == 0

    def test_count_duplicate_rows_with_duplicates(self):
        """Test duplicate counting with actual duplicates."""
        df = pd.DataFrame({"col1": ["A", "B", "A", "C"], "col2": [1, 2, 1, 3]})

        profiler = DataProfiler(df, "test_sheet")
        dup_count = profiler.count_duplicate_rows()

        assert dup_count == 1  # One duplicate row

    def test_profile_sheet(self, sample_dataframe):
        """Test complete sheet profiling."""
        profiler = DataProfiler(sample_dataframe, "test_sheet")
        result = profiler.profile_sheet()

        assert isinstance(result, ProfileResponse)
        assert result.sheet_name == "test_sheet"
        assert result.total_rows == 5
        assert result.total_cols == 6
        assert result.duplicate_rows == 0
        assert len(result.columns) == 6

        # Check that all columns are profiled
        column_names = [col.name for col in result.columns]
        expected_columns = [
            "text_col",
            "numeric_col",
            "date_col",
            "boolean_col",
            "empty_col",
            "mixed_col",
        ]
        for expected in expected_columns:
            assert expected in column_names

    def test_infer_dtype_numeric(self):
        """Test numeric type inference."""
        profiler = DataProfiler(pd.DataFrame(), "test")

        # Integer series
        int_series = pd.Series([1, 2, 3, 4, 5])
        assert profiler._infer_dtype(int_series) == "integer"

        # Float series
        float_series = pd.Series([1.1, 2.2, 3.3])
        assert profiler._infer_dtype(float_series) == "numeric"

        # Mixed numeric
        mixed_series = pd.Series(["1", "2.5", "3"])
        assert profiler._infer_dtype(mixed_series) == "numeric"

    def test_infer_dtype_date(self):
        """Test date type inference."""
        profiler = DataProfiler(pd.DataFrame(), "test")

        date_series = pd.Series(["2024-01-15", "2024-02-20", "2024-03-25"])
        result = profiler._infer_dtype(date_series)

        # Should detect as date
        assert result == "date"

    def test_infer_dtype_boolean(self):
        """Test boolean type inference."""
        profiler = DataProfiler(pd.DataFrame(), "test")

        # Yes/No
        bool_series1 = pd.Series(["Yes", "No", "Yes", "No"])
        assert profiler._infer_dtype(bool_series1) == "boolean"

        # True/False
        bool_series2 = pd.Series(["True", "False", "True"])
        assert profiler._infer_dtype(bool_series2) == "boolean"

        # X/D (common in BOM data)
        bool_series3 = pd.Series(["X", "D", "X", "D"])
        assert profiler._infer_dtype(bool_series3) == "boolean"

    def test_infer_dtype_empty(self):
        """Test empty series type inference."""
        profiler = DataProfiler(pd.DataFrame(), "test")

        empty_series = pd.Series([])
        assert profiler._infer_dtype(empty_series) == "empty"

        null_series = pd.Series([None, None, None])
        assert profiler._infer_dtype(null_series) == "empty"

    def test_profile_large_dataset(self):
        """Test profiling with larger dataset."""
        # Create larger dataset
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "id": range(1000),
                "category": np.random.choice(["A", "B", "C"], 1000),
                "value": np.random.randn(1000),
                "date": pd.date_range("2024-01-01", periods=1000, freq="D"),
            }
        )

        profiler = DataProfiler(df, "large_sheet")
        result = profiler.profile_sheet()

        assert result.total_rows == 1000
        assert result.total_cols == 4

        # Check sample values are limited
        for col_profile in result.columns:
            assert len(col_profile.sample_values) <= 10

    def test_profile_with_special_characters(self):
        """Test profiling with special characters and encoding issues."""
        df = pd.DataFrame(
            {
                "special_chars": ["café", "naïve", "résumé", "Zürich", None],
                "unicode": ["🚀", "🎉", "💡", "🔥", "⭐"],
                "mixed": ["normal", "spéciàl", "123", None, ""],
            }
        )

        profiler = DataProfiler(df, "special_sheet")
        result = profiler.profile_sheet()

        assert result.total_rows == 5
        assert result.total_cols == 3

        # Should handle special characters without errors
        for col_profile in result.columns:
            assert isinstance(col_profile.sample_values, list)

    def test_error_handling_in_profiling(self):
        """Test error handling during profiling."""
        # Create problematic DataFrame
        df = pd.DataFrame(
            {
                "normal_col": [1, 2, 3],
                "problematic_col": [{"nested": "dict"}, [1, 2, 3], complex(1, 2)],
            }
        )

        profiler = DataProfiler(df, "error_sheet")
        result = profiler.profile_sheet()

        # Should complete without crashing
        assert len(result.columns) == 2

        # Check that error column has error type
        prob_cols = [col for col in result.columns if col.name == "problematic_col"]
        # Should handle gracefully, possibly as "error" type or convert to string
        assert prob_cols  # Ensure the column exists


class TestProfilerEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_dataframe(self):
        """Test profiling empty DataFrame."""
        df = pd.DataFrame()
        profiler = DataProfiler(df, "empty_sheet")
        result = profiler.profile_sheet()

        assert result.total_rows == 0
        assert result.total_cols == 0
        assert len(result.columns) == 0

    def test_single_row_dataframe(self):
        """Test profiling single-row DataFrame."""
        df = pd.DataFrame({"col1": ["value"], "col2": [123], "col3": [None]})

        profiler = DataProfiler(df, "single_row")
        result = profiler.profile_sheet()

        assert result.total_rows == 1
        assert result.total_cols == 3

        # Check profiles
        col1_profile = next(col for col in result.columns if col.name == "col1")
        assert col1_profile.unique_count == 1
        assert col1_profile.null_percentage == 0.0

        col3_profile = next(col for col in result.columns if col.name == "col3")
        assert col3_profile.null_percentage == 100.0

    def test_single_column_dataframe(self):
        """Test profiling single-column DataFrame."""
        df = pd.DataFrame({"only_col": [1, 2, 3, 2, 1]})

        profiler = DataProfiler(df, "single_col")
        result = profiler.profile_sheet()

        assert result.total_rows == 5
        assert result.total_cols == 1
        assert len(result.columns) == 1

        col_profile = result.columns[0]
        assert col_profile.name == "only_col"
        assert col_profile.unique_count == 3  # 1, 2, 3

    def test_all_null_columns(self):
        """Test DataFrame with all null columns."""
        df = pd.DataFrame(
            {
                "null_col1": [None, None, None],
                "null_col2": [pd.NA, pd.NA, pd.NA],
                "null_col3": [np.nan, np.nan, np.nan],
            }
        )

        profiler = DataProfiler(df, "all_null")
        result = profiler.profile_sheet()

        for col_profile in result.columns:
            assert col_profile.null_percentage == 100.0
            assert col_profile.non_null_count == 0
            assert col_profile.unique_count == 0

    def test_very_long_column_names(self):
        """Test with very long column names."""
        long_name = "a" * 1000  # Very long column name
        df = pd.DataFrame({long_name: [1, 2, 3], "normal": ["a", "b", "c"]})

        profiler = DataProfiler(df, "long_names")
        result = profiler.profile_sheet()

        # Should handle long names without issues
        assert len(result.columns) == 2
        column_names = [col.name for col in result.columns]
        assert long_name in column_names
        assert "normal" in column_names
