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

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    email, password = request.data.get('email'), request.data.get('password')
    if not email or not password:
        return api_response(None, RM.common.EMAIL_PASSWORD_REQUIRED, 400)

    try:
        user = AppUser.objects.get(email=email, role=1)
    except AppUser.DoesNotExist:
        return api_response(None, RM.common.INVALID_CREDENTIALS, 401)

    if not check_password(password, user.password):
        return api_response(None, RM.common.INVALID_CREDENTIALS, 401)

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
def admin_forget_password(request):
    step = request.data.get('step', 'send_otp')
    email, otp, password, confirm = request.data.get('email'), request.data.get('otp'), request.data.get('password'), request.data.get('confirm_password')
    if not email: return api_response(None, RM.common.REQUIRED_FIELDS, 400)
    try: user = AppUser.objects.get(email=email, role=1)
    except AppUser.DoesNotExist: return api_response(None, RM.admin.ADMIN_NOT_FOUND, 404)

    if step == 'send_otp':
        user.otp = generate_otp(); user.save()
        print(f"Sending OTP to {email}: {user.otp}")
        return api_response(None, RM.admin.OTP_SENT, 200)
    if step == 'verify_otp':
        if str(user.otp) != str(otp): return api_response(None, RM.admin.INVALID_OTP, 400)
        return api_response(None, RM.admin.OTP_VERIFIED, 200)
    if step == 'set_password':
        if not all([password, confirm]): return api_response(None, RM.common.REQUIRED_FIELDS, 400)
        if password != confirm: return api_response(None, RM.common.PASSWORD_MISMATCH, 400)
        user.password = make_password(password); user.otp = ''; user.save()
        return api_response(AppUserSerializer(user).data, RM.admin.PASSWORD_RESET_SUCCESS, 200)
    return api_response(None, RM.common.INVALID_STEP, 400)
