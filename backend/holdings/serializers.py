from rest_framework import serializers

from catalog.models import Zine
from repositories.models import Repository

from .models import AccessStatus, DistroStatus, Holding


class AccessStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessStatus
        fields = ["code", "label"]


class DistroStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistroStatus
        fields = ["code", "label"]


class HoldingSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="holding_id")
    repository_id = serializers.CharField(source="repository.repo_id", read_only=True)
    zine_id = serializers.CharField(source="zine.zine_id", read_only=True)

    class Meta:
        model = Holding
        fields = [
            "id",
            "repository_id",
            "zine_id",
            "call_number",
            "location",
            "access_status",
            "condition",
            "copy_count",
            "barcode",
            "digital_available",
            "digital_url",
            "distro_status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class HoldingWriteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="holding_id")
    repository_id = serializers.SlugRelatedField(
        source="repository",
        slug_field="repo_id",
        queryset=Repository.objects.all(),
    )
    zine_id = serializers.SlugRelatedField(
        source="zine",
        slug_field="zine_id",
        queryset=Zine.objects.all(),
    )

    class Meta:
        model = Holding
        fields = [
            "id",
            "repository_id",
            "zine_id",
            "call_number",
            "location",
            "access_status",
            "condition",
            "copy_count",
            "barcode",
            "digital_available",
            "digital_url",
            "distro_status",
            "notes",
        ]
