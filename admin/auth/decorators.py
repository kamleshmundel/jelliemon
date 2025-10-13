from functools import wraps
from django.contrib.auth.hashers import check_password
from config.resp_middle import api_response
from config.resp_messages import RM
from base.models import AppUser
from config.conatants import ROLES

def require_fields(fields):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            data = getattr(request, 'data', {})
            missing = [f for f in fields if not data.get(f)]
            if missing:
                return api_response(None, f"Missing fields: {', '.join(missing)}", 400)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def ensure_admin_exists(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        email = request.data.get('email') or getattr(request.user, 'email', None)
        try:
            user = AppUser.objects.get(email=email, role=ROLES.ADMIN)
        except AppUser.DoesNotExist:
            return api_response(None, RM.admin.ADMIN_NOT_FOUND, 404)
        request.admin_user = user
        return view_func(request, *args, **kwargs)
    return wrapper

def verify_admin_password(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = getattr(request, 'admin_user', None)
        password = request.data.get('password')
        if not user or not check_password(password, user.password):
            return api_response(None, RM.common.INVALID_CREDENTIALS, 401)
        return view_func(request, *args, **kwargs)
    return wrapper

def validate_forget_password_fields(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        data = getattr(request, 'data', {})
        step = data.get('step')
        if not step:
            return api_response(None, "Missing field: step", 400)

        allowed_fields = {'send_otp': ['email', 'step'],
                          'verify_otp': ['email', 'step', 'otp'],
                          'set_password': ['email', 'step', 'password', 'confirm_password']}.get(step, [])

        missing = [f for f in allowed_fields if f not in data or data[f] in [None, '']]
        extra = [f for f in data if f not in allowed_fields]

        if missing:
            return api_response(None, f"Missing fields: {', '.join(missing)}", 400)
        if extra:
            return api_response(None, f"Unexpected fields: {', '.join(extra)}", 400)

        return view_func(request, *args, **kwargs)
    return wrapper
