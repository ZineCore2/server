from rest_framework import viewsets

from .models import Genre, RightsStatement, Subject, Zine
from .serializers import (
    GenreSerializer,
    RightsStatementSerializer,
    SubjectSerializer,
    ZineSerializer,
    ZineWriteSerializer,
)


class ZineViewSet(viewsets.ModelViewSet):
    queryset = Zine.objects.prefetch_related("subjects", "genres").all()
    search_fields = ["title", "creator", "subject"]
    ordering_fields = ["title", "created_at", "updated_at"]
    ordering = ["-created_at"]
    lookup_field = "zine_id"

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
