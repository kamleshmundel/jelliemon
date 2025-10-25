from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from config.resp_messages import RM
from config.resp_middle import api_response
from myproject.permissions import IsNormalUser
from base.models import Language, UserInfo, Country, State, City
from .decorators import require_fields
from rest_framework import status

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
            "language": {
                "id": user.language.id,
                "name": user.language.name,
            } if getattr(user, "language", None) else None,
            "avatar": user.avatar,
        },
        "info": getattr(user, "info", None) and {
            "school": user.info.school,
            "board": user.info.board,
            "current_class": user.info.user_class,
            "country": getattr(user.info.country, "name", None),
            "state": user.info.state,
            "city": user.info.city,
        },
        "checkpoint" : [{
            "subject_id": 1,
            "last_lesson_id": 1,
            "stars": [
                { "lesson_id": 1, "stars": 2, },
                { "lesson_id": 2, "stars": 3, },
            ]
        }],
        "stars": {
            "earned": 10,
            "total": 30,
        }
    }, RM.common.SUCCESS, 200)

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsNormalUser])
@require_fields(['language', 'avatar', 'school', 'board', 'class', 'country', 'state', 'city'])
def update_profile(request):
    user, data = request.user, request.data

    if 'language' in data:
        try: user.language = Language.objects.get(id=data['language'])
        except Language.DoesNotExist: return api_response(None, RM.common.LANG_FOUND, status=status.HTTP_400_BAD_REQUEST)

    if 'avatar' in data: user.avatar = data['avatar']
    if 'name' in data: user.name = data['name']
    user.save()

    info, _ = UserInfo.objects.get_or_create(user=user)

    if 'school' in data: info.school = data['school']
    if 'board' in data: info.board = data['board']
    if 'class' in data: info.user_class = data['class']

    if 'country' in data:
        try: info.country = Country.objects.get(id=data['country'])
        except Country.DoesNotExist: return api_response(None, RM.common.COUNTRY_FOUND, status=status.HTTP_400_BAD_REQUEST)

    if 'state' in data:
        try: info.state = State.objects.get(id=data['state'])
        except State.DoesNotExist: return api_response(None, RM.common.STATE_FOUND, status=status.HTTP_400_BAD_REQUEST)

    if 'city' in data:
        try: info.city = City.objects.get(id=data['city'])
        except City.DoesNotExist: return api_response(None, RM.common.CITY_FOUND, status=status.HTTP_400_BAD_REQUEST)

    info.save()
    return api_response(None, RM.user.PROFILE_UPDATED, 200)
