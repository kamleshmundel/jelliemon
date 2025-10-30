# api/user_auth/views.py
from django.urls import path
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from base.models import AppUser, UserState
from base.serializers import AppUserSerializer
from rest_framework.exceptions import AuthenticationFailed
from config.resp_middle import api_response
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from facebook import GraphAPI
from myproject.utils import create_access_token, generate_tokens
from config.resp_messages import RM
import random, jwt, datetime
from config.helpers import generate_otp
from config.conatants import ROLES, EMAIL_SUBJECTS, EMAIL_TEMPLATES
from myproject.permissions import IsNormalUser
from django.utils import timezone
from config.email_service import send_email, send_templated_email

def handle_google_auth(token):
    if not token: return api_response(None, RM.user.GOOGLE_AUTH_SUCCESS, 400)
    try:
        info = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
        email, name = info.get('email'), info.get('name', '')
        if not email: return api_response(None, RM.common.REQUIRED_FIELDS, 400)
        u, _ = AppUser.objects.get_or_create(email=email, defaults={'is_verified': True, 'name': name})
        return api_response(generate_tokens(u, AppUserSerializer), RM.user.GOOGLE_AUTH_SUCCESS, 200)
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
        return api_response(generate_tokens(u, AppUserSerializer), RM.user.FACEBOOK_AUTH_SUCCESS, 200)
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
        state, _ = UserState.objects.get_or_create(user=u)
        state.last_login = timezone.now()
        state.save()
        return api_response(generate_tokens(u, AppUserSerializer), RM.user.LOGIN_SUCCESS, 200)

    if action == 'login' and mode == 'mobile':
        step, mobile = request.data.get('step', 'send_otp'), request.data.get('mobile')

        # Ensure mobile number is provided
        if not mobile:
            return api_response(None, RM.common.REQUIRED_FIELDS, 400)

        # Step to verify OTP (Frontend handles OTP process, backend just updates status)
        if step == 'verify_otp':
            # Check if the user exists by phone number
            try:
                u = AppUser.objects.get(phone=mobile)
            except AppUser.DoesNotExist:
                return api_response(None, RM.common.NOT_FOUND, 404)

            # Assuming OTP verification has already been done on the frontend, we just mark user as verified
            u.is_verified = True
            u.save()

            # Generate and return tokens (assuming your `generate_tokens` function is correct)
            return api_response(generate_tokens(u, AppUserSerializer), RM.user.MOBILE_LOGIN_SUCCESS, 200)

    if action == 'signup' and mode == 'email':
        step, email, otp = request.data.get('step', 'send_otp'), request.data.get('email'), request.data.get('otp')
        if not email: return api_response(None, RM.common.REQUIRED_FIELDS, 400)
        if step == 'send_otp':
            u, _ = AppUser.objects.get_or_create(email=email)
            state, _ = UserState.objects.get_or_create(user=u)
            if u.is_verified: return api_response(None, RM.user.ALREADY_VERIFIED, 200)
            state.otp, u.is_verified = generate_otp(), False
            state.save(); u.save()
            print(f"OTP to {email}: {state.otp}")

            # send_email("Welcome!", f"Your account has been created successfully. Use this OTP: {u.otp}", [email])

            send_templated_email(
                EMAIL_SUBJECTS.WELCOME.value,
                EMAIL_TEMPLATES.WELCOME.value,
                {
                    "otp": state.otp,
                    "validity_minutes": 10,
                    "support_url": "https://jelliemon.com/support",
                },
                [email]
            )

            return api_response(None, RM.user.OTP_SENT_EMAIL, 200)
        if step == 'verify_otp':
            try: u = AppUser.objects.get(email=email)
            except AppUser.DoesNotExist: return api_response(None, RM.common.NOT_FOUND, 404)
            state = getattr(u, 'state', None)
            if not state or str(state.otp) != str(otp): return api_response(None, RM.common.REQUIRED_FIELDS, 400)
            u.is_verified, state.otp = True, None
            u.save(); state.save()
            return api_response(None, RM.user.OTP_VERIFIED, 200)

        if step == 'set_password':
            pwd, confirm = request.data.get('password'), request.data.get('confirm_password')
            if not all([email, pwd, confirm]): return api_response(None, RM.common.REQUIRED_FIELDS, 400)
            if pwd != confirm: return api_response(None, RM.common.PASSWORD_MISMATCH, 400)
            try: u = AppUser.objects.get(email=email)
            except AppUser.DoesNotExist: return api_response(None, RM.common.NOT_FOUND, 404)
            if not u.is_verified: return api_response(None, RM.common.EMAIL_NOT_VERIFIED, 403)
            u.password = make_password(pwd); u.save()
            return api_response(None, RM.user.PASSWORD_SET_SUCCESS, 200)

    if action == 'signup' and mode == 'mobile':
        step, mobile = request.data.get('step', 'send_otp'), request.data.get('mobile')

        # Ensure mobile number is provided
        if not mobile:
            return api_response(None, RM.common.REQUIRED_FIELDS, 400)

        # Step to verify OTP (Firebase handles OTP process on the frontend)
        if step == 'verify_user':
            # Check if the user already exists by mobile number
            u, created = AppUser.objects.get_or_create(phone=mobile)

            # If user is newly created, initialize additional information (if needed)
            if created:
                # Optionally, initialize other fields when the user is created (e.g., user state, profile)
                state, _ = UserState.objects.get_or_create(user=u)
                state.is_verified = True  # Mark new user as verified immediately after frontend OTP verification
                state.save()

            # Update the user as verified (regardless of whether they are newly created or not)
            u.is_verified = True
            u.save()

            # Return success response indicating user is verified
            return api_response(None, RM.user.MOBILE_VERIFIED, 200)

    if action == 'logout':
        try:
            user = AppUser.objects.get(id=request.user.id, role=ROLES.USER)
            state = getattr(user, 'state', None)
            if state:
                state.token = None
                state.last_logout_at = timezone.now()
                state.save()
            return api_response(None, RM.admin.LOGOUT_SUCCESS, 200)
        except AppUser.DoesNotExist:
            return api_response(None, RM.admin.ADMIN_NOT_FOUND, 404)

    return api_response(None, RM.common.INVALID_REQUEST, 400)

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
    state, _ = UserState.objects.get_or_create(user=u)
    if step == 'send_otp':
        state.otp = generate_otp(); state.save()
        print(f"OTP to {email}: {state.otp}")

        send_templated_email(
            EMAIL_SUBJECTS.FORGET_PASS.value,
            EMAIL_TEMPLATES.FORGET_PASS.value,
            context={
                "name": u.name,
                "otp": state.otp,
                "validity_minutes": 10,
                "support_url": "https://jelliemon.com/support",
            },
            recipient_list=[u.email]
        )
        return api_response(None, RM.user.OTP_SENT_EMAIL, 200)
    if step == 'verify_otp':
        if not otp or str(state.otp) != str(otp): return api_response(None, RM.common.REQUIRED_FIELDS, 400)
        return api_response(None, RM.user.OTP_VERIFIED, 200)
    if step == 'set_password':
        if not all([pwd, confirm]): return api_response(None, RM.common.REQUIRED_FIELDS, 400)
        if pwd != confirm: return api_response(None, RM.common.PASSWORD_MISMATCH, 400)
        u.password = make_password(pwd); state.otp = None; u.save(); state.save()
        return api_response(generate_tokens(u, AppUserSerializer), RM.user.PASSWORD_RESET_SUCCESS, 200)
    return api_response(None, RM.common.INVALID_STEP, 400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsNormalUser])
def delete_account(request):
    try:
        user = AppUser.objects.get(id=request.user.id)
        user.delete()
        return api_response(None, RM.user.ACC_DELETED, 200)
    except AppUser.DoesNotExist:
        return api_response(None, RM.common.NOT_FOUND, 404)