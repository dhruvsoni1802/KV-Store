#!/usr/bin/env python3

from typing import Any, Optional
from pydantic import BaseModel


class PutRequest(BaseModel):
    value: Any


class VersionedValueResponse(BaseModel):
    value: Any
    version: int
    timestamp: float
    source: str  # "cache" or "database"


class PutResponse(BaseModel):
    operation: str
    key: str
    version: Optional[int] = None
    new_version: Optional[int] = None
    previous_version: Optional[int] = None
    total_versions: int
