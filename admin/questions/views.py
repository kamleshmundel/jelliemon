from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from base.models import Country, Language, Subject, Unit, Lesson, Question, Answer
from config.resp_middle import paginated_response
from config.resp_messages import RM
from myproject.permissions import IsNormalUser, IsAdmin
from config.resp_middle import api_response
from rest_framework import status

from config.gcp import delete_audio_from_gcp
from django.conf import settings

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def questions_view(request):
    if request.method == 'GET':
        que_id = request.GET.get('queId')
        unit_id = request.GET.get('unit_id')
        qs = Question.objects.select_related('unit__lesson__subject').prefetch_related('answers').all().order_by('id')
        if unit_id:
            qs = qs.filter(unit_id=unit_id)
        
        if que_id:
            qs = qs.filter(id=que_id)

        def serialize_question(q):
            return {
                "id": q.id,
                "title": q.title,
                "content": q.content,
                "type": q.type,
                "asset": q.asset.url if q.asset else None,
                "option_images": q.option_images,
                "hint": q.hint,
                "unit_id": q.unit.id,
                "unit_title": q.unit.title,
                "audio": q.audio.url if q.audio else None,
                "subject_id":q.unit.lesson.subject.id,
                "lesson_id":q.unit.lesson.id,
                "unit_id":q.unit.id,
                "answers": [
                    {
                        "id": a.id,
                        "text": a.text,
                        "image": a.image.url if a.image else None,
                        "is_correct": a.is_correct
                    } for a in q.answers.all()
                ]
            }

        return paginated_response(qs, request, serialize_question)

    

    if request.method == "POST":
        try:
            unit_id = request.data.get("unit")
            title = request.data.get("title")

            if not unit_id or not title:
                return api_response(None, "Required fields missing", status=status.HTTP_400_BAD_REQUEST)

            try:
                unit = Unit.objects.get(id=unit_id)
            except Unit.DoesNotExist:
                return api_response(None, "Unit not found", status=status.HTTP_404_NOT_FOUND)

            option_images = str(request.data.get("optionImage", False)).lower() in ["true", "1"]
            audio = request.FILES.get("audio")

            question = Question.objects.create(
                unit=unit,
                title=title,
                content=request.data.get("content", ""),
                type=request.data.get("type", "mcq"),
                asset=request.FILES.get("asset"),
                option_images=option_images,
                hint=request.data.get("hint", ""),
                audio=audio,
            )

            index = 0
            while True:
                text_key = f"options[{index}][text]"
                correct_key = f"options[{index}][is_correct]"
                img_key = f"options[{index}][image]"

                ans_text = request.data.get(text_key)
                if not ans_text:
                    break

                ans_correct = request.data.get(correct_key) in ["true", "True", "1"]
                ans_img = request.FILES.get(img_key)

                Answer.objects.create(
                    question=question,
                    text=ans_text,
                    image=ans_img if ans_img else None,
                    is_correct=ans_correct,
                )
                index += 1

            return api_response({"id": question.id}, "Question created successfully", status=status.HTTP_201_CREATED)

        except Exception as e:
            return api_response({"error": str(e)}, "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ------------------------ UPDATE ------------------------
    if request.method == "PUT":
        try:
            que_id = request.data.get("id")
            unit_id = request.data.get("unit")
            title = request.data.get("title")

            if not que_id or not unit_id or not title:
                return api_response(None, "Required fields missing", status=status.HTTP_400_BAD_REQUEST)

            try:
                unit = Unit.objects.get(id=unit_id)
            except Unit.DoesNotExist:
                return api_response(None, "Unit not found", status=status.HTTP_404_NOT_FOUND)

            try:
                question = Question.objects.get(id=que_id)
            except Question.DoesNotExist:
                return api_response(None, "Question not found", status=status.HTTP_404_NOT_FOUND)

            option_images = str(request.data.get("optionImage", False)).lower() in ["true", "1"]
            question.unit = unit
            question.title = title
            question.content = request.data.get("content", "")
            question.type = request.data.get("type", "mcq")
            question.option_images = option_images
            question.hint = request.data.get("hint", question.hint)

            asset_file = request.FILES.get("asset")
            if asset_file:
                question.asset = asset_file

            audio_file = request.FILES.get("audio")
            if audio_file:
                question.audio = audio_file

            question.save()

            # Delete audio if requested
            deleted_audio_urls = request.data.get("deletedAudio", [])
            if deleted_audio_urls and question.audio and question.audio.url in deleted_audio_urls:
                question.audio.delete()
                question.audio = None
                question.save()

            # Update answers
            index = 0
            existing_answers = {a.id: a for a in Answer.objects.filter(question=question)}

            while True:
                text_key = f"options[{index}][text]"
                correct_key = f"options[{index}][is_correct]"
                img_key = f"options[{index}][image]"
                id_key = f"options[{index}][id]"

                ans_text = request.data.get(text_key)
                if not ans_text:
                    break

                ans_correct = request.data.get(correct_key) in ["true", "True", "1"]
                ans_img = request.FILES.get(img_key)
                ans_id = request.data.get(id_key)

                if ans_id and ans_id.isdigit() and int(ans_id) in existing_answers:
                    ans = existing_answers.pop(int(ans_id))
                    ans.text = ans_text
                    ans.is_correct = ans_correct
                    if ans_img:
                        ans.image = ans_img
                    ans.save()
                else:
                    Answer.objects.create(
                        question=question,
                        text=ans_text,
                        image=ans_img if ans_img else None,
                        is_correct=ans_correct,
                    )

                index += 1

            # Delete answers not re-sent
            for ans in existing_answers.values():
                ans.delete()

            return api_response({"id": question.id}, "Question updated successfully", status=status.HTTP_200_OK)

        except Exception as e:
            return api_response({"error": str(e)}, "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if request.method == 'DELETE':
        que_id = request.GET.get('id') or request.data.get('id')
        if not que_id:
            return api_response(None, RM.common.REQUIRED_FIELDS, status=status.HTTP_400_BAD_REQUEST)

        try:
            question = Question.objects.get(id=que_id)
        except Question.DoesNotExist:
            return api_response(None, RM.admin.NO_QUE, status=status.HTTP_404_NOT_FOUND)

        if question.audio: delete_audio_from_gcp(question.audio.url.replace(settings.MEDIA_URL, ""))
        
        question.delete()  # Cascade delete will remove UnitPart due to on_delete=models.CASCADE
        return api_response(None, RM.common.DELETED_SUCCESSFULLY, status=status.HTTP_200_OK)