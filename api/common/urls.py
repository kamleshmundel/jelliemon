from django.urls import path, include
from .views import get_countries, get_states, get_cities, get_languages, subjects_view, units_view, lessons_view, badges_view, next_view

urlpatterns = [
  path('/countries', get_countries),
  path('/states', get_states),
  path('/cities', get_cities),
  path('/languages', get_languages),
  path('/subjects', subjects_view),
  path('/lessons', lessons_view),
  path('/units', units_view),
  path('/badges', badges_view),
  path('/next', next_view),
]