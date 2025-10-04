# Performance Optimization Configuration
# Add these settings to improve processing speed

import warnings

# Pandas Performance Settings
import pandas as pd

# Configure pandas for better performance
pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", 50)

# Disable some warnings that slow down processing
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
warnings.filterwarnings("ignore", message="Could not infer format")

# Memory and processing optimizations
pd.options.mode.chained_assignment = None  # Disable chain assignment warnings for speed

# Set chunk size for large operations
CHUNK_SIZE = 10000
LARGE_FILE_THRESHOLD = 50000  # Rows
DATETIME_SAMPLE_SIZE = 100  # Sample size for date format detection
