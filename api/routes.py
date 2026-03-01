from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from core.engine import FeatureFlagEngine
from core.models import FeatureFlag
from core.exceptions import FlagNotFoundError, DuplicateFlagError
from api.dependencies import get_engine
from api.schemas import FlagCreate, FlagUpdate, OverrideCreate, EvaluateRequest

router = APIRouter(prefix="/flags", tags=["flags"])

@router.post("/", response_model=FeatureFlag, status_code=status.HTTP_201_CREATED)
def create_flag(flag_in: FlagCreate, engine: FeatureFlagEngine = Depends(get_engine)):
    """Create a new global feature flag."""
    try:
        return engine.create_flag(flag_in.name, flag_in.enabled, flag_in.description)
    except DuplicateFlagError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[FeatureFlag])
def list_flags(engine: FeatureFlagEngine = Depends(get_engine)):
    """List all feature flags."""
    return engine.get_all_flags()

@router.get("/{name}", response_model=FeatureFlag)
def get_flag(name: str, engine: FeatureFlagEngine = Depends(get_engine)):
    """Get a specific feature flag by name."""
    try:
        return engine.get_flag(name)
    except FlagNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{name}", response_model=FeatureFlag)
def update_flag(name: str, flag_in: FlagUpdate, engine: FeatureFlagEngine = Depends(get_engine)):
    """Update a feature flag's global state."""
    try:
        return engine.update_flag(name, flag_in.enabled)
    except FlagNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flag(name: str, engine: FeatureFlagEngine = Depends(get_engine)):
    """Delete a feature flag and cascade delete all its overrides."""
    try:
        engine.delete_flag(name)
    except FlagNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{name}/overrides", status_code=status.HTTP_201_CREATED)
def set_override(name: str, override_in: OverrideCreate, engine: FeatureFlagEngine = Depends(get_engine)):
    """Set a context-specific override for a flag."""
    try:
        # get_flag ensures it exists before setting the override
        engine.get_flag(name)
        engine.set_override(name, override_in.override_type, override_in.value, override_in.enabled)
        return {"message": f"Override set for {name}[{override_in.override_type}={override_in.value}]"}
    except FlagNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{name}/overrides/{override_type}/{value}", status_code=status.HTTP_204_NO_CONTENT)
def delete_override(name: str, override_type: str, value: str, engine: FeatureFlagEngine = Depends(get_engine)):
    """Delete a context-specific override."""
    try:
        engine.get_flag(name)
        engine.delete_override(name, override_type, value)
    except FlagNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{name}/evaluate")
def evaluate_flag(name: str, eval_in: EvaluateRequest, engine: FeatureFlagEngine = Depends(get_engine)):
    """Evaluate a feature flag's truthiness taking into account all overrides for the provided context."""
    try:
        result = engine.evaluate(name, eval_in.context)
        return {"flag": name, "result": result, "context": eval_in.context}
    except FlagNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
