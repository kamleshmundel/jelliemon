# urls.py
from django.urls import path
from .views import get_profile, update_profile, update_progress

urlpatterns = [
    path('', get_profile),
    path('/update', update_profile),
    path('/progress', update_progress),
]
