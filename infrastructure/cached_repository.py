from typing import Optional, List
from core.repository import FlagRepository
from core.models import FeatureFlag
from core.cache import CacheBackend

class CachedFlagRepository(FlagRepository):
    """
    A proxy repository that transparently caches read operations before falling
    back to a primary repository (like SQLite), and invalidates caches on writes.
    """

    # Cache keys
    ALL_FLAGS_KEY = "flags:all"

    def __init__(self, fallback_repository: FlagRepository, cache: CacheBackend):
        self.fallback = fallback_repository
        self.cache = cache

    def _flag_key(self, name: str) -> str:
        return f"flag:{name}"

    def _override_key(self, flag_name: str, override_type: str, value: str) -> str:
        return f"override:{flag_name}:{override_type}:{value}"

    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        key = self._flag_key(name)
        cached_val = self.cache.get(key)
        
        if cached_val is not None:
            # We explicitly cache "MISS_SENTINEL" to avoid repeated db lookups for non-existent flags
            if cached_val == "MISS_SENTINEL":
                return None
            return cached_val

        # Fallback to the underlying database repository
        flag = self.fallback.get_flag(name)
        
        # Cache the result or the sentinel
        if flag is not None:
            self.cache.set(key, flag)
        else:
            self.cache.set(key, "MISS_SENTINEL")
            
        return flag

    def get_all_flags(self) -> List[FeatureFlag]:
        cached_flags = self.cache.get(self.ALL_FLAGS_KEY)
        if cached_flags is not None:
            return cached_flags
            
        flags = self.fallback.get_all_flags()
        self.cache.set(self.ALL_FLAGS_KEY, flags)
        return flags

    def save_flag(self, flag: FeatureFlag) -> FeatureFlag:
        saved_flag = self.fallback.save_flag(flag)
        
        # Invalidate/Update caches
        self.cache.set(self._flag_key(flag.name), saved_flag)
        self.cache.delete(self.ALL_FLAGS_KEY)
        
        return saved_flag

    def update_flag(self, name: str, enabled: bool) -> FeatureFlag:
        updated_flag = self.fallback.update_flag(name, enabled)
        
        # Invalidate/Update caches
        self.cache.set(self._flag_key(name), updated_flag)
        self.cache.delete(self.ALL_FLAGS_KEY)
        
        return updated_flag

    def delete_flag(self, name: str) -> None:
        self.fallback.delete_flag(name)
        
        # Invalidate caches
        self.cache.delete(self._flag_key(name))
        self.cache.delete(self.ALL_FLAGS_KEY)
        # Note: We don't individually clear override caches here in the simplistic
        # pattern. A robust implementation would either namespace keys or use SQL 
        # cascading deletes with clear-all or prefixes, but for simple flags this suffices.
        # It means stale overrides might be cached if fetched without a parent flag, but 
        # engine evaluating checks flag existence first anyway.

    def get_override(self, flag_name: str, override_type: str, value: str) -> Optional[bool]:
        key = self._override_key(flag_name, override_type, value)
        cached_val = self.cache.get(key)
        
        if cached_val is not None:
            if cached_val == "MISS_SENTINEL":
                return None
            return cached_val
            
        override = self.fallback.get_override(flag_name, override_type, value)
        
        if override is not None:
            self.cache.set(key, override)
        else:
            self.cache.set(key, "MISS_SENTINEL")
            
        return override

    def set_override(self, flag_name: str, override_type: str, value: str, enabled: bool) -> None:
        self.fallback.set_override(flag_name, override_type, value, enabled)
        
        key = self._override_key(flag_name, override_type, value)
        self.cache.set(key, enabled)

    def delete_override(self, flag_name: str, override_type: str, value: str) -> None:
        self.fallback.delete_override(flag_name, override_type, value)
        
        key = self._override_key(flag_name, override_type, value)
        self.cache.delete(key)
