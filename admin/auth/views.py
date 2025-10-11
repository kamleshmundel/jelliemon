# api/admin_auth/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.hashers import check_password, make_password
from base.models import AppUser
from base.serializers import AppUserSerializer
from config.resp_middle import api_response
import jwt, datetime, random
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from config.resp_messages import RM
from config.helpers import generate_otp
from .decorators import require_fields, ensure_admin_exists, verify_admin_password, validate_forget_password_fields

@api_view(['POST'])
@permission_classes([AllowAny])
@require_fields(['email', 'password'])
@ensure_admin_exists
@verify_admin_password
def admin_login(request):
    user = request.user_obj

    # Invalidate old refresh token
    user.token = None

    # Create new access token
    access_payload = {
        'user_id': str(user.id),
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=5)
    }
    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')

    # Create refresh token
    refresh_payload = {
        'user_id': str(user.id),
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')

    # Save refresh token in DB
    user.token = refresh_token
    user.save()

    return api_response({
        "access": access_token,
        "refresh": refresh_token,
        "user": AppUserSerializer(user).data
    }, RM.admin.LOGIN_SUCCESS, 200)

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    token = request.data.get('refresh')
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = AppUser.objects.get(id=payload['user_id'], token=token)
    except (jwt.ExpiredSignatureError, jwt.DecodeError, AppUser.DoesNotExist):
        raise AuthenticationFailed(RM.common.INVALID_REFRESH_TOKEN)

    new_access_payload = {
        'user_id': str(user.id),
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    }
    new_access_token = jwt.encode(new_access_payload, settings.SECRET_KEY, algorithm='HS256')
    return api_response({'access': new_access_token}, RM.admin.TOKEN_REFRESSHED, 200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        token = RefreshToken(request.data.get('refresh'))
        token.blacklist()
        request.user.token = None
        request.user.save()
        return api_response(None, "Logged out successfully.", 200)
    except:
        return api_response(None, "Invalid token.", 400)


@api_view(['POST'])
@permission_classes([AllowAny])
@validate_forget_password_fields
@ensure_admin_exists
def admin_forget_password(request):
    user, data = request.admin_user, request.data
    step = data.get('step', 'send_otp')

    if step == 'send_otp':
        user.otp = generate_otp(); user.save()
        print(f"Sending OTP to {user.email}: {user.otp}")
        return api_response(None, RM.admin.OTP_SENT, 200)
    if step == 'verify_otp':
        if str(user.otp) != str(data.get('otp')): return api_response(None, RM.admin.INVALID_OTP, 400)
        return api_response(None, RM.admin.OTP_VERIFIED, 200)
    if step == 'set_password':
        password, confirm = data.get('password'), data.get('confirm_password')
        if password != confirm: return api_response(None, RM.common.PASSWORD_MISMATCH, 400)
        user.password = make_password(password); user.otp = ''; user.save()
        return api_response(AppUserSerializer(user).data, RM.admin.PASSWORD_RESET_SUCCESS, 200)
    return api_response(None, RM.common.INVALID_STEP, 400)
