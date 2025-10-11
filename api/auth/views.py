# api/user_auth/views.py
from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from base.models import AppUser
from base.serializers import AppUserSerializer
from rest_framework.exceptions import AuthenticationFailed
from config.resp_middle import api_response
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from facebook import GraphAPI
from myproject.utils import create_access_token, create_refresh_token
from config.resp_messages import RM
import random, jwt, datetime
from config.helpers import generate_otp

def generate_tokens(u):
    data = {'user_id': str(u.id), 'role': u.role}
    access, refresh = create_access_token(data), create_refresh_token(data)
    u.token = refresh; u.save()
    return {"access": access, "refresh": refresh, "user": AppUserSerializer(u).data}

def handle_google_auth(token):
    if not token: return api_response(None, RM.user.GOOGLE_AUTH_SUCCESS, 400)
    try:
        info = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
        email, name = info.get('email'), info.get('name', '')
        if not email: return api_response(None, RM.common.REQUIRED_FIELDS, 400)
        u, _ = AppUser.objects.get_or_create(email=email, defaults={'is_verified': True, 'name': name})
        return api_response(generate_tokens(u), RM.user.GOOGLE_AUTH_SUCCESS, 200)
    except Exception:
        return api_response(None, RM.common.INVALID_REFRESH_TOKEN, 400)

def handle_facebook_auth(token):
    if not token: return api_response(None, RM.common.INVALID_REQUEST, 400)
    try:
        graph = GraphAPI(access_token=token)
        p = graph.get_object('me', fields='id,name,email')
        email, name = p.get('email'), p.get('name', '')
        if not email: return api_response(None, RM.common.REQUIRED_FIELDS, 400)
        u, _ = AppUser.objects.get_or_create(email=email, defaults={'is_verified': True, 'name': name})
        return api_response(generate_tokens(u), RM.user.FACEBOOK_AUTH_SUCCESS, 200)
    except Exception:
        return api_response(None, RM.common.INVALID_REFRESH_TOKEN, 400)

@api_view(['POST'])
@permission_classes([AllowAny])
def auth_handler(request):
    action, mode = request.data.get('action'), request.data.get('mode')
    if mode == 'google': return handle_google_auth(request.data.get('token'))
    if mode == 'facebook': return handle_facebook_auth(request.data.get('token'))

    if action == 'login' and mode == 'email':
        email, pwd = request.data.get('email'), request.data.get('password')
        if not email or not pwd: return api_response(None, RM.common.EMAIL_PASSWORD_REQUIRED, 400)
        try: u = AppUser.objects.get(email=email)
        except AppUser.DoesNotExist: return api_response(None, RM.common.INVALID_CREDENTIALS, 401)
        if not u.is_verified or not check_password(pwd, u.password): return api_response(None, RM.common.INVALID_CREDENTIALS, 401)
        return api_response(generate_tokens(u), RM.user.LOGIN_SUCCESS, 200)

    if action == 'login' and mode == 'mobile':
        step, mobile, otp = request.data.get('step', 'send_otp'), request.data.get('mobile'), request.data.get('otp')
        if not mobile: return api_response(None, RM.common.REQUIRED_FIELDS, 400)
        if step == 'send_otp':
            u, _ = AppUser.objects.get_or_create(phone=mobile)
            u.otp, u.is_verified = generate_otp(), False; u.save()
            print(f"OTP to {mobile}: {u.otp}")
            return api_response(None, RM.user.OTP_SENT_MOBILE, 200)
        if step == 'verify_otp':
            try: u = AppUser.objects.get(phone=mobile)
            except AppUser.DoesNotExist: return api_response(None, RM.common.NOT_FOUND, 404)
            if str(u.otp) != str(otp): return api_response(None, RM.common.REQUIRED_FIELDS, 400)
            u.is_verified, u.otp = True, ''; u.save()
            return api_response(generate_tokens(u), RM.user.MOBILE_LOGIN_SUCCESS, 200)

    if action == 'signup' and mode == 'email':
        step, email, otp = request.data.get('step', 'send_otp'), request.data.get('email'), request.data.get('otp')
        if not email: return api_response(None, RM.common.REQUIRED_FIELDS, 400)
        if step == 'send_otp':
            u, _ = AppUser.objects.get_or_create(email=email)
            if u.is_verified: return api_response(None, RM.user.OTP_VERIFIED, 200)
            u.otp, u.is_verified = generate_otp(), False; u.save()
            print(f"OTP to {email}: {u.otp}")
            return api_response(None, RM.user.OTP_SENT_EMAIL, 200)
        if step == 'verify_otp':
            try: u = AppUser.objects.get(email=email)
            except AppUser.DoesNotExist: return api_response(None, RM.common.NOT_FOUND, 404)
            if str(u.otp) != str(otp): return api_response(None, RM.common.REQUIRED_FIELDS, 400)
            u.is_verified, u.otp = True, ''; u.save()
            return api_response(AppUserSerializer(u).data, RM.user.OTP_VERIFIED, 200)
        if step == 'set_password':
            pwd, confirm = request.data.get('password'), request.data.get('confirm_password')
            if not all([email, pwd, confirm]): return api_response(None, RM.common.REQUIRED_FIELDS, 400)
            if pwd != confirm: return api_response(None, RM.common.PASSWORD_MISMATCH, 400)
            try: u = AppUser.objects.get(email=email)
            except AppUser.DoesNotExist: return api_response(None, RM.common.NOT_FOUND, 404)
            if not u.is_verified: return api_response(None, RM.common.EMAIL_NOT_VERIFIED, 403)
            u.password = make_password(pwd); u.save()
            return api_response(generate_tokens(u), RM.user.PASSWORD_SET_SUCCESS, 200)

    if action == 'signup' and mode == 'mobile':
        step, mobile, otp = request.data.get('step', 'send_otp'), request.data.get('mobile'), request.data.get('otp')
        if not mobile: return api_response(None, RM.common.REQUIRED_FIELDS, 400)
        if step == 'send_otp':
            u, _ = AppUser.objects.get_or_create(phone=mobile)
            u.otp, u.is_verified = generate_otp(), False; u.save()
            print(f"OTP to {mobile}: {u.otp}")
            return api_response(None, RM.user.OTP_SENT_MOBILE, 200)
        if step == 'verify_otp':
            try: u = AppUser.objects.get(phone=mobile)
            except AppUser.DoesNotExist: return api_response(None, RM.common.NOT_FOUND, 404)
            if str(u.otp) != str(otp): return api_response(None, RM.common.REQUIRED_FIELDS, 400)
            u.is_verified, u.otp = True, ''; u.save()
            return api_response(generate_tokens(u), RM.user.MOBILE_VERIFIED, 200)

    return api_response(None, RM.common.INVALID_REQUEST, 400)

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    token = request.data.get('refresh')
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = AppUser.objects.get(id=payload['user_id'], token=token)
    except (jwt.ExpiredSignatureError, jwt.DecodeError, AppUser.DoesNotExist):
        raise AuthenticationFailed(RM.common.INVALID_REFRESH_TOKEN)
    new_data = {'user_id': str(user.id), 'role': user.role}
    new_access = create_access_token(new_data)
    return api_response({'access': new_access}, RM.common.INVALID_REFRESH_TOKEN, 200)

@api_view(['POST'])
@permission_classes([AllowAny])
def forget_password(request):
    step, email, otp = request.data.get('step', 'send_otp'), request.data.get('email'), request.data.get('otp')
    pwd, confirm = request.data.get('password'), request.data.get('confirm_password')
    if not email: return api_response(None, RM.common.REQUIRED_FIELDS, 400)
    try: u = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist: return api_response(None, RM.common.NOT_FOUND, 404)
    if step == 'send_otp':
        u.otp = generate_otp(); u.save()
        print(f"OTP to {email}: {u.otp}")
        return api_response(None, RM.user.OTP_SENT_EMAIL, 200)
    if step == 'verify_otp':
        if not otp or str(u.otp) != str(otp): return api_response(None, RM.common.REQUIRED_FIELDS, 400)
        return api_response(None, RM.user.OTP_VERIFIED, 200)
    if step == 'set_password':
        if not all([pwd, confirm]): return api_response(None, RM.common.REQUIRED_FIELDS, 400)
        if pwd != confirm: return api_response(None, RM.common.PASSWORD_MISMATCH, 400)
        u.password = make_password(pwd); u.otp = ''; u.save()
        return api_response(generate_tokens(u), RM.user.PASSWORD_RESET_SUCCESS, 200)
    return api_response(None, RM.common.INVALID_STEP, 400)