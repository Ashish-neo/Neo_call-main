import requests
import random
import os
from django.conf import settings

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

def send_otp_user(phone_number):
    """Send OTP via WhatsApp using Twilio"""
    try:
        otp = random.randint(1000, 9999)
        
        # Try Twilio WhatsApp first
        twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM')  # Format: whatsapp:+14155238886
        
        if TWILIO_AVAILABLE and twilio_account_sid and twilio_auth_token and twilio_whatsapp_from:
            try:
                client = Client(twilio_account_sid, twilio_auth_token)
                # Ensure phone number is in E.164 format (e.g., +919876543210)
                if not str(phone_number).startswith('+'):
                    phone_number_formatted = '+' + str(phone_number)
                else:
                    phone_number_formatted = str(phone_number)
                
                message = client.messages.create(
                    from_=twilio_whatsapp_from,
                    to=f"whatsapp:{phone_number_formatted}",
                    body=f"Your One Time Password (OTP) is: {otp}\n\nDo not share this with anyone."
                )
                print(f"WhatsApp OTP sent: {message.sid}")
                return otp
            except Exception as twilio_error:
                print(f"Twilio WhatsApp failed: {twilio_error}")
                # Fallback to SMS if WhatsApp fails
                pass
        
        # Fallback: Use SMS via 2factor.in if WhatsApp is not configured
        url = f'https://2factor.in/API/V1/{settings.API_KEY}/SMS/{phone_number}/{otp}/One_time_verification'
        response = requests.get(url)
        print(f"send_otp_user", response, otp)
        return otp
        
    except Exception as e:
        print(f"error_in_send_otp_user", e)
        return None


def send_otp_whatsapp_only(phone_number):
    """Send OTP ONLY via WhatsApp (strict mode)"""
    try:
        otp = random.randint(1000, 9999)
        
        twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM')
        
        if not TWILIO_AVAILABLE:
            raise ValueError("Twilio not installed. Run: pip install twilio")
        
        if not all([twilio_account_sid, twilio_auth_token, twilio_whatsapp_from]):
            raise ValueError("Twilio WhatsApp credentials not configured in environment variables")
        
        client = Client(twilio_account_sid, twilio_auth_token)
        
        # Ensure phone number is in E.164 format
        if not str(phone_number).startswith('+'):
            phone_number_formatted = '+' + str(phone_number)
        else:
            phone_number_formatted = str(phone_number)
        
        message = client.messages.create(
            from_=twilio_whatsapp_from,
            to=f"whatsapp:{phone_number_formatted}",
            body=f"Your One Time Password (OTP) is: {otp}\n\nDo not share this with anyone."
        )
        print(f"WhatsApp OTP sent successfully: {message.sid}")
        return otp
        
    except Exception as e:
        print(f"Error sending WhatsApp OTP: {e}")
        return None


# # two factor api key : e662832f-b79f-11ef-8b17-0200cd936042
