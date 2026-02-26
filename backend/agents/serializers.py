from rest_framework import serializers

from core.models import ExternalIdentifier, ExternalUri
from core.serializers import (
    ExternalIdentifierReadSerializer,
    ExternalIdentifierWriteSerializer,
    ExternalUriReadSerializer,
    ExternalUriWriteSerializer,
)
from geography.models import GeoPlace
from geography.serializers import GeoPlaceCompactSerializer

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
    location = GeoPlaceCompactSerializer(read_only=True)
    external_ids = ExternalIdentifierReadSerializer(many=True, read_only=True)
    external_uris = ExternalUriReadSerializer(many=True, read_only=True)

    class Meta:
        model = Agent
        fields = [
            "id",
            "kind",
            "display_name",
            "legal_name",
            "aliases",
            "location",
            "external_ids",
            "external_uris",
            "public",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AgentWriteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="agent_id", required=False)
    kind = serializers.SlugRelatedField(
        slug_field="code",
        queryset=AgentKind.objects.all(),
    )
    location_geoname_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )
    external_ids = ExternalIdentifierWriteSerializer(many=True, required=False)
    external_uris = ExternalUriWriteSerializer(many=True, required=False)

    class Meta:
        model = Agent
        fields = [
            "id",
            "kind",
            "display_name",
            "legal_name",
            "aliases",
            "location_geoname_id",
            "external_ids",
            "external_uris",
            "public",
            "notes",
        ]

    def validate_location_geoname_id(self, value):
        if value is not None:
            if not GeoPlace.objects.filter(geoname_id=value).exists():
                raise serializers.ValidationError(
                    f"GeoPlace with geoname_id {value} does not exist."
                )
        return value

    def _resolve_location(self, validated_data):
        geoname_id = validated_data.pop("location_geoname_id", None)
        if geoname_id is not None:
            validated_data["location"] = GeoPlace.objects.get(geoname_id=geoname_id)
        return validated_data

    def _save_external_ids(self, agent, external_ids_data):
        agent.external_ids.all().delete()
        for item in external_ids_data:
            ExternalIdentifier.objects.create(
                system=item["system"], value=item["value"], agent=agent
            )

    def _save_external_uris(self, agent, external_uris_data):
        agent.external_uris.all().delete()
        for item in external_uris_data:
            ExternalUri.objects.create(
                uri_type=item["uri_type"], uri=item["uri"], agent=agent
            )

    def create(self, validated_data):
        external_ids_data = validated_data.pop("external_ids", [])
        external_uris_data = validated_data.pop("external_uris", [])
        validated_data = self._resolve_location(validated_data)
        agent = super().create(validated_data)
        self._save_external_ids(agent, external_ids_data)
        self._save_external_uris(agent, external_uris_data)
        return agent

    def update(self, instance, validated_data):
        external_ids_data = validated_data.pop("external_ids", None)
        external_uris_data = validated_data.pop("external_uris", None)
        validated_data = self._resolve_location(validated_data)
        agent = super().update(instance, validated_data)
        if external_ids_data is not None:
            self._save_external_ids(agent, external_ids_data)
        if external_uris_data is not None:
            self._save_external_uris(agent, external_uris_data)
        return agent
