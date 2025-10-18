from enum import IntEnum, Enum
from django.db import models

class ROLES(IntEnum):
    USER = 0
    ADMIN = 1

class EMAIL_TEMPLATES(str, Enum):
    WELCOME = "emails/welcome.html"
    FORGET_PASS = "emails/forget_password.html"

class EMAIL_SUBJECTS(str, Enum):
    WELCOME = "Welcome to Jelliemon!"
    FORGET_PASS = "Reset Your Password - Jelliemon"

class AvatarChoices(models.TextChoices):
    AVATAR_1 = 'avatar_1', 'Avatar 1'
    AVATAR_2 = 'avatar_2', 'Avatar 2'
    AVATAR_3 = 'avatar_3', 'Avatar 3'
    AVATAR_4 = 'avatar_4', 'Avatar 4'
