"""AgentCore2 JSON importer."""

from typing import Optional

from agents.models import Agent, AgentKind
from agents.serializers import AgentWriteSerializer

from .base import BaseImporter


class AgentImporter(BaseImporter):
    """Importer for AgentCore2 JSON schema."""

    schema_name = "agentcore2"
    model = Agent
    write_serializer = AgentWriteSerializer
    id_field = "agent_id"

    def extract_id(self, data: dict) -> Optional[str]:
        """Extract agent_id from JSON data."""
        return data.get("id")

    def transform_to_django_format(self, data: dict) -> dict:
        """
        Transform AgentCore2 JSON to Django serializer format.

        AgentCore2 JSON → AgentWriteSerializer format:
        - id → agent_id (optional, auto-generated if omitted)
        - display_name → display_name
        - kind → kind (vocabulary code lookup)
        - biography → biography
        - pronouns → pronouns
        - website → external_uris (with type "homepage")
        - orcid → external_ids (with system "orcid")
        - wikidata_id → external_ids (with system "wikidata")
        """
        django_data = {}

        # Basic fields
        if "id" in data:
            django_data["agent_id"] = data["id"]

        django_data["display_name"] = data.get("display_name", "")

        # Kind (controlled vocabulary)
        if "kind" in data:
            kind_value = data["kind"]
            # If it's already a code, use it; if it's a label, look it up
            try:
                kind = AgentKind.objects.get(code=kind_value)
                django_data["kind"] = kind_value
            except AgentKind.DoesNotExist:
                # Try to find by label
                try:
                    kind = AgentKind.objects.get(label__iexact=kind_value)
                    django_data["kind"] = kind.code
                except AgentKind.DoesNotExist:
                    # Let the serializer handle the validation error
                    django_data["kind"] = kind_value

        # Optional text fields
        if "biography" in data:
            django_data["biography"] = data["biography"]
        if "pronouns" in data:
            django_data["pronouns"] = data["pronouns"]

        # External URIs (website, social media, etc.)
        external_uris = []
        if "website" in data and data["website"]:
            external_uris.append({"type_code": "homepage", "uri": data["website"]})

        if external_uris:
            django_data["external_uris"] = external_uris

        # External Identifiers (ORCID, Wikidata, etc.)
        external_ids = []
        if "orcid" in data and data["orcid"]:
            external_ids.append({"system_code": "orcid", "value": data["orcid"]})
        if "wikidata_id" in data and data["wikidata_id"]:
            external_ids.append({"system_code": "wikidata", "value": data["wikidata_id"]})

        if external_ids:
            django_data["external_ids"] = external_ids

        return django_data
