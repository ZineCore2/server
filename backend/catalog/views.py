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


class ZineViewSet(CSVPaginationBypassMixin, viewsets.ModelViewSet):
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


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    lookup_field = "code"
    search_fields = ["code", "label"]
    pagination_class = None


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = "code"
    search_fields = ["code", "label"]
    pagination_class = None


class RightsStatementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RightsStatement.objects.all()
    serializer_class = RightsStatementSerializer
    lookup_field = "code"
    search_fields = ["code", "label"]
    pagination_class = None


class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    lookup_field = "code"
    search_fields = ["code", "label"]
    pagination_class = None
