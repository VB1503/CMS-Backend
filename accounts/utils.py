
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import random
import requests
from django.conf import settings
from .models import User, OneTimePassword



def send_generated_otp_to_sms(phone_number, request): 
    otp=random.randint(100000, 999999) 
    user = User.objects.get(phone_number=phone_number)
    otp_obj=OneTimePassword.objects.create(user=user, otp=otp)
    api_key = settings.TWO_FACTOR_API_KEY
    api_url = f"https://2factor.in/API/V1/{api_key}/SMS/{user.phone_number}/{otp}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        json_response = response.json()
        if json_response['Status'] == 'Success':
            print("OTP Sent successfully. Session ID:", json_response['Details'])
        else:
            return Exception(f"Failed to send OTP. Reason: {json_response['Details']}")
    except requests.RequestException as e:
        return Exception(f"Request to 2Factor.in failed. Reason: {str(e)}")
    except Exception as e:
        return e
   
def resend_otp(phone_number,user,request):
    otp=random.randint(100000, 999999) 
    currentOtp = OneTimePassword.objects.get(user=user)
    currentOtp.otp = otp
    currentOtp.save()
    api_key = settings.TWO_FACTOR_API_KEY
    api_url = f"https://2factor.in/API/V1/{api_key}/SMS/{phone_number}/{otp}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        json_response = response.json()
        if json_response['Status'] == 'Success':
            print("OTP Sent successfully. Session ID:", json_response['Details'])
        else:
            return Exception(f"Failed to send OTP. Reason: {json_response['Details']}")
    except requests.RequestException as e:
        return Exception(f"Request to 2Factor.in failed. Reason: {str(e)}")
    except Exception as e:
        return e



def send_normal_email(data):
    email_body = data.get('email_body', '')
    subject = data.get('email_subject', '')
    receiver = data.get('to_email', '')
    from_email = data.get('from_email', '')
    context = data.get('context', {})  # Add context to data dictionary

    # Render the message template with the provided context
    message = render_to_string(email_body, context)

    # Create the email
    msg = EmailMultiAlternatives(subject, '', from_email, [receiver])
    msg.attach_alternative(message, 'text/html')

    # Send the email
    try:
        msg.send()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

