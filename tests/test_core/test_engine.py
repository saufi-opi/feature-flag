import pytest
from core.engine import FeatureFlagEngine
from core.exceptions import FlagNotFoundError, DuplicateFlagError
from tests.conftest import InMemoryRepository

@pytest.fixture
def repo():
    return InMemoryRepository()

@pytest.fixture
def engine(repo):
    # Tests a complex 5-level lookup chain
    return FeatureFlagEngine(repo, lookup_chain=["tenant", "user", "group", "region", "cohort"])

def test_engine_returns_global_default_if_no_context(engine):
    engine.create_flag("dark_mode", enabled=False)
    assert engine.evaluate("dark_mode") is False

    engine.update_flag("dark_mode", enabled=True)
    assert engine.evaluate("dark_mode") is True

def test_engine_raises_error_if_flag_not_found(engine):
    with pytest.raises(FlagNotFoundError):
        engine.evaluate("nonexistent_flag")

def test_engine_cannot_create_duplicate_flag(engine):
    engine.create_flag("dark_mode", enabled=True)
    with pytest.raises(DuplicateFlagError):
        engine.create_flag("dark_mode", enabled=False)

def test_evaluate_respects_highest_priority_override(engine):
    engine.create_flag("dark_mode", enabled=False)
    
    # tenant > user > group > region > cohort
    
    # Set a cohort override to True
    engine.set_override("dark_mode", "cohort", "beta-testers", enabled=True)
    assert engine.evaluate("dark_mode", {"cohort": "beta-testers"}) is True
    
    # Set a region override to False (beats cohort)
    engine.set_override("dark_mode", "region", "US", enabled=False)
    assert engine.evaluate("dark_mode", {"cohort": "beta-testers", "region": "US"}) is False
    
    # Set a group override to True (beats region)
    engine.set_override("dark_mode", "group", "admin", enabled=True)
    assert engine.evaluate("dark_mode", {"cohort": "beta-testers", "region": "US", "group": "admin"}) is True
    
    # Set a user override to False (beats group)
    engine.set_override("dark_mode", "user", "alice", enabled=False)
    assert engine.evaluate("dark_mode", {
        "cohort": "beta-testers", "region": "US", "group": "admin", "user": "alice"
    }) is False
    
    # Set a tenant override to True (beats user - highest priority)
    engine.set_override("dark_mode", "tenant", "acme", enabled=True)
    assert engine.evaluate("dark_mode", {
        "cohort": "beta-testers", "region": "US", "group": "admin", "user": "alice", "tenant": "acme"
    }) is True

def test_evaluate_ignores_irrelevant_context(engine):
    engine.create_flag("dark_mode", enabled=False)
    engine.set_override("dark_mode", "user", "alice", enabled=True)
    
    # Passing context variables that have no overrides set shouldn't break anything, 
    # it should just fall back to the global default.
    assert engine.evaluate("dark_mode", {"user": "bob", "group": "staff"}) is False

def test_engine_can_delete_overrides(engine):
    engine.create_flag("dark_mode", enabled=False)
    engine.set_override("dark_mode", "user", "alice", enabled=True)
    
    assert engine.evaluate("dark_mode", {"user": "alice"}) is True
    
    engine.delete_override("dark_mode", "user", "alice")
    
    # Reverts to global default
    assert engine.evaluate("dark_mode", {"user": "alice"}) is False

def test_delete_flag_cascades_overrides_in_memory(engine):
    engine.create_flag("cascade_test", enabled=False)
    engine.set_override("cascade_test", "user", "alice", enabled=True)
    
    assert engine.evaluate("cascade_test", {"user": "alice"}) is True
    
    # Delete the flag
    engine.delete_flag("cascade_test")
    
    # It shouldn't exist anymore
    with pytest.raises(FlagNotFoundError):
        engine.evaluate("cascade_test", {"user": "alice"})
    
    # And the override dict should be scrubbed cleanly by the InMemoryRepository
    assert engine.repo.get_override("cascade_test", "user", "alice") is None
