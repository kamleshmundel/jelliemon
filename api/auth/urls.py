# urls.py
from django.urls import path
from .views import auth_handler

urlpatterns = [
    path('', auth_handler),
]
