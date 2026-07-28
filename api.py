import pandas as pd
import requests
import datetime as dt
import os
import sqlite3 as db

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
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.RequestException as e:
    print("Request failed: ", e)

######################OGARNIANIE DICTIONARY "DATA" NA POJEDYNCZE MIASTA#################################
cities_data = []
for given_city in data:
    df_given_city = pd.DataFrame(given_city["hourly"])
    df_given_city["latitude"] = given_city["latitude"]    
    df_given_city["longitude"] = given_city["longitude"]
    df_given_city["fetch_time"] = str_data_download_time
    cities_data.append(df_given_city)

df_final = pd.concat(cities_data, ignore_index=True)

#print(df_final.head(10), len(df_final))
#print(df_final.isna().sum())
#print(df_final.info())

##################PO SPRAWDZENIU NIE MA NULL, ALE TIME I fetch_TIME SĄ STRINGAMI WIĘC:#############################################
df_final["time"] = pd.to_datetime(df_final["time"])
df_final["fetch_time"] = pd.to_datetime(df_final["fetch_time"], format="%Y-%m-%d_%H-%M")
df_final["lead_time"] = (df_final["time"] - df_final["fetch_time"]) / pd.Timedelta(hours=1)
df_final["lead_time"] = df_final["lead_time"].astype(int)

##################CZY TE DANE WGL MAJĄ SENS?##############################################
df_final["temperature_2m"] = df_final["temperature_2m"].clip(lower = -40, upper = 60)
df_final["relative_humidity_2m"] = df_final["relative_humidity_2m"].clip(lower = 0, upper = 100)
df_final["precipitation_probability"] = df_final["precipitation_probability"].clip(lower = 0, upper = 100)
df_final = df_final.drop_duplicates(subset = ["time", "latitude", "longitude"], keep="first")

#################TWORZENIE TABELI Z PROGNOZA I Z RZECZYWISTA TEMP###############################
fact_actual = df_final[df_final["lead_time"] == 0].copy().drop_duplicates(subset=["time", "longitude", "latitude"], keep="last")
fact_forecast = df_final[df_final["lead_time"] != 0].copy()
print(fact_actual.info())
with db.connect("weather_data.db") as conn:
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS dim_cities (
                            city_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            city_name TEXT, 
                            country TEXT, 
                            longitude REAL, 
                            latitude REAL,
                            UNIQUE(latitude, longitude))""")
    cursor.execute("""INSERT OR IGNORE INTO dim_cities (city_name, country, longitude, latitude)
                    VALUES('Kwidzyn','Poland', 18.9311, 53.7249  ),
                        ('HEL','Poland', 18.8035, 54.6038  ),
                        ('London','England', -0.1257, 51.5085  ),
                        ('Los Angeles','USA', -118.2437, 34.0522  ),
                        ('Bridgetown','Barbados', -59.6202, 13.1073  )
                       """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_actual (
            time DATETIME,temperature_2m REAL, relative_humidity_2m REAL, apparent_temperature REAL
            ,precipitation REAL, precipitation_probability REAL,rain REAL,
            pressure_msl REAL, wind_speed_10m REAL, wind_direction_10m REAL,
            wind_direction_80m REAL, wind_speed_80m REAL,
            latitude REAL, longitude REAL, fetch_time DATETIME, lead_time INTEGER,
            UNIQUE(time, latitude, longitude)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_forecast (
            time DATETIME,temperature_2m REAL, relative_humidity_2m REAL, apparent_temperature REAL
            ,precipitation REAL, precipitation_probability REAL,rain REAL,
            pressure_msl REAL, wind_speed_10m REAL, wind_direction_10m REAL,
            wind_direction_80m REAL, wind_speed_80m REAL,
            latitude REAL, longitude REAL, fetch_time DATETIME, lead_time INTEGER,
            UNIQUE(time, latitude, longitude,fetch_Time)
        )
    """)
    fact_actual.to_sql(name="temp_actual", con=conn, if_exists="replace", index=False )
    fact_forecast.to_sql(name="temp_forecast", con = conn, if_exists="replace", index=False)

    cursor.execute("INSERT OR IGNORE INTO fact_actual SELECT * FROM temp_actual")
    cursor.execute("INSERT OR IGNORE INTO fact_forecast SELECT * FROM temp_forecast")

    cursor.execute("DROP TABLE temp_actual")
    cursor.execute("DROP TABLE temp_forecast")

#print(pd.DataFrame(data[3]).info())
#print(df_3)
