"""RepoCore2 JSON importer."""

from typing import Optional

from geography.models import GeoPlace
from repositories.models import RepoKind, Repository
from repositories.serializers import RepositoryWriteSerializer

from .base import BaseImporter


class RepositoryImporter(BaseImporter):
    """Importer for RepoCore2 JSON schema."""

    schema_name = "repocore2"
    model = Repository
    write_serializer = RepositoryWriteSerializer
    id_field = "repo_id"

    def extract_id(self, data: dict) -> Optional[str]:
        """Extract repo_id from JSON data."""
        return data.get("id")

    def transform_to_django_format(self, data: dict) -> dict:
        """
        Transform RepoCore2 JSON to Django serializer format.

        RepoCore2 JSON → RepositoryWriteSerializer format:
        - id → repo_id
        - name → name
        - kind → kind (vocabulary code)
        - city, region, country → location (GeoPlace lookup)
        - address → address (combine city + region if not provided)
        - homepage → external_uris (type "homepage")
        - marc_org_code → external_ids (system "marc-org")
        - isil → external_ids (system "isil")
        - ror_id → external_ids (system "ror")
        - access_policy → access_policy
        - hours → hours
        - notes → notes (array)
        """
        django_data = {}

        # Basic fields
        if "id" in data:
            django_data["repo_id"] = data["id"]

        django_data["name"] = data.get("name", "")

        # Kind (controlled vocabulary)
        if "kind" in data:
            kind_value = data["kind"]
            try:
                kind = RepoKind.objects.get(code=kind_value)
                django_data["kind"] = kind_value
            except RepoKind.DoesNotExist:
                # Try by label
                try:
                    kind = RepoKind.objects.get(label__iexact=kind_value)
                    django_data["kind"] = kind.code
                except RepoKind.DoesNotExist:
                    django_data["kind"] = kind_value

        # Location (try to resolve from city/region/country)
        # This is complex - for now, we'll store as address text
        # Future: Add geocoding service or manual GeoPlace lookup
        city = data.get("city", "")
        region = data.get("region", "")
        country = data.get("country", "")

        if "address" in data:
            django_data["address"] = data["address"]
        elif city and region:
            django_data["address"] = f"{city}, {region}"
        elif city:
            django_data["address"] = city

        # Optional: Try to lookup GeoPlace if we have enough info
        # For now, we'll leave location as null and require manual assignment
        # TODO: Implement GeoPlace lookup/geocoding

        # Text fields
        if "access_policy" in data:
            django_data["access_policy"] = data["access_policy"]
        if "hours" in data:
            django_data["hours"] = data["hours"]
        if "notes" in data:
            django_data["notes"] = data["notes"]

        # External URIs
        external_uris = []
        if "homepage" in data and data["homepage"]:
            external_uris.append({"type_code": "homepage", "uri": data["homepage"]})

        if external_uris:
            django_data["external_uris"] = external_uris

        # External Identifiers
        external_ids = []
        if "marc_org_code" in data and data["marc_org_code"]:
            external_ids.append(
                {"system_code": "marc_org", "value": data["marc_org_code"]}
            )
        if "isil" in data and data["isil"]:
            external_ids.append({"system_code": "isil", "value": data["isil"]})
        if "ror_id" in data and data["ror_id"]:
            external_ids.append({"system_code": "ror", "value": data["ror_id"]})

        if external_ids:
            django_data["external_ids"] = external_ids

        return django_data
