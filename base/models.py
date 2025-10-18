import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class AppUserManager(BaseUserManager):
    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError('Either email or phone must be set')
        if email:
            email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, phone, password, **extra_fields)

class AppUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    language = models.CharField(max_length=50, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    password = models.CharField(max_length=128, null=True, blank=True)
    role = models.PositiveSmallIntegerField(default=0)  # 0=user, 1=admin
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AppUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'app_user'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email or self.phone})"
    
class UserState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE, related_name='state')
    token = models.TextField(null=True, blank=True)
    otp = models.IntegerField(null=True, blank=True)
    current_step = models.CharField(max_length=255, null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    last_logout_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'user_state'
        ordering = ['-last_login']

    def __str__(self):
        return f"{self.user.name} State"
    
class UserInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE, related_name='info')
    school = models.CharField(max_length=255, null=True, blank=True)
    board = models.CharField(max_length=255, null=True, blank=True)
    user_class = models.CharField(max_length=50, null=True, blank=True, db_column='class')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_info'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.name} Info"

class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.CharField(max_length=100)
    subject_class = models.CharField(max_length=50, db_column='class')
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'subject'
        ordering = ['board', 'subject_class', 'name']

    def __str__(self):
        return f"{self.name} - {self.board} ({self.subject_class})"


class Unit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='units')
    title = models.CharField(max_length=255)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'unit'
        ordering = ['sort_order', 'title']

    def __str__(self):
        return self.title


class Lesson(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    sort_order = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    class Meta:
        db_table = 'lesson'
        ordering = ['sort_order', 'title']

    def __str__(self):
        return self.title


class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('normal', 'Normal'),
        ('hard', 'Hard'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions')
    stem = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='normal')
    options = models.JSONField()  # Array of 4 options
    correct_index = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(3)])
    hints = models.JSONField(default=list)

    class Meta:
        db_table = 'question'
        indexes = [
            models.Index(fields=['lesson'], name='idx_question_lesson'),
        ]

    def __str__(self):
        return f"Q: {self.stem[:50]}..."


class Progress(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='progress')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    stars = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    badges = models.JSONField(default=list)
    last_checkpoint = models.JSONField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'progress'
        unique_together = ['user', 'lesson']

    def __str__(self):
        return f"{self.user.name} - {self.lesson.title} ({self.status})"


class Badge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    art_url = models.URLField(null=True, blank=True)
    criteria_json = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'badge'

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    image_url = models.URLField(null=True, blank=True)
    external_url = models.URLField()
    tags = ArrayField(models.CharField(max_length=50), default=list, blank=True)

    class Meta:
        db_table = 'product'

    def __str__(self):
        return self.title


class Event(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    params_json = models.JSONField(null=True, blank=True)
    ts = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'event'
        ordering = ['-ts']
        indexes = [
            models.Index(fields=['user', '-ts']),
            models.Index(fields=['name', '-ts']),
        ]

    def __str__(self):
        return f"{self.name} - {self.ts}"
