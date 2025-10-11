# authentication.py
import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from base.models import AppUser

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        try:
            token_type, token = auth_header.split()
            if token_type.lower() != 'bearer':
                raise AuthenticationFailed('Invalid token header')
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = AppUser.objects.get(id=payload['user_id'])
            request.user = user
            return (user, None)
        except (jwt.ExpiredSignatureError, jwt.DecodeError, AppUser.DoesNotExist):
            raise AuthenticationFailed('Invalid or expired token')