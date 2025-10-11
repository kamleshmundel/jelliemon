# utils.py
from rest_framework.response import Response

def api_response(data=None, message='', status=200):
    return Response({"data": data, "message": message, "status": status}, status=status)
