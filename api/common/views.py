from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from base.models import Country, Language, Subject, Unit, Lesson
from config.resp_middle import paginated_response
from config.resp_messages import RM
from myproject.permissions import IsNormalUser, IsAdmin
from config.resp_middle import api_response
from rest_framework import status

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


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def subjects_view(request):
    if request.method == 'GET':
        qs = Subject.objects.all().order_by('name')
        return paginated_response(qs, request, lambda l: {"id": l.id, "board": l.board, "name": l.name})
    
    if request.method == 'POST':
        subject_id = request.data.get('id')
        name = request.data.get('name')
        board = request.data.get('board')
        if not name or not board:
            return api_response(None, RM.common.REQUIRED_FIELDS, status=status.HTTP_400_BAD_REQUEST)
        if subject_id:
            try:
                subject = Subject.objects.get(id=subject_id)
                subject.name = name
                subject.board = board
                subject.save()
                return api_response({"id": subject.id, "name": subject.name, "board": subject.board}, RM.common.SUCCESS, status.HTTP_200_OK)
            except Subject.DoesNotExist:
                return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        else:
            subject = Subject.objects.create(name=name, board=board)
            return api_response({"id": subject.id, "name": subject.name, "board": subject.board}, RM.common.SUCCESS, status.HTTP_201_CREATED)
    
    if request.method == 'DELETE':
        subject_id = request.data.get('id')
        try:
            subject = Subject.objects.get(id=subject_id)
            subject.delete()
            return api_response(None, RM.common.SUCCESS, status=status.HTTP_200_OK)
        except Subject.DoesNotExist:
            return api_response(None, RM.admin.NO_SUBJECT, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def units_view(request):
    if request.method == 'GET':
        subject_id = request.GET.get('subjectId')
        qs = Unit.objects.select_related('subject').all().order_by('title')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        return paginated_response(qs, request, lambda u: {"id": u.id, "title": u.title, "subject_id": u.subject.id, "subject_name": u.subject.name})


    if request.method == 'POST':
        unit_id = request.data.get('id')
        title = request.data.get('title')
        subject_id = request.data.get('subjectId')
        if not title or not subject_id:
            return api_response(None, RM.common.REQUIRED_FIELDS, status=status.HTTP_400_BAD_REQUEST)
        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        if unit_id:
            try:
                unit = Unit.objects.get(id=unit_id)
                unit.title = title
                unit.subject = subject
                unit.save()
                return api_response({"id": unit.id, "title": unit.title, "subject_id": subject.id, "subject_name": subject.name}, RM.common.SUCCESS, status.HTTP_200_OK)
            except Unit.DoesNotExist:
                return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        else:
            unit = Unit.objects.create(title=title, subject=subject)
            return api_response({"id": unit.id, "title": unit.title, "subject_id": subject.id, "subject_name": subject.name}, RM.common.SUCCESS, status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        unit_id = request.data.get('id')
        try:
            unit = Unit.objects.get(id=unit_id)
            unit.delete()
            return api_response({"success": True}, RM.common.SUCCESS, status.HTTP_200_OK)
        except Unit.DoesNotExist:
            return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def lessons_view(request):
    if request.method == 'GET':
        unit_id = request.GET.get('unit')
        qs = Lesson.objects.select_related('unit').all().order_by('title')
        if unit_id:
            qs = qs.filter(unit_id=unit_id)
        return paginated_response(qs, request, lambda l: {"id": l.id, "title": l.title, "unit_id": l.unit.id, "unit_title": l.unit.title})

    if request.method == 'POST':
        lesson_id = request.data.get('id')
        title = request.data.get('title')
        unit_id = request.data.get('unitId')
        if not title or not unit_id:
            return api_response(None, RM.common.REQUIRED_FIELDS, status=status.HTTP_400_BAD_REQUEST)
        try:
            unit = Unit.objects.get(id=unit_id)
        except Unit.DoesNotExist:
            return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        if lesson_id:
            try:
                lesson = Lesson.objects.get(id=lesson_id)
                lesson.title = title
                lesson.unit = unit
                lesson.save()
                return api_response({"id": lesson.id, "title": lesson.title, "unit_id": unit.id, "unit_title": unit.title}, RM.common.SUCCESS, status.HTTP_200_OK)
            except Lesson.DoesNotExist:
                return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        else:
            lesson = Lesson.objects.create(title=title, unit=unit)
            return api_response({"id": lesson.id, "title": lesson.title, "unit_id": unit.id, "unit_title": unit.title}, RM.common.SUCCESS, status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        lesson_id = request.GET.get('id') or request.data.get('id')
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            lesson.delete()
            return api_response({"success": True}, RM.admin.LESSION_DELETED, status.HTTP_200_OK)
        except Lesson.DoesNotExist:
            return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)