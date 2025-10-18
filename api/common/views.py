from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from base.models import Country, Language
from config.resp_middle import paginated_response
from config.resp_messages import RM
from myproject.permissions import IsNormalUser, IsAdmin

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_countries(request):
    qs = Country.objects.all().order_by('name')
    return paginated_response(qs, request, lambda c: {"id": c.id, "name": c.name, "code": c.code})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_languages(request):
    qs = Language.objects.all().order_by('name')
    return paginated_response(qs, request, lambda l: {"id": l.id, "name": l.name, "code": l.code})