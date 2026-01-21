from .models import CropRecommendation,PreviousCropRequest, FertilizerRecommendationRequest
from rest_framework import serializers
from accounts.models import Landmark
class CropRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CropRecommendation
        fields = '__all__'

    def create(self, validated_data):
        return CropRecommendation.objects.create(**validated_data)

class LandmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Landmark
        fields = "__all__"

class CropYieldPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreviousCropRequest
        fields = '__all__'

    def create(self, validated_data):
        return PreviousCropRequest.objects.create(**validated_data)
    
class FertilizerRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FertilizerRecommendationRequest
        fields = '__all__'

    def create(self, validated_data):
        return FertilizerRecommendationRequest.objects.create(**validated_data)