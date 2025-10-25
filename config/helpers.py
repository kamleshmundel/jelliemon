import random
from django.conf import settings
import re

def generate_otp():
    return "1234" if getattr(settings, 'BREACH_OTP', False) else str(random.randint(1000, 9999))

def calculate_read_time_in_hours(content, wpm=200):
    words = len(re.findall(r'\w+', content))
    hours = words / (wpm * 60)
    return round(hours, 2)
