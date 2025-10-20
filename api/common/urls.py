from django.urls import path, include
from .views import get_countries, get_languages, subjects_view, units_view, lessons_view

urlpatterns = [
  path('/countries', get_countries),
  path('/languages', get_languages),
  path('/subjects', subjects_view),
  path('/units', units_view),
  path('/lessons', lessons_view),
]