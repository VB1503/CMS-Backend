from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.managers import UserManager
# Create your models here.

AUTH_PROVIDERS ={'email':'email', 'google':'google'}

class User(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True, editable=False) 
    email = models.EmailField(
        max_length=255, verbose_name=_("Email Address"), unique=True
    )
    phone_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=100, verbose_name=_("Last Name"), null=True, blank=True)
    profile_pic = models.URLField(default="https://cdn-icons-png.flaticon.com/128/149/149071.png")
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified=models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    auth_provider=models.CharField(max_length=50, blank=False, null=False, default=AUTH_PROVIDERS.get('email'))
    

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def tokens(self):    
        refresh = RefreshToken.for_user(self)
        return {
            "refresh":str(refresh),
            "access":str(refresh.access_token)
        }


    def __str__(self):
        return f"{self.email} {self.first_name}"

    @property
    def get_full_name(self):
        return f"{self.first_name.title()} {self.last_name.title()}"


class Landmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    landId=models.BigAutoField(primary_key=True, editable=False)
    coordinates = models.JSONField(default=list)
    location_details = models.JSONField(default=list)
class OneTimePassword(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE)
    otp=models.CharField(max_length=6)


    def __str__(self):
        return f"{self.user.first_name} - {self.user.phone_number}"