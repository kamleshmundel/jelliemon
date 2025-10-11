from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from base.models import AppUser
from base.serializers import AppUserSerializer
from rest_framework.decorators import authentication_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from myproject.permissions import IsNormalUser
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsNormalUser])
def getData(request):
  users = AppUser.objects.all()
  serializer = AppUserSerializer(users, many=True)
  return Response(serializer.data)