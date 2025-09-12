#!/usr/bin/env python3

import sqlite3
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path


class DatabaseLayer:  
    def __init__(self, db_path: str = "kv_store.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Creating keys table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keys (
                    key TEXT PRIMARY KEY,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            
            # Creating values table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `values` (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    `key` TEXT NOT NULL,
                    value TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (`key`) REFERENCES keys (`key`)
                )
            """)
            
            # Creating index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_key_version 
                ON `values` (`key`, version)
            """)
            
            conn.commit()
    
    def put(self, key: str, value: Any) -> Dict[str, Any]:
        current_time = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if key exists
            cursor.execute("SELECT version FROM `values` WHERE `key` = ? ORDER BY version DESC LIMIT 1", (key,))
            result = cursor.fetchone()
            
            if result:
                # Key exists, increment version
                new_version = result[0] + 1
                cursor.execute("""
                    INSERT INTO `values` (`key`, value, version, timestamp) 
                    VALUES (?, ?, ?, ?)
                """, (key, json.dumps(value), new_version, current_time))
                
                # Update keys table
                cursor.execute("""
                    UPDATE keys SET updated_at = ? WHERE `key` = ?
                """, (current_time, key))
                
                operation = 'update'
                previous_version = result[0]
            else:
                # New key
                new_version = 1
                cursor.execute("""
                    INSERT INTO keys (`key`, created_at, updated_at) 
                    VALUES (?, ?, ?)
                """, (key, current_time, current_time))
                
                cursor.execute("""
                    INSERT INTO `values` (`key`, value, version, timestamp) 
                    VALUES (?, ?, ?, ?)
                """, (key, json.dumps(value), new_version, current_time))
                
                operation = 'create'
                previous_version = None
            
            conn.commit()
            
            return {
                'operation': operation,
                'key': key,
                'version': new_version if operation == 'create' else None,
                'new_version': new_version if operation == 'update' else None,
                'previous_version': previous_version
            }
    
    def get(self, key: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a value from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if version is None:
                # Get latest version
                cursor.execute("""
                    SELECT value, version, timestamp 
                    FROM `values` 
                    WHERE `key` = ? 
                    ORDER BY version DESC 
                    LIMIT 1
                """, (key,))
            else:
                # Get specific version
                cursor.execute("""
                    SELECT value, version, timestamp 
                    FROM `values` 
                    WHERE `key` = ? AND version = ?
                """, (key, version))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    'value': json.loads(result[0]),
                    'version': result[1],
                    'timestamp': result[2]
                }
            
            return None
    
    def key_exists(self, key: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM keys WHERE `key` = ? LIMIT 1", (key,))
            return cursor.fetchone() is not None
    
    def get_stats(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count unique keys
            cursor.execute("SELECT COUNT(*) FROM keys")
            total_keys = cursor.fetchone()[0]
            
            # Count total versions
            cursor.execute("SELECT COUNT(*) FROM `values`")
            total_versions = cursor.fetchone()[0]
            
            # Get database file size
            db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            
            return {
                'total_keys': total_keys,
                'total_versions': total_versions,
                'database_size_bytes': db_size
            }
