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
