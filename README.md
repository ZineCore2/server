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

## Quick Start

```bash
git clone --recurse-submodules git@github.com:ZineCore2/server.git
cd server
./onboarding.sh     # Interactive setup wizard (sets up everything)
./start.sh           # Start the dev server
```

The onboarding script handles Docker, database, migrations, vocabularies, sample data, and superuser creation via an interactive TUI.

### Manual Setup

If you prefer to set up manually:

```bash
git submodule update --init             # Pull spec submodule
cp .env.example .env                    # Create .env
docker compose up -d                    # Start PostgreSQL
uv sync                                 # Install Python deps

DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py migrate
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py load_geonames
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py load_languages
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py load_vocabularies
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py loaddata data/fixtures.json
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py createsuperuser
```

## Project Structure

```
server/
├── onboarding.sh               # Interactive setup wizard
├── start.sh                    # Start dev server
├── docker-compose.yml          # PostgreSQL 17 (dev only)
├── .env.example
├── data/
│   └── fixtures.json           # Sample fixture data
├── spec/                       # Git submodule → ZineCore2/spec
└── backend/
    ├── pyproject.toml          # uv-managed dependencies
    ├── manage.py
    ├── zinecore/               # Django project
    │   ├── settings/
    │   │   ├── base.py         # Shared settings
    │   │   └── development.py  # DEBUG=True
    │   └── urls.py             # Root URL router
    ├── core/                   # Abstract models, permissions, pagination, renderers
    ├── catalog/                # ZineCore2 (zines + subject/genre/rights vocabs)
    ├── agents/                 # AgentCore2 (agents + kind/role vocabs)
    ├── repositories/           # RepoCore2 (repos + kind vocab)
    ├── holdings/               # HoldingCore2 (holdings + access/distro vocabs)
    └── geography/              # GeoNames-based place lookups
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
| `GET /api/vocabularies/languages/` | ISO 639-1 languages (read-only) |
| `GET /api/vocabularies/rights-statements/` | Rights statements (read-only) |
| `GET /api/vocabularies/agent-kinds/` | Agent kinds (read-only) |
| `GET /api/vocabularies/agent-roles/` | Agent roles (read-only) |
| `GET /api/vocabularies/repo-kinds/` | Repository kinds (read-only) |
| `GET /api/vocabularies/access-statuses/` | Holding access statuses (read-only) |
| `GET /api/vocabularies/distro-statuses/` | Holding distro statuses (read-only) |
| `GET /api/vocabularies/external-id-systems/` | External identifier systems (read-only) |
| `GET /api/vocabularies/external-uri-types/` | External URI types (read-only) |
| `GET /api/docs/` | Swagger UI |
| `GET /api/schema/` | OpenAPI schema |
| `POST /api/auth/token/` | Obtain auth token |

## Output Formats

All profile endpoints support multiple output formats. Use the `?format=` query parameter or the `Accept` header:

| Format | `?format=` | `Accept` header | Endpoints |
|--------|-----------|----------------|-----------|
| JSON | `json` | `application/json` | All |
| JSON-LD | `jsonld` | `application/ld+json` | All |
| CSV | `csv` | `text/csv` | All |
| Dublin Core XML | `dc-xml` | `application/xml` | All |
| RDF/Turtle | `turtle` | `text/turtle` | All |
| BibTeX | `bibtex` | `application/x-bibtex` | Zines only |
| MARCXML | `marcxml` | `application/marcxml+xml` | Zines, Holdings |

**Examples:**

```bash
# JSON-LD
curl http://localhost:8000/api/zines/?format=jsonld

# Dublin Core XML
curl -H "Accept: application/xml" http://localhost:8000/api/zines/

# MARCXML for a single zine
curl http://localhost:8000/api/zines/zn-001/?format=marcxml

# BibTeX export (all zines, no pagination)
curl http://localhost:8000/api/zines/?format=bibtex

# CSV export (pagination bypassed automatically)
curl http://localhost:8000/api/agents/?format=csv
```

## Authentication

- **Read**: Public (no auth required)
- **Write**: Session or Token authentication required
- Token endpoint: `POST /api/auth/token/` with `username` and `password`

```bash
# Obtain a token
curl -X POST http://localhost:8000/api/auth/token/ \
     -d "username=admin&password=yourpassword"

# Use the token
curl -H "Authorization: Token <your-token>" \
     -X POST http://localhost:8000/api/zines/ \
     -H "Content-Type: application/json" \
     -d '{"title": "My Zine"}'
```

## Metadata Profiles

The API implements four Dublin Core Application Profiles defined in the `spec/` submodule:

| Profile | Endpoint | Description |
|---------|----------|-------------|
| **ZineCore2** | `/api/zines/` | Bibliographic records for individual zines |
| **AgentCore2** | `/api/agents/` | People, organizations, and groups |
| **RepoCore2** | `/api/repositories/` | Physical and digital zine collections |
| **HoldingCore2** | `/api/holdings/` | Links between zines and the repositories that hold them |

## Spec Submodule

The `spec/` directory is a git submodule tracking the `develop` branch of `ZineCore2/spec`. The `load_vocabularies` management command reads canonical vocabulary JSON from `spec/vocabularies/canonical/`.

To update the submodule:

```bash
git submodule update --remote spec
```

## Related Repositories

- [ZineCore2/spec](https://github.com/ZineCore2/spec) — Metadata specification (included as submodule)
- [ZineCore2/website](https://github.com/ZineCore2/website) — Documentation site at [zinecore.org](https://zinecore.org)
