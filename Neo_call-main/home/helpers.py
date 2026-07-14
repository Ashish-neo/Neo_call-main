import requests
import random
from django.conf import settings

def send_otp_user(phone_number):
    # try catch for error 
    try:
        otp = random.randint(1000,9999)
        url = f'https://2factor.in/API/V1/{settings.API_KEY}/SMS/{phone_number}/{otp}/One_time_verification'
        
        response = requests.get(url)
        print("send_otp_user",response,otp)
        return otp
    except Exception as e:
        print("error_in_send_otp_user",e)
        return None


# # two factor api key : e662832f-b79f-11ef-8b17-0200cd936042