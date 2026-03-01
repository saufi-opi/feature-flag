import click
from typing import Dict, Any

from core.engine import FeatureFlagEngine
from core.exceptions import FlagNotFoundError, DuplicateFlagError
from infrastructure.database import SessionLocal, init_db as _init_db
from infrastructure.sqlite_repository import SQLiteFlagRepository

def get_engine() -> FeatureFlagEngine:
    """Helper to inject dependencies into the CLI commands"""
    # Automatically ensure the database and tables exist!
    _init_db()
    
    db = SessionLocal()
    repo = SQLiteFlagRepository(db)
    # Using the same lookup chain as the tests
    engine = FeatureFlagEngine(repo, lookup_chain=["user", "group", "region"])
    return engine

@click.group()
def cli():
    """Feature Flag Engine CLI"""
    pass

@cli.command()
def init_db():
    """Create the SQLite database and tables"""
    _init_db()
    click.echo("✅ Database initialized successfully.")

@cli.command()
@click.argument('name')
@click.option('--enabled/--disabled', default=False, help="Initial state of the flag")
@click.option('--desc', default=None, help="Description of the feature")
def create_flag(name: str, enabled: bool, desc: str):
    """Create a new global feature flag"""
    engine = get_engine()
    try:
        engine.create_flag(name, enabled, desc)
        click.echo(f"🎉 Flag '{name}' created successfully (Enabled: {enabled})")
    except DuplicateFlagError as e:
        click.echo(f"❌ Error: {str(e)}", err=True)

@cli.command()
@click.argument('name')
@click.option('--user', help="User ID context")
@click.option('--group', help="Group ID context")
@click.option('--region', help="Region ID context")
def evaluate(name: str, user: str, group: str, region: str):
    """Evaluate a feature flag's truthiness taking into account all overrides"""
    engine = get_engine()
    
    # Pack only provided options into the context dictionary
    context: Dict[str, Any] = {}
    if user: context["user"] = user
    if group: context["group"] = group
    if region: context["region"] = region

    try:
        result = engine.evaluate(name, context)
        click.echo(f"🧩 Evaluation result for '{name}': {'🟩 True' if result else '🟥 False'}")
    except FlagNotFoundError as e:
        click.echo(f"❌ Error: {str(e)}", err=True)

@cli.command()
@click.argument('flag_name')
@click.argument('override_type')
@click.argument('value')
@click.option('--enabled/--disabled', default=True, help="Set the override to True or False")
def set_override(flag_name: str, override_type: str, value: str, enabled: bool):
    """Set a context-specific override for a flag"""
    engine = get_engine()
    try:
        engine.set_override(flag_name, override_type, value, enabled)
        click.echo(f"🛠️  Override set: {flag_name}[{override_type}={value}] -> {enabled}")
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)

@cli.command()
def list_flags():
    """List all feature flags in the system"""
    engine = get_engine()
    flags = engine.get_all_flags()
    if not flags:
        click.echo("No flags found in the system.")
        return
    
    click.echo(f"Found {len(flags)} flags:")
    for flag in flags:
        status = "🟩 ON" if flag.enabled else "🟥 OFF"
        click.echo(f"  - {flag.name}: {status} ({flag.description or 'No desc'})")

@cli.command()
@click.argument('name')
def get_flag(name: str):
    """Get details for a specific feature flag"""
    engine = get_engine()
    flag = engine.get_flag(name)
    if flag:
        status = "🟩 ON" if flag.enabled else "🟥 OFF"
        click.echo(f"Flag '{flag.name}':\n  Status: {status}\n  Description: {flag.description}")
    else:
        click.echo(f"❌ Error: Flag '{name}' not found.", err=True)

@cli.command()
@click.argument('name')
@click.option('--enabled/--disabled', required=True, help="New state of the flag")
def update_flag(name: str, enabled: bool):
    """Update the global default state of a feature flag"""
    engine = get_engine()
    try:
        flag = engine.update_flag(name, enabled)
        status = "🟩 ON" if flag.enabled else "🟥 OFF"
        click.echo(f"✅ Flag '{name}' updated to {status}")
    except FlagNotFoundError as e:
        click.echo(f"❌ Error: {str(e)}", err=True)

@cli.command()
@click.argument('flag_name')
@click.argument('override_type')
@click.argument('value')
def delete_override(flag_name: str, override_type: str, value: str):
    """Delete a context-specific override for a flag"""
    engine = get_engine()
    try:
        engine.delete_override(flag_name, override_type, value)
        click.echo(f"🗑️  Override deleted: {flag_name}[{override_type}={value}]")
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)

@cli.command()
@click.argument('name')
def delete_flag(name: str):
    """Permanently delete a feature flag and all its overrides"""
    engine = get_engine()
    try:
        engine.delete_flag(name)
        click.echo(f"💣 Flag '{name}' and all its overrides were permanently deleted.")
    except FlagNotFoundError as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
