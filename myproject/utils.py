import jwt, datetime
from django.conf import settings

def create_access_token(data: dict, exp_hours=30):
    payload = {**data, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=exp_hours)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def create_refresh_token(data: dict, exp_days=30):
    payload = {**data, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=exp_days)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
