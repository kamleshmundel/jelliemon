# translate_middleware.py
from django.utils.deprecation import MiddlewareMixin
from .resp_messages import tr
import json

class TranslateResponseMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        try:
            if hasattr(response, 'data') and isinstance(response.data, dict) and "message" in response.data:
                msg = tr(response.data["message"], getattr(request, 'user', None))
                response.data["message"] = msg
                response.content = json.dumps(response.data).encode('utf-8')
        except Exception as e:
            print("Translation middleware error:", e)
        return response
