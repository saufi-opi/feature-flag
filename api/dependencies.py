from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from infrastructure.database import SessionLocal
from infrastructure.sqlite_repository import SQLiteFlagRepository
from infrastructure.cache import InMemoryCacheBackend
from infrastructure.cached_repository import CachedFlagRepository
from core.engine import FeatureFlagEngine

in_memory_cache = InMemoryCacheBackend()

def get_db_session() -> Generator[Session, None, None]:
    """Dependency to provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_engine(db: Session = Depends(get_db_session)) -> FeatureFlagEngine:
    """Dependency to provide the Feature Flag Engine."""
    sqlite_repo = SQLiteFlagRepository(db)
    cached_repo = CachedFlagRepository(fallback_repository=sqlite_repo, cache=in_memory_cache)
    
    return FeatureFlagEngine(cached_repo, lookup_chain=["user", "group", "region"])
