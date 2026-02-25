import csv
import io
import json
import xml.etree.ElementTree as ET

from rest_framework.renderers import BaseRenderer

# ---------------------------------------------------------------------------
# Dublin Core XML namespace constants
# ---------------------------------------------------------------------------

_NS_OAI_DC = "http://www.openarchives.org/OAI/2.0/oai_dc/"
_NS_DCTERMS = "http://purl.org/dc/terms/"
_NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
_NS_ZINE = "https://zinecore.org/v2/zine#"
_NS_AGENT = "https://zinecore.org/v2/agent#"
_NS_HOLDING = "https://zinecore.org/v2/holding#"
_NS_REPO = "https://zinecore.org/v2/repo#"
_NS_FOAF = "http://xmlns.com/foaf/0.1/"
_NS_SCHEMA = "https://schema.org/"


def _q(ns, local):
    return f"{{{ns}}}{local}"


# Field maps: ordered (field_name, clark_tag) pairs.
# Fields absent from the list are skipped in XML output.
_ZINE_FIELDS = [
    ("id", _q(_NS_DCTERMS, "identifier")),
    ("title", _q(_NS_DCTERMS, "title")),
    ("series_title", _q(_NS_DCTERMS, "isPartOf")),
    ("issue_designation", _q(_NS_ZINE, "issueDesignation")),
    ("edition_statement", _q(_NS_ZINE, "editionStatement")),
    ("alternative_title", _q(_NS_DCTERMS, "alternative")),
    ("creator", _q(_NS_DCTERMS, "creator")),
    ("contributor", _q(_NS_DCTERMS, "contributor")),
    ("subject", _q(_NS_DCTERMS, "subject")),
    ("genre", _q(_NS_ZINE, "genre")),
    ("abstract", _q(_NS_DCTERMS, "description")),
    ("table_of_contents", _q(_NS_DCTERMS, "tableOfContents")),
    ("public_notes", _q(_NS_ZINE, "publicNotes")),
    ("publisher", _q(_NS_DCTERMS, "publisher")),
    ("publish_date", _q(_NS_DCTERMS, "date")),
    ("physical_dimensions", _q(_NS_DCTERMS, "format")),
    ("number_of_pages", _q(_NS_DCTERMS, "format")),
    ("format", _q(_NS_DCTERMS, "format")),
    ("binding_features", _q(_NS_ZINE, "binding")),
    ("language", _q(_NS_DCTERMS, "language")),
    ("place_of_publication", _q(_NS_DCTERMS, "coverage")),
    ("coverage", _q(_NS_DCTERMS, "coverage")),
    ("source", _q(_NS_DCTERMS, "source")),
    ("relation", _q(_NS_DCTERMS, "relation")),
    ("rights", _q(_NS_DCTERMS, "rights")),
    ("identifier", _q(_NS_DCTERMS, "identifier")),
]

_AGENT_FIELDS = [
    ("id", _q(_NS_AGENT, "agentId")),
    ("kind", _q(_NS_AGENT, "agentKind")),
    ("display_name", _q(_NS_FOAF, "name")),
    ("legal_name", _q(_NS_SCHEMA, "legalName")),
    ("aliases", _q(_NS_SCHEMA, "alternateName")),
    ("location", _q(_NS_DCTERMS, "coverage")),
    ("notes", _q(_NS_DCTERMS, "description")),
]

_REPO_FIELDS = [
    ("id", _q(_NS_REPO, "repoId")),
    ("name", _q(_NS_DCTERMS, "title")),
    ("kind", _q(_NS_REPO, "repoKind")),
    ("location", _q(_NS_DCTERMS, "coverage")),
    ("access_policy", _q(_NS_DCTERMS, "rights")),
    ("hours", _q(_NS_REPO, "hours")),
    ("notes", _q(_NS_DCTERMS, "description")),
]

_HOLDING_FIELDS = [
    ("id", _q(_NS_HOLDING, "holdingId")),
    ("repository_id", _q(_NS_HOLDING, "repository")),
    ("zine_id", _q(_NS_HOLDING, "zine")),
    ("call_number", _q(_NS_HOLDING, "callNumber")),
    ("location", _q(_NS_HOLDING, "location")),
    ("access_status", _q(_NS_HOLDING, "accessStatus")),
    ("condition", _q(_NS_HOLDING, "condition")),
    ("copy_count", _q(_NS_HOLDING, "copyCount")),
    ("barcode", _q(_NS_HOLDING, "barcode")),
    ("digital_available", _q(_NS_HOLDING, "digitalAvailable")),
    ("digital_url", _q(_NS_HOLDING, "digitalUrl")),
    ("distro_status", _q(_NS_HOLDING, "distroStatus")),
    ("notes", _q(_NS_DCTERMS, "description")),
]

_DC_XML_PROFILE_MAP = {
    "ZineViewSet": {
        "fields": _ZINE_FIELDS,
        "namespaces": {
            "oai_dc": _NS_OAI_DC,
            "dcterms": _NS_DCTERMS,
            "zine": _NS_ZINE,
        },
    },
    "AgentViewSet": {
        "fields": _AGENT_FIELDS,
        "namespaces": {
            "oai_dc": _NS_OAI_DC,
            "dcterms": _NS_DCTERMS,
            "zine-agent": _NS_AGENT,
            "foaf": _NS_FOAF,
            "schema": _NS_SCHEMA,
        },
    },
    "RepositoryViewSet": {
        "fields": _REPO_FIELDS,
        "namespaces": {
            "oai_dc": _NS_OAI_DC,
            "dcterms": _NS_DCTERMS,
            "zine-repo": _NS_REPO,
        },
    },
    "HoldingViewSet": {
        "fields": _HOLDING_FIELDS,
        "namespaces": {
            "oai_dc": _NS_OAI_DC,
            "dcterms": _NS_DCTERMS,
            "zine-holding": _NS_HOLDING,
        },
    },
}


def _to_text_values(value):
    """Return a list of text strings for an XML element from a serializer value."""
    if value is None:
        return []
    if isinstance(value, bool):
        return [str(value).lower()]
    if isinstance(value, (int, float)):
        return [str(value)]
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        texts = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, dict):
                text = item.get("name") or item.get("label") or item.get("display_name")
                if text:
                    texts.append(str(text))
            else:
                texts.append(str(item))
        return texts
    if isinstance(value, dict):
        text = value.get("name") or value.get("label") or value.get("display_name")
        return [str(text)] if text else []
    return [str(value)]

PROFILE_MAP = {
    "ZineViewSet": {
        "context": "https://zinecore.org/v2/zine",
        "type": "Zine",
        "url_segment": "zines",
    },
    "AgentViewSet": {
        "context": "https://zinecore.org/v2/agent",
        "type": "Agent",
        "url_segment": "agents",
    },
    "RepositoryViewSet": {
        "context": "https://zinecore.org/v2/repo",
        "type": "Repository",
        "url_segment": "repositories",
    },
    "HoldingViewSet": {
        "context": "https://zinecore.org/v2/holding",
        "type": "Holding",
        "url_segment": "holdings",
    },
}


class JSONLDRenderer(BaseRenderer):
    media_type = "application/ld+json"
    format = "jsonld"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""

        renderer_context = renderer_context or {}
        view = renderer_context.get("view")
        request = renderer_context.get("request")

        view_name = view.__class__.__name__ if view else ""
        profile = PROFILE_MAP.get(view_name)

        if profile is None:
            return json.dumps(data, ensure_ascii=False).encode("utf-8")

        if "results" in data:
            ld_data = self._render_paginated_list(data, profile, request)
        elif isinstance(data, list):
            ld_data = self._render_list(data, profile, request)
        else:
            ld_data = self._render_detail(data, profile, request)

        return json.dumps(ld_data, ensure_ascii=False, indent=2).encode("utf-8")

    def _render_detail(self, data, profile, request):
        result = {
            "@context": profile["context"],
            "@type": profile["type"],
        }
        if request:
            result["@id"] = request.build_absolute_uri()
        result.update(data)
        return result

    def _render_paginated_list(self, data, profile, request):
        ld_data = {
            "@context": profile["context"],
            "@graph": [
                self._item_with_id(item, profile, request)
                for item in data.get("results", [])
            ],
        }
        if data.get("count") is not None:
            ld_data["totalItems"] = data["count"]
        if data.get("next"):
            ld_data["next"] = data["next"]
        if data.get("previous"):
            ld_data["previous"] = data["previous"]
        return ld_data

    def _render_list(self, data, profile, request):
        return {
            "@context": profile["context"],
            "@graph": [
                self._item_with_id(item, profile, request) for item in data
            ],
        }

    def _item_with_id(self, item, profile, request):
        result = {"@type": profile["type"]}
        item_id = item.get("id")
        if request and item_id is not None:
            result["@id"] = request.build_absolute_uri(
                f"/api/{profile['url_segment']}/{item_id}/"
            )
        result.update(item)
        return result


def _flatten_value(value):
    if value is None:
        return ""
    if isinstance(value, list):
        if not value:
            return ""
        if all(isinstance(v, (str, int, float, bool)) or v is None for v in value):
            return "|".join("" if v is None else str(v) for v in value)
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


class CSVRenderer(BaseRenderer):
    media_type = "text/csv"
    format = "csv"
    charset = "utf-8"

    FILENAME_MAP = {
        "ZineViewSet": "zines",
        "AgentViewSet": "agents",
        "RepositoryViewSet": "repositories",
        "HoldingViewSet": "holdings",
    }

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""

        renderer_context = renderer_context or {}
        view = renderer_context.get("view")
        response = renderer_context.get("response")

        view_name = view.__class__.__name__ if view else ""
        filename = self.FILENAME_MAP.get(view_name, "export")

        if response is not None:
            response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'

        if "results" in data:
            rows = data["results"]
        elif isinstance(data, list):
            rows = data
        else:
            rows = [data]

        if not rows:
            return b""

        output = io.StringIO()
        writer = csv.writer(output)
        headers = list(rows[0].keys())
        writer.writerow(headers)
        for row in rows:
            writer.writerow([_flatten_value(row.get(h)) for h in headers])

        return output.getvalue().encode(self.charset)


class DublinCoreXMLRenderer(BaseRenderer):
    media_type = "application/xml"
    format = "dc-xml"
    charset = "utf-8"

    _OAI_DC_TAG = _q(_NS_OAI_DC, "dc")
    _SCHEMA_LOCATION = (
        f"{_NS_OAI_DC} http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
    )

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""

        renderer_context = renderer_context or {}
        view = renderer_context.get("view")

        view_name = view.__class__.__name__ if view else ""
        profile = _DC_XML_PROFILE_MAP.get(view_name)

        # Register namespace prefixes globally for ET serialisation.
        ET.register_namespace("xsi", _NS_XSI)
        if profile:
            for prefix, uri in profile["namespaces"].items():
                ET.register_namespace(prefix, uri)

        total: int | None = None
        if "results" in data:
            records, is_list = data["results"], True
            total = data.get("count")
        elif isinstance(data, list):
            records, is_list = data, True
        else:
            records, is_list = [data], False

        if is_list:
            root = ET.Element("records")
            if total is not None:
                root.set("totalItems", str(total))
            for record in records:
                root.append(self._build_dc(record, profile))
            output = root
        else:
            output = self._build_dc(records[0], profile)

        xml_str = ET.tostring(output, encoding="unicode")
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'.encode(self.charset)

    def _build_dc(self, record, profile):
        attrs = {_q(_NS_XSI, "schemaLocation"): self._SCHEMA_LOCATION}
        dc_el = ET.Element(self._OAI_DC_TAG, attrs)

        if profile is None:
            return dc_el

        for field, tag in profile["fields"]:
            for text in _to_text_values(record.get(field)):
                child = ET.SubElement(dc_el, tag)
                child.text = text

        return dc_el
