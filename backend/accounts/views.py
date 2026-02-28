from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Profile, SubmissionStatus, ZineSubmission
from .permissions import IsOwner, IsOwnerOrRepositoryStaff
from .serializers import (
    ProfileSerializer,
    ProfileWriteSerializer,
    SubmissionStatusSerializer,
    ZineSubmissionSerializer,
    ZineSubmissionWriteSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["Accounts"], summary="List user profiles (owner only)"),
    retrieve=extend_schema(tags=["Accounts"], summary="Retrieve a user profile"),
    update=extend_schema(tags=["Accounts"], summary="Update a user profile"),
    partial_update=extend_schema(
        tags=["Accounts"], summary="Partially update a user profile"
    ),
)
class ProfileViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for user profiles.

    Users can only view and edit their own profile.
    """

    queryset = Profile.objects.select_related(
        "user", "agent__kind", "repository__kind"
    ).all()
    permission_classes = [IsAuthenticated, IsOwner]
    http_method_names = ["get", "put", "patch"]  # No create (auto-created) or delete

    def get_queryset(self):
        """Filter to only show the authenticated user's profile."""
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        return self.queryset.none()

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return ProfileWriteSerializer
        return ProfileSerializer


@extend_schema_view(
    list=extend_schema(tags=["Accounts"], summary="List zine submissions"),
    retrieve=extend_schema(tags=["Accounts"], summary="Retrieve a zine submission"),
    create=extend_schema(tags=["Accounts"], summary="Create a zine submission"),
    update=extend_schema(tags=["Accounts"], summary="Update a zine submission"),
    partial_update=extend_schema(
        tags=["Accounts"], summary="Partially update a zine submission"
    ),
    destroy=extend_schema(tags=["Accounts"], summary="Delete a zine submission"),
)
class ZineSubmissionViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for zine submissions.

    Users can create and manage their own submissions.
    Repository staff can view submissions to their repository (read-only).
    """

    queryset = ZineSubmission.objects.select_related(
        "user", "zine", "repository", "status"
    ).all()
    permission_classes = [IsAuthenticated, IsOwnerOrRepositoryStaff]

    def get_queryset(self):
        """
        Filter submissions based on user permissions:
        - Owner sees their own submissions
        - Repository staff see submissions to their repository
        """
        user = self.request.user
        if not user.is_authenticated:
            return self.queryset.none()

        # Start with user's own submissions
        queryset = self.queryset.filter(user=user)

        # If user has a profile with a linked repository, also show submissions to that repo
        if hasattr(user, "profile") and user.profile.repository:
            queryset = queryset | self.queryset.filter(
                repository=user.profile.repository
            )

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ZineSubmissionWriteSerializer
        return ZineSubmissionSerializer

    def perform_create(self, serializer):
        """Set the user to the authenticated user when creating a submission."""
        serializer.save(user=self.request.user)


@extend_schema(tags=["Vocabularies"])
class SubmissionStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """Submission status controlled vocabulary (read-only)."""

    queryset = SubmissionStatus.objects.all()
    serializer_class = SubmissionStatusSerializer
    lookup_field = "code"
    pagination_class = None
