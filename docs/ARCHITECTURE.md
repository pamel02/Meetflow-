# Architecture

The project uses a layered modular monolith. HTTP concerns must stay in `api/`,
business rules in `services/`, and persistence queries in `repositories/`.

```text
Client React
    |
    v
Nginx -> Flask API -> service -> repository -> SQLAlchemy models
                       |              |
                       v              v
                 AI / workers    SQLite or MySQL
                       |
                       v
             NVIDIA NIM / ChromaDB / Whisper
```

## Backend boundaries

- `api/`: request parsing, authentication decorators and HTTP responses.
- `services/`: authorization-aware use cases and orchestration.
- `repositories/`: database access only.
- `models/`: SQLAlchemy entities and relationships.
- `schemas/`: input validation and normalization.
- `ai/`: adapters for NVIDIA NIM, Whisper, local embeddings and RAG.
- `workers/`: bounded background execution. A durable queue is recommended when
  horizontal scaling or guaranteed delivery becomes necessary.
- `middleware/`: cross-cutting HTTP concerns.
- `utils/`: small infrastructure helpers without business rules.
- `tests/`: regression and unit tests.

## Frontend boundaries

- `pages/`: route-level composition.
- `components/`: reusable presentation.
- `services/`: the only layer allowed to call the backend.
- `hooks/`: stateful browser capabilities and polling.
- `context/`: application-wide session and UI state.
- `utils/`: pure formatting and mapping functions.

## Dependency rule

Routes depend on services, services depend on repositories, and repositories
depend on models. Models must not import services or HTTP code.
