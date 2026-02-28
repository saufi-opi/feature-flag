from typing import Optional, List, Dict
from core.repository import FlagRepository
from core.models import FeatureFlag
from core.exceptions import FlagNotFoundError

class InMemoryRepository(FlagRepository):
    def __init__(self):
        self.flags: Dict[str, FeatureFlag] = {}
        # override_type -> value -> flag_name -> enabled
        self.overrides: Dict[str, Dict[str, Dict[str, bool]]] = {}

    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        return self.flags.get(name)

    def get_all_flags(self) -> List[FeatureFlag]:
        return list(self.flags.values())

    def save_flag(self, flag: FeatureFlag) -> FeatureFlag:
        self.flags[flag.name] = flag
        return flag

    def update_flag(self, name: str, enabled: bool) -> FeatureFlag:
        flag = self.flags.get(name)
        if not flag:
            raise FlagNotFoundError(name)
        flag.enabled = enabled
        return flag

    def get_override(self, flag_name: str, override_type: str, value: str) -> Optional[bool]:
        return self.overrides.get(override_type, {}).get(value, {}).get(flag_name)

    def set_override(self, flag_name: str, override_type: str, value: str, enabled: bool) -> None:
        if override_type not in self.overrides:
            self.overrides[override_type] = {}
        if value not in self.overrides[override_type]:
            self.overrides[override_type][value] = {}
        self.overrides[override_type][value][flag_name] = enabled

    def delete_override(self, flag_name: str, override_type: str, value: str) -> None:
        if override_type in self.overrides and value in self.overrides[override_type]:
            if flag_name in self.overrides[override_type][value]:
                del self.overrides[override_type][value][flag_name]
