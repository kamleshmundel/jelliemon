from rest_framework import serializers
from .models import (
    AppUser, UserInfo, UserState, Subject, Unit, Lesson, Question,
    Progress, Badge, Product, Event
)

class AppUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ['id', 'email', 'phone', 'name', 'language', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        if not data.get('email') and not data.get('phone'):
            raise serializers.ValidationError("Either email or phone is required")
        return data

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = ['id', 'user', 'school', 'board', 'user_class', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserState
        fields = ['id', 'user', 'token', 'otp', 'current_step', 'last_login', 'last_logout_at']
        read_only_fields = ['id', 'last_login', 'last_logout_at']


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'lesson', 'stem', 'difficulty', 'options', 'correct_index', 'hints']
        read_only_fields = ['id']

    def validate_options(self, value):
        if not isinstance(value, list) or len(value) != 4:
            raise serializers.ValidationError("Options must be an array of exactly 4 items")
        return value

    def validate_correct_index(self, value):
        if value < 0 or value > 3:
            raise serializers.ValidationError("Correct index must be between 0 and 3")
        return value


class QuestionListSerializer(serializers.ModelSerializer):
    """Serializer for listing questions without showing correct answer"""
    class Meta:
        model = Question
        fields = ['id', 'stem', 'difficulty', 'options', 'hints']


class LessonSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ['id', 'unit', 'title', 'sort_order', 'status', 'questions_count']
        read_only_fields = ['id']

    def get_questions_count(self, obj):
        return obj.questions.count()


class LessonDetailSerializer(serializers.ModelSerializer):
    questions = QuestionListSerializer(many=True, read_only=True)
    unit_title = serializers.CharField(source='unit.title', read_only=True)
    
    class Meta:
        model = Lesson
        fields = ['id', 'unit', 'unit_title', 'title', 'sort_order', 'status', 'questions']
        read_only_fields = ['id']


class UnitSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Unit
        fields = ['id', 'subject', 'title', 'sort_order', 'lessons_count']
        read_only_fields = ['id']

    def get_lessons_count(self, obj):
        return obj.lessons.count()


class UnitDetailSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        model = Unit
        fields = ['id', 'subject', 'subject_name', 'title', 'sort_order', 'lessons']
        read_only_fields = ['id']


class SubjectSerializer(serializers.ModelSerializer):
    units_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = ['id', 'board', 'subject_class', 'name', 'units_count']
        read_only_fields = ['id']

    def get_units_count(self, obj):
        return obj.units.count()


class SubjectDetailSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)
    
    class Meta:
        model = Subject
        fields = ['id', 'board', 'subject_class', 'name', 'units']
        read_only_fields = ['id']


class ProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        model = Progress
        fields = [
            'user', 'subject', 'subject_name', 'lesson', 'lesson_title',
            'status', 'stars', 'badges', 'last_checkpoint', 'updated_at'
        ]
        read_only_fields = ['updated_at']


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['id', 'name', 'art_url', 'criteria_json']
        read_only_fields = ['id']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'image_url', 'external_url', 'tags']
        read_only_fields = ['id']


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'user', 'name', 'params_json', 'ts']
        read_only_fields = ['id', 'ts']
