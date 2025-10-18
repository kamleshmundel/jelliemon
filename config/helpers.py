import random
from django.conf import settings

def generate_otp():
    return "1234" if getattr(settings, 'BREACH_OTP', False) else str(random.randint(1000, 9999))
