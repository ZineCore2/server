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


# ---------------------------------------------------------------------------
# BibTeX renderer — issue #5 (Zines only)
# ---------------------------------------------------------------------------

_BIBTEX_ESCAPE = str.maketrans(
    {"&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}"}
)


def _bibtex_escape(text):
    return str(text).translate(_BIBTEX_ESCAPE)


class BibTeXRenderer(BaseRenderer):
    media_type = "application/x-bibtex"
    format = "bibtex"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""

        if "results" in data:
            records = data["results"]
        elif isinstance(data, list):
            records = data
        else:
            records = [data]

        return "\n\n".join(self._build_entry(r) for r in records).encode(self.charset)

    def _build_entry(self, record):
        cite_key = record.get("id", "unknown")
        fields = {}

        if title := record.get("title"):
            fields["title"] = _bibtex_escape(title)

        creators = record.get("creator") or []
        if creators:
            fields["author"] = " and ".join(_bibtex_escape(c) for c in creators)

        if publish_date := record.get("publish_date"):
            fields["year"] = str(publish_date)[:4]

        publishers = record.get("publisher") or []
        if publishers:
            fields["publisher"] = _bibtex_escape(", ".join(publishers))

        if abstract := record.get("abstract"):
            fields["note"] = _bibtex_escape(abstract)

        howpublished = record.get("format") or record.get("physical_dimensions")
        if howpublished:
            fields["howpublished"] = _bibtex_escape(howpublished)

        languages = record.get("language") or []
        if languages:
            fields["language"] = ", ".join(languages)

        lines = [f"@misc{{{cite_key},"]
        for key, val in fields.items():
            lines.append(f"  {key} = {{{val}}},")
        lines.append("}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# RDF/Turtle renderer — issue #6 (all four profiles)
# ---------------------------------------------------------------------------

_TURTLE_PROFILE_MAP = {
    "ZineViewSet": {
        "fields": _ZINE_FIELDS,
        "type_prefixed": "zine:Zine",
        "url_segment": "zines",
        "namespaces": {"dcterms": _NS_DCTERMS, "zine": _NS_ZINE},
    },
    "AgentViewSet": {
        "fields": _AGENT_FIELDS,
        "type_prefixed": "zine-agent:Agent",
        "url_segment": "agents",
        "namespaces": {
            "dcterms": _NS_DCTERMS,
            "zine-agent": _NS_AGENT,
            "foaf": _NS_FOAF,
            "schema": _NS_SCHEMA,
        },
    },
    "RepositoryViewSet": {
        "fields": _REPO_FIELDS,
        "type_prefixed": "zine-repo:Repository",
        "url_segment": "repositories",
        "namespaces": {"dcterms": _NS_DCTERMS, "zine-repo": _NS_REPO},
    },
    "HoldingViewSet": {
        "fields": _HOLDING_FIELDS,
        "type_prefixed": "zine-holding:Holding",
        "url_segment": "holdings",
        "namespaces": {"dcterms": _NS_DCTERMS, "zine-holding": _NS_HOLDING},
    },
}


def _turtle_escape(text):
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def _clark_to_prefixed(clark_tag, uri_to_prefix):
    for uri, prefix in uri_to_prefix.items():
        tag_prefix = f"{{{uri}}}"
        if clark_tag.startswith(tag_prefix):
            return f"{prefix}:{clark_tag[len(tag_prefix):]}"
    return f"<{clark_tag}>"


def _build_turtle_resource(subject_iri, record, profile):
    uri_to_prefix = {uri: prefix for prefix, uri in profile["namespaces"].items()}

    props: dict[str, list[str]] = {}
    for field, clark_tag in profile["fields"]:
        texts = _to_text_values(record.get(field))
        if texts:
            prop = _clark_to_prefixed(clark_tag, uri_to_prefix)
            props.setdefault(prop, []).extend(texts)

    type_line = f"    a {profile['type_prefixed']}"
    if not props:
        return f"<{subject_iri}>\n{type_line} ."

    prop_lines = [type_line]
    for prop, values in props.items():
        val_str = ", ".join(f'"{_turtle_escape(v)}"' for v in values)
        prop_lines.append(f"    {prop} {val_str}")

    return f"<{subject_iri}>\n" + " ;\n".join(prop_lines) + " ."


class TurtleRenderer(BaseRenderer):
    media_type = "text/turtle"
    format = "turtle"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""

        renderer_context = renderer_context or {}
        view = renderer_context.get("view")
        request = renderer_context.get("request")

        view_name = view.__class__.__name__ if view else ""
        profile = _TURTLE_PROFILE_MAP.get(view_name)
        if profile is None:
            return b""

        prefix_lines = [
            f"@prefix {prefix}: <{uri}> ."
            for prefix, uri in profile["namespaces"].items()
        ]
        header = "\n".join(prefix_lines) + "\n"

        if "results" in data:
            records, is_list = data["results"], True
        elif isinstance(data, list):
            records, is_list = data, True
        else:
            records, is_list = [data], False

        resources = []
        for record in records:
            if is_list:
                item_id = record.get("id")
                if request and item_id is not None:
                    iri = request.build_absolute_uri(
                        f"/api/{profile['url_segment']}/{item_id}/"
                    )
                else:
                    iri = str(item_id or "unknown")
            else:
                iri = request.build_absolute_uri() if request else ""
            resources.append(_build_turtle_resource(iri, record, profile))

        body = "\n\n".join(resources)
        return (header + "\n" + body + "\n").encode(self.charset)


# ---------------------------------------------------------------------------
# MARCXML renderer — issue #7 (Zines and Holdings)
# ---------------------------------------------------------------------------

_MARC_NS = "http://www.loc.gov/MARC21/slim"
_MARC_SCHEMA_LOC = (
    "http://www.loc.gov/MARC21/slim "
    "http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"
)
_MARC_LEADER_BIB = "00000nam a2200000 a 4500"
_MARC_LEADER_HOL = "00000nx  a2200000 a 4500"

_ISO639_1_TO_MARC = {
    "en": "eng", "fr": "fre", "de": "ger", "es": "spa", "it": "ita",
    "pt": "por", "nl": "dut", "ja": "jpn", "zh": "chi", "ko": "kor",
    "ru": "rus", "ar": "ara", "sv": "swe", "no": "nor", "da": "dan",
    "fi": "fin", "pl": "pol", "cs": "cze", "hu": "hun", "tr": "tur",
}


def _mq(local):
    return f"{{{_MARC_NS}}}{local}"


def _marc_008(record):
    from datetime import date

    today = date.today().strftime("%y%m%d")
    publish_date = record.get("publish_date") or ""
    year = str(publish_date)[:4].ljust(4)[:4]

    place = record.get("place_of_publication")
    country = (
        (place.get("country_code") or "   ")[:2].lower().ljust(3)[:3]
        if isinstance(place, dict)
        else "   "
    )

    languages = record.get("language") or []
    lang_code = languages[0] if languages else ""
    marc_lang = _ISO639_1_TO_MARC.get(lang_code, (lang_code[:3] or "   ").ljust(3)[:3])

    # 40 chars: positions 00-39
    return f"{today}s{year}    {country}           000 0 {marc_lang} d"


def _marc_add_datafield(rec_el, marc_tag, ind1, ind2, subfields):
    df = ET.SubElement(
        rec_el, _mq("datafield"), {"tag": marc_tag, "ind1": ind1, "ind2": ind2}
    )
    for code, text in subfields:
        if text is not None and str(text):
            sf = ET.SubElement(df, _mq("subfield"), {"code": code})
            sf.text = str(text)


def _build_marc_zine(record):
    rec_el = ET.Element(_mq("record"))
    ET.SubElement(rec_el, _mq("leader")).text = _MARC_LEADER_BIB
    ET.SubElement(rec_el, _mq("controlfield"), {"tag": "001"}).text = str(record.get("id", ""))
    ET.SubElement(rec_el, _mq("controlfield"), {"tag": "008"}).text = _marc_008(record)

    # 041 — language
    languages = record.get("language") or []
    if languages:
        df041 = ET.SubElement(rec_el, _mq("datafield"), {"tag": "041", "ind1": " ", "ind2": " "})
        for lang in languages:
            sf = ET.SubElement(df041, _mq("subfield"), {"code": "a"})
            sf.text = _ISO639_1_TO_MARC.get(lang, lang[:3].ljust(3))

    # 100/700 — creators
    creators = record.get("creator") or []
    if creators:
        _marc_add_datafield(rec_el, "100", "1", " ", [("a", creators[0])])
    for creator in creators[1:]:
        _marc_add_datafield(rec_el, "700", "1", " ", [("a", creator)])

    # 245 — title
    if title := record.get("title"):
        _marc_add_datafield(rec_el, "245", "1", "0", [("a", title)])

    # 490 — series/issue
    series_title = record.get("series_title")
    issue_designation = record.get("issue_designation")
    if series_title or issue_designation:
        subfields = []
        if series_title:
            subfields.append(("a", series_title))
        if issue_designation:
            subfields.append(("v", issue_designation))
        _marc_add_datafield(rec_el, "490", "0", " ", subfields)

    # 264 — publication
    place = record.get("place_of_publication")
    place_name = place.get("name") if isinstance(place, dict) else None
    publishers = record.get("publisher") or []
    publish_date = record.get("publish_date")
    pub_subfields = []
    if place_name:
        pub_subfields.append(("a", place_name))
    if publishers:
        pub_subfields.append(("b", publishers[0]))
    if publish_date:
        pub_subfields.append(("c", str(publish_date)[:4]))
    if pub_subfields:
        _marc_add_datafield(rec_el, "264", " ", "1", pub_subfields)

    # 300 — physical description
    phys_subfields = []
    if pages := record.get("number_of_pages"):
        phys_subfields.append(("a", str(pages)))
    if dims := record.get("physical_dimensions"):
        phys_subfields.append(("c", dims))
    if phys_subfields:
        _marc_add_datafield(rec_el, "300", " ", " ", phys_subfields)

    # 520 — abstract
    if abstract := record.get("abstract"):
        _marc_add_datafield(rec_el, "520", " ", " ", [("a", abstract)])

    # 650 — subjects (prefer full objects, fall back to flat list)
    subjects = record.get("subjects") or []
    subject_labels = (
        [s.get("label") for s in subjects if isinstance(s, dict) and s.get("label")]
        if subjects
        else record.get("subject") or []
    )
    for label in subject_labels:
        _marc_add_datafield(rec_el, "650", " ", "7", [("a", label)])

    # 655 — genres
    genres = record.get("genres") or []
    genre_labels = (
        [g.get("label") for g in genres if isinstance(g, dict) and g.get("label")]
        if genres
        else record.get("genre") or []
    )
    for label in genre_labels:
        _marc_add_datafield(rec_el, "655", " ", "7", [("a", label)])

    # 540 — rights
    for rights in record.get("rights") or []:
        _marc_add_datafield(rec_el, "540", " ", " ", [("a", rights)])

    # 020/024 — identifiers
    for identifier in record.get("identifier") or []:
        id_str = str(identifier)
        if id_str.upper().startswith("ISBN"):
            isbn = id_str.split(":", 1)[-1].strip() if ":" in id_str else id_str[4:].strip()
            _marc_add_datafield(rec_el, "020", " ", " ", [("a", isbn)])
        else:
            _marc_add_datafield(rec_el, "024", "8", " ", [("a", id_str)])

    return rec_el


def _build_marc_holding(record):
    rec_el = ET.Element(_mq("record"))
    ET.SubElement(rec_el, _mq("leader")).text = _MARC_LEADER_HOL
    ET.SubElement(rec_el, _mq("controlfield"), {"tag": "001"}).text = str(record.get("id", ""))

    # 004 — link to bibliographic record
    if zine_id := record.get("zine_id"):
        ET.SubElement(rec_el, _mq("controlfield"), {"tag": "004"}).text = str(zine_id)

    # 852 — location/call number/barcode
    subfields_852 = []
    if repo_id := record.get("repository_id"):
        subfields_852.append(("a", repo_id))
    if location := record.get("location"):
        subfields_852.append(("b", str(location)))
    if call_number := record.get("call_number"):
        subfields_852.append(("c", str(call_number)))
    if barcode := record.get("barcode"):
        subfields_852.append(("p", str(barcode)))
    if subfields_852:
        _marc_add_datafield(rec_el, "852", " ", " ", subfields_852)

    # 856 — digital URL
    if record.get("digital_available") and (url := record.get("digital_url")):
        _marc_add_datafield(rec_el, "856", "4", "0", [("u", url)])

    return rec_el


class MARCXMLRenderer(BaseRenderer):
    media_type = "application/marcxml+xml"
    format = "marcxml"
    charset = "utf-8"

    _BUILDERS = {
        "ZineViewSet": _build_marc_zine,
        "HoldingViewSet": _build_marc_holding,
    }

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""

        renderer_context = renderer_context or {}
        view = renderer_context.get("view")
        view_name = view.__class__.__name__ if view else ""
        builder = self._BUILDERS.get(view_name)

        ET.register_namespace("", _MARC_NS)
        ET.register_namespace("xsi", _NS_XSI)

        if "results" in data:
            records, is_list = data["results"], True
        elif isinstance(data, list):
            records, is_list = data, True
        else:
            records, is_list = [data], False

        if is_list:
            root = ET.Element(
                _mq("collection"),
                {_q(_NS_XSI, "schemaLocation"): _MARC_SCHEMA_LOC},
            )
            for record in records:
                if builder:
                    root.append(builder(record))
            output = root
        else:
            output = builder(records[0]) if builder else ET.Element(_mq("record"))

        xml_str = ET.tostring(output, encoding="unicode")
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'.encode(self.charset)
