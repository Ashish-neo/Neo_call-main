# WhatsApp OTP Setup Guide

This guide explains how to set up WhatsApp OTP delivery using Twilio.

## Steps to Setup Twilio WhatsApp OTP

### 1. Create a Twilio Account
- Go to https://www.twilio.com/
- Sign up for a free account
- Verify your email and phone number

### 2. Get Twilio Credentials
- Log in to your Twilio Console: https://console.twilio.com
- Find your **Account SID** and **Auth Token** (keep these secret!)
- Navigate to **Messaging > Try it out > Send a WhatsApp message**
- Note the **WhatsApp Sandbox Number** (looks like: `whatsapp:+14155238886`)

### 3. Enable WhatsApp Sandbox (for testing)
- Go to **Messaging > WhatsApp > Sandbox**
- Follow the instructions to join the sandbox
- Send "join XXXXX" to the provided WhatsApp number from your phone
- You'll get a confirmation message

### 4. Set Environment Variables on Your AWS Server

Add these to your `.env` file or set them as environment variables on AWS:

```bash
export TWILIO_ACCOUNT_SID="your_account_sid_here"
export TWILIO_AUTH_TOKEN="your_auth_token_here"
export TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"  # Replace with your sandbox number
```

### 5. For AWS EC2/Production

If using AWS, add these environment variables:
- Via **Systems Manager Parameter Store**
- Or in your **Elastic Beanstalk configuration**
- Or in your **deployment script**

Example for EC2:
```bash
#!/bin/bash
export TWILIO_ACCOUNT_SID="your_account_sid_here"
export TWILIO_AUTH_TOKEN="your_auth_token_here"
export TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"
python -m daphne pratic_django.asgi:application --bind 0.0.0.0 --port 8000
```

### 6. Update Phone Number Format

Make sure phone numbers are stored in E.164 format:
- ✓ +919876543210 (correct)
- ✗ 919876543210 (missing +)
- ✗ 9876543210 (missing country code)

## How It Works

1. User enters phone number during signup
2. `send_otp_user()` is called
3. If Twilio credentials are set → **OTP sent via WhatsApp**
4. If Twilio credentials are NOT set → **Fallback to SMS via 2factor.in**

## Testing Locally

To test locally with Twilio:

```python
from home.helpers import send_otp_whatsapp_only

# Test sending OTP
otp = send_otp_whatsapp_only("+919876543210")
if otp:
    print(f"OTP sent: {otp}")
else:
    print("Failed to send OTP")
```

## Switching Between SMS and WhatsApp

### Option 1: Send to WhatsApp First, Fallback to SMS
```python
# In helpers.py (already configured)
from home.helpers import send_otp_user
send_otp_user(phone_number)  # Tries WhatsApp, then SMS
```

### Option 2: WhatsApp Only (Strict Mode)
```python
from home.helpers import send_otp_whatsapp_only
send_otp_whatsapp_only(phone_number)  # Only WhatsApp, no fallback
```

### Option 3: Keep SMS Only (If you don't want WhatsApp)
Just don't set the Twilio environment variables, and it will use SMS.

## Production Upgrade to WhatsApp Business Account

For production, upgrade from **Sandbox** to **WhatsApp Business Account**:
1. Go to **Twilio Console > Messaging > WhatsApp**
2. Click **"Get Production Access"**
3. Submit your business details
4. Once approved, update `TWILIO_WHATSAPP_FROM` with your business number

## Troubleshooting

### OTP not being sent
- Check that Twilio credentials are set in environment variables
- Verify phone number format (must start with +)
- Check Twilio account balance (free account has limited messages)

### Still receiving SMS instead of WhatsApp
- Confirm `TWILIO_WHATSAPP_FROM` is set
- Check that the phone is registered in the sandbox

### "Invalid phone number" error
- Ensure phone number includes country code
- Format: +91 for India, +1 for USA, etc.
- Remove any spaces or dashes

## Related Files Modified
- `home/helpers.py` - Updated OTP sending logic
- `requirements.txt` - Added Twilio package
- `home/views.py` - Uses `send_otp_user()` during signup
