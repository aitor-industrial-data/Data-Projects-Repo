import requests
import logging
import os
import time
from typing import Dict, Any
from dotenv import load_dotenv
from extract_openweather import get_weather_forecast
from transform_openweather import transform_weather_forecast


load_dotenv()


# ==============================================================================
# TEST OPEN-WEATHER
# ==============================================================================
lat = os.getenv("SITE_LATITUDE",40.4167)
lon = os.getenv("SITE_LONGITUDE",-3.7033)
weather_data=get_weather_forecast(lat,lon)
print(f"A las {weather_data[0]['dt_txt']} habrá {weather_data[0]['main']['temp']}°C y un {weather_data[0]['clouds']['all']}% de nubes.")

clean_data_weather=[]
for item in weather_data:
    clean_item = transform_weather_forecast(item)
    print (f'\n clean: {clean_item}')
    clean_data_weather.append(clean_item)

print(clean_data_weather)