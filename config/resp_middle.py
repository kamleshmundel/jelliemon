# utils.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from config.resp_messages import RM
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

def api_response(data=None, message='', status=200):
    return Response({"data": data, "message": message, "status": status}, status=status)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

def paginated_response(queryset, request, serializer_func):
    """
    Returns paginated or full response consistently for any queryset.
    - no_pagination=true => returns all items
    - otherwise => paginated response with next/previous/count
    """
    if request.query_params.get('no_pagination') == 'true':
        data = [serializer_func(obj) for obj in queryset]
        return api_response(data, RM.common.SUCCESS, 200)

    paginator = StandardResultsSetPagination()
    result_page = paginator.paginate_queryset(queryset, request)
    data = [serializer_func(obj) for obj in result_page]

    # Wrap the paginated response in api_response format
    paginated_data = {
        "count": paginator.page.paginator.count,
        "next": paginator.get_next_link(),
        "previous": paginator.get_previous_link(),
        "results": data
    }
    return api_response(paginated_data, RM.common.SUCCESS, 200)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Override the response to match your api_response format
        custom_response = {
            "data": None,
            "message": str(exc.detail),
            "status": response.status_code
        }
        return Response(custom_response, status=response.status_code)

    return response

class JsonErrorMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if settings.DEBUG:
            return None  # show Django debug page in development
        return JsonResponse({
            "data": None,
            "message": str(exception),
            "status": 500
        }, status=500)