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
            "class": user.info.user_class,
            "country": getattr(user.info.country, "name", None),
            "state": user.info.state,
            "city": user.info.city,
        }
    }, RM.common.SUCCESS, 200)

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsNormalUser])
@require_fields(['language', 'school', 'board', 'class', 'country', 'state', 'city'])
def update_profile(request):
    user = request.user
    data = request.data

    if lid := data.get('language'):
        try: user.language = Language.objects.get(id=lid)
        except Language.DoesNotExist: pass

    user.avatar = data.get('avatar', user.avatar)
    user.save()

    info, _ = UserInfo.objects.get_or_create(user=user)
    info.school = data.get('school', info.school)
    info.board = data.get('board', info.board)
    info.user_class = data.get('class', info.user_class)
    if cid := data.get('country'):
        try: info.country = Country.objects.get(id=cid)
        except Country.DoesNotExist: pass
    info.state = data.get('state', info.state)
    info.city = data.get('city', info.city)
    info.save()

    return api_response(None, RM.user.PROFILE_UPDATED, 200)

