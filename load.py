import sqlite3 as db


def load(fact_actual, fact_forecast):
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
                        VALUES('Kwidzyn','Poland', 18.939999, 53.72  ),
                            ('HEL','Poland', 18.8, 54.62  ),
                            ('London','England', -0.25, 51.5  ),
                            ('Los Angeles','USA', -118.23433, 34.060257  ),
                            ('Bridgetown','Barbados', -59.59018, 13.110721  )
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