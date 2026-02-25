from rest_framework import viewsets

from core.mixins import CSVPaginationBypassMixin

from .models import Agent, AgentKind, AgentRole
from .serializers import (
    AgentKindSerializer,
    AgentRoleSerializer,
    AgentSerializer,
    AgentWriteSerializer,
)


class AgentViewSet(CSVPaginationBypassMixin, viewsets.ModelViewSet):
    queryset = Agent.objects.select_related("kind", "location").prefetch_related(
        "external_ids__system", "external_uris__uri_type"
    ).all()
    search_fields = ["display_name", "aliases", "location__name"]
    ordering_fields = ["display_name", "created_at", "updated_at"]
    ordering = ["-created_at"]
    lookup_field = "agent_id"

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return AgentWriteSerializer
        return AgentSerializer


class AgentKindViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgentKind.objects.all()
    serializer_class = AgentKindSerializer
    lookup_field = "code"
    pagination_class = None


class AgentRoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgentRole.objects.all()
    serializer_class = AgentRoleSerializer
    lookup_field = "code"
    pagination_class = None
