from django.urls import path, include
from . import views

urlpatterns = [
  path('', views.getData),
  path('/auth', include('api.auth.urls')),
  path('/test', views.getData),
]