from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from base.models import Country, Language, Subject, Unit, Lesson, Question, Answer
from config.resp_middle import paginated_response
from config.resp_messages import RM
from myproject.permissions import IsNormalUser, IsAdmin
from config.resp_middle import api_response
from rest_framework import status

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def questions_view(request):
    if request.method == 'GET':

        unit_id = request.GET.get('unit_id')
        qs = Question.objects.select_related('unit').prefetch_related('answers').all().order_by('id')
        if unit_id:
            qs = qs.filter(unit_id=unit_id)

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
        # unit_id = request.GET.get('unit_id')
        # qs = Question.objects.select_related('unit').prefetch_related('answers').all().order_by('id')
        # if unit_id:
        #     qs = qs.filter(unit_id=unit_id)
        # return paginated_response(qs, request, lambda q: {
        #     "id": q.id,
        #     "title": q.title,
        #     "content": q.content,
        #     "type": q.type,
        #     "asset": q.asset,
        #     "option_images": q.option_images,
        #     "hint": q.hint,
        #     "unit_id": q.unit.id,
        #     "unit_title": q.unit.title,
        #     "answers": [{"id": a.id, "text": a.text, "image": a.image, "is_correct": a.is_correct} for a in q.answers.all()]
        # })

    if request.method == 'POST':

        try:
            unit_id = request.data.get('unit')
            if not unit_id or not request.data.get('title'):
                return api_response(None, RM.common.REQUIRED_FIELDS, status=status.HTTP_400_BAD_REQUEST)

            try:
                unit = Unit.objects.get(id=unit_id)
            except Unit.DoesNotExist:
                return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
            
            option_images_raw = request.data.get('optionImage', False)
            option_images = str(option_images_raw).lower() in ['true', '1']


            question = Question.objects.create(
                unit=unit,
                title=request.data.get('title'),
                content=request.data.get('content', ''),
                type=request.data.get('type', 'mcq'),
                asset=request.FILES.get('asset'),
                option_images=option_images,
                hint=request.data.get('hint', '')
            )

            options = request.data.getlist('options') or []
            for i, _ in enumerate(options):
                text = request.data.get(f'options[{i}][text]', '')
                is_correct_raw = request.data.get(f'options[{i}][is_correct]', False)
                is_correct = str(is_correct_raw).lower() in ['true', '1']  # ensures boolean
                image = request.FILES.get(f'options[{i}][image]')
                print('is_correct >>>>>>>>>>>>>>>>>>>>> ',is_correct)
                Answer.objects.create(question=question, text=text, image=image, is_correct=is_correct)


            return api_response({'id': question.id}, RM.admin.QUE_ADDED, status.HTTP_201_CREATED)

        except Exception as e:
            return api_response({'error': str(e)}, RM.common.SOMETHING_WRONG, status.HTTP_500_INTERNAL_SERVER_ERROR)

        # question_data = {
        #     "unit_id": request.data.get("unit"),
        #     "title": request.data.get("title"),
        #     "content": request.data.get("content"),
        #     "type": request.data.get("type"),
        #     "asset": request.data.get("asset"),
        #     "option_images": request.data.get("optionImage", False),
        #     "hint": request.data.get("hint"),
        # }

        # options = request.data.get("options", [])
        # answers = [*options] if isinstance(options, (list, tuple, set)) else [options]

        # unit_id = question_data["unit_id"]
        # if not unit_id or not question_data["title"]:
        #     return api_response(None, RM.common.REQUIRED_FIELDS, status=status.HTTP_400_BAD_REQUEST)

        # try:
        #     unit = Unit.objects.get(id=unit_id)
        # except Unit.DoesNotExist:
        #     return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        # question = Question.objects.create(
        #     unit=unit,
        #     title=question_data["title"],
        #     content=question_data["content"],
        #     type=question_data["type"],
        #     asset=question_data["asset"],
        #     option_images=question_data["option_images"],
        #     hint=question_data["hint"]
        # )

        # for ans in answers:
        #     Answer.objects.create(
        #         question=question,
        #         text=ans.get("text"),
        #         image=ans.get("image"),
        #         is_correct=ans.get("is_correct", False)
        #     )

        # return api_response({"id": question.id}, RM.admin.QUE_ADDED, status.HTTP_201_CREATED)