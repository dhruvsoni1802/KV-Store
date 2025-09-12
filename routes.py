#!/usr/bin/env python3

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from models import PutRequest, PutResponse, VersionedValueResponse
from store import VersionedKeyValueStore
from database import DatabaseLayer

# Create router
router = APIRouter()

# Global database instance
db = DatabaseLayer()

# Global store instance with database
store = VersionedKeyValueStore(database=db, max_cache_size=2)


@router.post("/put/{key}", response_model=PutResponse)
async def put_value(key: str, request: PutRequest):
    return store.put(key, request.value)


@router.get("/get/{key}", response_model=VersionedValueResponse)
async def get_value(key: str, version: Optional[int] = Query(None, description="Specific version to retrieve")):
    result = store.get(key, version)
    if result is None:
        if version is None:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
        else:
            raise HTTPException(status_code=404, detail=f"Key '{key}' version {version} not found")
    return result


@router.get("/cache/stats")
async def get_cache_stats():
    return store.get_cache_stats()


@router.get("/db/stats")
async def get_db_stats():
    return db.get_stats()

