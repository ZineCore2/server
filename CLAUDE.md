# CLAUDE.md — ZineCore2 Server

## What This Repo Is

A **Django REST API backend** implementing the four ZineCore2 metadata profiles (ZineCore2, AgentCore2, HoldingCore2, RepoCore2) with PostgreSQL.

The spec repo is included as a **git submodule** at `spec/`. After cloning, run `git submodule update --init`.

## Development Workflow

First-time setup uses the interactive onboarding TUI:
```bash
./onboarding.sh      # Sets up everything interactively
./start.sh           # Start dev server (use after onboarding)
```

Docker Compose runs **PostgreSQL only**. Django runs locally.

For manage.py commands from the project root:
```bash
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py <command>
```

For migrations: `makemigrations <app>` then `migrate`.

To load vocabularies: `load_vocabularies` (fetches from `zinecore.org/api/vocabularies/`).

To load ISO 639-1 language codes from Library of Congress: `load_languages` (fetches from `id.loc.gov`).

To load ISO 3166-1 country codes from Library of Congress: `load_countries` (fetches from `id.loc.gov`).

To load sample data: `loaddata data/sample-data.json`.

## Package Management

Use **uv** exclusively. Never use pip or system Python.

The root `pyproject.toml` defines a workspace with `backend/` as a member. Dependencies live in `backend/pyproject.toml`. `textual` is a dev dependency used by the onboarding TUI.

```bash
uv sync               # Install/update from project root
uv add --directory backend <package>   # Add a dependency
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
| `catalog` | ZineCore2 | `Zine`, `Subject`, `Genre`, `RightsStatement`, `Language` |
| `agents` | AgentCore2 | `Agent`, `AgentKind`, `AgentRole` |
| `repositories` | RepoCore2 | `Repository`, `RepoKind`, `Country` |
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
/api/vocabularies/languages/   → catalog.LanguageViewSet (read-only, ISO 639-1)
/api/vocabularies/countries/   → repositories.CountryViewSet (read-only, ISO 3166-1)
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

The `load_vocabularies` management command fetches controlled vocabularies from the zinecore.org API (`https://zinecore.org/api/vocabularies/{vocab}`). It loads: subjects, genres, rights_statements, agent_kinds, agent_roles, repo_kinds, holding_access_statuses, and holding_distro_statuses. Use `--local` to load from `spec/vocabularies/canonical/` instead. The `VOCAB_MAP` dict must stay aligned with the spec repo's `scripts/build-vocabularies.js` `DJANGO_MODELS` mapping.

The `load_languages` management command fetches ISO 639-1 language codes directly from the Library of Congress vocabulary API (`id.loc.gov/vocabulary/iso639-1.json`). Run with `--dry-run` to preview without saving. This is separate from the spec-based vocabularies since languages use an external authoritative source.

The `load_countries` management command fetches ISO 3166-1 alpha-2 country codes from the Library of Congress MARC Countries vocabulary (`id.loc.gov/vocabulary/countries.json`). Only 2-character codes are loaded by default (excluding US states and Canadian provinces). Use `--include-subdivisions` to load all codes, or `--dry-run` to preview.

## Environment Variables

See `.env.example`:
- `DATABASE_NAME` — Database name (default: `zinecore`)
- `DATABASE_USER` — Database user (default: `zinecore`)
- `DATABASE_PASSWORD` — Database password (default: `zinecore_dev`)
- `DJANGO_SECRET_KEY` — Django secret key
- `DATABASE_HOST` — Database host (default: `localhost`)
- `DATABASE_PORT` — Database port (default: `5433`)
- `VOCAB_CANONICAL_DIR` — Path to canonical vocabulary JSON (default: `spec/vocabularies/canonical` relative to project root)
