# api/admin_auth/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.hashers import check_password, make_password
from base.models import AppUser
from base.serializers import AppUserSerializer
from config.resp_middle import api_response
import jwt, datetime, random
from django.conf import settings

def generate_otp(): return str(random.randint(1000, 9999))

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    email, password = request.data.get('email'), request.data.get('password')
    if not email or not password: return api_response(None, "Email and password required.", 400)
    try: user = AppUser.objects.get(email=email, role=1)
    except AppUser.DoesNotExist: return api_response(None, "Invalid credentials.", 401)
    if not check_password(password, user.password): return api_response(None, "Invalid credentials.", 401)
    payload = {'user_id': str(user.id), 'email': user.email, 'role': user.role, 'exp': datetime.datetime.utcnow()+datetime.timedelta(hours=24)}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    user.token = token; user.save()
    return api_response({"token": token, "user": AppUserSerializer(user).data}, "Login successful.", 200)

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_forget_password(request):
    step = request.data.get('step', 'send_otp')
    email, otp, password, confirm = request.data.get('email'), request.data.get('otp'), request.data.get('password'), request.data.get('confirm_password')
    if not email: return api_response(None, "Email required.", 400)
    try: user = AppUser.objects.get(email=email, role=1)
    except AppUser.DoesNotExist: return api_response(None, "Admin not found.", 404)

    if step == 'send_otp':
        user.otp = generate_otp(); user.save()
        print(f"Sending OTP to {email}: {user.otp}")
        return api_response(None, "OTP sent to admin email.", 200)
    if step == 'verify_otp':
        if str(user.otp) != str(otp): return api_response(None, "Invalid OTP.", 400)
        return api_response(None, "OTP verified successfully.", 200)
    if step == 'set_password':
        if not all([password, confirm]): return api_response(None, "Password fields required.", 400)
        if password != confirm: return api_response(None, "Passwords do not match.", 400)
        user.password = make_password(password); user.otp = ''; user.save()
        return api_response(AppUserSerializer(user).data, "Password reset successfully.", 200)
    return api_response(None, "Invalid step.", 400)
