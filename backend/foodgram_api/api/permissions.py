from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешение на выполнение действий из небезопасных
    методов, если пользователь является автором записи"""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or ((request.user and obj.author) == request.user)
        )
