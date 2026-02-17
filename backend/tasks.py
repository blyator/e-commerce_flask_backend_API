from celery import shared_task
from flask_mail import Message
from extensions import mail

@shared_task(ignore_result=True)
def send_celery_email(subject, recipients, html, body):
    msg = Message(
        subject=subject,
        recipients=recipients,
        html=html,
        body=body
    )
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
