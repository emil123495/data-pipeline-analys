import streamlit as st
import pandas as pd
import sqlite3

@st.cache_data(ttl=3600)
def load_cities(city_name):

   # query =     ("""SELECT
   #                    fact_actual.time,
   #                    fact_actual.longitude,
   #                    fact_actual.latitude,
   #                    fact_actual.temperature_2m actual_temp,
   #                    fact_forecast.fetch_time,
   #                    fact_forecast.temperature_2m as predicted_temp,
   #                    fact_forecast.lead_time as how_many_hours_before,
   #                    ABS(fact_actual.temperature_2m - fact_forecast.temperature_2m) as error,
   #                    dim_cities.country,
   #                    dim_cities.city_name
   #                FROM fact_actual
   #                JOIN fact_forecast
   #                    ON fact_actual.latitude = fact_forecast.latitude
   #                    AND fact_actual.longitude = fact_forecast.longitude
   #                    AND fact_actual.time = fact_forecast.time
   #                JOIN dim_cities 
   #                    ON dim_cities.longitude = fact_actual.longitude
   #                    AND dim_cities.latitude = fact_actual.latitude
   #                WHERE how_many_hours_before > 0 AND dim_cities.city_name = ? AND fact_actual.time = "2026-07-30 11:00:00"
   #                ORDER BY fact_actual.longitude DESC 
   #                """)
    query =     ("""SELECT
                       fact_forecast.lead_time as how_many_hours_before,
                       AVG(ABS(fact_actual.temperature_2m - fact_forecast.temperature_2m)) as error,
                       COUNT(*) as samples_count
                   FROM fact_actual
                   JOIN fact_forecast
                       ON fact_actual.latitude = fact_forecast.latitude
                       AND fact_actual.longitude = fact_forecast.longitude
                       AND fact_actual.time = fact_forecast.time
                   JOIN dim_cities 
                       ON dim_cities.longitude = fact_actual.longitude
                       AND dim_cities.latitude = fact_actual.latitude
                   WHERE how_many_hours_before > 0 AND dim_cities.city_name = ? 
                   GROUP BY how_many_hours_before
                   ORDER BY how_many_hours_before ASC
                   """)   

    with sqlite3.connect("weather_data.db") as conn:
        df = pd.read_sql_query(query, conn, params=[city_name])
    return df


list_of_cities = ["Kwidzyn", "HEL", "Los Angeles", "Bridgetown", "London"]
selected_city = st.sidebar.selectbox("Select city", list_of_cities)
st.set_page_config(page_title="Weather Forecast Accuracy", layout="wide")
st.title("🌤️ Weather Forecast Accuracy Dashboard")
st.caption("Analysis of Open-Meteo forecast accuracy depending on lead time")
st.title(selected_city.upper())
df = load_cities(selected_city)
lead_time_hours = st.slider("Lead time hours:", min_value = 0, max_value = 168,value=24, step = 1)
col1, col2 = st.columns(2)
row = df[df["how_many_hours_before"] == lead_time_hours]["error"]
if not row.empty:
    col1.metric(f"Forecast error with {lead_time_hours}h lead time", f"{row.values[0]:.1f}°C")
    col2.metric(f"Samples count:", df[df["how_many_hours_before"] == lead_time_hours]["samples_count"].values[0])
else:
    col1.write("No data available")
#col2.metric("Błąd przy prognozie 168h (7 dni)", f"{df[df.how_many_hours_before==168].error.values[0]:.1f}°C")
st.line_chart(df, x = "how_many_hours_before", y = "error", x_label= "Lead time [h]", y_label= "Forecast error [°C]")
#for city in list_of_cities:
#    st.write(city.upper())
#    st.line_chart(load_cities(city), x = "how_many_hours_before", y = "error")

