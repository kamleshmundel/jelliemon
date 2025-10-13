import jwt, datetime
from django.conf import settings

def create_access_token(data: dict, exp_hours=30):
    now = datetime.datetime.utcnow()
    payload = {**data, 'iat': now, 'exp': now + datetime.timedelta(hours=exp_hours)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def create_refresh_token(data: dict, exp_days=30):
    now = datetime.datetime.utcnow()
    payload = {**data, 'iat': now, 'exp': now + datetime.timedelta(days=exp_days)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def generate_tokens(u, AppUserSerializer):
    data = {'user_id': str(u.id), 'role': u.role}
    access, refresh = create_access_token(data), create_refresh_token(data)
    u.token = refresh; u.save()
    return {"access": access, "refresh": refresh, "user": AppUserSerializer(u).data}