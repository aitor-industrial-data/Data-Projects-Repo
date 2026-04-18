import requests
import logging
import os
import time
from typing import Dict, Any
from dotenv import load_dotenv
from extract_openweather import get_weather_forecast
from transform_openweather import transform_weather_data
from extract_pvgis import get_pvgis_data


load_dotenv()


# ==============================================================================
# TEST OPEN-WEATHER
# ==============================================================================

weather_data=get_weather_forecast()
#print(f"A las {weather_data[0]['dt_txt']} hará {weather_data[0]['main']['temp']}°C y un {weather_data[0]['clouds']['all']}% de nubes.")
#print(weather_data[0])

data_pvgis=get_pvgis_data()
print(data_pvgis['outputs']['hourly'][0])
'''for item in weather_data:
    print(item)
    #print (f'\n clean: {clean_item}')
    #clean_data_weather.append(clean_item)

#print(clean_data_weather)'''

'''
pvgis_data = get_pvgis()
print(pvgis_data)
#print(f"Producción anual: {pvgis_data['outputs']['totals']['fixed']['E_y']} kWh")
'''
'''clean_data_weather=[]
for item in weather_data:
    clean_item = transform_weather_forecast(item)
    print (f'\n clean: {clean_item}')
    #clean_data_weather.append(clean_item)

#print(clean_data_weather)'''