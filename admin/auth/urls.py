# api/admin_auth/urls.py
from django.urls import path
from .views import admin_login, admin_forget_password

urlpatterns = [
    path('/login', admin_login),
    path('/forget-password', admin_forget_password),
]
