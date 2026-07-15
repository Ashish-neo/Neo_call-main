from __future__ import unicode_literals
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from home.manager import UserManager

# Create your models here.
class Request_User(AbstractBaseUser,PermissionsMixin):

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50,null=False,blank=False)
    age = models.IntegerField(null=False, blank=False,default=18)
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default='Male',
        null=False
    )

    occupation = models.CharField(max_length=50,null=False,blank=False,default="Student")
    phone_number = models.BigIntegerField(unique=True,null=False,blank=True,default="+910123456789")
    email = models.EmailField(unique=True,max_length=100,null=False,blank=True,default="Unknown")
    password = models.CharField(max_length=255,null=False)
    is_Verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD='phone_number'
    REQUIRED_FIELDS = ['name', 'age', 'gender', 'occupation' , 'email','password']

    def __str__(self):
        return self.name


class Requestor_User(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    name = models.CharField(max_length=50,null=False,blank=True)
    age = models.IntegerField(null=False, blank=False,default=18)
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default='Male',
        null=False
        )
    email = models.EmailField(max_length=100,null=False,blank=True)
    phone_number = models.BigIntegerField(null=False,default="0123456789")
    password = models.CharField(max_length=125,null=False,blank=True)

class login_auth(models.Model):
    user_name = models.CharField(max_length=20,null=False,blank=True)
    password = models.CharField(max_length=125,null=False,blank=True)


# otp verification code :
class PhoneOTP(models.Model):
 
    phone_regex = RegexValidator( regex = r'^\+?1?\d{9,10}$', message ="Phone number must be entered in the format +919999999999. Up to 14 digits allowed.")
    phone       = models.CharField(validators =[phone_regex], max_length=17, unique = True)
    otp         = models.CharField(max_length=9, blank = True, null=True)
    count       = models.IntegerField(default=0, help_text = 'Number of otp_sent')
    validated   = models.BooleanField(default = False, help_text = 'If it is true, that means user have validate otp correctly in second API')
    otp_session_id = models.CharField(max_length=120, null=True, default = "")
    name    = models.CharField(max_length=20, blank = True, null = True, default = None )
    email       = models.CharField(max_length=50, null = True, blank = True, default = None) 
    password    = models.CharField(max_length=125, null = True, blank = True, default = None) 

    
    def __str__(self):
        return str(self.phone) + ' is sent ' + str(self.otp) 
    