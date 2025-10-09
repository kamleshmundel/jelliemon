# utils.py
import jwt, datetime
from django.conf import settings

def create_access_token(user_id):
    return jwt.encode(
        {'user_id': user_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)},
        settings.SECRET_KEY, algorithm='HS256'
    )

def create_refresh_token(user_id):
    return jwt.encode(
        {'user_id': user_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)},
        settings.SECRET_KEY, algorithm='HS256'
    )