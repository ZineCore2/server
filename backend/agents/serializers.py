from rest_framework import serializers

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

    class Meta:
        model = Agent
        fields = [
            "id",
            "kind",
            "display_name",
            "legal_name",
            "aliases",
            "location",
            "website",
            "orcid",
            "wikidata_id",
            "public",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AgentWriteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="agent_id", required=False)
    location_geoname_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Agent
        fields = [
            "id",
            "kind",
            "display_name",
            "legal_name",
            "aliases",
            "location_geoname_id",
            "website",
            "orcid",
            "wikidata_id",
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

    def create(self, validated_data):
        validated_data = self._resolve_location(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self._resolve_location(validated_data)
        return super().update(instance, validated_data)
