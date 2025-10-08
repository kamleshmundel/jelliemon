from django.urls import path
from . import views


urlpatterns = [
  # login
  path('login/email', views.login_with_email),
  path('login/mobile', views.login_with_mobile),
  path('login/verify-mobile-otp', views.verify_mobile_otp),
  
  # signup
  path('signup/email', views.signup_with_email),
  path('signup/verify-email-otp', views.verify_signup_otp),
  path('signup/set-password', views.set_password),
  path('signup/mobile', views.login_with_mobile),
  path('signup/verify-mobile-otp', views.verify_mobile_otp),
]
