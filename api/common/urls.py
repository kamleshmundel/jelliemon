from django.urls import path, include
from .views import get_countries, get_languages

urlpatterns = [
  path('/countries', get_countries),
  path('/languages', get_languages),
]