from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from core.mixins import CSVPaginationBypassMixin

from .models import RepoKind, Repository
from .serializers import RepoKindSerializer, RepositorySerializer, RepositoryWriteSerializer


@extend_schema_view(
    list=extend_schema(tags=["Repositories"], summary="List repositories"),
    retrieve=extend_schema(tags=["Repositories"], summary="Retrieve a repository"),
    create=extend_schema(tags=["Repositories"], summary="Create a repository"),
    update=extend_schema(tags=["Repositories"], summary="Replace a repository"),
    partial_update=extend_schema(tags=["Repositories"], summary="Partially update a repository"),
    destroy=extend_schema(tags=["Repositories"], summary="Delete a repository"),
)
class RepositoryViewSet(CSVPaginationBypassMixin, viewsets.ModelViewSet):
    """
    CRUD operations for repository records (RepoCore2 profile).

    Repositories are physical or digital collections that hold zines.
    """

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


@extend_schema(tags=["Vocabularies"])
class RepoKindViewSet(viewsets.ReadOnlyModelViewSet):
    """Repository kind controlled vocabulary (read-only)."""

    queryset = RepoKind.objects.all()
    serializer_class = RepoKindSerializer
    lookup_field = "code"
    pagination_class = None
