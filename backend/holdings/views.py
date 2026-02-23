from rest_framework import viewsets

from .models import AccessStatus, DistroStatus, Holding
from .serializers import (
    AccessStatusSerializer,
    DistroStatusSerializer,
    HoldingSerializer,
    HoldingWriteSerializer,
)


class HoldingViewSet(viewsets.ModelViewSet):
    queryset = Holding.objects.select_related("repository", "zine").all()
    search_fields = ["holding_id", "call_number", "barcode"]
    ordering_fields = ["holding_id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    lookup_field = "holding_id"

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return HoldingWriteSerializer
        return HoldingSerializer


class AccessStatusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AccessStatus.objects.all()
    serializer_class = AccessStatusSerializer
    lookup_field = "code"
    pagination_class = None


class DistroStatusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DistroStatus.objects.all()
    serializer_class = DistroStatusSerializer
    lookup_field = "code"
    pagination_class = None
