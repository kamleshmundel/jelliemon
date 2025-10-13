# authentication.py
import jwt, datetime
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from base.models import AppUser
from datetime import datetime, timezone as dt_timezone

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

            # Check if user is active
            if not user.is_active:
                raise AuthenticationFailed('User inactive')

            # Convert iat to aware datetime in UTC
            issued_at = datetime.fromtimestamp(payload.get('iat', 0), tz=dt_timezone.utc)

            # Ensure last_logout_at is also in UTC (Django stores aware datetimes)
            last_logout = user.last_logout_at

            if last_logout and issued_at <= last_logout.astimezone(dt_timezone.utc):
                raise AuthenticationFailed('Token invalid after logout')

            request.user = user
            return (user, None)

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expired')
        except jwt.DecodeError:
            raise AuthenticationFailed('Invalid token')
        except AppUser.DoesNotExist:
            raise AuthenticationFailed('User not found')
