# ZineCore2 Server

Django REST API backend implementing the ZineCore2 family of metadata profiles.

## Tech Stack

- **Django 6.x** with Django REST Framework
- **PostgreSQL 17** (via Docker Compose)
- **Python 3.13+** managed with **uv**
- **drf-spectacular** for OpenAPI/Swagger docs

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Docker & Docker Compose (for PostgreSQL)

## Setup

```bash
# Clone with the spec submodule
git clone --recurse-submodules git@github.com:ZineCore2/server.git
cd server

# Or if already cloned without submodules
git submodule update --init

# Start PostgreSQL
docker compose up -d

# Install Python dependencies
cd backend
uv sync

# Run migrations and load vocabularies
DJANGO_SETTINGS_MODULE=zinecore.settings.development uv run manage.py migrate
DJANGO_SETTINGS_MODULE=zinecore.settings.development uv run manage.py load_vocabularies

# Create a superuser
DJANGO_SETTINGS_MODULE=zinecore.settings.development uv run manage.py createsuperuser

# Start the dev server
DJANGO_SETTINGS_MODULE=zinecore.settings.development uv run manage.py runserver
```

## Project Structure

```
server/
├── docker-compose.yml          # PostgreSQL 17 (dev only)
├── .env.example
├── spec/                       # Git submodule → ZineCore2/spec
└── backend/
    ├── pyproject.toml          # uv-managed dependencies
    ├── manage.py
    ├── zinecore/               # Django project
    │   ├── settings/
    │   │   ├── base.py         # Shared settings
    │   │   └── development.py  # DEBUG=True
    │   └── urls.py             # Root URL router
    ├── core/                   # Abstract models, permissions, pagination
    ├── catalog/                # ZineCore2 (zines + subject/genre/rights vocabs)
    ├── agents/                 # AgentCore2 (agents + kind/role vocabs)
    ├── repositories/           # RepoCore2 (repos + kind vocab)
    └── holdings/               # HoldingCore2 (holdings + access/distro vocabs)
```

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/zines/` | List/create zines |
| `GET /api/agents/` | List/create agents |
| `GET /api/repositories/` | List/create repositories |
| `GET /api/holdings/` | List/create holdings |
| `GET /api/vocabularies/subjects/` | Subject vocabulary (read-only) |
| `GET /api/vocabularies/genres/` | Genre vocabulary (read-only) |
| `GET /api/vocabularies/rights-statements/` | Rights statements (read-only) |
| `GET /api/vocabularies/agent-kinds/` | Agent kinds (read-only) |
| `GET /api/vocabularies/agent-roles/` | Agent roles (read-only) |
| `GET /api/vocabularies/repo-kinds/` | Repository kinds (read-only) |
| `GET /api/vocabularies/access-statuses/` | Holding access statuses (read-only) |
| `GET /api/vocabularies/distro-statuses/` | Holding distro statuses (read-only) |
| `GET /api/docs/` | Swagger UI |
| `GET /api/schema/` | OpenAPI schema |
| `POST /api/auth/token/` | Obtain auth token |

## Authentication

- **Read**: Public (no auth required)
- **Write**: Session or Token authentication required
- Token endpoint: `POST /api/auth/token/` with `username` and `password`

## Spec Submodule

The `spec/` directory is a git submodule tracking the `develop` branch of `ZineCore2/spec`. The `load_vocabularies` management command reads canonical vocabulary JSON from `spec/vocabularies/canonical/`.

## Related Repositories

- [ZineCore2/spec](https://github.com/ZineCore2/spec) — Metadata specification (included as submodule)
- [ZineCore2/website](https://github.com/ZineCore2/website) — Documentation site at [zinecore.org](https://zinecore.org)
