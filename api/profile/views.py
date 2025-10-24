from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from config.resp_messages import RM
from config.resp_middle import api_response
from myproject.permissions import IsNormalUser
from base.models import Language, UserInfo, Country
from .decorators import require_fields

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsNormalUser])
def get_profile(request):
    user = request.user
    return api_response({
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "language": getattr(user.language, "name", None),
            "avatar": user.avatar,
        },
        "info": getattr(user, "info", None) and {
            "school": user.info.school,
            "board": user.info.board,
            "current_class": user.info.user_class,
            "country": getattr(user.info.country, "name", None),
            "state": user.info.state,
            "city": user.info.city,
        }
    }, RM.common.SUCCESS, 200)

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsNormalUser])
@require_fields(['language', 'avatar', 'school', 'board', 'class', 'country', 'state', 'city'])
def update_profile(request):
    user, data = request.user, request.data

    if 'language' in data:
        try: user.language = Language.objects.get(id=data['language'])
        except Language.DoesNotExist: pass

    if 'avatar' in data: user.avatar = data['avatar']
    user.save()

    info, _ = UserInfo.objects.get_or_create(user=user)
    for field in ['school', 'board', 'class', 'state', 'city']:
        if field in data: setattr(info, 'user_class' if field == 'class' else field, data[field])

    if 'country' in data:
        try: info.country = Country.objects.get(id=data['country'])
        except Country.DoesNotExist: pass

    info.save()
    return api_response(None, RM.user.PROFILE_UPDATED, 200)

