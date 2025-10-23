from functools import wraps
from config.resp_middle import api_response

def require_fields(fields):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            data = getattr(request, 'data', {})
            missing = [f for f in fields if f in data and not data.get(f)]
            if missing:
                return api_response(None, f"Missing fields: {', '.join(missing)}", 400)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
