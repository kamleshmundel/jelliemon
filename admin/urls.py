from django.urls import path, include
from . import views

urlpatterns = [
  path('/auth', include("admin.auth.urls")),
  path('/test', views.test_admin),
]