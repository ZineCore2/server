from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from core.mixins import CSVPaginationBypassMixin

from .models import Agent, AgentKind, AgentRole
from .serializers import (
    AgentKindSerializer,
    AgentRoleSerializer,
    AgentSerializer,
    AgentWriteSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["Agents"], summary="List agents"),
    retrieve=extend_schema(tags=["Agents"], summary="Retrieve an agent"),
    create=extend_schema(tags=["Agents"], summary="Create an agent"),
    update=extend_schema(tags=["Agents"], summary="Replace an agent"),
    partial_update=extend_schema(tags=["Agents"], summary="Partially update an agent"),
    destroy=extend_schema(tags=["Agents"], summary="Delete an agent"),
)
class AgentViewSet(CSVPaginationBypassMixin, viewsets.ModelViewSet):
    """
    CRUD operations for agent records (AgentCore2 profile).

    Agents represent people, organizations, or groups associated with zines
    as creators, contributors, or publishers.
    """

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


@extend_schema(tags=["Vocabularies"])
class AgentKindViewSet(viewsets.ReadOnlyModelViewSet):
    """Agent kind controlled vocabulary (read-only)."""

    queryset = AgentKind.objects.all()
    serializer_class = AgentKindSerializer
    lookup_field = "code"
    pagination_class = None


@extend_schema(tags=["Vocabularies"])
class AgentRoleViewSet(viewsets.ReadOnlyModelViewSet):
    """Agent role controlled vocabulary (read-only)."""

    queryset = AgentRole.objects.all()
    serializer_class = AgentRoleSerializer
    lookup_field = "code"
    pagination_class = None
