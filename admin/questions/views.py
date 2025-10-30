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
        qs = Question.objects.select_related('unit').prefetch_related('answers').all().order_by('id')
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

    if request.method == 'POST':
        try:
            unit_id = request.data.get('unit')
            # Check for required fields
            if not unit_id or not request.data.get('title'):
                return api_response(None, "Required fields missing", status=status.HTTP_400_BAD_REQUEST)

            # Check if unit exists
            try:
                unit = Unit.objects.get(id=unit_id)
            except Unit.DoesNotExist:
                return api_response(None, "Unit not found", status=status.HTTP_404_NOT_FOUND)

            # Handle optionImages (string -> boolean conversion)
            option_images_raw = request.data.get('optionImage', False)
            option_images = str(option_images_raw).lower() in ['true', '1']

            audio = request.FILES.get('audio')

            # Create the new question
            question = Question.objects.create(
                unit=unit,
                title=request.data.get('title'),
                content=request.data.get('content', ''),
                type=request.data.get('type', 'mcq'),
                asset=request.FILES.get('asset'),
                option_images=option_images,
                hint=request.data.get('hint', ''),
                audio=audio
            )

            # Handle options (answers)
            index = 0
            while True:
                text_key = f"options[{index}][text]"
                correct_key = f"options[{index}][is_correct]"
                img_key = f"options[{index}][image]"

                ans_text = request.data.get(text_key)
                ans_correct = request.data.get(correct_key) in ['true', 'True', '1']
                ans_img = request.FILES.get(img_key)

                if not ans_text:
                    break  # Break when no more options are provided

                # Create answers
                if ans_img:
                    Answer.objects.create(question=question, text=ans_text, image=ans_img, is_correct=ans_correct)
                else:
                    Answer.objects.create(question=question, text=ans_text, is_correct=ans_correct)

                index += 1

            # Return success response
            return api_response({'id': question.id}, "Question created successfully", status=status.HTTP_201_CREATED)

        except Exception as e:
            # Return error response if an exception occurs
            return api_response({'error': str(e)}, "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    if request.method == 'PUT':
        try:
            que_id = request.data.get('id')  # Question ID for updating
            unit_id = request.data.get('unit')

            # Check for required fields
            if not unit_id or not request.data.get('title') or not que_id:
                return api_response(None, "Required fields missing", status=status.HTTP_400_BAD_REQUEST)

            # Check if unit exists
            try:
                unit = Unit.objects.get(id=unit_id)
            except Unit.DoesNotExist:
                return api_response(None, "Unit not found", status=status.HTTP_404_NOT_FOUND)

            # Handle optionImages (string -> boolean conversion)
            option_images_raw = request.data.get('optionImage', False)
            option_images = str(option_images_raw).lower() in ['true', '1']

            # Get the existing question to update
            try:
                question = Question.objects.get(id=que_id)
            except Question.DoesNotExist:
                return api_response(None, "Question not found", status=status.HTTP_404_NOT_FOUND)

            # Update the question
            question.unit = unit
            question.title = request.data.get('title')
            question.content = request.data.get('content', '')
            question.type = request.data.get('type', 'mcq')
            question.asset = request.FILES.get('asset', question.asset)  # Retain existing asset if not provided
            question.option_images = option_images
            question.hint = request.data.get('hint', question.hint)

            # Fetch audio from request and update if present
            audio = request.FILES.get('audio')
            if audio:
                question.audio = audio

            # Save the updated question
            question.save()

            # Handle the deletion of audio if the current audio is in the 'deletedAudio' list
            deleted_audio_urls = request.data.get('deletedAudio', [])
            if deleted_audio_urls and question.audio and question.audio.url in deleted_audio_urls:
                question.audio.delete()
                question.audio = None
                question.save()

            # Handle options (answers)
            index = 0
            existing_answers = {answer.text: answer for answer in Answer.objects.filter(question=question)}

            while True:
                text_key = f"options[{index}][text]"
                correct_key = f"options[{index}][is_correct]"
                img_key = f"options[{index}][image]"
                id_key = f"options[{index}][id]"  # Assuming you're sending answer ID

                ans_text = request.data.get(text_key)
                ans_correct = request.data.get(correct_key) in ['true', 'True', '1']
                ans_img = request.FILES.get(img_key)
                ans_id = request.data.get(id_key)

                if not ans_text:
                    break  # Break when no more options are provided

                if ans_id:
                    # Update existing answer
                    try:
                        answer = Answer.objects.get(id=ans_id, question=question)
                        answer.text = ans_text
                        answer.is_correct = ans_correct
                        if ans_img:
                            answer.image = ans_img
                        answer.save()

                        # Remove the updated answer from the existing answers
                        if ans_text in existing_answers:
                            del existing_answers[ans_text]
                    except Answer.DoesNotExist:
                        # If the answer doesn't exist, create a new one
                        if ans_img:
                            Answer.objects.create(question=question, text=ans_text, image=ans_img, is_correct=ans_correct)
                        else:
                            Answer.objects.create(question=question, text=ans_text, is_correct=ans_correct)
                else:
                    # If no ID provided, it's a new answer
                    if ans_img:
                        Answer.objects.create(question=question, text=ans_text, image=ans_img, is_correct=ans_correct)
                    else:
                        Answer.objects.create(question=question, text=ans_text, is_correct=ans_correct)

                index += 1

            # Handle deletion of answers that were not sent
            for text, answer in existing_answers.items():
                answer.delete()

            # Return success response
            return api_response({'id': question.id}, "Question updated successfully", status=status.HTTP_200_OK)

        except Exception as e:
            # Return error response if an exception occurs
            return api_response({'error': str(e)}, "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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