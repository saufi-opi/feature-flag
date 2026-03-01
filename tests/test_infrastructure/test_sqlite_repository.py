import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.orm_models import Base
from infrastructure.sqlite_repository import SQLiteFlagRepository
from core.models import FeatureFlag

@pytest.fixture
def db_session():
    # An isolated, ephemeral in-memory database exclusively for tests
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def repo(db_session):
    return SQLiteFlagRepository(db_session)

def test_save_and_get_flag(repo):
    flag = FeatureFlag(name="test_flag", enabled=True, description="Test flag")
    repo.save_flag(flag)
    
    saved_flag = repo.get_flag("test_flag")
    assert saved_flag is not None
    assert saved_flag.name == "test_flag"
    assert saved_flag.enabled is True

def test_get_nonexistent_flag(repo):
    assert repo.get_flag("not_exists") is None

def test_get_all_flags(repo):
    repo.save_flag(FeatureFlag(name="flag1", enabled=True))
    repo.save_flag(FeatureFlag(name="flag2", enabled=False))
    
    flags = repo.get_all_flags()
    assert len(flags) == 2
    
def test_update_flag(repo):
    flag = FeatureFlag(name="update_flag", enabled=False, description="Test")
    repo.save_flag(flag)
    
    updated = repo.update_flag("update_flag", enabled=True)
    assert updated.enabled is True
    
    retrieved = repo.get_flag("update_flag")
    assert retrieved.enabled is True

def test_set_and_get_override(repo):
    repo.save_flag(FeatureFlag(name="target_flag", enabled=False))
    
    # Override not set initially
    assert repo.get_override("target_flag", "tenant", "acme") is None
    
    # Set override
    repo.set_override("target_flag", "tenant", "acme", enabled=True)
    assert repo.get_override("target_flag", "tenant", "acme") is True
    
    # Update existing override
    repo.set_override("target_flag", "tenant", "acme", enabled=False)
    assert repo.get_override("target_flag", "tenant", "acme") is False

def test_delete_override(repo):
    repo.save_flag(FeatureFlag(name="del_target", enabled=False))
    repo.set_override("del_target", "user", "bob", enabled=True)
    assert repo.get_override("del_target", "user", "bob") is True
    
    repo.delete_override("del_target", "user", "bob")
    assert repo.get_override("del_target", "user", "bob") is None
