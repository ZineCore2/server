from rest_framework import serializers

from geography.models import GeoPlace
from geography.serializers import GeoPlaceCompactSerializer

from .models import RepoKind, Repository


class RepoKindSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepoKind
        fields = ["code", "label"]


class RepositorySerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="repo_id")
    location = GeoPlaceCompactSerializer(read_only=True)

    class Meta:
        model = Repository
        fields = [
            "id",
            "name",
            "kind",
            "homepage",
            "address",
            "location",
            "marc_org_code",
            "isil",
            "ror_id",
            "access_policy",
            "hours",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class RepositoryWriteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="repo_id", required=False)
    location_geoname_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Repository
        fields = [
            "id",
            "name",
            "kind",
            "homepage",
            "address",
            "location_geoname_id",
            "marc_org_code",
            "isil",
            "ror_id",
            "access_policy",
            "hours",
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
