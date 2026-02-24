from rest_framework import serializers

from .models import (
    ExternalIdentifier,
    ExternalIdSystem,
    ExternalUri,
    ExternalUriType,
)


# ---------------------------------------------------------------------------
# Vocabulary serializers (read-only API endpoints)
# ---------------------------------------------------------------------------


class ExternalIdSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalIdSystem
        fields = [
            "code",
            "label",
            "description",
            "lookup_uri",
            "info_uri",
            "owner_uri",
            "applicable_to",
        ]


class ExternalUriTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalUriType
        fields = ["code", "label", "base_uri", "category", "icon"]


# ---------------------------------------------------------------------------
# Nested read serializers (embedded in Agent/Repository responses)
# ---------------------------------------------------------------------------


class ExternalIdentifierReadSerializer(serializers.ModelSerializer):
    system = serializers.CharField(source="system.code", read_only=True)

    class Meta:
        model = ExternalIdentifier
        fields = ["system", "value"]


class ExternalUriReadSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="uri_type.code", read_only=True)
    category = serializers.CharField(source="uri_type.category", read_only=True)

    class Meta:
        model = ExternalUri
        fields = ["type", "category", "uri"]


# ---------------------------------------------------------------------------
# Nested write serializers (accepted in Agent/Repository create/update)
# ---------------------------------------------------------------------------


class ExternalIdentifierWriteSerializer(serializers.Serializer):
    system_code = serializers.SlugRelatedField(
        slug_field="code",
        queryset=ExternalIdSystem.objects.all(),
        source="system",
    )
    value = serializers.CharField(max_length=255)


class ExternalUriWriteSerializer(serializers.Serializer):
    type_code = serializers.SlugRelatedField(
        slug_field="code",
        queryset=ExternalUriType.objects.all(),
        source="uri_type",
    )
    uri = serializers.URLField()
