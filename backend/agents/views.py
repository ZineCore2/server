from rest_framework import viewsets

from .models import Agent, AgentKind, AgentRole
from .serializers import AgentKindSerializer, AgentRoleSerializer, AgentSerializer


class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    search_fields = ["display_name", "aliases"]
    ordering_fields = ["display_name", "created_at", "updated_at"]
    ordering = ["-created_at"]
    lookup_field = "agent_id"


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
