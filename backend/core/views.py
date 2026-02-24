from rest_framework import viewsets

from .models import ExternalIdSystem, ExternalUriType
from .serializers import ExternalIdSystemSerializer, ExternalUriTypeSerializer


class ExternalIdSystemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExternalIdSystem.objects.all()
    serializer_class = ExternalIdSystemSerializer
    lookup_field = "code"
    pagination_class = None


class ExternalUriTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExternalUriType.objects.all()
    serializer_class = ExternalUriTypeSerializer
    lookup_field = "code"
    pagination_class = None
