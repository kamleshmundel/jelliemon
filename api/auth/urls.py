# urls.py
from django.urls import path
from .views import auth_handler, forget_password, refresh_token

urlpatterns = [
    path('', auth_handler),
    path('/forget-password', forget_password),
    path('/refresh', refresh_token),
]
