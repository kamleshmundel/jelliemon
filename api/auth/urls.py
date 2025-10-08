from django.urls import path
from . import views


urlpatterns = [
  path('login/email', views.login_with_email),
  path('login/mobile', views.login_with_mobile),
  path('signup/email', views.signup_with_email),
  path('signup/verify-email-otp', views.verify_signup_otp),
  path('signup/set-password', views.set_password),
]
