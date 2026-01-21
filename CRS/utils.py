import pickle
import numpy as np
import pandas as pd
import requests
from django.conf import settings
import os
import requests
from bs4 import BeautifulSoup
import json
# Load the Random Forest model from the pickle file


def get_weather_data(latitude, longitude):
    api_key = '31a8d1a6588a42a78ff115005242702'  # Replace with your WeatherAPI key
    base_url = 'http://api.weatherapi.com/v1/current.json'
    params = {'key': api_key, 'q': f'{latitude},{longitude}'}
   
    response = requests.get(base_url, params=params)
    data = response.json()

    if 'error' in data:
        print(f"Error from WeatherAPI: {data['error']['message']}")
        return None

   
    weather_data = {
        'city': data['location']['name'],
        'last_updated': data['current']['last_updated'],
        'temp_c': data['current']['temp_c'],
        'temp_f': data['current']['temp_f'],
        'is_day': data['current']['is_day'],
        'text': data['current']['condition']['text'],
        'icon': data['current']['condition']['icon'],
        'wind_mph': data['current']['wind_mph'],
        'wind_kph': data['current']['wind_kph'],
        'wind_degree': data['current']['wind_degree'],
        'wind_dir': data['current']['wind_dir'],
        'pressure_mb': data['current']['pressure_mb'],
        'pressure_in': data['current']['pressure_in'],
        'rainfall': data['current']['precip_mm'],
        'precip_in': data['current']['precip_in'],
        'humidity': data['current']['humidity'],
        'cloud': data['current']['cloud'],
        'feelslike_c': data['current']['feelslike_c'],
        'feelslike_f': data['current']['feelslike_f'],
        'vis_km': data['current']['vis_km'],
        'vis_miles': data['current']['vis_miles'],
        'gust_mph': data['current']['gust_mph'],
        'gust_kph': data['current']['gust_kph'],
        'uv': data['current']['uv'],
    }
    return weather_data

def get_prediction(request,N,P,K,temperature,humidity,ph,rainfall):
    model_path = os.path.join(settings.BASE_DIR, 'CRS', 'models', 'model.pkl')
    with open(model_path, 'rb') as f:
        RF = pickle.load(f)
    

    data = np.array([[N, P, K, temperature, humidity, ph, rainfall]])

    # Make prediction using the loaded model
    prediction = RF.predict(data)

    # Output the prediction
    print(f"The recommended crop is {prediction[0]}")

    return prediction[0]

def crop_yield_pred(year, season, crop, area, avg_temp, avg_rainfall):
    model_path = os.path.join(settings.BASE_DIR, 'CRS', 'models', 'cyp_model.pkl')
    with open(model_path, 'rb') as f:
        CYP = pickle.load(f)
    
    data = np.array([[area, crop, year, avg_rainfall, season, avg_temp]])

    # Make prediction using the loaded model
    predicted_yield = float(CYP.predict(data)[0])   # hg per hectare
    # Calculate total production using area (hectare)
    production = predicted_yield * float(area)      # total production in hg

    # Optional: convert hectogram (hg) to kilogram (kg)
    production_kg = production * 0.1

    # Round the values to two decimal places
    production_rounded = round(production_kg, 2)
    yield_rounded = round(predicted_yield, 2)

    return {
        "production": production_rounded,  # in kg
        "yield": yield_rounded              # in hg/ha
}




def get_fertilizer_recommendation(request, temperature, humidity, moisture, soil_type, crop_type, nitrogen, potassium, phosphorous):
    model_path = os.path.join(settings.BASE_DIR, 'CRS', 'models', 'rf_pipeline.pkl')
    with open(model_path, 'rb') as f:
        rf_pipeline = pickle.load(f)
    
    data = np.array([[temperature, humidity, moisture, soil_type, crop_type, nitrogen, potassium, phosphorous]])
    prediction = rf_pipeline.predict(data)
    print(prediction)
    recommendation = prediction[0]

    # Fertilizer labels
    fertilizer_labels = [
            '10-26-26',   # 0
            '14-35-14',   # 1
            '17-17-17',   # 2
            '20-20',      # 3
            '28-28',      # 4
            'DAP',        # 5
            'Urea'        # 6
        ]


    fertilizer = {
    0: "The 10-26-26 fertilizer is a phosphorus and potassium-rich fertilizer with a lower proportion of nitrogen. It typically contains 10% nitrogen, 26% phosphorus pentoxide (P2O5), and 26% potassium oxide (K2O). This formulation is ideal for promoting root development, flowering, and fruiting in plants. It is suitable for flowering plants, fruit-bearing trees, and root vegetables. Apply evenly to the soil before planting or during flowering and fruiting stages. Incorporate into the soil and follow recommended application rates.",

    1: "The 14-35-14 fertilizer is a phosphorus-rich fertilizer containing 14% nitrogen, 35% phosphorus pentoxide (P2O5), and 14% potassium oxide (K2O). It is ideal for crops requiring strong root development and improved flowering and fruit formation. Apply before planting or as a side dressing and mix well with soil.",

    2: "The 17-17-17 fertilizer is a balanced fertilizer containing equal proportions of nitrogen, phosphorus, and potassium. It supports overall plant growth, flowering, and fruiting. Suitable for vegetables, fruits, grains, and ornamental plants. Apply evenly before planting or as a top dressing.",

    3: "The 20-20 fertilizer provides balanced nutrition with 20% nitrogen, 20% phosphorus, and 20% potassium. It promotes healthy foliage, root growth, and flowering. Suitable for a wide range of crops. Apply evenly and incorporate into the soil.",

    4: "The 28-28 fertilizer contains equal amounts of nitrogen, phosphorus, and potassium at higher concentrations. It is useful during the active growing season to boost plant growth, flowering, and root development. Avoid overapplication.",

    5: "Diammonium phosphate (DAP) contains high phosphorus and moderate nitrogen (18-46-0). It promotes early root growth and plant vigor. Commonly applied before planting or as a basal fertilizer. Avoid direct root contact.",

    6: "Urea is a nitrogen-rich fertilizer containing about 46% nitrogen. It promotes vegetative growth and is widely used for crops such as cereals, vegetables, and grasses. Apply evenly and irrigate after application to prevent nitrogen loss."
}

    recommended_fertilizer = {"fertilizer":fertilizer[recommendation],"name":fertilizer_labels[recommendation]}

    # Scrape fertilizer standards and content from a reliable source

    
    return recommended_fertilizer
