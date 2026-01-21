from django.contrib import admin
from .models import CropRecommendation,PreviousCropRequest,FertilizerRecommendationRequest
# Register your models here.
@admin.register(CropRecommendation)
class CropRecommendationAdmin(admin.ModelAdmin):
    list_display = ['user','start_date','prediction','cropId']
    search_fields = ['user__first_name','user__last_name', 'prediction','user__phone_number','user__email']
    list_filter = ['start_date','prediction']
@admin.register(PreviousCropRequest)
class CropYieldPredictionAdmin(admin.ModelAdmin):
    list_display = ['user', 'landId','year','season','crop','production','yield_per_hectare','created_at']

@admin.register(FertilizerRecommendationRequest)
class FertilizerRecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'landId','fertilizer','created_at']