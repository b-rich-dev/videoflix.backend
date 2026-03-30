from rest_framework import permissions

class IsAdminOrStaff(permissions.BasePermission):
    """Grants access only to users with staff or superuser privileges."""

    def has_permission(self, request, view):
        return request.user and (request.user.is_staff or request.user.is_superuser)
    