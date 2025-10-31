from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from base.models import Country, State, City, Language, Subject, Unit, UnitPart, Lesson, Question, Badge, Score
from config.resp_middle import paginated_response
from config.resp_messages import RM
from myproject.permissions import IsNormalUser, IsAdmin
from config.resp_middle import api_response
from rest_framework import status
from config.helpers import calculate_read_time_in_hours
from config.gcp import delete_audio_from_gcp
from django.conf import settings

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_countries(request):
    qs = Country.objects.all().order_by('name')
    return paginated_response(qs, request, lambda c: {"id": c.id, "name": c.name, "code": c.code})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_states(request):
    country_id = request.query_params.get('country_id')
    if not country_id:
        return api_response(None, RM.common.REQUIRED_FIELDS, status=status.HTTP_400_BAD_REQUEST)
    qs = State.objects.filter(country_id=country_id).order_by('name')
    return paginated_response(qs, request, lambda s: {"id": s.id, "name": s.name, "code": s.code, "country_id": s.country_id})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cities(request):
    state_id = request.query_params.get('state_id')
    if not state_id:
        return api_response(None, RM.common.REQUIRED_FIELDS, status=status.HTTP_400_BAD_REQUEST)
    qs = City.objects.filter(state_id=state_id).order_by('name')
    return paginated_response(qs, request, lambda c: {"id": c.id, "name": c.name, "state_id": c.state_id})

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
        board = request.GET.get('board')
        if board:
            qs = qs.filter(board=board)
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
        subject_id = request.GET.get('id') or request.data.get('id')
        try:
            subject = Subject.objects.get(id=subject_id)
            subject.delete()
            return api_response(None, RM.admin.SUBJECT_DELETED, status=status.HTTP_200_OK)
        except Subject.DoesNotExist:
            return api_response(None, RM.admin.NO_SUBJECT, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def lessons_view(request):
    if request.method == 'GET':
        subject_id = request.GET.get('subject')
        includesUnits = request.GET.get('includesUnits') == 'true'
        includesUnitsQue = request.GET.get('includesUnitsQue') == 'true'
        user = request.user

        qs = Lesson.objects.select_related('subject').prefetch_related('units__parts').all().order_by('title')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)

        def serialize_lesson(l):
            data = {
                "id": l.id,
                "title": l.title,
                "subject_id": l.subject.id,
                "subject_title": l.subject.name,
            }
            if includesUnits:
                units_data = []
                for u in l.units.all():
                    score = Score.objects.filter(user=user, unit=u).first()
                    unit_data = {
                        "id": u.id,
                        "title": u.title,
                        "parts": [{
                            "id": p.id, "title": p.title, "content": p.content,
                            "audio": p.audio.url if p.audio else None,

                        } for p in u.parts.all()],
                        "read_time": round(sum(calculate_read_time_in_hours(p.content) for p in u.parts.all()), 2),
                        "score": {
                            "earned": int(score.earned) if score else 0,
                            "out_of": int(score.out_of) if score else 0,
                        }
                    }
                    if includesUnitsQue:
                        unit_data["questions"] = [{
                            "id": q.id,
                            "title": q.title,
                            "content": q.content,
                            "type": q.type,
                            "asset": q.asset,
                            "hint": q.hint,
                            "answers": [{"id": a.id, "text": a.text, "is_correct": a.is_correct, "asset": a.image} for a in q.answers.all()]
                        } for q in Question.objects.filter(unit=u).prefetch_related('answers')]
                    units_data.append(unit_data)
                data["units"] = units_data
            return data

        return paginated_response(qs, request, serialize_lesson)


    if request.method == 'POST':
        lesson_id = request.data.get('id')
        title = request.data.get('title')
        subject_id = request.data.get('subjectId')
        if not title or not subject_id:
            return api_response(None, RM.common.REQUIRED_FIELDS, status=status.HTTP_400_BAD_REQUEST)
        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return api_response(None, RM.admin.NO_SUBJECT, status=status.HTTP_404_NOT_FOUND)
        if lesson_id:
            try:
                lesson = Lesson.objects.get(id=lesson_id)
                lesson.title = title
                lesson.subject = subject
                lesson.save()
                return api_response({"id": lesson.id, "title": lesson.title, "subject_id": subject.id, "subject_title": subject.name}, RM.common.SUCCESS, status.HTTP_200_OK)
            except Lesson.DoesNotExist:
                return api_response(None, RM.admin.NO_LESSION, status=status.HTTP_404_NOT_FOUND)
        else:
            lesson = Lesson.objects.create(title=title, subject=subject)
            return api_response({"id": lesson.id, "title": lesson.title, "subject_id": subject.id, "subject_title": subject.name}, RM.common.SUCCESS, status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        lesson_id = request.GET.get('id') or request.data.get('id')
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            lesson.delete()
            return api_response(None, RM.admin.LESSION_DELETED, status.HTTP_200_OK)
        except Lesson.DoesNotExist:
            return api_response(None, RM.admin.NO_LESSION, status=status.HTTP_404_NOT_FOUND)
        
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def units_view(request):
    if request.method == 'GET':
        unit_id = request.GET.get('unitId')
        lesson_id = request.GET.get('lessonId')
        include_questions = request.GET.get('includeQuestions')

        qs = Unit.objects.select_related('lesson').prefetch_related('parts').all().order_by('title')
        if unit_id:
            qs = qs.filter(id=unit_id)
        elif lesson_id:
            qs = qs.filter(lesson_id=lesson_id)

        def serialize_unit(u):
            score = Score.objects.filter(user=request.user, unit=u).first()

            data = {
                "id": u.id,
                "title": u.title,
                "lesson_id": u.lesson.id,
                "lesson_name": u.lesson.title,
                "parts": [{
                    "id": p.id, "title": p.title, "content": p.content,
                    "audio": p.audio.url if p.audio else None,
                } for p in u.parts.all()],
                "read_time": round(sum(calculate_read_time_in_hours(p.content) for p in u.parts.all()), 2),
                 "score": {
                    "earned": int(score.earned) if score else 0,
                    "out_of": int(score.out_of) if score else 0,
                },
            }
            if include_questions:
                questions = Question.objects.filter(unit=u).prefetch_related('answers').order_by('id')
                data["questions"] = [{
                    "id": q.id,
                    "title": q.title,
                    "content": q.content,
                    "type": q.type,
                    "asset": q.asset.url if q.asset else None,
                    "audio": q.audio.url if q.audio else None,
                    "hint": q.hint,
                    "answers": [{
                        "id": a.id, "text": a.text, "is_correct": a.is_correct,
                        "asset": a.image.url if a.image else None
                    } for a in q.answers.all()]
                } for q in questions]
            return data

        return paginated_response(qs, request, serialize_unit)

    if request.method == 'POST':
        unit_id = request.data.get('id')
        title = request.data.get('title')
        lesson_id = request.data.get('lessonId')
        deleted_audio_urls = request.data.get('deletedAudio')  # Frontend sends array of full URLs

        # Check if it's a single string, and split it if necessary
        if deleted_audio_urls:
            if isinstance(deleted_audio_urls, str):
                deleted_audio_urls = deleted_audio_urls.split(',')

        if not title or not lesson_id:
            return api_response(None, RM.common.REQUIRED_FIELDS, status=status.HTTP_400_BAD_REQUEST)

        # Validate lesson
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return api_response(None, RM.admin.NO_LESSION, status=status.HTTP_404_NOT_FOUND)

        # Create or update unit
        if unit_id:
            try:
                unit = Unit.objects.get(id=unit_id)
                unit.title = title  # Update title
                unit.lesson = lesson  # Update lesson
                unit.save()

                # Handle UnitParts (this is a simplified approach)
                unit.parts.all().delete()  # Remove all existing parts

            except Unit.DoesNotExist:
                return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        else:
            unit = Unit.objects.create(title=title, lesson=lesson)

        # Delete audio URLs from GCP if any
        if deleted_audio_urls:
            for url in deleted_audio_urls:
                delete_audio_from_gcp(url.replace(settings.MEDIA_URL, ""))

        # Parse the dynamic fields for unit parts (parts[0].title, parts[0].content, parts[0].audio, etc.)
        parts = []
        index = 0
        while True:
            title_key = f"parts[{index}].title"
            content_key = f"parts[{index}].content"
            audio_key = f"parts[{index}].audio"

            part_title = request.data.get(title_key)
            part_content = request.data.get(content_key)
            part_audio = request.FILES.get(audio_key)
            part_audio_url = request.data.get(audio_key)

            if not part_audio and part_audio_url:
                part_audio = part_audio_url

            if not part_content:
                break  # Stop when no more parts are found
            
            # Create or update parts
            if part_audio:  # New audio is uploaded
                part = UnitPart.objects.create(
                    unit=unit,
                    title=part_title,
                    content=part_content,
                    audio=part_audio
                )
            else:
                # No new audio, just update the text fields (title, content)
                part = UnitPart.objects.create(
                    unit=unit,
                    title=part_title,
                    content=part_content,
                    audio=part_audio
                )
            
            parts.append(part)
            index += 1

        # Response with the updated unit information
        return api_response({
            "id": unit.id,
            "title": unit.title,
            "lesson_id": lesson.id,
            "lesson_name": lesson.title,
            "parts": [
                {
                    "title": p.title,
                    "content": p.content,
                    "audio": p.audio.url if p.audio else None,
                }
                for p in unit.parts.all()
            ]
        }, RM.common.SUCCESS, status.HTTP_200_OK if unit_id else status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        unit_id = request.GET.get('id') or request.data.get('id')
        if not unit_id:
            return api_response(None, RM.common.REQUIRED_FIELDS, status=status.HTTP_400_BAD_REQUEST)

        try:
            unit = Unit.objects.get(id=unit_id)
        except Unit.DoesNotExist:
            return api_response(None, RM.admin.NO_UNIT, status=status.HTTP_404_NOT_FOUND)
        
        # Delete audio files from the UnitParts related to the unit
        unit_parts = UnitPart.objects.filter(unit=unit)
        for part in unit_parts:
            # Assuming 'audio' is the field storing the audio file URL in GCP
            if part.audio: delete_audio_from_gcp(part.audio.url.replace(settings.MEDIA_URL, ""))

        unit.delete()  # Cascade delete will remove UnitPart due to on_delete=models.CASCADE
        return api_response(None, RM.common.DELETED_SUCCESSFULLY, status=status.HTTP_200_OK)



    # if request.method == 'POST':
    #     unit_id = request.data.get('id')
    #     title = request.data.get('title')
    #     lesson_id = request.data.get('lessonId')
    #     parts = request.data.get('parts', [])

    #     if not title or not lesson_id:
    #         return api_response(None, RM.common.REQUIRED_FIELDS, status=status.HTTP_400_BAD_REQUEST)
    #     try:
    #         lesson = Lesson.objects.get(id=lesson_id)
    #     except Lesson.DoesNotExist:
    #         return api_response(None, RM.admin.NO_LESSION, status=status.HTTP_404_NOT_FOUND)

    #     if unit_id:
    #         try:
    #             unit = Unit.objects.get(id=unit_id)
    #             unit.title, unit.lesson = title, lesson
    #             unit.save()
    #             unit.parts.all().delete()
    #             for p in parts:
    #                 if p.get('title') and p.get('content'):
    #                     UnitPart.objects.create(unit=unit, title=p['title'], content=p['content'])
    #             return api_response({
    #                 "id": unit.id,
    #                 "title": unit.title,
    #                 "lesson_id": lesson.id,
    #                 "lesson_name": lesson.title,
    #                 "parts": [{"title": p.title, "content": p.content} for p in unit.parts.all()]
    #             }, RM.common.SUCCESS, status.HTTP_200_OK)
    #         except Unit.DoesNotExist:
    #             return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
    #     else:
    #         unit = Unit.objects.create(title=title, lesson=lesson)
    #         for p in parts:
    #             if p.get('title') and p.get('content'):
    #                 UnitPart.objects.create(unit=unit, title=p['title'], content=p['content'])
    #         return api_response({
    #             "id": unit.id,
    #             "title": unit.title,
    #             "lesson_id": lesson.id,
    #             "lesson_name": lesson.title,
    #             "parts": [{"title": p.title, "content": p.content} for p in unit.parts.all()]
    #         }, RM.common.SUCCESS, status.HTTP_201_CREATED)


    # if request.method == 'DELETE':
    #     unit_id = request.GET.get('id') or request.data.get('id')
    #     try:
    #         unit = Unit.objects.get(id=unit_id)
    #         unit.delete()
    #         return api_response(None, RM.common.SUCCESS, status.HTTP_200_OK)
    #     except Unit.DoesNotExist:
    #         return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def badges_view(request):
    if request.method == 'GET':
        badges = Badge.objects.all().order_by('name')
        data = [{"id": b.id, "name": b.name, } for b in badges]
        return api_response(data, RM.common.SUCCESS, status.HTTP_200_OK)

    if request.method == 'POST':
        return api_response(None, RM.common.SUCCESS, status.HTTP_200_OK)

    if request.method == 'DELETE':
        return api_response(None, RM.common.SUCCESS, status.HTTP_200_OK)