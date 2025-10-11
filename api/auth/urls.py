# urls.py
from django.urls import path
from .views import auth_handler, forget_password

urlpatterns = [
    path('', auth_handler),
    path('/forget-password', forget_password),
]
