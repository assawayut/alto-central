# Alto Central Backend Architecture

## Overview

A modular Python backend designed for:
- Real-time HVAC data APIs (READ from production databases)
- Machine Learning (training, inference, model management)
- Data Analytics & Processing
- Mathematical Optimization (HVAC control optimization)
- LLM Integration (natural language insights)

**Critical Constraint**: Backend is READ-ONLY for production data sources.

---

## Data Source Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Data Flow Architecture                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   EXTERNAL DATABASES (READ-ONLY)              LOCAL DATABASE (R/W)   │
│   ════════════════════════════                ═══════════════════    │
│                                                                       │
│   ┌─────────────────┐                        ┌─────────────────┐     │
│   │    Supabase     │ ◀── Query Only ──────  │    PostgreSQL   │     │
│   │  (Production)   │                        │     (Local)     │     │
│   ├─────────────────┤                        ├─────────────────┤     │
│   │ • latest_data   │                        │ • ml_models     │     │
│   │ • Real-time     │                        │ • optimization  │     │
│   │   WebSocket     │                        │ • chat_history  │     │
│   └─────────────────┘                        │ • cache         │     │
│                                              │ • app_config    │     │
│   ┌─────────────────┐                        └─────────────────┘     │
│   │  TimescaleDB    │ ◀── Query Only ────────────────┘               │
│   │  (Production)   │                                                 │
│   ├─────────────────┤                                                 │
│   │ • timeseries    │                                                 │
│   │ • historical    │                                                 │
│   │ • aggregates    │                                                 │
│   └─────────────────┘                                                 │
│                                                                       │
│   ⚠️  NEVER WRITE TO PRODUCTION DATABASES                            │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Framework** | FastAPI | Async I/O, WebSocket, auto-docs, ML-friendly |
| **Prod DB (RT)** | Supabase | External - READ ONLY (real-time data) |
| **Prod DB (TS)** | TimescaleDB | External - READ ONLY (historical) |
| **Local DB** | PostgreSQL | App data: models, cache, chat |
| **Cache** | Redis | Query cache, real-time pub/sub |
| **Task Queue** | Celery + Redis | Background ML/optimization jobs |
| **ML Framework** | scikit-learn, PyTorch | Model training and inference |
| **Model Storage** | MLflow + Local FS | Model versioning (local) |
| **Optimization** | scipy, cvxpy, OR-Tools | Mathematical optimization |
| **LLM** | LangChain + Anthropic | Natural language processing |
| **Data Processing** | Pandas, NumPy, Polars | Analytics, feature engineering |

---

## Project Structure

```
alto-central-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entry
│   ├── config.py                   # Settings, environment variables
│   │
│   ├── api/                        # API Layer (REST endpoints)
│   │   ├── __init__.py
│   │   ├── deps.py                 # Dependency injection
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py           # Aggregates all v1 routes
│   │   │   ├── realtime.py         # GET /realtime/latest
│   │   │   ├── ontology.py         # GET /ontology/entities
│   │   │   ├── timeseries.py       # GET/POST /timeseries/query
│   │   │   ├── energy.py           # GET /energy/daily
│   │   │   ├── afdd.py             # GET /afdd/alerts
│   │   │   ├── ml.py               # ML model endpoints
│   │   │   ├── optimization.py     # Optimization endpoints
│   │   │   └── chat.py             # LLM chat endpoints
│   │   └── websocket.py            # WebSocket handlers
│   │
│   ├── core/                       # Core utilities
│   │   ├── __init__.py
│   │   ├── security.py             # Auth, API keys
│   │   ├── exceptions.py           # Custom exceptions
│   │   └── logging.py              # Structured logging
│   │
│   ├── db/                         # Database Layer
│   │   ├── __init__.py
│   │   ├── connections/            # Database connections
│   │   │   ├── __init__.py
│   │   │   ├── supabase.py         # Supabase client (READ-ONLY)
│   │   │   ├── timescale.py        # TimescaleDB conn (READ-ONLY)
│   │   │   └── local.py            # Local PostgreSQL (READ-WRITE)
│   │   ├── repositories/           # Data access patterns
│   │   │   ├── __init__.py
│   │   │   ├── realtime_repo.py    # Queries Supabase
│   │   │   ├── timeseries_repo.py  # Queries TimescaleDB
│   │   │   ├── ontology_repo.py    # Queries prod DBs
│   │   │   ├── ml_models_repo.py   # Local DB (R/W)
│   │   │   ├── cache_repo.py       # Local DB (R/W)
│   │   │   └── chat_repo.py        # Local DB (R/W)
│   │   └── migrations/             # Alembic (local DB only)
│   │       └── versions/
│   │
│   ├── models/                     # Pydantic & ORM Models
│   │   ├── __init__.py
│   │   ├── domain/                 # SQLAlchemy models (local DB)
│   │   │   ├── __init__.py
│   │   │   ├── ml_model.py
│   │   │   ├── optimization_result.py
│   │   │   └── chat.py
│   │   └── schemas/                # Pydantic schemas (API)
│   │       ├── __init__.py
│   │       ├── realtime.py
│   │       ├── timeseries.py
│   │       ├── ontology.py
│   │       ├── ml.py
│   │       └── chat.py
│   │
│   ├── services/                   # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── realtime_service.py     # Fetches from Supabase
│   │   ├── timeseries_service.py   # Fetches from TimescaleDB
│   │   ├── ontology_service.py     # Equipment data
│   │   ├── energy_service.py       # Energy calculations
│   │   └── cache_service.py        # Redis caching layer
│   │
│   ├── ml/                         # Machine Learning Layer
│   │   ├── __init__.py
│   │   ├── registry.py             # Model registry (MLflow/local)
│   │   ├── training/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── anomaly_detection.py
│   │   │   ├── load_forecasting.py
│   │   │   └── efficiency_prediction.py
│   │   ├── inference/
│   │   │   ├── __init__.py
│   │   │   └── predictor.py
│   │   └── features/
│   │       ├── __init__.py
│   │       └── extractors.py
│   │
│   ├── analytics/                  # Data Analytics Layer
│   │   ├── __init__.py
│   │   ├── aggregators.py          # Time-based aggregations
│   │   ├── calculators.py          # KPI calculations
│   │   └── processors/
│   │       ├── __init__.py
│   │       └── data_cleaner.py
│   │
│   ├── optimization/               # Optimization Layer
│   │   ├── __init__.py
│   │   ├── solvers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── chiller_sequencing.py
│   │   │   ├── setpoint_optimizer.py
│   │   │   └── load_distribution.py
│   │   └── constraints/
│   │       ├── __init__.py
│   │       └── equipment.py
│   │
│   ├── llm/                        # LLM Integration Layer
│   │   ├── __init__.py
│   │   ├── client.py               # Anthropic/OpenAI client
│   │   ├── chains/
│   │   │   ├── __init__.py
│   │   │   ├── qa_chain.py
│   │   │   └── analysis_chain.py
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   └── templates.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── query_data.py
│   │       └── run_analysis.py
│   │
│   └── workers/                    # Background Tasks
│       ├── __init__.py
│       ├── celery_app.py
│       └── tasks/
│           ├── __init__.py
│           ├── training_tasks.py
│           ├── optimization_tasks.py
│           └── analytics_tasks.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   └── integration/
│
├── scripts/
│   ├── seed_local_db.py
│   └── train_models.py
│
├── notebooks/                      # R&D notebooks
│   ├── exploration/
│   └── model_development/
│
├── ml_artifacts/                   # Local model storage
│   ├── models/
│   └── experiments/
│
├── config/
│   └── sites.yaml                  # Shared with frontend
│
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.worker
│   └── docker-compose.yml
│
├── alembic.ini
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Database Connections

### Connection Configuration

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # External databases (READ-ONLY)
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    TIMESCALE_HOST: str
    TIMESCALE_PORT: int = 5432
    TIMESCALE_DB: str
    TIMESCALE_USER: str
    TIMESCALE_PASSWORD: str

    # Local database (READ-WRITE)
    LOCAL_DB_URL: str  # postgresql://user:pass@localhost:5432/alto_local

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # LLM
    ANTHROPIC_API_KEY: str

    class Config:
        env_file = ".env"
```

### Read-Only Connection Pattern

```python
# app/db/connections/timescale.py
from contextlib import asynccontextmanager
import asyncpg

class TimescaleDBConnection:
    """READ-ONLY connection to production TimescaleDB."""

    def __init__(self, settings):
        self.settings = settings
        self._pool = None

    async def connect(self):
        self._pool = await asyncpg.create_pool(
            host=self.settings.TIMESCALE_HOST,
            port=self.settings.TIMESCALE_PORT,
            database=self.settings.TIMESCALE_DB,
            user=self.settings.TIMESCALE_USER,
            password=self.settings.TIMESCALE_PASSWORD,
            min_size=5,
            max_size=20,
            # READ-ONLY: Use read replica or set transaction read only
            server_settings={
                'default_transaction_read_only': 'on'
            }
        )

    @asynccontextmanager
    async def get_connection(self):
        async with self._pool.acquire() as conn:
            # Enforce read-only at connection level
            await conn.execute("SET TRANSACTION READ ONLY")
            yield conn

    async def fetch(self, query: str, *args):
        """Execute read-only query."""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
```

### Supabase Client (Read-Only)

```python
# app/db/connections/supabase.py
from supabase import create_client, Client

class SupabaseConnection:
    """READ-ONLY connection to production Supabase."""

    def __init__(self, settings):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )

    async def get_latest_data(self, site_id: str):
        """Fetch latest sensor data for a site."""
        response = self.client.table("latest_data") \
            .select("*") \
            .eq("site_id", site_id) \
            .execute()
        return response.data

    def subscribe_realtime(self, site_id: str, callback):
        """Subscribe to real-time updates (read-only)."""
        return self.client.channel(f"site:{site_id}") \
            .on_postgres_changes(
                event="UPDATE",
                schema="public",
                table="latest_data",
                filter=f"site_id=eq.{site_id}",
                callback=callback
            ) \
            .subscribe()
```

---

## Local Database Schema

Only for application-specific data (ML, optimization, chat):

```sql
-- ML Models Registry (local)
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(100),
    site_id VARCHAR(50),  -- Reference, not FK
    artifact_path TEXT,
    metrics JSONB,
    parameters JSONB,
    status VARCHAR(20) DEFAULT 'trained',
    trained_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, version)
);

-- Optimization Results Cache (local)
CREATE TABLE optimization_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id VARCHAR(50) NOT NULL,
    optimization_type VARCHAR(100),
    input_hash VARCHAR(64),  -- Hash of input params
    solution JSONB,
    objective_value DECIMAL,
    valid_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_opt_cache_lookup (site_id, optimization_type, input_hash)
);

-- Query Cache (local)
CREATE TABLE query_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    data JSONB,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chat Sessions (local)
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    site_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id),
    role VARCHAR(20),
    content TEXT,
    tool_calls JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature Store (local) - Cached features for ML
CREATE TABLE feature_store (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id VARCHAR(50) NOT NULL,
    feature_set VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    features JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_features_lookup (site_id, feature_set, timestamp DESC)
);
```

---

## API Endpoints

### Real-Time Data (Reads from Supabase)
```
GET  /api/v1/sites/{site_id}/realtime/latest
GET  /api/v1/sites/{site_id}/realtime/latest/{device_id}
WS   /api/v1/ws/realtime?site_id={site_id}
```

### Timeseries (Reads from TimescaleDB)
```
POST /api/v1/sites/{site_id}/timeseries/query
GET  /api/v1/sites/{site_id}/timeseries/aggregated
```

### Energy (Computed from TimescaleDB queries)
```
GET  /api/v1/sites/{site_id}/energy/daily
GET  /api/v1/sites/{site_id}/energy/monthly
```

### ML (Uses local DB + reads prod for training data)
```
GET  /api/v1/ml/models
POST /api/v1/sites/{site_id}/ml/predict/load
POST /api/v1/sites/{site_id}/ml/predict/anomaly
POST /api/v1/ml/training/start  # Reads prod, writes model locally
```

### Optimization (Reads prod, caches results locally)
```
POST /api/v1/sites/{site_id}/optimization/chiller-sequence
POST /api/v1/sites/{site_id}/optimization/setpoints
GET  /api/v1/sites/{site_id}/optimization/recommendations
```

### LLM Chat (Reads prod for context, stores chat locally)
```
POST /api/v1/sites/{site_id}/chat/message
GET  /api/v1/sites/{site_id}/chat/sessions
```

---

## ML Pipeline

### Training Flow (Reads production data)

```
┌─────────────────────────────────────────────────────────────────┐
│                     ML Training Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │ TimescaleDB  │ ─READ─▶ │   Feature    │                      │
│  │ (Production) │         │  Extraction  │                      │
│  └──────────────┘         └──────────────┘                      │
│                                  │                               │
│                                  ▼                               │
│                          ┌──────────────┐                       │
│                          │   Training   │                       │
│                          │   Pipeline   │                       │
│                          └──────────────┘                       │
│                                  │                               │
│                                  ▼                               │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │ Local Model  │ ◀─WRITE─│    Model     │                      │
│  │   Storage    │         │   Registry   │                      │
│  └──────────────┘         └──────────────┘                      │
│                                                                  │
│  ⚠️ Training READS from prod, WRITES to local only              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Inference Flow

```python
# app/ml/inference/predictor.py
class LoadForecaster:
    def __init__(self, model_registry, timescale_conn):
        self.registry = model_registry
        self.ts_conn = timescale_conn  # READ-ONLY

    async def predict(self, site_id: str, horizon_hours: int = 24):
        # 1. Load model from local storage
        model = self.registry.load_model("load_forecast", site_id)

        # 2. Fetch recent data from prod (READ-ONLY)
        recent_data = await self.ts_conn.fetch("""
            SELECT time, device_id, datapoint, value
            FROM timeseries_data
            WHERE site_id = $1
              AND time > NOW() - INTERVAL '7 days'
              AND device_id = 'plant'
            ORDER BY time
        """, site_id)

        # 3. Extract features
        features = self.extract_features(recent_data)

        # 4. Make predictions
        predictions = model.predict(features, horizon_hours)

        return predictions
```

---

## Optimization Layer

```python
# app/optimization/solvers/chiller_sequencing.py
import cvxpy as cp
import numpy as np

class ChillerSequencingSolver:
    """Optimal chiller staging based on load."""

    def __init__(self, timescale_conn, cache_repo):
        self.ts_conn = timescale_conn  # READ-ONLY
        self.cache = cache_repo        # LOCAL R/W

    async def solve(self, site_id: str, target_load: float):
        # 1. Check cache first
        cached = await self.cache.get_optimization(
            site_id, "chiller_sequence", target_load
        )
        if cached and cached.valid_until > datetime.now():
            return cached.solution

        # 2. Fetch equipment data (READ-ONLY)
        chillers = await self.ts_conn.fetch("""
            SELECT device_id,
                   MAX(CASE WHEN datapoint='capacity' THEN value END) as capacity,
                   MAX(CASE WHEN datapoint='min_load' THEN value END) as min_load
            FROM equipment_specs
            WHERE site_id = $1 AND device_id LIKE 'chiller_%'
            GROUP BY device_id
        """, site_id)

        # 3. Formulate optimization problem
        n_chillers = len(chillers)
        x = cp.Variable(n_chillers, boolean=True)  # On/off
        load = cp.Variable(n_chillers, nonneg=True)  # Load per chiller

        # Objective: minimize energy (simplified)
        objective = cp.Minimize(cp.sum(load * 0.6))  # kW/RT efficiency

        # Constraints
        constraints = [
            cp.sum(load) >= target_load,
            load <= [c['capacity'] for c in chillers] * x,
            load >= [c['min_load'] for c in chillers] * x,
        ]

        problem = cp.Problem(objective, constraints)
        problem.solve()

        solution = {
            "chillers_on": [c['device_id'] for i, c in enumerate(chillers) if x.value[i] > 0.5],
            "loads": {c['device_id']: load.value[i] for i, c in enumerate(chillers)},
            "total_power": problem.value
        }

        # 4. Cache result locally
        await self.cache.save_optimization(
            site_id, "chiller_sequence", target_load, solution,
            valid_for_minutes=15
        )

        return solution
```

---

## LLM Integration

```python
# app/llm/chains/qa_chain.py
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent

class HVACAssistant:
    def __init__(self, timescale_conn, supabase_conn):
        self.llm = ChatAnthropic(model="claude-sonnet-4-20250514")
        self.ts_conn = timescale_conn    # READ-ONLY
        self.supa_conn = supabase_conn   # READ-ONLY

        self.tools = [
            self._create_query_tool(),
            self._create_analysis_tool(),
        ]

    def _create_query_tool(self):
        """Tool to query HVAC data (READ-ONLY)."""
        @tool
        async def query_hvac_data(
            site_id: str,
            device_id: str,
            datapoints: list[str],
            hours_back: int = 24
        ) -> dict:
            """Query historical HVAC sensor data."""
            data = await self.ts_conn.fetch("""
                SELECT time, datapoint, value
                FROM timeseries_data
                WHERE site_id = $1
                  AND device_id = $2
                  AND datapoint = ANY($3)
                  AND time > NOW() - $4 * INTERVAL '1 hour'
                ORDER BY time
            """, site_id, device_id, datapoints, hours_back)
            return {"data": data}

        return query_hvac_data

    async def chat(self, site_id: str, message: str, session_id: str):
        # Agent with tools for querying data
        agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        executor = AgentExecutor(agent=agent, tools=self.tools)

        response = await executor.ainvoke({
            "input": message,
            "site_id": site_id,
        })

        return response["output"]
```

---

## Caching Strategy

Since we're querying external production databases, caching is critical:

```python
# app/services/cache_service.py
import redis.asyncio as redis
import hashlib
import json

class CacheService:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get_or_fetch(
        self,
        key: str,
        fetch_fn,
        ttl_seconds: int = 60
    ):
        """Cache-aside pattern for external queries."""
        # Try cache first
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        # Fetch from external DB (READ-ONLY)
        data = await fetch_fn()

        # Cache locally
        await self.redis.setex(key, ttl_seconds, json.dumps(data))

        return data

    def make_key(self, prefix: str, **params) -> str:
        """Generate cache key from parameters."""
        param_str = json.dumps(params, sort_keys=True)
        hash_val = hashlib.sha256(param_str.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_val}"
```

---

## Docker Compose

```yaml
# docker/docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - TIMESCALE_HOST=${TIMESCALE_HOST}
      - TIMESCALE_PORT=${TIMESCALE_PORT}
      - TIMESCALE_DB=${TIMESCALE_DB}
      - TIMESCALE_USER=${TIMESCALE_USER}
      - TIMESCALE_PASSWORD=${TIMESCALE_PASSWORD}
      - LOCAL_DB_URL=postgresql://alto:alto@local-db:5432/alto_local
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - local-db
      - redis

  worker:
    build:
      context: ..
      dockerfile: docker/Dockerfile.worker
    environment:
      # Same as api
    depends_on:
      - local-db
      - redis

  # LOCAL services only (not production DBs)
  local-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: alto
      POSTGRES_PASSWORD: alto
      POSTGRES_DB: alto_local
    volumes:
      - local_db_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  local_db_data:
  redis_data:
```

---

## Summary

| Data Source | Access | Purpose |
|-------------|--------|---------|
| **Supabase (Prod)** | READ-ONLY | Real-time sensor data |
| **TimescaleDB (Prod)** | READ-ONLY | Historical timeseries |
| **PostgreSQL (Local)** | READ-WRITE | ML models, cache, chat |
| **Redis (Local)** | READ-WRITE | Query cache, pub/sub |

**Key Principles:**
1. Never write to production databases
2. Cache external queries aggressively
3. Store ML artifacts locally
4. Use connection pooling for external DBs
5. Set transaction read-only at connection level
