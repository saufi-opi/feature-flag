import pytest
from unittest.mock import patch
from click.testing import CliRunner
from cli.commands import cli
from core.engine import FeatureFlagEngine
from core.exceptions import FlagNotFoundError
from tests.conftest import InMemoryRepository

@pytest.fixture
def mock_engine():
    # Inject an InMemoryRepository so CLI tests do NOT hit the real local SQL DB
    repo = InMemoryRepository()
    engine = FeatureFlagEngine(repo, lookup_chain=["user", "group", "region"])
    return engine

@pytest.fixture
def runner():
    return CliRunner()

@patch("cli.commands.get_engine")
def test_create_flag_command(mock_get_engine, runner, mock_engine):
    mock_get_engine.return_value = mock_engine
    
    result = runner.invoke(cli, ["create-flag", "test_feature", "--enabled"])
    assert result.exit_code == 0
    assert "created successfully" in result.output
    
    # Verify the underlying engine state changed
    assert mock_engine.evaluate("test_feature") is True

@patch("cli.commands.get_engine")
def test_evaluate_command(mock_get_engine, runner, mock_engine):
    mock_get_engine.return_value = mock_engine
    mock_engine.create_flag("test_feature", enabled=False)
    mock_engine.set_override("test_feature", "user", "alice", True)
    
    # Call evaluate via CLI passing the dynamic kwargs context
    result = runner.invoke(cli, ["evaluate", "test_feature", "--user", "alice"])
    assert result.exit_code == 0
    assert "🟩 True" in result.output

@patch("cli.commands.get_engine")
def test_set_override_command(mock_get_engine, runner, mock_engine):
    mock_get_engine.return_value = mock_engine
    mock_engine.create_flag("test_feature", enabled=False)
    
    result = runner.invoke(cli, ["set-override", "test_feature", "group", "admin", "--enabled"])
    assert result.exit_code == 0
    assert "Override set: test_feature[group=admin] -> True" in result.output
    
    assert mock_engine.evaluate("test_feature", {"group": "admin"}) is True

@patch("cli.commands._init_db")
def test_init_db_command(mock_init_db, runner):
    result = runner.invoke(cli, ["init-db"])
    assert result.exit_code == 0
    assert "Database initialized successfully" in result.output
    mock_init_db.assert_called_once()

@patch("cli.commands.get_engine")
def test_delete_flag_command(mock_get_engine, runner, mock_engine):
    mock_get_engine.return_value = mock_engine
    mock_engine.create_flag("del_test", enabled=False)
    
    result = runner.invoke(cli, ["delete-flag", "del_test"])
    assert result.exit_code == 0
    assert "permanently deleted" in result.output
    
    # Verify the underlying engine state changed
    with pytest.raises(FlagNotFoundError):
        mock_engine.get_flag("del_test")
