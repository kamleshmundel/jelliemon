from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from base.models import AppUser
from base.serializers import AppUserSerializer
from rest_framework import status
import random, jwt, datetime
from rest_framework.response import Response
from config.resp_middle import api_response

def generate_otp(): return str(random.randint(1000, 9999))

@api_view(['POST'])
@permission_classes([AllowAny])
def auth_handler(request):
    action, mode = request.data.get('action'), request.data.get('mode')
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
