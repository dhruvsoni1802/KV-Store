#!/usr/bin/env python3
"""
Database Cleanup Script for Key-Value Store

This script cleans all database files in the data directory by:
1. Deleting all data from the 'values' table
2. Deleting all data from the 'keys' table
3. Resetting AUTOINCREMENT counters
4. Running VACUUM to reclaim disk space

Usage:
    python clean_databases.py [--dry-run] [--confirm]
    
Options:
    --dry-run    Show what would be cleaned without actually doing it
    --confirm    Skip confirmation prompt
"""

import sqlite3
import os
import sys
import argparse
from pathlib import Path


def get_database_files():
    """Get all database files in the data directory and subdirectories"""
    # Get the project root directory (parent of scripts folder)
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    db_files = []
    
    # Find all .db files recursively in the data directory
    if data_dir.exists():
        for db_file in data_dir.rglob("*.db"):
            db_files.append(str(db_file))
    
    return sorted(db_files)


def get_database_stats(db_path):
    """Get statistics about the database before cleaning"""
    if not os.path.exists(db_path):
        return None
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Count records in keys table
            cursor.execute("SELECT COUNT(*) FROM keys")
            keys_count = cursor.fetchone()[0]
            
            # Count records in values table
            cursor.execute("SELECT COUNT(*) FROM `values`")
            values_count = cursor.fetchone()[0]
            
            # Get database file size
            file_size = os.path.getsize(db_path)
            
            return {
                'keys_count': keys_count,
                'values_count': values_count,
                'file_size': file_size
            }
    except sqlite3.Error as e:
        print(f"Error reading database {db_path}: {e}")
        return None


def clean_database(db_path, dry_run=False):
    """Clean a single database file"""
    if not os.path.exists(db_path):
        print(f"Warning: Database file {db_path} does not exist")
        return False
    
    if dry_run:
        stats = get_database_stats(db_path)
        if stats:
            print(f"Would clean {db_path}:")
            print(f"  - {stats['keys_count']} keys")
            print(f"  - {stats['values_count']} values")
            print(f"  - {stats['file_size']} bytes")
        else:
            print(f"Would clean {db_path} (could not read stats)")
        return True
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Delete all data from tables
            cursor.execute("DELETE FROM `values`")
            cursor.execute("DELETE FROM keys")
            
            # Reset AUTOINCREMENT counter
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='values'")
            
            # Commit the changes
            conn.commit()
            
            # Run VACUUM to reclaim disk space
            cursor.execute("VACUUM")
            
            print(f"✓ Cleaned database: {db_path}")
            return True
            
    except sqlite3.Error as e:
        print(f"✗ Error cleaning database {db_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Clean all key-value store databases")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be cleaned without actually doing it")
    parser.add_argument("--confirm", action="store_true",
                       help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    # Get all database files
    db_files = get_database_files()
    
    if not db_files:
        print("No database files found in the data directory")
        return 0
    
    print("Found database files:")
    for db_file in db_files:
        relative_path = os.path.relpath(db_file, Path(__file__).parent.parent)
        print(f"  - {relative_path}")
    
    if args.dry_run:
        print("\n--- DRY RUN MODE ---")
        print("The following databases would be cleaned:\n")
        
        for db_file in db_files:
            print(f"Database: {os.path.relpath(db_file, Path(__file__).parent.parent)}")
            clean_database(db_file, dry_run=True)
            print()
        
        print("Dry run complete. Use without --dry-run to actually clean the databases.")
        return 0
    
    # Show current stats
    print("\nCurrent database statistics:")
    total_keys = 0
    total_values = 0
    total_size = 0
    
    for db_file in db_files:
        stats = get_database_stats(db_file)
        if stats:
            relative_path = os.path.relpath(db_file, Path(__file__).parent.parent)
            print(f"  {relative_path}:")
            print(f"    - {stats['keys_count']} keys")
            print(f"    - {stats['values_count']} values")
            print(f"    - {stats['file_size']} bytes")
            total_keys += stats['keys_count']
            total_values += stats['values_count']
            total_size += stats['file_size']
    
    print(f"\nTotal: {total_keys} keys, {total_values} values, {total_size} bytes")
    
    # Confirmation prompt
    if not args.confirm:
        print("\n⚠️  WARNING: This will permanently delete ALL data from ALL databases!")
        response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
        if response not in ['yes', 'y']:
            print("Operation cancelled.")
            return 0
    
    # Clean all databases
    print("\nCleaning databases...")
    success_count = 0
    
    for db_file in db_files:
        if clean_database(db_file, dry_run=False):
            success_count += 1
    
    print(f"\n✓ Successfully cleaned {success_count}/{len(db_files)} databases")
    
    if success_count == len(db_files):
        print("All databases have been cleaned successfully!")
        return 0
    else:
        print("Some databases could not be cleaned. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
