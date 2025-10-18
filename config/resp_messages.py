# config/resp_messages.py
from googletrans import Translator
from django.conf import settings
translator = Translator()

def tr(msg, user=None, lang=None):
    lang = lang or (getattr(user, 'language', None) if user else None) or getattr(settings, 'DEFAULT_LANGUAGE', 'en')
    return translator.translate(msg, dest=lang).text if lang != 'en' else msg

class CommonMessages:
    INVALID_REQUEST = "Invalid request."
    REQUIRED_FIELDS = "All required fields must be provided."
    NOT_FOUND = "User not found."
    OTP_REQUIRED = "OTP is required."
    PASSWORD_MISMATCH = "Passwords do not match."
    INVALID_CREDENTIALS = "Invalid credentials."
    EMAIL_NOT_VERIFIED = "Email not verified."
    INVALID_REFRESH_TOKEN = "Invalid or expired refresh token."
    INVALID_TOKEN = "Invalid token."
    EMAIL_PASSWORD_REQUIRED = "Email and password required."
    INVALID_STEP = "Invalid step."

class AdminMessages:
    ADMIN_NOT_FOUND = "Admin not found."
    OTP_SENT = "OTP sent to admin email."
    OTP_VERIFIED = "OTP verified successfully."
    PASSWORD_RESET_SUCCESS = "Admin password reset successfully."
    LOGIN_SUCCESS = "Login successful."
    LOGOUT_SUCCESS = "Logged out successfully."
    INVALID_OTP = "Invalid OTP."
    TOKEN_REFRESSHED = "Token refreshed."

class UserMessages:
    OTP_SENT_EMAIL = "OTP sent to your email."
    OTP_SENT_MOBILE = "OTP sent to your mobile number."
    OTP_VERIFIED = "OTP verified successfully."
    MOBILE_VERIFIED = "Mobile verified successfully."
    PASSWORD_SET_SUCCESS = "Password set successfully."
    LOGIN_SUCCESS = "Login successful."
    MOBILE_LOGIN_SUCCESS = "Mobile login successful."
    GOOGLE_AUTH_SUCCESS = "Google authentication successful."
    FACEBOOK_AUTH_SUCCESS = "Facebook login successful."
    PASSWORD_RESET_SUCCESS = "Password reset successfully."
    INVALID_OTP = "Invalid OTP."
    ACC_DELETED = "Account deleted successfully"

class RM:
    common = CommonMessages
    admin = AdminMessages
    user = UserMessages

