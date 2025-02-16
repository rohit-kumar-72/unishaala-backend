from django.db import models
from django.contrib.auth.models import User
from .choices import GENDER_CHOICE

# Create your models here.
class Base_model(models.Model):
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        abstract=True


class Profile(Base_model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICE, null=True, blank=True)
    phone_number = models.CharField(max_length=10, unique=True, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)

    def __str__(self):
        return f'profile - {self.user.username}'


class Education(Base_model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='educations')
    grade_or_degree = models.CharField(max_length=100)
    school_or_college = models.CharField(max_length=200)
    completion_year = models.DateField(auto_now=False, auto_now_add=False)

    def __str__(self):
        return f"{self.grade_or_degree} - {self.school_or_college}"


class Otp(Base_model):
    email=models.EmailField(unique=True,null=True,blank=True)
    otp=models.CharField(max_length=4,null=True,blank=True)
    isActive=models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} - {self.otp}"