from typing import Optional, List, Dict, Any
from core.repository import FlagRepository
from core.exceptions import FlagNotFoundError, DuplicateFlagError
from core.models import FeatureFlag

class FeatureFlagEngine:
    def __init__(self, repo: FlagRepository, lookup_chain: Optional[List[str]] = None):
        self.repo = repo
        # Default chain if none provided.
        self.lookup_chain = lookup_chain or ["user", "group", "region"]

    def create_flag(self, name: str, enabled: bool, description: Optional[str] = None) -> FeatureFlag:
        if self.repo.get_flag(name):
            raise DuplicateFlagError(name)
        return self.repo.save_flag(FeatureFlag(name=name, enabled=enabled, description=description))

    def get_flag(self, name: str) -> FeatureFlag:
        flag = self.repo.get_flag(name)
        if not flag:
            raise FlagNotFoundError(name)
        return flag

    def get_all_flags(self) -> List[FeatureFlag]:
        return self.repo.get_all_flags()

    def update_flag(self, name: str, enabled: bool) -> FeatureFlag:
        """Update the global status of an existing feature flag."""
        flag = self.get_flag(name) # Ensures it exists
        return self.repo.update_flag(flag.name, enabled)

    def delete_flag(self, name: str) -> None:
        """Delete a feature flag and cascade delete all its overrides."""
        self.get_flag(name) # Ensures it exists before deleting
        self.repo.delete_flag(name)

    def evaluate(self, flag_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
        flag = self.get_flag(flag_name)

        if context:
            for override_type in self.lookup_chain:
                # E.g., if override_type="user", check context["user"]
                # E.g., if override_type="region", check context["region"]
                value = context.get(override_type)
                if value is not None:
                    result = self.repo.get_override(flag.name, override_type, value)
                    if result is not None:
                        return result

        return flag.enabled

    def set_override(self, flag_name: str, override_type: str, value: str, enabled: bool) -> None:
        flag = self.get_flag(flag_name)
        self.repo.set_override(flag.name, override_type, value, enabled)

    def delete_override(self, flag_name: str, override_type: str, value: str) -> None:
        flag = self.get_flag(flag_name)
        self.repo.delete_override(flag.name, override_type, value)
