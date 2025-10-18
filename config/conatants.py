from enum import IntEnum, Enum

class ROLES(IntEnum):
    USER = 0
    ADMIN = 1

class EMAIL_TEMPLATES(str, Enum):
    WELCOME = "emails/welcome.html"
    FORGET_PASS = "emails/forget_password.html"

class EMAIL_SUBJECTS(str, Enum):
    WELCOME = "Welcome to Jelliemon!"
    FORGET_PASS = "Reset Your Password - Jelliemon"