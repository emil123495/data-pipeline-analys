from extract import extract
from transform import transform
from load import load

def etl():
     print("Start of extract")
     data, str_data_download_time = extract()
     print("End of extract")

     print("Start of Transform")
     fact_actual, fact_forecast = transform(data, str_data_download_time)
     print("End of Transform")

     print("Start of Load")
     load(fact_actual, fact_forecast)
     print("End of Load")

if __name__ == "__main__":
    etl()