# api/admin_auth/urls.py
from django.urls import path
from .views import admin_login, refresh_token, admin_forget_password, admin_logout

urlpatterns = [
    path('/login', admin_login),
    path('/logout', admin_logout),
    path('/refresh', refresh_token),
    path('/forget-password', admin_forget_password),
]
