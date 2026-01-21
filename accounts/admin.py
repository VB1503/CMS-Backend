from django.contrib import admin
from .models import User, OneTimePassword, Landmark
from django.utils.html import format_html

admin.site.register(OneTimePassword)

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['image_tag','phone_number','first_name','last_name','email','id']
    search_fields = ['first_name','last_name','phone_number','email']
    list_filter = ['is_active','is_verified','auth_provider']

    def image_tag(self, obj):
        if not obj.profile_pic:
            return "No Image"

        image_url = obj.profile_pic.url if hasattr(obj.profile_pic, "url") else obj.profile_pic

        return format_html(
            '<img src="{}" style="max-width:30px; max-height:30px; border-radius:50%; object-fit:cover;" />',
            image_url
        )


@admin.register(Landmark)
class LandmarkAdmin(admin.ModelAdmin):
    list_display = ['user','landId']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone_number', 'user__email']
