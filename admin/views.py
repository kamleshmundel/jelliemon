# api/views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from myproject.permissions import IsAdmin, IsNormalUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import authentication_classes

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def test_auth(request):
    role = "Admin" if request.user.is_staff else "User"
    return Response({"username": request.user.email, "role": role, "message": "You are authenticated!"})

@api_view(['GET'])
# @authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsNormalUser])
def test_admin(request):
    return Response({"username": request.user.email, "role": "Admin", "message": "Admin access granted!"})

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsNormalUser])
def test_user(request):
    return Response({"username": request.user.email, "role": "User", "message": "User access granted!"})
