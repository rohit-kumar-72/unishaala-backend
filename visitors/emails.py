from django.core.mail import send_mail
from .models import Otp
from django.contrib.auth.models import User
from django.conf import settings
import random


def send_otp_via_mail(to_email):
    subject = "Account Verification Code"
    # otp = random.randint(1000, 9999)
    otp=1000
    # message = f"Your account verification code is {otp}"
    # print("********************************")
    # print({settings})
    # try:
    #     successful = send_mail(
    #         subject=subject,
    #         message=message,
    #         from_email=settings.DEFAULT_FROM_EMAIL,
    #         recipient_list=[to_email]
    #     )

    #     if successful == 0:
    #         raise Exception("Email sending failed. Please try again.")
    
    # except Exception as e:
    #     print({e})
    #     raise Exception(f"Error sending email: {str(e)}")

    return otp

