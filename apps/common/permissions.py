from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin or request.user.is_superuser:
            return True
        user_id = str(request.user.id)
        for fk in ('member_id', 'writer_id', 'user_id'):
            if hasattr(obj, fk) and str(getattr(obj, fk)) == user_id:
                return True
        return False
