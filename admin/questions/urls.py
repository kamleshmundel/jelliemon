from django.urls import path, include
from .views import questions_view

urlpatterns = [
  path('', questions_view),
]