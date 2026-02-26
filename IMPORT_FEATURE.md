# JSON Import Feature

## Overview

The Django Admin now includes a web-based JSON import feature that allows you to paste JSON data conforming to any of the four ZineCore2 schemas (ZineCore2, AgentCore2, RepoCore2, HoldingCore2) and import it directly into the database.

## Access

Navigate to **Data Management → Import JSON** in the Django Admin sidebar.

URL: `/admin/import-json/`

## Features

- **Paste-in Interface**: Paste JSON directly into a textarea (no file upload required)
- **Auto-detection**: Automatically detects which schema type the JSON conforms to
- **Validation**: Two-phase validation:
  1. JSON Schema validation against spec schemas
  2. Django model validation via DRF serializers
- **Batch Import**: Import single objects or arrays of objects
- **Transactional**: All-or-nothing mode (default) or skip-on-error mode
- **Dry Run**: Validate-only mode to check for errors without importing
- **Detailed Feedback**: Shows created/updated IDs and detailed error messages

## Usage

### 1. Prepare Your JSON Data

The import accepts JSON in two formats:

**Single Object:**
```json
{
  "id": "a-example",
  "display_name": "Example Agent",
  "kind": "person"
}
```

**Array of Objects:**
```json
[
  {
    "id": "a-example-1",
    "display_name": "First Agent",
    "kind": "person"
  },
  {
    "id": "a-example-2",
    "display_name": "Second Agent",
    "kind": "organization"
  }
]
```

### 2. Paste into the Admin

1. Navigate to **Data Management → Import JSON**
2. Paste your JSON into the textarea
3. Select schema type (or leave as "Auto-detect")
4. Choose options:
   - **All-or-Nothing Import**: If checked, entire batch rolls back on any error
   - **Validate Only**: If checked, validates without importing

5. Click **Process Import**

### 3. Review Results

The results page shows:
- **Summary**: Total records, successful, failed
- **Created IDs**: List of newly created records
- **Updated IDs**: List of updated records (if IDs already existed)
- **Errors**: Detailed error messages for failed records

## Schema Support

### AgentCore2 (Agents)

**Example:**
```json
{
  "id": "a-doris",
  "display_name": "Doris",
  "kind": "person",
  "biography": "Zinester from Portland",
  "pronouns": "she/her",
  "website": "https://example.com",
  "orcid": "0000-0001-2345-6789"
}
```

**Field Mapping:**
- `id` → `agent_id`
- `kind` → vocabulary code lookup (person, organization, etc.)
- `website` → creates ExternalUri with type "homepage"
- `orcid`, `wikidata_id` → creates ExternalIdentifier records

### RepoCore2 (Repositories)

**Example:**
```json
{
  "id": "r-qzap",
  "name": "Queer Zine Archive Project",
  "kind": "archive",
  "homepage": "https://qzap.org",
  "city": "Portland",
  "region": "OR",
  "country": "US",
  "access_policy": "Open access",
  "hours": "24/7 online",
  "notes": ["Digital archive", "LGBTQ+ focus"]
}
```

**Field Mapping:**
- `id` → `repo_id`
- `kind` → vocabulary code lookup
- `homepage` → creates ExternalUri
- `marc_org_code`, `isil`, `ror_id` → creates ExternalIdentifier records
- `city` + `region` → combined into `address` field
- `notes` → stored as PostgreSQL array

### ZineCore2 (Zines)

**Example:**
```json
{
  "id": "z-example",
  "title": "Example Zine",
  "creator": ["a-doris", "a-jane"],
  "publisher": ["a-microcosm"],
  "subject": ["feminism", "diy-culture"],
  "genre": ["perzine"],
  "language": ["en"],
  "date": ["2024"],
  "description": "A perzine about DIY culture",
  "rights": "cc-by-sa-4.0"
}
```

**Field Mapping:**
- `id` → `zine_id`
- `creator` → requires existing agent_ids (creates ZineCreator through models)
- `publisher` → requires existing agent_ids (creates ZinePublisher through models)
- `contributor` → can include role info:
  ```json
  "contributor": [
    {"agent_id": "a-jane", "role": "editor", "order": 0}
  ]
  ```
- `subject`, `genre`, `language` → vocabulary code lookups
- `rights` → single vocabulary code
- `date` → takes first value if array
- `description` → maps to `abstract`

### HoldingCore2 (Holdings)

**Status:** Not yet implemented

## Important Notes

### Create vs Update

- If `id` field is provided and exists → **UPDATE**
- If `id` field is provided but doesn't exist → **CREATE** with specified ID
- If `id` field is omitted → **CREATE** with auto-generated ID

### Dependencies

**Strict Mode (Current):** All related objects must exist before import.

For zines, you must:
1. Import agents first (creators, publishers, contributors)
2. Then import zines that reference those agents

**Example workflow:**
```bash
# 1. Import agents
{
  "id": "a-doris",
  "display_name": "Doris",
  "kind": "person"
}

# 2. Then import zines
{
  "id": "z-doris-zine",
  "title": "Doris's Zine",
  "creator": ["a-doris"]  # References existing agent
}
```

### Controlled Vocabularies

Vocabulary fields accept either:
- **Code** (preferred): `"kind": "person"`
- **Label**: `"kind": "Person"` (case-insensitive lookup)

If a label doesn't match exactly, you'll get a validation error.

### Geographic Locations

**Current limitation:** The Repository importer stores city/region as text in the `address` field but doesn't automatically resolve to GeoPlace records.

**Workaround:** Manually assign `location` after import via the admin interface.

## Error Handling

### Error Types

1. **Schema Error**: JSON doesn't match the spec schema
   - Missing required fields
   - Wrong data types
   - Invalid patterns

2. **Validation Error**: Django/DRF validation failed
   - Unknown vocabulary codes
   - Missing related objects (e.g., agent_id doesn't exist)
   - Invalid field values

3. **Database Error**: Database constraint violation
   - Duplicate unique fields
   - Foreign key constraints

### Example Error Output

```
✗ 2 records failed to import

Record #1 (id: "z-example-1"):
  • Validation Error: creator_ids - agent_id "a-nonexistent" does not exist

Record #2 (no id provided):
  • Schema Error: Missing required field "title"
```

## Implementation Details

### Architecture

```
core/
├── forms.py                      # ImportJSONForm
├── admin_views.py                # ImportJSONView
├── templates/admin/
│   └── import_json.html         # Import UI
└── importers/
    ├── base.py                  # BaseImporter abstract class
    ├── agent_importer.py        # AgentCore2 → Agent
    ├── repository_importer.py   # RepoCore2 → Repository
    └── zine_importer.py         # ZineCore2 → Zine
```

### Validation Flow

1. **Parse JSON** → Detect errors early
2. **Schema Validation** → Validate against spec JSON schemas
3. **Transform Data** → Convert from spec format to Django format
4. **Serializer Validation** → Use existing DRF write serializers
5. **Database Save** → Create or update model instances

### Transaction Modes

**Atomic (default):**
```python
@transaction.atomic
def import_batch(data_list):
    # All or nothing - any error rolls back entire batch
```

**Non-atomic:**
```python
def import_batch(data_list):
    # Skip failed records, continue with successful ones
```

## Future Enhancements

1. **Auto-Create Mode**: Automatically create related objects (e.g., agents) if they don't exist
2. **GeoPlace Resolution**: Geocoding service to resolve city/region/country to GeoPlace records
3. **Fuzzy Matching**: Use difflib for vocabulary label matching
4. **Progress Indicators**: Real-time progress for large batches
5. **CSV Export**: Download import results as CSV
6. **Management Command**: CLI wrapper for scripted imports
7. **Holding Importer**: Complete the HoldingCore2 importer

## Testing

### Unit Tests

Located in `backend/core/tests/test_importers.py`:

```python
pytest backend/core/tests/test_importers.py
```

### Manual Testing

Sample JSON files available in `backend/core/fixtures/sample_imports/`:
- `sample_agents.json`
- `sample_repositories.json`
- `sample_zines.json`

## Troubleshooting

### "Could not auto-detect schema type"

**Solution:** Manually select the schema type from the dropdown.

### "agent_id 'a-xyz' does not exist"

**Solution:** Import agents before importing zines that reference them.

### "Schema validation error"

**Solution:** Check that your JSON matches the schema at `spec/schemas/*.schema.json`.
- Ensure required fields are present
- Check data types (strings vs arrays vs objects)
- Verify vocabulary codes are valid

### Import successful but location not set

**Current behavior:** Repository import doesn't auto-resolve GeoPlace.

**Solution:** After import, manually assign the `location` field in the admin.

## Security

- **Authentication Required**: Must be logged in as staff/admin
- **Audit Logging**: All imports are logged (TODO: implement)
- **Rate Limiting**: Consider adding django-ratelimit in production
- **Size Limits**: No enforced limit (consider adding max JSON size check)

## Dependencies

- `jsonschema>=4.0` - JSON Schema validation
- Existing DRF serializers - Model validation
- Django transactions - Atomic imports
