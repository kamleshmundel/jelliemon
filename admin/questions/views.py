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

@api_view(['GET', 'POST', 'DELETE'])
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
            que_id = request.data.get('id')  # Question ID for updating
            unit_id = request.data.get('unit')

            # Check for required fields
            if not unit_id or not request.data.get('title'):
                return api_response(None, RM.common.REQUIRED_FIELDS, status=status.HTTP_400_BAD_REQUEST)

            # Check if unit exists
            try:
                unit = Unit.objects.get(id=unit_id)
            except Unit.DoesNotExist:
                return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

            # Handle optionImages (string -> boolean conversion)
            option_images_raw = request.data.get('optionImage', False)
            option_images = str(option_images_raw).lower() in ['true', '1']

            deleted_audio_urls = request.data.get('deletedAudio')  # Frontend sends array of full URLs

            # Check if it's a single string, and split it if necessary
            if deleted_audio_urls:
                if isinstance(deleted_audio_urls, str):
                    deleted_audio_urls = deleted_audio_urls.split(',')

            # Delete audio URLs from GCP if any
            if deleted_audio_urls:
                for url in deleted_audio_urls:
                    delete_audio_from_gcp(url.replace(settings.MEDIA_URL, ""))


            # If que_id exists, update the existing question, else create a new one
            if que_id:
                try:
                    # Update existing question
                    question = Question.objects.get(id=que_id)
                    question.unit = unit
                    question.title = request.data.get('title')
                    question.content = request.data.get('content', '')
                    question.type = request.data.get('type', 'mcq')
                    question.asset = request.FILES.get('asset', question.asset)  # Retain existing asset if not provided
                    question.option_images = option_images
                    question.hint = request.data.get('hint', question.hint)  # Retain existing hint if not provided

                    # Fetch audio from request
                    audio = request.FILES.get('audio')

                    # If the current audio exists and it is in the deleted_audio_urls, delete the existing audio
                    if question.audio and question.audio.url in deleted_audio_urls:
                        # If the URL of the current audio is in the deleted list, set the audio field to None
                        question.audio.delete()  # Deleting the audio file from storage
                        question.audio = None

                    # If a new audio file is provided, set the audio field to the new file
                    if audio:
                        question.audio = audio

                    # Save the updated question
                    question.save()

                except Question.DoesNotExist:
                    return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
            else:

                audio = request.FILES.get('audio')

                # If que_id does not exist, create a new question
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

            # Track existing answers
            existing_answers = {answer.text: answer for answer in Answer.objects.filter(question=question)}

            # Now, handle options (answers)
            index = 0
            received_answers = []  # To keep track of answers that are being sent

            while True:
                text_key = f"options[{index}][text]"
                correct_key = f"options[{index}][is_correct]"
                img_key = f"options[{index}][image]"

                ans_text = request.data.get(text_key)
                ans_correct = request.data.get(correct_key) in ['true', 'True', '1']
                ans_img = request.FILES.get(img_key)

                if not ans_text:
                    break  # Break when no more options are provided

                # Add to received answers
                received_answers.append(ans_text)

                # If it's an update (que_id exists), check if the option already exists
                if que_id:
                    if ans_text in existing_answers:
                        # Update the existing answer
                        answer = existing_answers[ans_text]
                        answer.text = ans_text
                        answer.is_correct = ans_correct
                        if ans_img:
                            answer.image = ans_img
                        answer.save()
                        # Remove from existing_answers to keep track of deleted options later
                        del existing_answers[ans_text]
                    else:
                        # Create new answer if it doesn't exist
                        if ans_img:
                            Answer.objects.create(question=question, text=ans_text, image=ans_img, is_correct=ans_correct)
                        else:
                            Answer.objects.create(question=question, text=ans_text, is_correct=ans_correct)

                else:
                    # If creating a new question, create new options
                    if ans_img:
                        Answer.objects.create(question=question, text=ans_text, image=ans_img, is_correct=ans_correct)
                    else:
                        Answer.objects.create(question=question, text=ans_text, is_correct=ans_correct)

                index += 1

            # After processing all incoming answers, delete the options that were not received
            for text, answer in existing_answers.items():
                answer.delete()

            # Return success response
            return api_response({'id': question.id}, RM.admin.QUE_ADDED, status.HTTP_201_CREATED if not que_id else status.HTTP_200_OK)

        except Exception as e:
            # Return error response if an exception occurs
            return api_response({'error': str(e)}, RM.common.SOMETHING_WRONG, status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    

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