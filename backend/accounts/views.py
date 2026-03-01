from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Profile, ProfileAgentClaim, ProfileRepositoryClaim, SubmissionStatus, ZineSubmission
from .permissions import IsOwner, IsOwnerOrRepositoryStaff
from .serializers import (
    ProfileAgentClaimSerializer,
    ProfileAgentClaimWriteSerializer,
    ProfileRepositoryClaimSerializer,
    ProfileRepositoryClaimWriteSerializer,
    ProfileSerializer,
    ProfileWriteSerializer,
    SubmissionStatusSerializer,
    ZineSubmissionSerializer,
    ZineSubmissionWriteSerializer,
)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """
    Authenticate user and return token + user data

    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    Returns: { "token": "...", "user": {...} }
    """
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"detail": "Username and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {"detail": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Get or create token
    token, created = Token.objects.get_or_create(user=user)

    # Get user profile if exists
    try:
        profile = Profile.objects.get(user=user)
        profile_data = ProfileSerializer(profile).data
    except Profile.DoesNotExist:
        profile_data = None

    return Response({
        "token": token.key,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "profile": profile_data,
        },
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout user by deleting their token

    POST /api/auth/logout/
    """
    try:
        request.user.auth_token.delete()
    except Exception:
        pass

    return Response({"detail": "Successfully logged out"})


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


@extend_schema_view(
    list=extend_schema(tags=["Accounts"], summary="List agent claims for profile"),
    retrieve=extend_schema(tags=["Accounts"], summary="Retrieve an agent claim"),
    create=extend_schema(tags=["Accounts"], summary="Create an agent claim"),
    update=extend_schema(tags=["Accounts"], summary="Update an agent claim"),
    partial_update=extend_schema(tags=["Accounts"], summary="Partially update an agent claim"),
    destroy=extend_schema(tags=["Accounts"], summary="Delete an agent claim"),
)
class ProfileAgentClaimViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for profile agent claims.

    Users can manage claims on agent records (e.g., 'this is me').
    """

    queryset = ProfileAgentClaim.objects.select_related("profile__user", "agent__kind").all()
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        """Filter to only show the authenticated user's profile claims."""
        if self.request.user.is_authenticated and hasattr(self.request.user, "profile"):
            return self.queryset.filter(profile=self.request.user.profile)
        return self.queryset.none()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProfileAgentClaimWriteSerializer
        return ProfileAgentClaimSerializer

    def perform_create(self, serializer):
        """Set the profile to the authenticated user's profile when creating a claim."""
        serializer.save(profile=self.request.user.profile)


@extend_schema_view(
    list=extend_schema(tags=["Accounts"], summary="List repository claims for profile"),
    retrieve=extend_schema(tags=["Accounts"], summary="Retrieve a repository claim"),
    create=extend_schema(tags=["Accounts"], summary="Create a repository claim"),
    update=extend_schema(tags=["Accounts"], summary="Update a repository claim"),
    partial_update=extend_schema(tags=["Accounts"], summary="Partially update a repository claim"),
    destroy=extend_schema(tags=["Accounts"], summary="Delete a repository claim"),
)
class ProfileRepositoryClaimViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for profile repository claims.

    Users can manage claims on repository records (e.g., 'I work at this repository').
    """

    queryset = ProfileRepositoryClaim.objects.select_related("profile__user", "repository__kind").all()
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        """Filter to only show the authenticated user's profile claims."""
        if self.request.user.is_authenticated and hasattr(self.request.user, "profile"):
            return self.queryset.filter(profile=self.request.user.profile)
        return self.queryset.none()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProfileRepositoryClaimWriteSerializer
        return ProfileRepositoryClaimSerializer

    def perform_create(self, serializer):
        """Set the profile to the authenticated user's profile when creating a claim."""
        serializer.save(profile=self.request.user.profile)
