#!/usr/bin/env python3
"""
Script to clean up old uploaded files and processed files.
Run this periodically to prevent disk space issues.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.core.config import settings
from backend.core.logging import logger


def cleanup_old_uploads(keep_days: int = 7):
    """Remove uploaded files older than specified days."""
    uploads_folder = settings.upload_folder_path
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    
    if not uploads_folder.exists():
        logger.info("Uploads folder does not exist")
        return 0
    
    files_removed = 0
    total_size_freed = 0
    
    for file_path in uploads_folder.iterdir():
        if file_path.is_file() and file_path.name != ".gitkeep":
            # Check file age
            file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            if file_modified < cutoff_date:
                file_size = file_path.stat().st_size
                try:
                    file_path.unlink()
                    files_removed += 1
                    total_size_freed += file_size
                    logger.info(f"Removed old upload: {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to remove {file_path.name}: {e}")
    
    logger.info(
        "Upload cleanup completed",
        files_removed=files_removed,
        size_freed_mb=round(total_size_freed / (1024 * 1024), 2)
    )
    
    return files_removed


def cleanup_processed_files():
    """Remove all processed files."""
    processed_folder = settings.processed_folder_path
    
    if not processed_folder.exists():
        logger.info("Processed folder does not exist")
        return 0
    
    files_removed = 0
    total_size_freed = 0
    
    for file_path in processed_folder.iterdir():
        if file_path.is_file() and file_path.name != ".gitkeep":
            file_size = file_path.stat().st_size
            try:
                file_path.unlink()
                files_removed += 1
                total_size_freed += file_size
                logger.info(f"Removed processed file: {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to remove {file_path.name}: {e}")
    
    logger.info(
        "Processed files cleanup completed", 
        files_removed=files_removed,
        size_freed_mb=round(total_size_freed / (1024 * 1024), 2)
    )
    
    return files_removed


def main():
    """Main cleanup function."""
    print("🧹 Starting ETL Dashboard Cleanup...")
    print("=" * 50)
    
    # Cleanup old uploads (older than 7 days)
    print("🗂️  Cleaning old uploaded files...")
    uploads_removed = cleanup_old_uploads(keep_days=7)
    print(f"   ✅ Removed {uploads_removed} old upload files")
    
    # Cleanup processed files (all)
    print("🗄️  Cleaning processed files...")
    processed_removed = cleanup_processed_files()
    print(f"   ✅ Removed {processed_removed} processed files")
    
    print("=" * 50)
    print(f"🎉 Cleanup completed!")
    print(f"   • Uploads removed: {uploads_removed}")
    print(f"   • Processed files removed: {processed_removed}")
    print(f"   • Total files removed: {uploads_removed + processed_removed}")


if __name__ == "__main__":
    main()