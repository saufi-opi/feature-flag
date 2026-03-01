import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_engine
from core.engine import FeatureFlagEngine
from tests.conftest import InMemoryRepository

# Create a clean engine instance per test session/function if needed.
# We'll use a pytest fixture to yield a fresh client with the overridden dependency.
@pytest.fixture
def mock_engine():
    repo = InMemoryRepository()
    engine = FeatureFlagEngine(repo, lookup_chain=["user", "group", "region"])
    return engine

@pytest.fixture
def client(mock_engine):
    # Override the get_engine dependency to use our isolated mock_engine
    app.dependency_overrides[get_engine] = lambda: mock_engine
    with TestClient(app) as c:
        yield c
    # Clean up overrides after the test
    app.dependency_overrides.clear()

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_and_list_flags(client):
    # Create
    response = client.post("/flags/", json={"name": "beta_ui", "enabled": True, "description": "New UI test"})
    assert response.status_code == 201
    assert response.json()["name"] == "beta_ui"
    assert response.json()["enabled"] is True
    
    # List
    response = client.get("/flags/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "beta_ui"

def test_get_flag_not_found(client):
    response = client.get("/flags/missing_flag")
    assert response.status_code == 404
    assert "not exist" in response.json()["detail"].lower()

def test_evaluate_flag_with_context(client, mock_engine):
    # Setup flag and override directly on the engine to avoid API chaining logic for this specific test
    mock_engine.create_flag("dark_theme", enabled=False)
    mock_engine.set_override("dark_theme", "user", "admin_alice", enabled=True)
    
    # Evaluate generic context over the API
    response = client.post("/flags/dark_theme/evaluate", json={"context": {"user": "bob"}})
    assert response.status_code == 200
    assert response.json()["result"] is False # Global default
    
    # Evaluate specific override context
    response = client.post("/flags/dark_theme/evaluate", json={"context": {"user": "admin_alice"}})
    assert response.status_code == 200
    assert response.json()["result"] is True # Override triggered

def test_delete_flag_cascades(client, mock_engine):
    # Setup
    mock_engine.create_flag("deprecated_feature", enabled=True)
    mock_engine.set_override("deprecated_feature", "region", "eu", enabled=False)
    
    # Delete via API
    response = client.delete("/flags/deprecated_feature")
    assert response.status_code == 204
    
    # Verify via API that it's gone
    response = client.get("/flags/deprecated_feature")
    assert response.status_code == 404
    
    # Engine verification of cascade (should have dropped from memory dict)
    assert mock_engine.repo.get_override("deprecated_feature", "region", "eu") is None

def test_api_can_set_and_delete_overrides(client, mock_engine):
    mock_engine.create_flag("ab_test", enabled=False)
    
    # Set override
    response = client.post("/flags/ab_test/overrides", json={
        "override_type": "group",
        "value": "testers",
        "enabled": True
    })
    assert response.status_code == 201
    
    assert mock_engine.evaluate("ab_test", {"group": "testers"}) is True
    
    # Delete override
    response = client.delete("/flags/ab_test/overrides/group/testers")
    assert response.status_code == 204
    
    # Falls back to default
    assert mock_engine.evaluate("ab_test", {"group": "testers"}) is False
