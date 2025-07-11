#!/usr/bin/env python3
"""UTILS MODULE STUB"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_current_date() -> datetime:
    return datetime.now()

def get_recent_dates(days: int = 7) -> List[datetime]:
    today = datetime.now()
    return [today - timedelta(days=i) for i in range(days)]

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = name.strip()
    for suffix in [' Jr.', ' Sr.', ' III', ' II', ' IV']:
        name = name.replace(suffix, '')
    name = name.replace("'", "")
    name = name.replace("-", " ")
    return name.strip().upper()

class DataCache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if datetime.now() - self._timestamps[key] < timedelta(hours=1):
                return self._cache[key]
        return None
    
    def set(self, key: str, value: Any):
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
    
    def clear(self):
        self._cache.clear()
        self._timestamps.clear()

cache = DataCache()

def log_info(message: str):
    logger.info(message)

def log_error(message: str):
    logger.error(message)
