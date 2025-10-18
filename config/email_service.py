# utils/email_service.py
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string

def send_email(subject, message, recipient_list):
    return send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        fail_silently=False,
    )

def send_templated_email(subject, template_name, context, recipient_list):
    html_content = render_to_string(template_name, context)
    text_content = render_to_string(template_name, context).replace('<[^<]+?>', '')  # simple strip HTML
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    msg.send()