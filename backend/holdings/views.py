from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from core.mixins import CSVPaginationBypassMixin
from core.renderers import MARCXMLRenderer

from .models import AccessStatus, DistroStatus, Holding
from .serializers import (
    AccessStatusSerializer,
    DistroStatusSerializer,
    HoldingSerializer,
    HoldingWriteSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["Holdings"], summary="List holdings"),
    retrieve=extend_schema(tags=["Holdings"], summary="Retrieve a holding"),
    create=extend_schema(tags=["Holdings"], summary="Create a holding"),
    update=extend_schema(tags=["Holdings"], summary="Replace a holding"),
    partial_update=extend_schema(tags=["Holdings"], summary="Partially update a holding"),
    destroy=extend_schema(tags=["Holdings"], summary="Delete a holding"),
)
class HoldingViewSet(CSVPaginationBypassMixin, viewsets.ModelViewSet):
    """
    CRUD operations for holding records (HoldingCore2 profile).

    Holdings link a zine to the repository that holds it, with location
    and access/distribution status information.
    """

    queryset = Holding.objects.select_related("repository", "zine").all()
    search_fields = ["call_number", "barcode"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_renderers(self):
        return super().get_renderers() + [MARCXMLRenderer()]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return HoldingWriteSerializer
        return HoldingSerializer


@extend_schema(tags=["Vocabularies"])
class AccessStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """Access status controlled vocabulary (read-only)."""

    queryset = AccessStatus.objects.all()
    serializer_class = AccessStatusSerializer
    lookup_field = "code"
    pagination_class = None


@extend_schema(tags=["Vocabularies"])
class DistroStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """Distribution status controlled vocabulary (read-only)."""

    queryset = DistroStatus.objects.all()
    serializer_class = DistroStatusSerializer
    lookup_field = "code"
    pagination_class = None
