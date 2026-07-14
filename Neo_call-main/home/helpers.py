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
    """Send OTP via WhatsApp using Twilio (signup only - no fallback)
    
    Args:
        phone_number: User's phone number in E.164 format (e.g., +919876543210)
    
    Returns:
        OTP (1000-9999) if sent successfully, None if failed
    """
    try:
        otp = random.randint(1000, 9999)
        
        # WhatsApp via Twilio (required for signup)
        twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM')  # Format: whatsapp:+14155238886
        
        if not TWILIO_AVAILABLE:
            print(f"❌ Twilio not installed. Run: pip install twilio")
            return None
        
        if not all([twilio_account_sid, twilio_auth_token, twilio_whatsapp_from]):
            print("❌ Twilio credentials missing:")
            print(f"   TWILIO_ACCOUNT_SID: {'SET' if twilio_account_sid else 'NOT SET'}")
            print(f"   TWILIO_AUTH_TOKEN: {'SET' if twilio_auth_token else 'NOT SET'}")
            print(f"   TWILIO_WHATSAPP_FROM: {'SET' if twilio_whatsapp_from else 'NOT SET'}")
            return None
        
        try:
            client = Client(twilio_account_sid, twilio_auth_token)
            
            # Ensure phone number is in E.164 format (e.g., +919876543210)
            if not str(phone_number).startswith('+'):
                phone_number_formatted = '+' + str(phone_number)
            else:
                phone_number_formatted = str(phone_number)
            
            # DEBUG: Show which user number is getting the OTP
            print(f"\n Sending OTP to USER's WhatsApp number: {phone_number_formatted}")
            print(f"   OTP Code: {otp}")
            print(f"   From Twilio: {twilio_whatsapp_from}\n")
            
            message = client.messages.create(
                from_=twilio_whatsapp_from,
                to=f"whatsapp:{phone_number_formatted}",
                body=f"Your One Time Password (OTP) is: {otp}\n\nDo not share this with anyone."
            )
            print(f"WhatsApp OTP successfully sent!")
            print(f"   Message SID: {message.sid}")
            print(f"   Sent to: {phone_number_formatted}\n")
            return otp
            
        except Exception as twilio_error:
            print(f"WhatsApp OTP failed: {twilio_error}")
            return None
        
    except Exception as e:
        print(f"Error in send_otp_user: {e}")
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
