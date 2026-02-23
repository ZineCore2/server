# CLAUDE.md — ZineCore2 Server

## What This Repo Is

A **Django REST API backend** implementing the four ZineCore2 metadata profiles (ZineCore2, AgentCore2, HoldingCore2, RepoCore2) with PostgreSQL.

The spec repo is included as a **git submodule** at `spec/`. After cloning, run `git submodule update --init`.

## Development Workflow

Docker Compose runs **PostgreSQL only**. Django runs locally via `uv`.

```bash
docker compose up -d                    # Start Postgres
cd backend
uv sync                                 # Install deps
DJANGO_SETTINGS_MODULE=zinecore.settings.development uv run manage.py runserver
```

For migrations: `uv run manage.py makemigrations <app>` then `uv run manage.py migrate`.

To load vocabularies: `uv run manage.py load_vocabularies` (reads from `spec/vocabularies/canonical/`).

## Package Management

Use **uv** exclusively. Never use pip or system Python. Dependencies are in `backend/pyproject.toml`.

```bash
cd backend
uv add <package>      # Add a dependency
uv sync               # Install/update
uv run <command>      # Run in the venv
```

## Architecture

### Settings (`zinecore/settings/`)
- `base.py` — Shared config. Database defaults to `localhost:5433`. REST framework uses `ReadOnlyOrAuthenticated` permission + `StandardPagination` (25/page).
- `development.py` — `DEBUG=True`, `ALLOWED_HOSTS=["*"]`

### Apps
Each app follows the pattern: `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`.

| App | Profile | Models |
|---|---|---|
| `core` | (shared) | `TimestampedModel` (abstract), `BaseVocabulary` (abstract) |
| `catalog` | ZineCore2 | `Zine`, `Subject`, `Genre`, `RightsStatement` |
| `agents` | AgentCore2 | `Agent`, `AgentKind`, `AgentRole` |
| `repositories` | RepoCore2 | `Repository`, `RepoKind` |
| `holdings` | HoldingCore2 | `Holding`, `AccessStatus`, `DistroStatus` |

### Model Patterns
- All models inherit `TimestampedModel` (provides `created_at`, `updated_at`)
- All vocabulary models inherit `BaseVocabulary` (provides `code`, `label`)
- Integer BigAutoField PKs internally + separate unique CharField for external IDs (`zine_id`, `agent_id`, `repo_id`, `holding_id`)
- PostgreSQL `ArrayField` for repeatable metadata elements (requires `django.contrib.postgres`)

### Serializer Patterns
- External `id` field maps to internal `*_id` field: `id = serializers.CharField(source="zine_id")`
- Separate read/write serializers for Zine and Holding (M2M and FK resolution)
- `SlugRelatedField` resolves FKs by external string ID (e.g., holding's `repository_id` → `Repository.repo_id`)

### ViewSet Patterns
- Profile ViewSets use `ModelViewSet` with `lookup_field` set to the external ID field
- Vocabulary ViewSets use `ReadOnlyModelViewSet` with `lookup_field="code"` and no pagination

### URL Structure
```
/admin/
/api/zines/                    → catalog.ZineViewSet
/api/agents/                   → agents.AgentViewSet
/api/repositories/             → repositories.RepositoryViewSet
/api/holdings/                 → holdings.HoldingViewSet
/api/vocabularies/subjects/    → catalog.SubjectViewSet (read-only)
/api/vocabularies/genres/      → catalog.GenreViewSet (read-only)
/api/vocabularies/rights-statements/
/api/vocabularies/agent-kinds/
/api/vocabularies/agent-roles/
/api/vocabularies/repo-kinds/
/api/vocabularies/access-statuses/
/api/vocabularies/distro-statuses/
/api/auth/                     → DRF browsable API login
/api/auth/token/               → obtain_auth_token
/api/schema/                   → OpenAPI schema
/api/docs/                     → Swagger UI
```

## Vocabulary Loading

The `load_vocabularies` management command in `catalog/management/commands/` reads canonical JSON from `spec/vocabularies/canonical/` and uses `update_or_create` on `code`. The `VOCAB_MAP` dict must stay aligned with the spec repo's `scripts/build-vocabularies.js` `DJANGO_MODELS` mapping.

## Environment Variables

See `.env.example`:
- `POSTGRES_PASSWORD` — Database password (default: `zinecore_dev`)
- `DJANGO_SECRET_KEY` — Django secret key
- `DATABASE_HOST` — Database host (default: `localhost`)
- `DATABASE_PORT` — Database port (default: `5433`)
- `VOCAB_CANONICAL_DIR` — Path to canonical vocabulary JSON (default: `spec/vocabularies/canonical` relative to project root)
