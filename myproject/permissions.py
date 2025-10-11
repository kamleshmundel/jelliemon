from rest_framework.permissions import BasePermission
from config.conatants import ROLES

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == ROLES.ADMIN

class IsNormalUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == ROLES.USER
