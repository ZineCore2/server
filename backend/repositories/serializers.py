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

from .models import RepoKind, Repository


class RepoKindSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepoKind
        fields = ["code", "label"]


class RepositorySerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="repo_id")
    location = GeoPlaceCompactSerializer(read_only=True)
    external_ids = ExternalIdentifierReadSerializer(many=True, read_only=True)
    external_uris = ExternalUriReadSerializer(many=True, read_only=True)

    class Meta:
        model = Repository
        fields = [
            "id",
            "name",
            "kind",
            "address",
            "location",
            "external_ids",
            "external_uris",
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
    external_ids = ExternalIdentifierWriteSerializer(many=True, required=False)
    external_uris = ExternalUriWriteSerializer(many=True, required=False)

    class Meta:
        model = Repository
        fields = [
            "id",
            "name",
            "kind",
            "address",
            "location_geoname_id",
            "external_ids",
            "external_uris",
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

    def _save_external_ids(self, repo, external_ids_data):
        repo.external_ids.all().delete()
        for item in external_ids_data:
            ExternalIdentifier.objects.create(
                system=item["system"], value=item["value"], repository=repo
            )

    def _save_external_uris(self, repo, external_uris_data):
        repo.external_uris.all().delete()
        for item in external_uris_data:
            ExternalUri.objects.create(
                uri_type=item["uri_type"], uri=item["uri"], repository=repo
            )

    def create(self, validated_data):
        external_ids_data = validated_data.pop("external_ids", [])
        external_uris_data = validated_data.pop("external_uris", [])
        validated_data = self._resolve_location(validated_data)
        repo = super().create(validated_data)
        self._save_external_ids(repo, external_ids_data)
        self._save_external_uris(repo, external_uris_data)
        return repo

    def update(self, instance, validated_data):
        external_ids_data = validated_data.pop("external_ids", None)
        external_uris_data = validated_data.pop("external_uris", None)
        validated_data = self._resolve_location(validated_data)
        repo = super().update(instance, validated_data)
        if external_ids_data is not None:
            self._save_external_ids(repo, external_ids_data)
        if external_uris_data is not None:
            self._save_external_uris(repo, external_uris_data)
        return repo
