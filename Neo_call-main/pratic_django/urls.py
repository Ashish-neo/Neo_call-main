"""
URL configuration for pratic_django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from home.views import *



urlpatterns = [
    path('', home ,name="home"),
    path('sign_up/',sign_up,name="sign_up"),
    path('admin/', admin.site.urls),    
    path('about_page/', about_page, name='about_page'),
    path('contact_page/', contact_page, name='contact_page'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout_page/', LogoutView.as_view(next_page='/'), name='logout_page'),
    path('login_page/', login_page, name='login_page'),
    # path('send-otp/', send_otp, name='send_otp'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('call/<str:phone_no>/',call_page,name='call_page'),
    path('call/', call_page, name='call_page'),  # For /call?target=...
]

