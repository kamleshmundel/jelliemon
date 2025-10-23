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
        lesson_id = request.GET.get('lesson_id')
        qs = Question.objects.select_related('lesson').prefetch_related('answers').all().order_by('id')
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        return paginated_response(qs, request, lambda q: {
            "id": q.id,
            "title": q.title,
            "content": q.content,
            "type": q.type,
            "asset": q.asset,
            "option_images": q.option_images,
            "hint": q.hint,
            "lesson_id": q.lesson.id,
            "lesson_title": q.lesson.title,
            "answers": [{"id": a.id, "text": a.text, "image": a.image, "is_correct": a.is_correct} for a in q.answers.all()]
        })

    if request.method == 'POST':
        question_data = {
            "lesson_id": request.data.get("lesson"),
            "title": request.data.get("title"),
            "content": request.data.get("content"),
            "type": request.data.get("type"),
            "asset": request.data.get("asset"),
            "option_images": request.data.get("optionImage", False),
            "hint": request.data.get("hint"),
        }

        options = request.data.get("options", [])
        answers = [*options] if isinstance(options, (list, tuple, set)) else [options]

        lesson_id = question_data["lesson_id"]
        if not lesson_id or not question_data["title"]:
            return api_response(None, RM.common.PASSWORD_MISMATCH, status=status.HTTP_400_BAD_REQUEST)

        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return api_response(None, RM.common.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        question = Question.objects.create(
            lesson=lesson,
            title=question_data["title"],
            content=question_data["content"],
            type=question_data["type"],
            asset=question_data["asset"],
            option_images=question_data["option_images"],
            hint=question_data["hint"]
        )

        for ans in answers:
            Answer.objects.create(
                question=question,
                text=ans.get("text"),
                image=ans.get("image"),
                is_correct=ans.get("is_correct", False)
            )

        return api_response({"id": question.id}, RM.admin.QUE_ADDED, status.HTTP_201_CREATED)