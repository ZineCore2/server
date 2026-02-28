from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view and edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Profile objects have a user field
        if hasattr(obj, "user"):
            return obj.user == request.user
        return False


class IsOwnerOrRepositoryStaff(permissions.BasePermission):
    """
    Custom permission to allow:
    - Owner of a submission to view/edit it
    - Repository staff to view submissions to their repository
    """

    def has_object_permission(self, request, view, obj):
        # Owner can always access their submission
        if hasattr(obj, "user") and obj.user == request.user:
            return True

        # Repository staff can view (but not edit) submissions to their repository
        if hasattr(obj, "repository"):
            # Check if the user's profile is associated with this repository
            if hasattr(request.user, "profile") and request.user.profile.repository:
                if request.user.profile.repository == obj.repository:
                    # Repository staff can only view (safe methods), not edit
                    return request.method in permissions.SAFE_METHODS

        return False
