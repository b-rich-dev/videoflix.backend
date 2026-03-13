from rest_framework import permissions


class IsAuthenticatedAndActive(permissions.BasePermission):
    """
    Custom permission to only allow authenticated and active users to access the view.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)
