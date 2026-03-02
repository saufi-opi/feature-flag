import pytest
from unittest.mock import MagicMock
from core.models import FeatureFlag
from infrastructure.cached_repository import CachedFlagRepository

@pytest.fixture
def mock_fallback() -> MagicMock:
    return MagicMock()

@pytest.fixture
def mock_cache() -> MagicMock:
    return MagicMock()

@pytest.fixture
def repo(mock_fallback, mock_cache) -> CachedFlagRepository:
    return CachedFlagRepository(mock_fallback, mock_cache)

def test_get_flag_cache_miss_hit(repo, mock_fallback, mock_cache):
    # Setup cache miss, DB hit
    mock_cache.get.return_value = None
    mock_flag = FeatureFlag("test", True)
    mock_fallback.get_flag.return_value = mock_flag
    
    flag = repo.get_flag("test")
    
    # Assert DB called, Cache set
    mock_fallback.get_flag.assert_called_once_with("test")
    mock_cache.set.assert_called_once_with("flag:test", mock_flag)
    assert flag == mock_flag
    
    # Setup cache hit DB should not be called
    mock_cache.get.return_value = mock_flag
    mock_fallback.reset_mock()
    mock_cache.set.reset_mock()
    
    flag2 = repo.get_flag("test")
    mock_fallback.get_flag.assert_not_called()
    mock_cache.set.assert_not_called()
    assert flag2 == mock_flag

def test_get_flag_cache_miss_db_miss(repo, mock_fallback, mock_cache):
    # Setup cache miss, DB miss
    mock_cache.get.return_value = None
    mock_fallback.get_flag.return_value = None
    
    flag = repo.get_flag("missing")
    
    mock_fallback.get_flag.assert_called_once_with("missing")
    # Assert sentinel is cached to avoid repeated DB hits on Missing
    mock_cache.set.assert_called_once_with("flag:missing", "MISS_SENTINEL")
    assert flag is None
    
    # Next call hits sentinel
    mock_cache.get.return_value = "MISS_SENTINEL"
    mock_fallback.reset_mock()
    mock_cache.set.reset_mock()
    
    flag2 = repo.get_flag("missing")
    mock_fallback.get_flag.assert_not_called()
    assert flag2 is None

def test_cache_invalidation_on_save(repo, mock_fallback, mock_cache):
    mock_flag = FeatureFlag("new_flag", True)
    mock_fallback.save_flag.return_value = mock_flag
    
    saved = repo.save_flag(mock_flag)
    
    mock_fallback.save_flag.assert_called_once_with(mock_flag)
    # The new flag is cached
    mock_cache.set.assert_called_once_with("flag:new_flag", mock_flag)
    # The all flags catalog gets discarded because it changed
    mock_cache.delete.assert_called_once_with(repo.ALL_FLAGS_KEY)
    assert saved == mock_flag
