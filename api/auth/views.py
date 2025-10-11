from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from base.models import AppUser
from base.serializers import AppUserSerializer
from rest_framework import status
from config.resp_middle import api_response
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import random, jwt, datetime
from facebook import GraphAPI

def generate_otp(): return str(random.randint(1000, 9999))

def handle_google_auth(token):
    if not token: return api_response(None, "Google token required.", 400)
    try:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
        email, name = idinfo.get('email'), idinfo.get('name', '')
        if not email: return api_response(None, "Invalid Google token.", 400)
        u, _ = AppUser.objects.get_or_create(email=email, defaults={'is_verified': True, 'name': name})
        payload = {'user_id': str(u.id), 'email': u.email, 'exp': datetime.datetime.utcnow()+datetime.timedelta(hours=24), 'iat': datetime.datetime.utcnow()}
        jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        u.token = jwt_token; u.save()
        return api_response({"token": jwt_token, "user": AppUserSerializer(u).data}, "Google authentication successful.", 200)
    except ValueError:
        return api_response(None, "Invalid or expired Google token.", 400)
    
def handle_facebook_auth(token):
    if not token: return api_response(None, "Facebook token required.", 400)
    try:
        graph = GraphAPI(access_token=token)
        profile = graph.get_object('me', fields='id,name,email')
        email, name = profile.get('email'), profile.get('name', '')
        if not email: return api_response(None, "Facebook token missing email.", 400)
        u, _ = AppUser.objects.get_or_create(email=email, defaults={'is_verified': True, 'name': name})
        payload = {'user_id': str(u.id), 'email': u.email, 'exp': datetime.datetime.utcnow()+datetime.timedelta(hours=24), 'iat': datetime.datetime.utcnow()}
        jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        u.token = jwt_token; u.save()
        return api_response({"token": jwt_token, "user": AppUserSerializer(u).data}, "Facebook login successful.", 200)
    except Exception as e:
        return api_response(None, "Invalid or expired Facebook token.", 400)

@api_view(['POST'])
@permission_classes([AllowAny])
def auth_handler(request):
    action, mode = request.data.get('action'), request.data.get('mode')
    if mode == 'google': return handle_google_auth(request.data.get('token'))
    if mode == 'facebook': return handle_facebook_auth(request.data.get('token'))

    if action == 'login':
        if mode == 'email':
            email, password = request.data.get('email'), request.data.get('password')
            if not email or not password: return api_response(None, "Email and password required.", 400)
            try: u = AppUser.objects.get(email=email)
            except AppUser.DoesNotExist: return api_response(None, "Invalid email or password.", 401)
            if not u.is_verified: return api_response(None, "Email not verified.", 403)
            if not u.password or not check_password(password, u.password): return api_response(None, "Invalid email or password.", 401)
            payload = {'user_id': str(u.id), 'email': u.email, 'exp': datetime.datetime.utcnow()+datetime.timedelta(hours=24), 'iat': datetime.datetime.utcnow()}
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
            u.token = token; u.save()
            return api_response({"token": token, "user": AppUserSerializer(u).data}, "Login successful.", 200)
        if mode == 'mobile':
            step, mobile, otp = request.data.get('step', 'send_otp'), request.data.get('mobile'), request.data.get('otp')
            if not mobile: return api_response(None, "Mobile number required.", 400)
            if step == 'send_otp':
                u, _ = AppUser.objects.get_or_create(phone=mobile)
                u.otp, u.is_verified = generate_otp(), False; u.save()
                print(f"Sending OTP to {mobile}: {u.otp}")
                return api_response(None, "OTP sent to your mobile number.", 200)
            if step == 'verify_otp':
                try: u = AppUser.objects.get(phone=mobile)
                except AppUser.DoesNotExist: return api_response(None, "User not found.", 404)
                if str(u.otp) != str(otp): return api_response(None, "Invalid OTP.", 400)
                u.is_verified, u.otp = True, ''; u.save()
                payload = {'user_id': str(u.id), 'phone': u.phone, 'exp': datetime.datetime.utcnow()+datetime.timedelta(hours=24), 'iat': datetime.datetime.utcnow()}
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                u.token = token; u.save()
                return api_response({"token": token, "user": AppUserSerializer(u).data}, "Mobile login successful.", 200)

    if action == 'signup':
        if mode == 'email':
            step, email, otp = request.data.get('step', 'send_otp'), request.data.get('email'), request.data.get('otp')
            if not email: return api_response(None, "Email required.", 400)
            if step == 'send_otp':
                u, _ = AppUser.objects.get_or_create(email=email)
                if u.is_verified: return api_response(None, "Email already verified.", 200)
                u.otp, u.is_verified = generate_otp(), False; u.save()
                print(f"Sending OTP to {email}: {u.otp}")
                return api_response(None, "OTP sent to your email.", 200)
            if step == 'verify_otp':
                try: u = AppUser.objects.get(email=email)
                except AppUser.DoesNotExist: return api_response(None, "User not found.", 404)
                if u.is_verified: return api_response(None, "User already verified.", 200)
                if str(u.otp) != str(otp): return api_response(None, "Invalid OTP.", 400)
                u.is_verified, u.otp = True, ''; u.save()
                return api_response(AppUserSerializer(u).data, "OTP verified successfully.", 200)
            if step == 'set_password':
                pwd, confirm = request.data.get('password'), request.data.get('confirm_password')
                if not all([email, pwd, confirm]): return api_response(None, "Email, password, confirm password required.", 400)
                if pwd != confirm: return api_response(None, "Passwords do not match.", 400)
                try: u = AppUser.objects.get(email=email)
                except AppUser.DoesNotExist: return api_response(None, "User not found.", 404)
                if not u.is_verified: return api_response(None, "User email not verified.", 403)
                u.password = make_password(pwd); u.current_step += 1; u.save()
                return api_response(AppUserSerializer(u).data, "Password set successfully.", 200)
        if mode == 'mobile':
            step, mobile, otp = request.data.get('step', 'send_otp'), request.data.get('mobile'), request.data.get('otp')
            if not mobile: return api_response(None, "Mobile number required.", 400)
            if step == 'send_otp':
                u, _ = AppUser.objects.get_or_create(phone=mobile)
                u.otp, u.is_verified = generate_otp(), False; u.save()
                print(f"Sending OTP to {mobile}: {u.otp}")
                return api_response(None, "OTP sent to your mobile number.", 200)
            if step == 'verify_otp':
                try: u = AppUser.objects.get(phone=mobile)
                except AppUser.DoesNotExist: return api_response(None, "User not found.", 404)
                if str(u.otp) != str(otp): return api_response(None, "Invalid OTP.", 400)
                u.is_verified, u.otp = True, ''; u.save()
                return api_response(AppUserSerializer(u).data, "Mobile verified successfully.", 200)

    return api_response(None, "Invalid request.", 400)

@api_view(['POST'])
@permission_classes([AllowAny])
def forget_password(request):
    step = request.data.get('step', 'send_otp')
    email = request.data.get('email')
    otp = request.data.get('otp')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')

    if not email: return api_response(None, "Email is required.", 400)
    try: user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist: return api_response(None, "User not found.", 404)

    if step == 'send_otp':
        user.otp = generate_otp()
        user.save()
        print(f"Sending OTP to {email}: {user.otp}")  # replace with email send logic
        return api_response(None, "OTP sent to your email.", 200)

    if step == 'verify_otp':
        if not otp: return api_response(None, "OTP is required.", 400)
        if str(user.otp) != str(otp): return api_response(None, "Invalid OTP.", 400)
        return api_response(None, "OTP verified successfully.", 200)

    if step == 'set_password':
        if not all([password, confirm_password]): return api_response(None, "Password and confirm password required.", 400)
        if password != confirm_password: return api_response(None, "Passwords do not match.", 400)
        user.password = make_password(password)
        user.otp = ''
        user.save()
        return api_response(AppUserSerializer(user).data, "Password reset successfully.", 200)

    return api_response(None, "Invalid request.", 400)