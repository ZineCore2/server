"""ZineCore2 JSON importer."""

from typing import Optional

from catalog.models import Genre, Language, RightsStatement, Subject
from catalog.serializers import ZineWriteSerializer
from agents.models import Agent
from .base import BaseImporter


class ZineImporter(BaseImporter):
    """Importer for ZineCore2 JSON schema."""

    schema_name = "zinecore2"
    model = Agent  # Will be Zine, but need to import to avoid circular dependency
    write_serializer = ZineWriteSerializer
    id_field = "zine_id"

    def __init__(self):
        super().__init__()
        # Import here to avoid circular dependency
        from catalog.models import Zine

        self.model = Zine

    def extract_id(self, data: dict) -> Optional[str]:
        """Extract zine_id from JSON data."""
        return data.get("id")

    def transform_to_django_format(self, data: dict) -> dict:
        """
        Transform ZineCore2 JSON to Django serializer format.

        ZineCore2 JSON → ZineWriteSerializer format:
        - id → zine_id
        - title → title
        - creator → creator_ids (requires agent_id lookups)
        - subject → subject_codes (vocabulary codes)
        - description → abstract
        - publisher → publisher_ids
        - contributor → contributor_data (with roles)
        - date → publish_date (first value)
        - type → format
        - format → binding_features
        - identifier → identifier
        - source → source
        - language → language_codes
        - relation → relation
        - coverage → coverage
        - rights → rights_code
        """
        django_data = {}

        # Basic fields
        if "id" in data:
            django_data["zine_id"] = data["id"]

        # Required field
        django_data["title"] = data.get("title", "")

        # Optional string fields
        optional_fields = {
            "series_title": "series_title",
            "issue_designation": "issue_designation",
            "edition_statement": "edition_statement",
            "alternative_title": "alternative_title",
            "physical_dimensions": "physical_dimensions",
            "number_of_pages": "number_of_pages",
            "format": "format",
            "binding_features": "binding_features",
        }

        for json_key, django_key in optional_fields.items():
            if json_key in data:
                django_data[django_key] = data[json_key]

        # Description → abstract
        if "description" in data:
            # If it's an array, join; if string, use as-is
            desc = data["description"]
            if isinstance(desc, list):
                django_data["abstract"] = "\n\n".join(desc)
            else:
                django_data["abstract"] = desc

        # Table of contents (array → text)
        if "table_of_contents" in data:
            toc = data["table_of_contents"]
            if isinstance(toc, list):
                django_data["table_of_contents"] = "\n".join(toc)
            else:
                django_data["table_of_contents"] = toc

        # Public notes (array)
        if "public_notes" in data:
            django_data["public_notes"] = data["public_notes"]

        # Date → publish_date (take first value if array)
        if "date" in data:
            date_val = data["date"]
            if isinstance(date_val, list) and date_val:
                django_data["publish_date"] = date_val[0]
            else:
                django_data["publish_date"] = date_val

        # Array fields that stay as arrays
        if "coverage" in data:
            django_data["coverage"] = data["coverage"]
        if "source" in data:
            django_data["source"] = data["source"]
        if "relation" in data:
            django_data["relation"] = data["relation"]
        if "identifier" in data:
            django_data["identifier"] = data["identifier"]

        # Creator (array of names or agent_ids)
        # For strict mode, we expect agent_ids
        if "creator" in data and data["creator"]:
            creators = data["creator"]
            # Assume these are agent_ids (strict mode)
            # TODO: In future, add auto-create mode that looks up by display_name
            django_data["creator_ids"] = creators

        # Publisher (array of agent_ids)
        if "publisher" in data and data["publisher"]:
            django_data["publisher_ids"] = data["publisher"]

        # Contributor (array of objects or simple agent_ids)
        if "contributor" in data and data["contributor"]:
            contributors = data["contributor"]
            # If contributors include role info, preserve it
            # Otherwise, default to "contributor" role
            contributor_data = []
            for i, contrib in enumerate(contributors):
                if isinstance(contrib, dict):
                    contributor_data.append(
                        {
                            "agent_id": contrib.get("agent_id"),
                            "role_code": contrib.get("role", "contributor"),
                            "order": contrib.get("order", i),
                        }
                    )
                else:
                    # Simple agent_id string
                    contributor_data.append(
                        {
                            "agent_id": contrib,
                            "role_code": "contributor",
                            "order": i,
                        }
                    )
            django_data["contributor_data"] = contributor_data

        # Subject (array of labels or codes)
        if "subject" in data and data["subject"]:
            subject_codes = []
            for subj in data["subject"]:
                # Try to find by code first, then by label
                try:
                    s = Subject.objects.get(code=subj)
                    subject_codes.append(s.code)
                except Subject.DoesNotExist:
                    try:
                        s = Subject.objects.get(label__iexact=subj)
                        subject_codes.append(s.code)
                    except Subject.DoesNotExist:
                        # Let serializer handle error
                        subject_codes.append(subj)
            django_data["subject_codes"] = subject_codes

        # Genre (array of labels or codes)
        if "genre" in data and data["genre"]:
            genre_codes = []
            for gen in data["genre"]:
                try:
                    g = Genre.objects.get(code=gen)
                    genre_codes.append(g.code)
                except Genre.DoesNotExist:
                    try:
                        g = Genre.objects.get(label__iexact=gen)
                        genre_codes.append(g.code)
                    except Genre.DoesNotExist:
                        genre_codes.append(gen)
            django_data["genre_codes"] = genre_codes

        # Language (array of ISO codes)
        if "language" in data and data["language"]:
            language_codes = []
            for lang in data["language"]:
                try:
                    lg = Language.objects.get(code=lang)
                    language_codes.append(lg.code)
                except Language.DoesNotExist:
                    # Try by label
                    try:
                        lg = Language.objects.get(label__iexact=lang)
                        language_codes.append(lg.code)
                    except Language.DoesNotExist:
                        language_codes.append(lang)
            django_data["language_codes"] = language_codes

        # Rights (single value or array → single code)
        if "rights" in data and data["rights"]:
            rights_val = data["rights"]
            if isinstance(rights_val, list):
                rights_val = rights_val[0] if rights_val else None

            if rights_val:
                try:
                    rs = RightsStatement.objects.get(code=rights_val)
                    django_data["rights_code"] = rs.code
                except RightsStatement.DoesNotExist:
                    try:
                        rs = RightsStatement.objects.get(label__iexact=rights_val)
                        django_data["rights_code"] = rs.code
                    except RightsStatement.DoesNotExist:
                        django_data["rights_code"] = rights_val

        return django_data
