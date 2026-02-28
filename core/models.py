from dataclasses import dataclass
from typing import Optional

@dataclass
class FeatureFlag:
    name: str
    enabled: bool
    description: Optional[str] = None