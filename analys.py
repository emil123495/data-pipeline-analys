import sqlite3
import pandas as pd

with sqlite3.connect("weather_data.db") as conn:
    #cursor = conn.cursor()
    #cursor.execute("DROP TABLE dim_cities")
   #cursor.execute("DROP TABLE fact_forecast")
   query = "SELECT time, temperature_2m, wind_speed_10m FROM df_weather WHERE temperature_2m > 10 LIMIT 15 "
   query = "SELECT time, longitude, latitude, wind_speed_10m FROM df_weather ORDER BY wind_speed_10m DESC LIMIT 5"
   query = "SELECT AVG(apparent_temperature) as srednia_temp, MAX(precipitation_probability) as max_szansa_na_deszcz FROM df_weather GROUP BY longitude, latitude"
   query = "SELECT COUNT(*) as liczba_pechowych FROM df_weather WHERE rain > 0 AND pressure_msl < 1005"
   query = "SELECT longitude, latitude FROM df_weather GROUP BY longitude, latitude HAVING AVG(relative_humidity_2m) > 75"
   query = """SELECT
                   fact_actual.time,
                   fact_actual.longitude,
                   fact_actual.latitude,
                   fact_actual.temperature_2m actual_temp,
                   fact_forecast.fetch_time,
                   fact_forecast.temperature_2m as predicted_temp,
                   fact_forecast.lead_time as how_many_hours_before,
                   (fact_actual.temperature_2m - fact_forecast.temperature_2m) as error,
                   dim_cities.country,
                   dim_cities.city_name
               FROM fact_actual
               JOIN fact_forecast
                   ON fact_actual.latitude = fact_forecast.latitude
                   AND fact_actual.longitude = fact_forecast.longitude
                   AND fact_actual.time = fact_forecast.time
               JOIN dim_cities 
                   ON dim_cities.longitude = fact_actual.longitude
                   AND dim_cities.latitude = fact_actual.latitude
               ORDER BY fact_actual.longitude DESC """
   df_read = pd.read_sql_query(query, conn)
print(df_read)