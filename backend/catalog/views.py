from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from core.mixins import CSVPaginationBypassMixin
from core.renderers import BibTeXRenderer, MARCXMLRenderer

from .models import Genre, Language, RightsStatement, Subject, Zine
from .serializers import (
    GenreSerializer,
    LanguageSerializer,
    RightsStatementSerializer,
    SubjectSerializer,
    ZineSerializer,
    ZineWriteSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["Zines"], summary="List zines"),
    retrieve=extend_schema(tags=["Zines"], summary="Retrieve a zine"),
    create=extend_schema(tags=["Zines"], summary="Create a zine"),
    update=extend_schema(tags=["Zines"], summary="Replace a zine"),
    partial_update=extend_schema(tags=["Zines"], summary="Partially update a zine"),
    destroy=extend_schema(tags=["Zines"], summary="Delete a zine"),
)
class ZineViewSet(CSVPaginationBypassMixin, viewsets.ModelViewSet):
    """
    CRUD operations for zine records (ZineCore2 profile).

    Supports JSON, JSON-LD, CSV, Dublin Core XML, Turtle, BibTeX, and MARCXML output.
    Use the `?format=` query parameter or `Accept` header to select a format.
    """

    queryset = Zine.objects.select_related(
        "place_of_publication", "rights_statement"
    ).prefetch_related("subjects", "genres").all()
    search_fields = ["title", "creator", "subjects__label"]
    ordering_fields = ["title", "created_at", "updated_at"]
    ordering = ["-created_at"]
    lookup_field = "zine_id"

    def get_renderers(self):
        return super().get_renderers() + [BibTeXRenderer(), MARCXMLRenderer()]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ZineWriteSerializer
        return ZineSerializer


@extend_schema(tags=["Vocabularies"])
class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """Subject headings controlled vocabulary (read-only)."""

    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    lookup_field = "code"
    search_fields = ["code", "label"]
    pagination_class = None


@extend_schema(tags=["Vocabularies"])
class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    """Genre terms controlled vocabulary (read-only)."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = "code"
    search_fields = ["code", "label"]
    pagination_class = None


@extend_schema(tags=["Vocabularies"])
class RightsStatementViewSet(viewsets.ReadOnlyModelViewSet):
    """Rights statements controlled vocabulary (read-only)."""

    queryset = RightsStatement.objects.all()
    serializer_class = RightsStatementSerializer
    lookup_field = "code"
    search_fields = ["code", "label"]
    pagination_class = None


@extend_schema(tags=["Vocabularies"])
class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    """ISO 639-1 language codes (read-only)."""

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    lookup_field = "code"
    search_fields = ["code", "label"]
    pagination_class = None
