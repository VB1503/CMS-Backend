
from .models import User
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str, smart_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.conf import settings
from django.urls import reverse
from .utils import send_normal_email
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.utils.timezone import now

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    password2= serializers.CharField(max_length=68, min_length=6, write_only=True)
    id=serializers.CharField(max_length=50,read_only=True)
    class Meta:
        model=User
        fields = ['email',"phone_number", 'first_name', 'last_name', 'password', 'password2','id','profile_pic']

    def validate(self, attrs):
        password=attrs.get('password', '')
        password2 =attrs.get('password2', '')
        if password !=password2:
            raise serializers.ValidationError("passwords do not match")
         
        return attrs

    def create(self, validated_data):
        user= User.objects.create_user(
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            password=validated_data.get('password')
            )
        return user

class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=155, min_length=6)
    password=serializers.CharField(max_length=68, write_only=True)
    id=serializers.CharField(max_length=50,read_only=True)
    first_name=serializers.CharField(max_length=255,read_only=True)
    last_name=serializers.CharField(max_length=255,read_only=True)
    phone_number=serializers.CharField(max_length=20,read_only=True)
    profile_pic=serializers.URLField(read_only=True)
    is_verified=serializers.BooleanField(read_only=True)
    access_token=serializers.CharField(max_length=255, read_only=True)
    refresh_token=serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = User
        fields = ['email','id','password', 'access_token', 'refresh_token','first_name','last_name','phone_number','profile_pic','is_verified']

    

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        request=self.context.get('request')
        user = authenticate(request, email=email, password=password)
        if not user:
            raise AuthenticationFailed("invalid credential try again")
        tokens=user.tokens()
        return {
            'email':user.email,
            'id':user.id,
            'first_name':user.first_name,
            'last_name':user.last_name,
            'phone_number':user.phone_number,
            'is_verified' :user.is_verified,
            'profile_pic':user.profile_pic,
            "access_token":str(tokens.get('access')),
            "refresh_token":str(tokens.get('refresh'))
        }

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        fields = ['email']

    def validate(self, attrs):
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            current_site = settings.PASS_RESET_DOMAIN
            relative_link = f"/resetpassword/{uidb64}/{token}/"
            abslink = f"{current_site}{relative_link}"

            context = {
                'user': user,
                'reset_link': abslink
            }
            data = {
                'email_body': 'password_reset_email.html',  # Path to the email template
                'email_subject': "Reset your Password",
                'to_email': user.email,
                'from_email': settings.EMAIL_HOST_USER,
                'context': context  # Pass context to email
            }
            send_normal_email(data)

        return super().validate(attrs)

class ChangePasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    uidb64=serializers.CharField(read_only=True)
    token=serializers.CharField(read_only=True)
    class Meta:
        model = User
        fields = ['email','uidb64','token']

    def validate(self, attrs):
        
        email = attrs.get('email')
        print(email)
        if User.objects.filter(email=email).exists():
            user= User.objects.get(email=email)
            uidb64=urlsafe_base64_encode(smart_bytes(user.id))
            print(uidb64)
            token = PasswordResetTokenGenerator().make_token(user)
            print(token)
            
            return {
                'email':email,
                'uidb64':uidb64,
                'token':token,
            }
class SetNewPasswordSerializer(serializers.Serializer):
    password=serializers.CharField(max_length=100, min_length=6, write_only=True)
    confirm_password=serializers.CharField(max_length=100, min_length=6, write_only=True)
    uidb64=serializers.CharField(min_length=1, write_only=True)
    token=serializers.CharField(min_length=3, write_only=True)

    class Meta:
        fields = ['password', 'confirm_password', 'uidb64', 'token']

    def validate(self, attrs):
        try:
            token=attrs.get('token')
            uidb64=attrs.get('uidb64')
            password=attrs.get('password')
            confirm_password=attrs.get('confirm_password')

            user_id=force_str(urlsafe_base64_decode(uidb64))
            user=User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed("reset link is invalid or has expired", 401)
            if password != confirm_password:
                raise AuthenticationFailed("passwords do not match")
            user.set_password(password)
            user.save()
            return user
        except Exception as e:
            return AuthenticationFailed("link is invalid or has expired")


    
class LogoutUserSerializer(serializers.Serializer):
    refresh_token=serializers.CharField()

    default_error_message = {
        'bad_token': ('Token is expired or invalid')
    }

    def validate(self, attrs):
        self.token = attrs.get('refresh_token')

        return attrs

    def save(self, **kwargs):
        try:
            token=RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            return self.fail('bad_token')

    

    


