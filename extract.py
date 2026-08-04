import requests
import datetime as dt
import os

url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": [13.1073, 34.0522, 54.6038, 53.7249, 51.5085],
    "longitude": [-59.6202, -118.2437, 18.8035, 18.9311, -0.1257],
    "hourly": [
        "temperature_2m", 
        "relative_humidity_2m", 
        "apparent_temperature", 
        "precipitation", 
        "precipitation_probability", 
        "rain", 
        "pressure_msl", 
        "wind_speed_10m", 
        "wind_direction_10m", 
        "wind_direction_80m", 
        "wind_speed_80m"
    ],
    "forecast_days": 16
    }

def extract():
    data_download_time = dt.datetime.now(dt.timezone.utc).replace(minute = 0, second = 0, microsecond= 0)
    str_data_download_time = data_download_time.strftime("%Y-%m-%d_%H-%M")
    #####################ZCZYTYWANIE I ZAPISYWANIE DANYCH Z API#######################
    os.makedirs("data_raw", exist_ok=True)
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        with open(f"data_raw/raw_weahter_{str_data_download_time}.json", "w", encoding="utf-8") as file:
            file.write(response.text)
        data = response.json()
        return data, str_data_download_time
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.RequestException as e:
        print("Request failed: ", e)

