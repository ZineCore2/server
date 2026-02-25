from rest_framework import viewsets

from core.mixins import CSVPaginationBypassMixin

from .models import RepoKind, Repository
from .serializers import RepoKindSerializer, RepositorySerializer, RepositoryWriteSerializer


class RepositoryViewSet(CSVPaginationBypassMixin, viewsets.ModelViewSet):
    queryset = Repository.objects.select_related("location", "kind").prefetch_related(
        "external_ids__system", "external_uris__uri_type"
    ).all()
    search_fields = ["name", "location__name"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["-created_at"]
    lookup_field = "repo_id"

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return RepositoryWriteSerializer
        return RepositorySerializer


class RepoKindViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RepoKind.objects.all()
    serializer_class = RepoKindSerializer
    lookup_field = "code"
    pagination_class = None
