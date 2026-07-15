from django.shortcuts import render,redirect
from django.http import HttpResponse
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout # to match the password with encrypt with system
from home.manager import *
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
import re
from .helpers import send_otp_whatsapp_only
from django.urls import reverse_lazy
from django.http import JsonResponse
import os
import time

User = get_user_model()

# we use for session to next time no need to login
# from django.contrib.auth import User

# Create your views here.

def build_signaling_server_url(request):
    configured_url = os.getenv("SIGNALING_SERVER_URL", "").strip()
    if configured_url:
        return configured_url

    host = request.get_host()
    if ":" in host and host.rsplit(":", 1)[1].isdigit():
        hostname = host.rsplit(":", 1)[0]
    else:
        hostname = host

    scheme = "https" if request.is_secure() else "http"
    return f"{scheme}://{hostname}:5001"


def home(request):
    return render(request,'home_page.html')

def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        country_code = request.POST.get("country_code", "+91")  # Default to India
        login_pass = request.POST.get("pass1")
        
        # Combine country code with username (mobile number)
        full_phone = f"{country_code}{username}".replace(" ", "")
        
        user = authenticate(request, username=full_phone, password=login_pass)
        #if username and password is not valid 
        if user is None:
            print("Auth failed for:", full_phone, login_pass)
            messages.error(request,"Invalid username or password")
        else:
            login(request,user)
            return redirect('/dashboard/')

    return render(request, 'home_page.html')

def logout_page(request):
    if request.method == 'POST':
        logout(request)
        return redirect('/')
    return redirect('dashboard')

def about_page(request):
    return render(request,'about.html')

def contact_page(request):
    return render(request,'contact.html')

# use to verify the mobile number 
def validate_mobile(mobile):
    pattern = re.compile(r'^\+?[1-9]\d{1,14}$')
    return re.match(pattern, mobile) is not None


def sign_up(request):
    if request.method == 'POST':
        name = request.POST.get("name")
        age = request.POST.get("age")
        gender = request.POST.get("gender")
        occupation = request.POST.get("occupation")
        mobile = request.POST.get("mobile")
        country_code = request.POST.get("country_code", "+91")  # Default to India
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirmpassword = request.POST.get("confirmpassword")

        # Combine country code with mobile number
        phone_number = f"{country_code}{mobile}".replace(" ", "")

        # Mobile validation
        if not validate_mobile(phone_number):
            messages.error(request, "Invalid mobile number")
            return redirect('/sign_up/')

        # Validation email id
        try:
            # Email validation
            validate_email(email)
        except ValidationError:
            messages.error(request, "Invalid email format")
            return redirect('/sign_up/')

        # Check password match
        if password != confirmpassword:
            messages.error(request,"Passwords do not match.")
            return redirect('/sign_up/') 
        
        # Check email are exixts in db      
        if Request_User.objects.filter(email=email).exists():
            messages.error(request, "Email  already exists, Please sign-in with another email")
            return redirect('/sign_up/')
        
        # Check if phone  already exists
        if Request_User.objects.filter(phone_number=phone_number).exists():
            messages.error(request, "Mobile number already registered, Please sign-in with another number ")
            return redirect('/sign_up/')

        # Generate and send OTP
        print(f"   FINAL PHONE NUMBER: {phone_number}")
        print(f"   Sending OTP to this number...\n")
        
        otp = send_otp_whatsapp_only(phone_number)

        if not otp:
            messages.error(request, "Check Mobile is correct or not. Please try again.")
            return render(request, 'sign_up.html')
        
        print(f"OTP SENT successfully to {phone_number}")
        
        # Store signup data and OTP in session
        request.session['signup_data'] = {
            'name': name,
            'age': age,
            'gender': gender,
            'occupation': occupation,
            'mobile': phone_number,
            'email': email,
            'password': password # Securely hash password
        }
        print(request.session)
        request.session['signup_otp'] = otp
        request.session.set_expiry(900)  # OTP valid for 15 minutes

        # show message to user we send message to mobile number 
        messages.success(request, "OTP sent to your mobile number")
        return render(request, 'sign_up.html', {'show_otp': True})

     
    return render(request,'sign_up.html')


def verify_otp(request):
    if request.method == 'POST':
        # Get OTP from form
        # print("POST Data:", request.POST)
        user_otp = request.POST.get("otp") #convert string to integer
        
        # Retrieve stored OTP and signup data from session 
        stored_otp = request.session.get('signup_otp')
        signup_data = request.session.get('signup_data')
      
        # Validate OTP 
        if not user_otp or not stored_otp: 
            messages.error(request, "OTP session expired. Please restart signup.") 
            return render(request, 'sign_up.html') 
        # print("validate otp",type(int(user_otp)),type(stored_otp))
        if int(user_otp) != stored_otp:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, 'sign_up.html', {'show_otp': True})
        print("stroed_otp",stored_otp)

        print("signup_data--->",signup_data)
        # Create user
        try:
            print("Attempting to create user...")
            user = Request_User.objects.create(
                name=signup_data['name'],
                email=signup_data['email'],
                occupation=signup_data['occupation'],
                phone_number=signup_data['mobile'],
                age=signup_data['age'],
                gender=signup_data['gender'],
                password =make_password(signup_data['password']),  # Hash the password
                is_Verified=True
            )
            # Set password properly (hashes it)
            user.set_password(signup_data['password'])
            user.save()

            print("user--->", user)
            
            # Authenticate the user
            authenticated_user = authenticate(
                username=signup_data['mobile'],
                password=signup_data['password']
            )
            #print("Redirecting to dashboard with authenticated user:", authenticated_user)
            if authenticated_user:
                # Log in the user
                login(request, authenticated_user)

                # Clear session data
                del request.session['signup_otp']
                del request.session['signup_data']
                # request.session.flush()  # Ensures no stale session data remains

                messages.success(request, "Account created, but automatic login failed. Please log in manually.")
                #print("User authenticated:", request.user.is_authenticated)

                # Redirect to dashboard
                return redirect('/dashboard/') # '/dashboard/' if its not redirect then render to Dashboard
            else:
                messages.error(request, "Authentication failed. Now you can you manually!")
                return redirect('/login_page/')
            
        except Exception as e:
            # if verification faild in then stay in Sign up page 
            messages.error(request, f"Registration failed, Please enter correct OTP: {str(e)}")
            return render(request, 'sign_up.html')

    return render(request, 'sign_up.html')

@login_required(login_url='/login_page/')
def dashboard(request):
    # Fetch the logged-in user phone number
    login_user_number = request.user.phone_number
    # Fetch another active user from the database
    other_user = (
        Request_User.objects.exclude(id=request.user.id).filter(is_active=True).first()
    )
    other_user_number = other_user.phone_number if other_user else None
    other_user_id = other_user.id if other_user else None

    return render(request, 'mainDashboard/dashboard.html', {
        'login_user_number': login_user_number,
        'other_user_number': other_user_number,
        'other_user_id': other_user_id,
        'signaling_server_url': build_signaling_server_url(request),
    })

#To track the calling protocol with array and calling 20 sec
class CallManager:
    def __init__(self):
        self.call_attempts = {}  # Store call attempts and timestamps
        self.max_ring_time = 20  # Maximum time to wait for answer in seconds
        
    def get_next_available_number(self, number_list, current_number): # get next number from list
        try:
            current_index = number_list.index(current_number)
            next_index = (current_index + 1) % len(number_list)
            return number_list[next_index]
        except ValueError:
            return number_list[0] if number_list else None


@login_required
def call_page(request):
    # Fetch 10 active users from the database
    active_users = Request_User.objects.filter(is_active=True)[:10]
    # put all number in list
    available_numbers  = [user.phone_number for user in active_users]
    curemt_no_in_list=request.GET.get('phone_number')
    call_manager= CallManager()

    context = {
        'current_number': curemt_no_in_list,
        'available_numbers': available_numbers,
        'signaling_server_url': build_signaling_server_url(request),
    } 

    return render(request, 'calls/call.html',context)


# start the call
def initiate_call(request):
    """API endpoint to initiate and manage calls"""
    if request.method == 'POST':
        current_number = request.POST.get('current_number')
        available_numbers = request.POST.getlist('available_numbers[]')
        
        # Simulate call attempt
        call_successful = attempt_call(current_number)
        
        if not call_successful:
            # Get next number if current call fails
            next_number = CallManager().get_next_available_number(available_numbers, current_number)
            return JsonResponse({
                'status': 'retry',
                'next_number': next_number
            })
            
        return JsonResponse({
            'status': 'success',
            'connected_number': current_number
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


def attempt_call(number):
    """Simulate call attempt - replace with actual calling logic"""
    # Add your actual calling logic here
    # This is just a simulation
    time.sleep(2)  # Simulate call attempt duration
    return False  # Return True if call connects, False if it fails
