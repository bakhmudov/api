from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Пользователи могут редактировать только свои собственные объекты.
    """

    def has_object_permission(self, request, view, obj):
        # Разрешено для чтения всем пользователям (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешено для записи только владельцу объекта
        return obj.user == request.user
