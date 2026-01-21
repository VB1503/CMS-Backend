from django.shortcuts import render
from .models import *
from .crop_mapping import CROP_NAME_TO_NUMBER
from .croptype_mapping import encoded_crop_names
from .utils import get_prediction,get_weather_data,crop_yield_pred,get_fertilizer_recommendation
from rest_framework.generics import GenericAPIView
from .serializers import CropRecommendationSerializer,LandmarkSerializer,CropYieldPredictionSerializer,FertilizerRecommendationSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Landmark
from rest_framework.views import APIView
from rest_framework.response import Response
from .utils import get_weather_data
from django.shortcuts import get_object_or_404


class ListCreateLandmarkAPIView(GenericAPIView):
    queryset = Landmark.objects.all()
    serializer_class = LandmarkSerializer

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('pk')
        user = User.objects.get(pk=user_id)

        landmarks = Landmark.objects.filter(user_id=user)
        serializer = self.get_serializer(landmarks, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class DeleteLandmarkAPIView(GenericAPIView):
    queryset = Landmark.objects.all()
    serializer_class = LandmarkSerializer

    def delete(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')  # Get user_id from URL or request kwargs
        land_id = kwargs.get('landId')  # Get landId from URL or request kwargs

        # Fetch the Landmark object that matches both user_id and landId
        landmark = get_object_or_404(Landmark, user_id=user_id, landId=land_id)

        # Delete the landmark
        landmark.delete()

        # Return success response
        return Response({"message": "Landmark deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
class CropRecomendationApiView(APIView):
    serializer_class = CropRecommendationSerializer

    def post(self, request):
        crop_data = request.data
        user = crop_data.get('user')
        landId = crop_data.get('landId')

        try:
            print(crop_data)
            # Fetch Landmark object based on user and landId
            landmark = Landmark.objects.get(user=user, landId=landId)

            # Access coordinates from the Landmark object
            coordinates = landmark.coordinates

            # Calculate median latitude and longitude
            latitudes = [coord['lat'] for coord in coordinates]
            longitudes = [coord['lng'] for coord in coordinates]

            median_latitude = sum(latitudes) / len(latitudes)
            median_longitude = sum(longitudes) / len(longitudes)

            # Fetch weather data based on the median coordinates
            weather_data = get_weather_data(median_latitude, median_longitude)
            if weather_data:
                # Process crop recommendation data using weather data
                n = crop_data.get('nitrogen')
                p = crop_data.get('phosphorus')
                k = crop_data.get('potassium')
                ph = crop_data.get('ph')
                prediction = get_prediction(N=n, P=p, K=k, temperature=weather_data['temp_c'], humidity=weather_data['humidity'], ph=ph, rainfall=weather_data['rainfall'], request=request)
                # Prepare data for serialization
                data = { 
                    "user": user,
                    "landId": landId, 
                    "N": n, 
                    "P": p, 
                    "K": k, 
                    "temperature": weather_data['temp_c'],  
                    "humidity": weather_data['humidity'], 
                    "ph": ph, 
                    "rainfall": weather_data['rainfall'],
                    "prediction": prediction
                }
               
                serializer = self.serializer_class(data=data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    user_data = serializer.data
                    return Response({
                        'data': user_data,
                        'message': 'Thanks for using our Recommendation System'
                    }, status=status.HTTP_201_CREATED)

            else:
                return Response({'success': False, 'message': 'Weather data not available'}, status=status.HTTP_400_BAD_REQUEST)

        except Landmark.DoesNotExist:
            return Response({'success': False, 'message': 'Landmark not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CropYieldPredictionView(APIView):
    serializer_class = CropYieldPredictionSerializer

    def post(self, request):
        crop_data = request.data

        user_id = int(crop_data.get('user'))
        land_id = int(crop_data.get('landId'))
        year = int(crop_data.get('year'))
        season = int(crop_data.get('season'))
        crop = crop_data.get('crop')
        area = float(crop_data.get('area'))
        if not year:
            return Response(
                {'success': False, 'message': 'Year is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
            landmark = Landmark.objects.get(landId=land_id, user=user)

            # Calculate median coordinates
            coordinates = landmark.coordinates
            latitudes = [coord['lat'] for coord in coordinates]
            longitudes = [coord['lng'] for coord in coordinates]

            median_latitude = sum(latitudes) / len(latitudes)
            median_longitude = sum(longitudes) / len(longitudes)

            # Fetch weather data
            weather_data = get_weather_data(median_latitude, median_longitude)
            if not weather_data:
                return Response(
                    {'success': False, 'message': 'Weather data not available'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Predict yield
            result = crop_yield_pred(
                year,
                season,
                CROP_NAME_TO_NUMBER[crop],              # crop is STRING
                area,
                avg_temp=weather_data['temp_c'],
                avg_rainfall=weather_data['rainfall']
            )
            season_names = ["Kharif","Whole Year","Autumn","Rabi","Summer","Winter"]
            # Prepare DB data
            data = {
                "user": user_id,
                "landId": land_id,
                "year": year,
                "season": season_names[season],
                "crop": crop,
                "area": area,
                "production": result.get("production"),
                "yield_per_hectare": result.get("yield"),
            }
            serializer = self.serializer_class(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({
                "data": serializer.data,
                "message": "Crop yield prediction saved successfully"
            }, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            return Response(
                {'success': False, 'message': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Landmark.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Landmark not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class FertilizerRecommendation(APIView):
    serializer_class = FertilizerRecommendationSerializer
    def post(self, request, format=None):
        # Extract data from the request
        user_id = int(request.data.get('user'))
        land_id = int(request.data.get('landId'))
        temperature = int(request.data.get('temperature'))
        humidity = int(request.data.get('humidity'))
        moisture = int(request.data.get('moisture'))
        soil_type = int(request.data.get('soil_type'))
        crop_type = request.data.get('crop_type')
        nitrogen = int(request.data.get('nitrogen'))
        phosphorous = int(request.data.get('phosphorous'))
        potassium = int(request.data.get('potassium'))

        # Call the utility function to get the fertilizer recommendation
        recommendation = get_fertilizer_recommendation(request=request,crop_type=encoded_crop_names[crop_type], nitrogen=nitrogen, phosphorous=phosphorous, potassium=potassium,temperature=temperature,humidity=humidity,soil_type=soil_type,moisture=moisture)
        soil_names = {0: 'Black', 1: 'Clayey', 2: 'Loamy', 3: 'Red', 4: 'Sandy'}
        print(recommendation['name'])
        data = {
            "user": user_id,
            "landId": land_id,
            "temperature":temperature,
            "humidity":humidity,
            "moisture":moisture,
            "soil_type":soil_names[soil_type],
            "crop_type":crop_type,
            "nitrogen":nitrogen,
            "phosphorous":phosphorous,
            "potassium":potassium,
            "fertilizer":recommendation['name']
        }
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"recommendation": recommendation}, status=status.HTTP_201_CREATED)


class UserPredictionHistory(APIView):
    """
    View to fetch complete prediction history for a user and specific landmark
    """
    def get(self, request, id, landId):
        try:
            user = User.objects.get(id=id)
            landmark = Landmark.objects.get(landId=landId, user=user)
            
            # Fetch all predictions for this user and landmark
            crop_recommendations = CropRecommendation.objects.filter(user=user, landId=landmark)
            crop_yields = PreviousCropRequest.objects.filter(user=user, landId=landmark)
            fertilizer_recommendations = FertilizerRecommendationRequest.objects.filter(user=user, landId=landmark)
            
            # Serialize data
            crop_rec_serializer = CropRecommendationSerializer(crop_recommendations, many=True)
            crop_yield_serializer = CropYieldPredictionSerializer(crop_yields, many=True)
            fertilizer_serializer = FertilizerRecommendationSerializer(fertilizer_recommendations, many=True)
            
            # Structure the response
            history_data = {
                "user_id": id,
                "landId": landId,
                "crop_recommendations": crop_rec_serializer.data,
                "crop_yield_predictions": crop_yield_serializer.data,
                "fertilizer_recommendations": fertilizer_serializer.data,
                "summary": {
                    "total_crop_recommendations": crop_recommendations.count(),
                    "total_crop_yields": crop_yields.count(),
                    "total_fertilizer_recommendations": fertilizer_recommendations.count()
                }
            }
            
            return Response({
                "data": history_data,
                "message": "User prediction history retrieved successfully"
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response(
                {'success': False, 'message': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Landmark.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Landmark not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    


