from rest_framework import serializers

from .models import Agent, AgentKind, AgentRole


class AgentKindSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentKind
        fields = ["code", "label"]


class AgentRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentRole
        fields = ["code", "label"]


class AgentSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="agent_id")

    class Meta:
        model = Agent
        fields = [
            "id",
            "kind",
            "display_name",
            "legal_name",
            "aliases",
            "roles",
            "website",
            "orcid",
            "wikidata_id",
            "public",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
