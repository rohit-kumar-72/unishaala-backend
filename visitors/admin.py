from django.contrib import admin
from .models import Profile,Education,Otp
# Register your models here.

admin.site.register(Otp)
admin.site.register(Profile)
admin.site.register(Education)