import pandas as pd
import datetime as dt

def transform(data, str_data_download_time):
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
    return fact_actual, fact_forecast