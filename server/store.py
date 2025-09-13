#!/usr/bin/env python3

import time
from typing import Dict, List, Any, Optional
import threading
from models import VersionedValueResponse, PutResponse


class VersionedValue:    
    def __init__(self, value: Any, version: int = 1):
        self.value = value
        self.version = version if version is not None else 1
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict:
        return {
            'value': self.value,
            'version': self.version,
            'timestamp': self.timestamp
        }
    
    def to_pydantic(self, source: str = "cache") -> VersionedValueResponse:
        return VersionedValueResponse(
            value=self.value,
            version=self.version,
            timestamp=self.timestamp,
            source=source
        )


class VersionedKeyValueStore:  
    def __init__(self, max_cache_size: int = 100, database=None):
        self._store: Dict[str, List[VersionedValue]] = {}
        self._lock = threading.RLock()
        self.max_cache_size = max_cache_size
        self._access_times: Dict[str, float] = {}
        self.database = database
    
    def put(self, key: str, value: Any) -> PutResponse:
        with self._lock:
            current_time = time.time()
            
            # Write to database first (write-through)
            if self.database:
                db_result = self.database.put(key, value)
                operation = db_result['operation']
                new_version = db_result.get('new_version', db_result.get('version'))
                previous_version = db_result.get('previous_version')
            else:
                # Fallback if no database
                operation = 'create'
                new_version = 1
                previous_version = None
            
            # Check if we need to evict before adding new key to cache
            if key not in self._store and self._should_evict():
                self._evict_lru()
            
            if key in self._store:
                # Update cache
                current_versions = self._store[key]
                versioned_value = VersionedValue(value, new_version)
                current_versions.append(versioned_value)
                self._access_times[key] = current_time
                
                return PutResponse(
                    operation=operation,
                    key=key,
                    new_version=new_version,
                    previous_version=previous_version,
                    total_versions=len(current_versions)
                )
            else:
                # Add to cache
                versioned_value = VersionedValue(value, new_version)
                self._store[key] = [versioned_value]
                self._access_times[key] = current_time
                
                return PutResponse(
                    operation=operation,
                    key=key,
                    version=new_version if operation == 'create' else None,
                    new_version=new_version if operation == 'update' else None,
                    previous_version=previous_version,
                    total_versions=1
                )
    
    def get(self, key: str, version: Optional[int] = None) -> Optional[VersionedValueResponse]:
        with self._lock:
            # First, try to get from cache
            if key in self._store:
                # Update access time for LRU
                self._access_times[key] = time.time()
                
                versions = self._store[key]
                
                if version is None:
                    latest = versions[-1]
                    return latest.to_pydantic(source="cache")
                else:
                    for v in versions:
                        if v.version == version:
                            return v.to_pydantic(source="cache")
                    # Cache miss for specific version, try database
                    return self._get_from_database(key, version)
            
            # Cache miss for key, try database
            return self._get_from_database(key, version)
    
    def _get_from_database(self, key: str, version: Optional[int] = None) -> Optional[VersionedValueResponse]:
        if not self.database:
            return None
        
        # Get from database
        db_result = self.database.get(key, version)
        if not db_result:
            return None
        
        # Convert to VersionedValueResponse
        # Ensure version is not None
        db_version = db_result['version']
        if db_version is None:
            db_version = 1  # Default to version 1 if None
        
        versioned_response = VersionedValueResponse(
            value=db_result['value'],
            version=db_version,
            timestamp=db_result['timestamp'],
            source="database"
        )
        
        # Add to cache if we have space (cache-aside pattern)
        # Only add if requesting latest version (version is None) or specific version
        current_time = time.time()
        
        # Check if we need to evict before adding
        if key not in self._store and self._should_evict():
            self._evict_lru()
        
        # Add to cache
        versioned_value = VersionedValue(
            value=db_result['value'],
            version=db_version
        )
        versioned_value.timestamp = db_result['timestamp']  # Preserve original timestamp
        
        if key in self._store:
            self._store[key].append(versioned_value)
        else:
            self._store[key] = [versioned_value]
        
        self._access_times[key] = current_time
        
        return versioned_response
    
    def _should_evict(self) -> bool:
        return len(self._store) >= self.max_cache_size
    
    def _evict_lru(self) -> str:
        if not self._access_times:
            return None
        
        # Finding the key with the oldest access time
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        
        # Removing from both store and access times
        del self._store[lru_key]
        del self._access_times[lru_key]
        
        return lru_key
    
    def get_cache_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'current_size': len(self._store),
                'max_size': self.max_cache_size,
                'is_full': self._should_evict()
            }
