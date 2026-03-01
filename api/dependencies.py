from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from infrastructure.database import SessionLocal
from infrastructure.sqlite_repository import SQLiteFlagRepository
from core.engine import FeatureFlagEngine

def get_db_session() -> Generator[Session, None, None]:
    """Dependency to provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_engine(db: Session = Depends(get_db_session)) -> FeatureFlagEngine:
    """Dependency to provide the Feature Flag Engine."""
    repo = SQLiteFlagRepository(db)
    # Using the same lookup chain as the CLI
    return FeatureFlagEngine(repo, lookup_chain=["user", "group", "region"])
