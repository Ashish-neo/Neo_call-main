from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUSerAdmin
from django.contrib.auth.models import Group
# Register your models here.
from .models import Request_User,Requestor_User
admin.site.register(Request_User)
admin.site.register(Requestor_User)