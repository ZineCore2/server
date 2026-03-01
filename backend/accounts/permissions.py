from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view and edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Profile objects have a user field
        if hasattr(obj, "user"):
            return obj.user == request.user
        # ProfileAgentClaim and ProfileRepositoryClaim have a profile field
        if hasattr(obj, "profile"):
            return obj.profile.user == request.user
        return False


class IsOwnerOrRepositoryStaff(permissions.BasePermission):
    """
    Custom permission to allow:
    - Owner of a submission to view/edit it
    - Repository staff (approved claims) to view submissions to their repository
    """

    def has_object_permission(self, request, view, obj):
        # Owner can always access their submission
        if hasattr(obj, "user") and obj.user == request.user:
            return True

        # Repository staff can view (but not edit) submissions to their repository
        if hasattr(obj, "repository") and hasattr(request.user, "profile"):
            # Check if the user has an approved claim on this repository
            from .models import ProfileRepositoryClaim

            has_approved_claim = ProfileRepositoryClaim.objects.filter(
                profile=request.user.profile,
                repository=obj.repository,
                status=ProfileRepositoryClaim.ClaimStatus.APPROVED,
            ).exists()

            if has_approved_claim:
                # Repository staff can only view (safe methods), not edit
                return request.method in permissions.SAFE_METHODS

        return False
