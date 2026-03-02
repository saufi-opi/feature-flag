# Feature Flag Engine

A robust, framework-agnostic feature flag system built in pure Python. The system exposes its capabilities via two primary interfaces: a FastAPI REST backend and a CLI, both powered seamlessly by the same decoupled core engine.

## Architecture Overview

The system strictly adheres to Clean Architecture principles separating the core business logic from framework boundaries and database persistence.

```text
┌─────────────────────┐    ┌─────────────────────┐
│   FastAPI (api/)    │    │   CLI (cli/)        │
│   REST routes       │    │   Click commands    │
└────────┬────────────┘    └──────────┬──────────┘
         │                            │
         └──────────┬─────────────────┘
                    ↓
        ┌───────────────────────┐
        │  core/engine.py       │  ← Pure Python, no framework dependencies
        │  FeatureFlagEngine    │
        └───────────┬───────────┘
                    ↓
        ┌───────────────────────┐
        │  core/repository.py   │  ← Interface (Protocol)
        │  FlagRepository       │
        └───────────┬───────────┘
                    ↓
        ┌───────────────────────┐
        │  infrastructure/      │  ← Concrete DB implementation
        │  SQLiteRepository     │
        └───────────────────────┘
```

### The Golden Rule
1. `core/` contains pure Python logic with **zero** imports from FastAPI, Click, or SQLAlchemy.
2. `api/` and `cli/` bounds only invoke the core engine. They **never** touch the database directly.
3. `tests/` leverage a fast, isolated memory repository so tests execute instantly without a real DB.

## Directory Structure

```text
feature-flag-engine/
│
├── core/                           # Pure business logic — NO framework code
│   ├── __init__.py
│   ├── models.py                   # Plain Python data structures
│   ├── engine.py                   # FeatureFlagEngine — the heart of the system
│   ├── repository.py               # Interface (Protocol definition)
│   └── exceptions.py               # Extensible application errors
│
├── infrastructure/                 # DB persistence & drivers
│   ├── __init__.py
│   ├── database.py                 # SQLAlchemy engine configuration
│   ├── orm_models.py               # SQLAlchemy ORM table definitions
│   └── sqlite_repository.py        # Implements FlagRepository using SQLite
│
├── api/                            # FastAPI network boundary
│   ├── __init__.py
│   ├── main.py                     # App initialisation & router mapping
│   ├── dependencies.py             # Dependency injection container
│   ├── schemas.py                  # Pydantic request validation models
│   └── routes/                     # REST sub-routers
│
├── cli/                            # Command Line Interface boundary
│   ├── __init__.py
│   └── commands.py                 # Click command groups
│
└── tests/                          # Automated Pytest validation suite
```

## Dynamic Evaluation Engine
The evaluation priority chain is fully dynamic. Adding a novel override dimension (like `tenant_id` or `cohort_identifier`) requires **no logic modifications** throughout the codebase. 

The evaluation context accepts a dynamic dictionary, and the engine evaluates based on the instantiated precedence list (e.g., `lookup_chain=["user", "group", "region"]`), keeping the system perfectly decoupled and infinitely extensible.

## Running the CLI

### Option 1: Native Python (Fastest)
If you have Python and `uv` installed on your machine, you can run the CLI instantly without container overhead:

```bash
# Create a virtual environment
uv venv

# Activate it (Mac/Linux)
source .venv/bin/activate
# Or on Windows:
.venv\Scripts\activate

# Install the CLI dependencies
uv sync --extra cli

# See all available commands
uv run python -m cli.main --help

# Create a new global flag
uv run python -m cli.main create-flag dark_mode --enabled

# List all flags
uv run python -m cli.main list-flags

# Set a context-specific override
uv run python -m cli.main set-override dark_mode user alice --disabled

# Evaluate the flag (Inherits the override priority)
uv run python -m cli.main evaluate dark_mode --user alice

# Delete a flag and cascade delete its overrides
uv run python -m cli.main delete-flag dark_mode
```

### Option 2: Docker Compose (Isolated)
If you don't have Python installed, or prefer to keep your host machine clean, you can run the CLI through Docker. A custom lightweight image is built specifically for the CLI that safely mounts your local directory so the SQLite database persists across runs.

*Note: Use `run` instead of `up` to pass commands directly to the container.*

```bash
# See all available commands
docker compose -f docker/docker-compose.cli.yml run --rm cli --help

# Create a new global flag
docker compose -f docker/docker-compose.cli.yml run --rm cli create-flag dark_mode --enabled

# Evaluate the resulting flag precedence
docker compose -f docker/docker-compose.cli.yml run --rm cli evaluate dark_mode --group staff
```

## Running the API

The Feature Flag Engine also includes a fully functional REST API built with FastAPI. It uses the exact same core engine and SQLite database as the CLI.

### Option 1: Native Python (Fastest)
If you have Python and `uv` installed, you can run the API server directly:

```bash
# Create a virtual environment (if you haven't already)
uv venv

# Activate it (Mac/Linux)
source .venv/bin/activate
# Or on Windows:
.venv\Scripts\activate

# Install the API dependencies
uv sync --extra api

# Run the FastAPI development server
uv run uvicorn api.main:app --reload
```

### Option 2: Docker Compose (Isolated)
You can also run the API entirely within an isolated Docker container. 

```bash
# Start the API server (add -d to run in the background)
docker compose -f docker/docker-compose.api.yml up api
```

Once running, navigate to [http://localhost:8000/docs](http://localhost:8000/docs) in your browser to interact with the interactive Swagger UI.

### API Examples

```bash
# List all feature flags
curl http://localhost:8000/flags/

# Create a new feature flag
curl -X POST http://localhost:8000/flags/ \
  -H "Content-Type: application/json" \
  -d '{"name": "dark_mode", "enabled": true, "description": "Enable dark mode"}'

# Set a context-specific override
curl -X POST http://localhost:8000/flags/dark_mode/overrides \
  -H "Content-Type: application/json" \
  -d '{"override_type": "user", "value": "alice", "enabled": false}'

# Evaluate a feature flag with context
curl -X POST http://localhost:8000/flags/dark_mode/evaluate \
  -H "Content-Type: application/json" \
  -d '{"context": {"user": "alice"}}'

# Delete a flag and cascade delete its overrides
curl -X DELETE http://localhost:8000/flags/dark_mode
```

## Running the Tests

The project includes a robust test suite covering core logic, infrastructure patterns (like the caching proxy), and API routes.

```bash
# Create a virtual environment (if you haven't already)
uv venv

# Activate it (Mac/Linux)
source .venv/bin/activate
# Or on Windows:
.venv\Scripts\activate

# Make sure dependencies are installed
uv sync --extra all --extra dev

# Run the entire test suite
uv run python -m pytest
```

## Assumptions & Tradeoffs

- **Storage**: Used SQLite for simplicity and portability so the project can be run easily by reviewers without needing a separate database service. Because the application uses the `FlagRepository` Protocol and Clean Architecture, swapping to PostgreSQL or MySQL would only require a new class in `infrastructure/` and zero changes to the `core` engine.
- **Caching**: Implemented an application-level in-memory cache proxy (`InMemoryCacheBackend` conforming to a `CacheBackend` Protocol) to reduce database reads on flag evaluations. The tradeoff is that this cache does not synchronize across multiple worker processes. If running with Uvicorn's `--workers 4`, each worker maintains its own cache.
- **Framework Separation**: The core engine contains pure Python without FastAPI or Click dependencies. This took slightly more setup but allows the identical engine to power both interfaces securely.

## What I'd Do Next with More Time

1. **Distributed Caching**: Implement a `RedisCacheBackend` that conforms to the `CacheBackend` Protocol so that cache state is synchronized across a distributed deployment of multiple workers.
2. **Management UI**: Build a modern React/Next.js frontend dashboard to visually manage feature flags, view audit logs, and easily attach complex rollout rules without using the CLI or direct API requests.
3. **Authentication/Authorization**: Add an auth layer (e.g. JWT and OAuth2) to the FastAPI endpoints to ensure only authorized admins can create or modify flags, while evaluation endpoints might remain publicly accessible via API keys.
4. **Enhanced Targeting Rules**: Extend the evaluation engine to handle percentage-based rollouts (e.g., 20% of users get the feature) and regex matching for flexible context evaluation.

## AI Tools Disclosure

In the interest of transparency for the evaluation process:
- **Tool Used**: Antigravity (Google Deepmind AI Coding Assistant)
- **Nature of Assistance**: Used to accelerate boilerplate generation, assist with architectural plan and decisions, generate isolated Pytest unit tests, and help draft this README documentation. All core logic and design paradigms were carefully reviewed and directed to adhere to SOLID principles and Clean Architecture.
