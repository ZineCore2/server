from rest_framework import serializers

from .models import RepoKind, Repository


class RepoKindSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepoKind
        fields = ["code", "label"]


class RepositorySerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="repo_id")

    class Meta:
        model = Repository
        fields = [
            "id",
            "name",
            "kind",
            "homepage",
            "city",
            "region",
            "country",
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
