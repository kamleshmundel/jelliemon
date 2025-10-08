from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password

import random
import jwt
import datetime
from django.conf import settings

from base.models import AppUser
from base.serializers import AppUserSerializer

def generate_otp():
    # Simple 6-digit OTP generator
    return str(random.randint(1000, 9999))

@api_view(['POST'])
@permission_classes([AllowAny])
def login_with_email(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {"error": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        return Response(
            {"error": "Invalid email or password."},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_verified:
        return Response(
            {"error": "Email not verified. Please complete verification."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if not user.password:
        return Response(
            {"error": "Password not set. Please set your password first."},
            status=status.HTTP_403_FORBIDDEN
        )

    if not check_password(password, user.password):
        return Response(
            {"error": "Invalid email or password."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Generate JWT token
    payload = {
        'user_id': str(user.id),          # uuid as string
        'email': user.email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),  # Token expires in 24 hours
        'iat': datetime.datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    # Save the token in user.token field
    user.token = token
    user.save()

    serializer = AppUserSerializer(user)
    
    return Response(
        {
            "message": "Login successful.",
            "data": {
                "token": token,
                "user": serializer.data
            },
            "status": status.HTTP_200_OK
        },
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def login_with_mobile(request):
    mobile = request.data.get('mobile')

    if not mobile:
        return Response({"error": "Mobile number is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Get or create user by mobile number
    user, created = AppUser.objects.get_or_create(phone=mobile)
    
    # Generate OTP and save
    otp = generate_otp()
    user.otp = otp
    user.is_verified = False  # Mark unverified on new login attempt
    user.save()

    # TODO: send OTP via SMS here; for now just print
    print(f"Sending OTP to {mobile}: {otp}")

    return Response({"message": "OTP sent to your mobile number."}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_mobile_otp(request):
    mobile = request.data.get('mobile')
    otp = request.data.get('otp')

    if not mobile or not otp:
        return Response({"error": "Mobile and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = AppUser.objects.get(phone=mobile)
    except AppUser.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    if int(user.otp) != otp:
        return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

    # Mark user as verified
    user.is_verified = True
    user.otp = ''  # clear OTP after verification
    user.save()

    # Generate JWT token
    payload = {
        'user_id': str(user.id),
        'phone': user.phone,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    # Save token in user record
    user.token = token
    user.save()

    serializer = AppUserSerializer(user)
    return Response({
        "message": "Mobile login successful.",
        "data": {
            "token": token,
            "user": serializer.data
        },
        "status": status.HTTP_200_OK
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup_with_email(request):
    email = request.data.get('email')
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user already exists
    user, created = AppUser.objects.get_or_create(email=email)
    if user.is_verified:
        return Response({"message": "Email is already verified."}, status=status.HTTP_200_OK)

    # Generate OTP and save
    otp = generate_otp()
    user.otp = otp
    user.is_verified = False
    user.save()

    # TODO: send OTP via email (for now, just print)
    print(f"Sending OTP to {email}: {otp}")

    return Response({
        "data": None,
        "message": "OTP sent to your email.",
        "status": status.HTTP_200_OK
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_signup_otp(request):
    email = request.data.get('email')
    otp = request.data.get('otp')

    if not email or not otp:
        return Response({"error": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    if user.is_verified:
        return Response({"message": "User already verified"}, status=status.HTTP_200_OK)

    if int(user.otp) == otp:
        user.is_verified = True
        user.otp = ''  # clear OTP after successful verification
        user.save()
        serializer = AppUserSerializer(user)
        return Response({"message": "OTP verified successfully", "data": serializer.data, "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def set_password(request):
    email = request.data.get('email')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')

    if not all([email, password, confirm_password]):
        return Response({"error": "Email, password and confirm password are required."}, status=status.HTTP_400_BAD_REQUEST)

    if password != confirm_password:
        return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    if not user.is_verified:
        return Response({"error": "User email is not verified. Complete OTP verification first."}, status=status.HTTP_403_FORBIDDEN)

    # Hash and set the password
    user.password = make_password(password)
    user.current_step = user.current_step + 1  # Example: advance onboarding step
    user.save()

    serializer = AppUserSerializer(user)
    return Response({"message": "Password set successfully.", "data": serializer.data, "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)