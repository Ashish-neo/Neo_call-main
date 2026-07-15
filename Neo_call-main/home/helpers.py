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
    """Send OTP via WhatsApp (primary) or SMS fallback
    
    Args:
        phone_number: User's phone number in E.164 format (e.g., +919876543210)
    
    Returns:
        OTP (1000-9999) if sent successfully, None if failed
    """
    try:
        otp = random.randint(1000, 9999)
        
        # Try WhatsApp via Twilio first
        twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM')
        
        # Ensure phone number is in E.164 format (e.g., +919876543210)
        if not str(phone_number).startswith('+'):
            phone_number_formatted = '+' + str(phone_number)
        else:
            phone_number_formatted = str(phone_number)
        
        print(f"\nAttempting to send OTP to: {phone_number_formatted}")
        print(f"   OTP Code: {otp}")
        
        # Try Twilio WhatsApp if credentials are available
        if TWILIO_AVAILABLE and twilio_account_sid and twilio_auth_token and twilio_whatsapp_from:
            try:
                print(f"   Method: WhatsApp (via Twilio)")
                client = Client(twilio_account_sid, twilio_auth_token)
                message = client.messages.create(
                    from_=twilio_whatsapp_from,
                    to=f"whatsapp:{phone_number_formatted}",
                    body=f"Your One Time Password (OTP) is: {otp}\n\nDo not share this with anyone.\n Welcome to Neo Call to Share."
                )
                print(f"   WhatsApp OTP sent! Message SID: {message.sid}\n")
                return otp
            except Exception as twilio_error:
                print(f"   WhatsApp failed: {twilio_error}")
                print(f"   Falling back to SMS...\n")
        else:
            print(f"   Twilio not configured, using SMS fallback")
        
        # FALLBACK: Send OTP via SMS using 2factor.in
        try:
            api_key = settings.API_KEY
            # Remove + from phone number for SMS API
            phone_for_sms = phone_number_formatted.lstrip('+')
            url = f'https://2factor.in/API/V1/{api_key}/SMS/{phone_for_sms}/{otp}/One_time_verification'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"   Method: SMS (via 2factor.in)")
                print(f"  SMS OTP sent! Response: {response.status_code}\n")
                return otp
            else:
                print(f" SMS failed with status {response.status_code}: {response.text}\n")
                return None
                
        except Exception as sms_error:
            print(f" SMS fallback failed: {sms_error}\n")
            return None
        
    except Exception as e:
        print(f" Error in send_otp_user: {e}\n")
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
            body=f"Your Neo Sign-up One Time Password (OTP) is: {otp}\n\nDo not share this with anyone. Welcome to Neo Call"
        )
        print(f"WhatsApp OTP sent successfully: {message.sid}")
        return otp
        
    except Exception as e:
        print(f"Error sending WhatsApp OTP: {e}")
        return None


# # two factor api key : e662832f-b79f-11ef-8b17-0200cd936042
