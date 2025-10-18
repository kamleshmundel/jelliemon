# api/admin_auth/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.hashers import check_password, make_password
from base.models import AppUser, UserState
from base.serializers import AppUserSerializer
from config.resp_middle import api_response
import jwt, datetime
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from config.resp_messages import RM
from config.helpers import generate_otp
from myproject.utils import generate_tokens
from django.utils import timezone
from myproject.permissions import IsAdmin
from config.conatants import ROLES
from .decorators import require_fields, ensure_admin_exists, verify_admin_password, validate_forget_password_fields

@api_view(['POST'])
@permission_classes([AllowAny])
@require_fields(['email', 'password'])
@ensure_admin_exists
@verify_admin_password
def admin_login(request):
    user = request.admin_user
    state, _ = UserState.objects.get_or_create(user=user)
    state.token = None
    state.save()
    tdata = generate_tokens(user, AppUserSerializer)
    access_token, refresh_token, loggedin_user = tdata['access'], tdata['refresh'], tdata['user']
    state.token = refresh_token
    state.save()
    return api_response({
        "access": access_token,
        "refresh": refresh_token,
        "user": loggedin_user
    }, RM.admin.LOGIN_SUCCESS, 200)

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    token = request.data.get('refresh')
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = AppUser.objects.get(id=payload['user_id'])
        state = getattr(user, 'state', None)
        if not state or state.token != token:
            raise AuthenticationFailed(RM.common.INVALID_REFRESH_TOKEN)
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
@permission_classes([IsAuthenticated, IsAdmin])
@ensure_admin_exists
def admin_logout(request):
    try:
        user = AppUser.objects.get(id=request.user.id, role=ROLES.ADMIN)
        state = getattr(user, 'state', None)
        if state:
            state.token = None
            state.last_logout_at = timezone.now()
            state.save()
        return api_response(None, RM.admin.LOGOUT_SUCCESS, 200)
    except AppUser.DoesNotExist:
        return api_response(None, RM.admin.ADMIN_NOT_FOUND, 404)

@api_view(['POST'])
@permission_classes([AllowAny])
@validate_forget_password_fields
@ensure_admin_exists
def admin_forget_password(request):
    user, data = request.admin_user, request.data
    state, _ = UserState.objects.get_or_create(user=user)
    step = data.get('step', 'send_otp')

    if step == 'send_otp':
        state.otp = generate_otp(); state.save()
        print(f"Sending OTP to {user.email}: {state.otp}")
        return api_response(None, RM.admin.OTP_SENT, 200)
    if step == 'verify_otp':
        if str(state.otp) != str(data.get('otp')): return api_response(None, RM.admin.INVALID_OTP, 400)
        return api_response(None, RM.admin.OTP_VERIFIED, 200)
    if step == 'set_password':
        password, confirm = data.get('password'), data.get('confirm_password')
        if password != confirm: return api_response(None, RM.common.PASSWORD_MISMATCH, 400)
        user.password = make_password(password); state.otp = ''; user.save(); state.save()
        return api_response(AppUserSerializer(user).data, RM.admin.PASSWORD_RESET_SUCCESS, 200)
    return api_response(None, RM.common.INVALID_STEP, 400)
