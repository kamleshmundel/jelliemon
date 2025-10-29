import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

from config.conatants import AvatarChoices

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
    language = models.ForeignKey('Language', null=True, blank=True, on_delete=models.SET_NULL, related_name='users')
    avatar = models.CharField(max_length=50, choices=AvatarChoices.choices, null=True, blank=True)
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
    id = models.AutoField(primary_key=True)
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
    
class Country(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'country'
        ordering = ['name']

    def __str__(self):
        return self.name

class State(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'state'
        unique_together = ('name', 'country')
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class City(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'city'
        unique_together = ('name', 'state')
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.state.name}"

class UserInfo(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE, related_name='info')
    school = models.CharField(max_length=255, null=True, blank=True)
    board = models.CharField(max_length=255, null=True, blank=True)
    user_class = models.CharField(max_length=50, null=True, blank=True, db_column='user_class')
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL, related_name='user_infos')
    state = models.ForeignKey(State, null=True, blank=True, on_delete=models.SET_NULL, related_name='user_infos')
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.SET_NULL, related_name='user_infos')
    xp = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_info'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.name} Info"
    
class Language(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'language'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class Subject(models.Model):
    id = models.AutoField(primary_key=True)
    board = models.CharField(max_length=100)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'subject'
        ordering = ['board', 'name']

    def __str__(self):
        return f"{self.name} - {self.board}"


class Lesson(models.Model):
    id = models.AutoField(primary_key=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)

    class Meta:
        db_table = 'lesson'
        ordering = ['title']

    def __str__(self):
        return self.title


class Unit(models.Model):
    id = models.AutoField(primary_key=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='units')
    title = models.CharField(max_length=255)

    class Meta:
        db_table = 'unit'
        ordering = ['title']

    def __str__(self):
        return self.title

class UnitPart(models.Model):
    id = models.AutoField(primary_key=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='parts')
    title = models.TextField()
    content = models.TextField()
    audio = models.ImageField(upload_to='audio/', null=True, blank=True)

    class Meta:
        db_table = 'unit_parts'
        indexes = [models.Index(fields=['unit'], name='idx_unitpart_unit')]
        ordering = ['title']

    def __str__(self):
        return self.title

class Question(models.Model):
    TYPE_CHOICES = [
        ('ssl', 'Single Selection'),
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
    ]

    id = models.AutoField(primary_key=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='questions')
    title = models.CharField(max_length=255)
    content = models.TextField()
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='mcq')
    asset = models.ImageField(upload_to='questions/', null=True, blank=True)
    option_images = models.BooleanField(default=False)
    hint = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'question'
        indexes = [models.Index(fields=['unit'], name='idx_question_unit')]
        ordering = ['title']

    def __str__(self):
        return self.title

class Answer(models.Model):
    id = models.AutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='answers/', null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = 'answer'
        indexes = [models.Index(fields=['question'], name='idx_answer_question')]
        ordering = ['id']

    def __str__(self):
        return f"Answer to Q{self.question_id}: {self.text or self.image}"

class Score(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='scores')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='scores')
    earned = models.FloatField(default=0)
    out_of = models.FloatField(default=0)

    class Meta:
        db_table = 'score'
        indexes = [
            models.Index(fields=['user'], name='idx_score_user'),
            models.Index(fields=['unit'], name='idx_score_unit'),
        ]
        unique_together = ('user', 'unit')
        ordering = ['unit']

    def __str__(self):
        return f"{self.user.name} - {self.lesson.title}: {self.earned}/{self.out_of}"

class Badge(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    art_url = models.URLField(null=True, blank=True)
    criteria_json = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'badge'

    def __str__(self):
        return self.name

class UserBadge(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='users')
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_badge'
        unique_together = ('user', 'badge')
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.user.name} - {self.badge.title}"

class Product(models.Model):
    id = models.AutoField(primary_key=True)
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
