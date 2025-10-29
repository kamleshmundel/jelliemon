import requests
from django.conf import settings
import logging
from google.auth.transport.requests import Request
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

SENDMAIL_URL = "https://us-central1-jelliemon-core-app.cloudfunctions.net/sendMail"
SERVICE_ACCOUNT_FILE = settings.GOOGLE_SERVICE_ACCOUNT_KEY  # Path to your service account JSON

def get_auth_token():
    """Get authentication token for Cloud Function invocation."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        credentials.refresh(Request())
        return credentials.token
    except Exception as e:
        logger.error(f"Failed to get auth token: {e}")
        return None

def send_email(subject, message, recipient_list):
    """
    Send a plain text email via Firebase Cloud Function.
    
    Args:
        subject (str): Email subject
        message (str): Email body text
        recipient_list (list): List of recipient email addresses
    
    Returns:
        dict: Response from the email service or error details
    """
    try:
        payload = {
            "to": recipient_list[0] if len(recipient_list) == 1 else recipient_list,
            "subject": subject,
            "text": message
        }
        
        # Get authentication token
        token = get_auth_token()

        if not token:
            return {
                "success": False,
                "message": "Failed to get authentication token",
                "status": 401,
                "data": None
            }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        resp = requests.post(SENDMAIL_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        
        return {
            "success": True,
            "data": resp.json(),
            "status": resp.status_code
        }
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error sending email: {e}, Status: {e.response.status_code}")
        return {
            "success": False,
            "message": f"Failed to send email: {str(e)}",
            "status": e.response.status_code if e.response else 500,
            "data": None
        }
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error sending email: {e}")
        return {
            "success": False,
            "message": "Failed to connect to email service",
            "status": 503,
            "data": None
        }
        
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout sending email: {e}")
        return {
            "success": False,
            "message": "Email service request timed out",
            "status": 504,
            "data": None
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error sending email: {e}")
        return {
            "success": False,
            "message": f"Request failed: {str(e)}",
            "status": 500,
            "data": None
        }
        
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "status": 500,
            "data": None
        }


def send_templated_email(subject, template_name, context, recipient_list):
    """
    Send a templated email via Firebase Cloud Function.
    
    Args:
        subject (str): Email subject
        template_name (str): Django template name
        context (dict): Template context variables
        recipient_list (list): List of recipient email addresses
    
    Returns:
        dict: Response from the email service or error details
    """
    try:
        from django.template.loader import render_to_string
        import re
        
        # Render HTML and text content
        html_content = render_to_string(template_name, context)
        text_content = re.sub(r'<[^<]+?>', '', html_content)
        
        payload = {
            "to": recipient_list[0] if len(recipient_list) == 1 else recipient_list,
            "subject": subject,
            "text": text_content,
            "html": html_content
        }
        
        # Get authentication token
        token = get_auth_token()

        if not token:
            return {
                "success": False,
                "message": "Failed to get authentication token",
                "status": 401,
                "data": None
            }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        resp = requests.post(SENDMAIL_URL, json=payload, headers=headers, timeout=30)


        resp.raise_for_status()

        data = {
            "success": True,
            "data": resp.json(),
            "status": resp.status_code
        }
        
        return data
        
    except ImportError as e:
        logger.error(f"Import error in send_templated_email: {e}")
        return {
            "success": False,
            "message": "Template rendering failed - missing dependencies",
            "status": 500,
            "data": None
        }
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error sending templated email: {e}, Status: {e.response.status_code}")
        return {
            "success": False,
            "message": f"Failed to send email: {str(e)}",
            "status": e.response.status_code if e.response else 500,
            "data": None
        }
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error sending templated email: {e}")
        return {
            "success": False,
            "message": "Failed to connect to email service",
            "status": 503,
            "data": None
        }
        
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout sending templated email: {e}")
        return {
            "success": False,
            "message": "Email service request timed out",
            "status": 504,
            "data": None
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error sending templated email: {e}")
        return {
            "success": False,
            "message": f"Request failed: {str(e)}",
            "status": 500,
            "data": None
        }
        
    except Exception as e:
        logger.error(f"Unexpected error sending templated email: {e}")
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "status": 500,
            "data": None
        }