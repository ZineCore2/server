from rest_framework import viewsets

from .models import RepoKind, Repository
from .serializers import RepoKindSerializer, RepositorySerializer


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer
    search_fields = ["name", "city", "country"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["-created_at"]
    lookup_field = "repo_id"


class RepoKindViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RepoKind.objects.all()
    serializer_class = RepoKindSerializer
    lookup_field = "code"
    pagination_class = None
