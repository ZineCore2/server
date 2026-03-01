from rest_framework import serializers

from agents.models import Agent
from agents.serializers import AgentSerializer
from catalog.models import Zine
from repositories.models import Repository
from repositories.serializers import RepositorySerializer

from .models import Profile, ProfileAgentClaim, ProfileRepositoryClaim, SubmissionStatus, ZineSubmission


class SubmissionStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionStatus
        fields = ["code", "label"]


class ProfileAgentClaimSerializer(serializers.ModelSerializer):
    """Read serializer for ProfileAgentClaim with nested agent."""

    agent = AgentSerializer(read_only=True)

    class Meta:
        model = ProfileAgentClaim
        fields = [
            "id",
            "agent",
            "status",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ProfileAgentClaimWriteSerializer(serializers.ModelSerializer):
    """Write serializer for ProfileAgentClaim using agent_id for FK resolution."""

    agent_id = serializers.SlugRelatedField(
        slug_field="agent_id",
        queryset=Agent.objects.all(),
        source="agent",
    )

    class Meta:
        model = ProfileAgentClaim
        fields = ["agent_id", "status", "note"]

    def validate(self, data):
        """Ensure profile is set from context."""
        request = self.context.get("request")
        if request and request.user and hasattr(request.user, "profile"):
            data["profile"] = request.user.profile
        return data


class ProfileRepositoryClaimSerializer(serializers.ModelSerializer):
    """Read serializer for ProfileRepositoryClaim with nested repository."""

    repository = RepositorySerializer(read_only=True)

    class Meta:
        model = ProfileRepositoryClaim
        fields = [
            "id",
            "repository",
            "status",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ProfileRepositoryClaimWriteSerializer(serializers.ModelSerializer):
    """Write serializer for ProfileRepositoryClaim using repo_id for FK resolution."""

    repository_id = serializers.SlugRelatedField(
        slug_field="repo_id",
        queryset=Repository.objects.all(),
        source="repository",
    )

    class Meta:
        model = ProfileRepositoryClaim
        fields = ["repository_id", "status", "note"]

    def validate(self, data):
        """Ensure profile is set from context."""
        request = self.context.get("request")
        if request and request.user and hasattr(request.user, "profile"):
            data["profile"] = request.user.profile
        return data


class ProfileSerializer(serializers.ModelSerializer):
    """Read-only serializer for Profile with nested claims."""

    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    agent_claims = ProfileAgentClaimSerializer(many=True, read_only=True)
    repository_claims = ProfileRepositoryClaimSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            "username",
            "email",
            "profile_image",
            "agent_claims",
            "repository_claims",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ProfileWriteSerializer(serializers.ModelSerializer):
    """Write serializer for Profile (profile_image only, claims managed separately)."""

    class Meta:
        model = Profile
        fields = ["profile_image"]


class ZineSubmissionSerializer(serializers.ModelSerializer):
    """Read-only serializer for ZineSubmission with nested related objects."""

    username = serializers.CharField(source="user.username", read_only=True)
    zine_title = serializers.CharField(source="zine.title", read_only=True)
    zine_id = serializers.CharField(source="zine.zine_id", read_only=True)
    repository_name = serializers.CharField(source="repository.name", read_only=True)
    repository_id = serializers.CharField(source="repository.repo_id", read_only=True)
    status = SubmissionStatusSerializer(read_only=True)

    class Meta:
        model = ZineSubmission
        fields = [
            "id",
            "username",
            "zine_id",
            "zine_title",
            "repository_id",
            "repository_name",
            "status",
            "notes",
            "send_digital",
            "send_print",
            "submitted_at",
            "responded_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ZineSubmissionWriteSerializer(serializers.ModelSerializer):
    """Write serializer for ZineSubmission using external IDs for FK resolution."""

    zine_id = serializers.SlugRelatedField(
        slug_field="zine_id",
        queryset=Zine.objects.all(),
        source="zine",
    )
    repository_id = serializers.SlugRelatedField(
        slug_field="repo_id",
        queryset=Repository.objects.all(),
        source="repository",
    )
    status = serializers.SlugRelatedField(
        slug_field="code",
        queryset=SubmissionStatus.objects.all(),
    )

    class Meta:
        model = ZineSubmission
        fields = [
            "zine_id",
            "repository_id",
            "status",
            "notes",
            "send_digital",
            "send_print",
            "submitted_at",
            "responded_at",
        ]

    def validate(self, data):
        """Auto-populate timestamp fields based on status changes."""
        request = self.context.get("request")
        if request and request.user:
            # For create operations, set the user from the request
            if not self.instance:
                data["user"] = request.user

            # Auto-populate submitted_at when status changes to 'submitted'
            status = data.get("status")
            if status and status.code == "submitted":
                if not data.get("submitted_at") and (
                    not self.instance or self.instance.status.code != "submitted"
                ):
                    from django.utils import timezone

                    data["submitted_at"] = timezone.now()

            # Auto-populate responded_at when status changes to 'accepted' or 'rejected'
            if status and status.code in ["accepted", "rejected"]:
                if not data.get("responded_at") and (
                    not self.instance
                    or self.instance.status.code not in ["accepted", "rejected"]
                ):
                    from django.utils import timezone

                    data["responded_at"] = timezone.now()

        return data
