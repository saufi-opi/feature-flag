from infrastructure.cache import InMemoryCacheBackend

def test_in_memory_cache_backend():
    cache = InMemoryCacheBackend()
    
    # Test get missing
    assert cache.get("nonexistent") is None
    
    # Test set and get
    cache.set("key", "value")
    assert cache.get("key") == "value"
    
    # Test delete
    cache.delete("key")
    assert cache.get("key") is None
    
    # Test clear
    cache.set("k1", "v1")
    cache.set("k2", "v2")
    cache.clear()
    assert cache.get("k1") is None
    assert cache.get("k2") is None
