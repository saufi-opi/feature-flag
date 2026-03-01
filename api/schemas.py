from pydantic import BaseModel
from typing import Optional, Dict, Any

class FlagCreate(BaseModel):
    name: str
    enabled: bool = False
    description: Optional[str] = None

class FlagUpdate(BaseModel):
    enabled: bool

class OverrideCreate(BaseModel):
    override_type: str
    value: str
    enabled: bool

class EvaluateRequest(BaseModel):
    context: Dict[str, Any] = {}
