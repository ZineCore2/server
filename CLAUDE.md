# CLAUDE.md — ZineCore2 Server

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A **Django REST API backend** implementing the four ZineCore2 metadata profiles (ZineCore2, AgentCore2, HoldingCore2, RepoCore2) with PostgreSQL.

The spec repo is included as a **git submodule** at `spec/`. After cloning, run `git submodule update --init`.

## Quick Command Reference

```bash
./onboarding.sh                 # First-time interactive setup
./start.sh                      # Start dev server
uv sync                         # Install/update dependencies
uv add --directory backend pkg  # Add dependency

# Migrations
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py makemigrations <app>
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py migrate

# Data loading (order matters!)
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py load_geonames
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py load_countries
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py load_languages
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py load_vocabularies
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py loaddata data/fixtures.json

# Data export
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py export_data

# Tests
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py test
```

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

For tests: Django's built-in test framework is used. Run with:
```bash
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py test
```

To load vocabularies: `load_vocabularies` (fetches from `zinecore.org/api/vocabularies/`).

To load GeoNames geographic data: `load_geonames` (fetches from `download.geonames.org`). **Must run before** `load_vocabularies` — some vocabularies reference GeoPlace for authority_scope.

To load ISO 639-1 language codes from Library of Congress: `load_languages` (fetches from `id.loc.gov`).

To load sample data: `loaddata data/fixtures.json`. **Must run after** `load_geonames`, `load_vocabularies`, and `load_languages` — fixtures use natural foreign keys that reference vocabulary and geography records.

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
- Admin interface uses **Unfold** theme (modern UI with improved UX)

### Apps
Each app follows the pattern: `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`.

| App | Profile | Models |
|---|---|---|
| `core` | (shared) | `TimestampedModel` (abstract), `BaseVocabulary` (abstract), `ExternalIdSystem`, `ExternalIdentifier`, `ExternalUriType`, `ExternalUri` |
| `catalog` | ZineCore2 | `Zine`, `Subject`, `Genre`, `RightsStatement`, `Language` |
| `agents` | AgentCore2 | `Agent`, `AgentKind`, `AgentRole` |
| `repositories` | RepoCore2 | `Repository`, `RepoKind`, `Country` |
| `holdings` | HoldingCore2 | `Holding`, `AccessStatus`, `DistroStatus` |
| `accounts` | (user features) | `Profile`, `ZineSubmission`, `SubmissionStatus` |
| `geography` | (geographic data) | `GeoPlace` (GeoNames hierarchy) |

### Model Patterns
- All models inherit `TimestampedModel` (provides `created_at`, `updated_at`)
- All vocabulary models inherit `BaseVocabulary` (provides `code`, `label`)
- Integer BigAutoField PKs internally + separate unique CharField for external IDs (`zine_id`, `agent_id`, `repo_id`, `holding_id`)
- PostgreSQL `ArrayField` for repeatable metadata elements (requires `django.contrib.postgres`)
- External identifiers and URIs use dynamic one-to-many pivot tables (`ExternalIdentifier`, `ExternalUri`) backed by controlled vocabularies (`ExternalIdSystem`, `ExternalUriType`) in the `core` app. Both pivot models use a `CheckConstraint` to enforce exactly one of `agent` or `repository` is set.

### Critical Architectural Patterns

**Natural Keys for Fixtures:**
- All profile models define `natural_key()` method returning external ID tuple
- Fixtures use `use_natural_foreign_keys=True` for cross-referencing
- This allows fixture loading to work without knowing internal integer PKs
- Example: Holding fixture references Zine by `zine_id`, not internal `pk`

**External ID Pattern:**
- Internal PKs are never exposed in API responses
- API uses `*_id` fields (`zine_id`, `agent_id`, etc.) as the public identifier
- Serializers map `id` → `*_id` via `source="zine_id"` parameter
- ViewSets use `lookup_field` to route by external ID, not internal PK

**Vocabulary Loading Dependencies:**
1. `load_geonames` FIRST (creates GeoPlace country records)
2. `load_countries` (ISO 3166-1 codes)
3. `load_languages` (ISO 639-1 codes)
4. `load_vocabularies` (references GeoPlace for `authority_scope`)
5. `loaddata` LAST (references all vocabularies via natural keys)

**M2M Through Tables:**
- `Zine` has creators/contributors/publishers via explicit through models (`ZineCreator`, `ZineContributor`, `ZinePublisher`)
- This allows ordering and additional metadata on relationships
- Serializers handle these automatically with nested representations

### Serializer Patterns
- External `id` field maps to internal `*_id` field: `id = serializers.CharField(source="zine_id")`
- Separate read/write serializers for Zine and Holding (M2M and FK resolution)
- `SlugRelatedField` resolves FKs by external string ID (e.g., holding's `repository_id` → `Repository.repo_id`)

### ViewSet Patterns
- Profile ViewSets use `ModelViewSet` with `lookup_field` set to the external ID field
- Vocabulary ViewSets use `ReadOnlyModelViewSet` with `lookup_field="code"` and no pagination

### URL Structure
```
/admin/                        → Django admin + Unfold UI
/admin/import-json/            → Web-based JSON import interface (staff only)
/api/zines/                    → catalog.ZineViewSet
/api/agents/                   → agents.AgentViewSet
/api/repositories/             → repositories.RepositoryViewSet
/api/holdings/                 → holdings.HoldingViewSet
/api/profiles/                 → accounts.ProfileViewSet (requires auth)
/api/submissions/              → accounts.ZineSubmissionViewSet (requires auth)
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
/api/vocabularies/submission-statuses/
/api/vocabularies/external-id-systems/
/api/vocabularies/external-uri-types/
/api/auth/                     → DRF browsable API login
/api/auth/token/               → obtain_auth_token
/api/schema/                   → OpenAPI schema
/api/docs/                     → Swagger UI
```

### Output Formats

All profile endpoints support 7 output formats via `?format=` parameter or `Accept` header:

| Format | Renderer | Endpoints | Media Type |
|---|---|---|---|
| JSON | `JSONRenderer` | All | `application/json` |
| JSON-LD | `JSONLDRenderer` | All 4 profiles | `application/ld+json` |
| CSV | `CSVRenderer` | All 4 profiles | `text/csv` |
| Dublin Core XML | `DublinCoreXMLRenderer` | All 4 profiles | `application/xml` |
| RDF/Turtle | `TurtleRenderer` | All 4 profiles | `text/turtle` |
| BibTeX | `BibTeXRenderer` | Zines only | `application/x-bibtex` |
| MARCXML | `MARCXMLRenderer` | Zines, Holdings | `application/marcxml+xml` |

All renderers defined in `core/renderers.py`. Each profile has a `PROFILE_MAP` entry mapping ViewSet name to context URL and namespace configuration.

## Data Import/Export

### Export Data

Export user-created data to JSON fixture files:
```bash
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py export_data
```

Creates two files in `data/`:
- `fixtures.json` — Repositories and their external IDs/URIs
- `custom.json` — Agents, zines, holdings, submissions, profiles, and their external IDs/URIs

Options: `--output-dir <path>`, `--indent <num>`

### Import Data

**Web Interface:** `/admin/import-json/` (requires staff login)
- Import ZineCore2, AgentCore2, RepoCore2 records from JSON
- Auto-detects schema type from record structure
- Validate-only mode + atomic transaction option
- Returns detailed results with created/updated IDs and error details

**Importer Architecture:** Located in `core/importers/`:
- `BaseImporter` — Abstract base class handling JSON schema validation
- `ZineImporter`, `AgentImporter`, `RepositoryImporter` — Profile-specific importers
- Each importer validates against `spec/schemas/{profile}.schema.json`
- Returns `ImportResult` dataclass with success/error tracking
- Uses write serializers for validation and natural keys for FK resolution

## Vocabulary Loading

**Prerequisites:** Run `load_geonames` BEFORE `load_vocabularies`. Some vocabularies (e.g., `ExternalIdSystem`) have an `authority_scope` field that references `GeoPlace` country records.

The `load_vocabularies` management command fetches controlled vocabularies from the zinecore.org API (`https://zinecore.org/api/vocabularies/{vocab}`). It loads: subjects, genres, rights_statements, agent_kinds, agent_roles, repo_kinds, holding_access_statuses, and holding_distro_statuses from the API.

**Note:** The `external_id_systems` and `external_uri_types` vocabularies are not available from the API and must be loaded from local files using `--local --vocab external_id_systems` and `--local --vocab external_uri_types`. The onboarding script handles this automatically.

Use `--local` to load from `spec/vocabularies/canonical/` instead of the API. The `VOCAB_MAP` dict must stay aligned with the spec repo's `scripts/build-vocabularies.js` `DJANGO_MODELS` mapping.

The `load_languages` management command fetches ISO 639-1 language codes directly from the Library of Congress vocabulary API (`id.loc.gov/vocabulary/iso639-1.json`). Run with `--dry-run` to preview without saving. This is separate from the spec-based vocabularies since languages use an external authoritative source.

The `load_countries` management command fetches ISO 3166-1 alpha-2 country codes from the Library of Congress MARC Countries vocabulary (`id.loc.gov/vocabulary/countries.json`). Only 2-character codes are loaded by default (excluding US states and Canadian provinces). Use `--include-subdivisions` to load all codes, or `--dry-run` to preview.

## User Features (Accounts App)

The `accounts` app provides user profiles and zine submission tracking:

### User Profiles
- `Profile` model: OneToOneField to Django User
- Optional FK to `Agent` (self-identification) or `Repository` (institutional affiliation)
- Profile images via `ImageField` (requires Pillow)
- Endpoint: `/api/profiles/` (requires authentication)

### Zine Submissions
- `ZineSubmission` model: tracks user submissions to repositories
- FK to User, Zine, Repository, and SubmissionStatus (controlled vocab)
- Auto-timestamps `submitted_at` and `responded_at` based on status changes
- Boolean fields: `send_digital`, `send_print`
- Endpoint: `/api/submissions/` (requires authentication)

### Repository Submission Settings
Repositories now have:
- `is_active` — Whether accepting submissions
- `submission_allowed` — Whether submissions are enabled
- `submission_notes` — Submission guidelines text

## Environment Variables

See `.env.example`:
- `DATABASE_NAME` — Database name (default: `zinecore`)
- `DATABASE_USER` — Database user (default: `zinecore`)
- `DATABASE_PASSWORD` — Database password (default: `zinecore_dev`)
- `DJANGO_SECRET_KEY` — Django secret key
- `DATABASE_HOST` — Database host (default: `localhost`)
- `DATABASE_PORT` — Database port (default: `5433`)
- `VOCAB_CANONICAL_DIR` — Path to canonical vocabulary JSON (default: `spec/vocabularies/canonical` relative to project root)
