from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import Profile,Education,Otp

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_]+$',
                message="Username must contain only letters, numbers, and underscores."
            )
        ]
    )
    password = serializers.CharField(min_length=3, write_only=True)
    admin = serializers.BooleanField(required=False, default=False)
    otp = serializers.CharField(write_only=True)

    def validate_email(self, email):
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email is already registered.")
        return email

    def validate_otp(self, otp):
        email = self.initial_data.get("email")
        if not Otp.objects.filter(email=email, otp=otp).exists():
            raise serializers.ValidationError("Invalid or expired OTP.")
        return otp

    def validate_username(self, username):
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username is already taken.")
        return username 

    def create(self, validated_data):
        otp=validated_data.get('otp')
        otp_instance=Otp.objects.get(email=validated_data['email'],otp=otp)
        otp_instance.isActive=True
        otp_instance.save()

        validated_data.pop('otp')
        print(f"validated_data-> {validated_data}")
        
        # Create the user
        user = User.objects.create(username=validated_data["username"], email=validated_data["email"])
        user.set_password(validated_data["password"])
        
        # Check if 'admin' field is True, make the user a superuser
        if validated_data.get("admin", False):
            user.is_superuser = True
            # user.is_staff = True  # Optional: To give access to the Django admin panel
        user.save()

        return validated_data

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_]+$',
                message="Username must contain only letters, numbers, and underscores."
            )
        ]
    )
    password=serializers.CharField()

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model=User
        fields=[
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'is_superuser',
        ]

class ProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        max_length=10,
        min_length=10,
        validators=[
            RegexValidator(
                regex=r'^\d+$',
                message="The phone number must contain only digits.",
                code='invalid_phone_number'
            )
        ]
    )

    class Meta:
        model=Profile
        fields='__all__'
        read_only_fields=['user']

class EducationSerializer(serializers.ModelSerializer):
    # profile=ProfileSerializer() this will ask for profile at the time of post request but adding depth will solve the issue also u can pass a context={"profile":profile} during passing data to serializer if want to use nested serialization

    class Meta:
        model=Education
        fields='__all__'
        read_only_fields=['profile']
        depth=1

class OtpSerializer(serializers.ModelSerializer):
    class Meta:
        model=Otp
        fields='__all__'
        read_only_fields=['created_at','updated_at']

