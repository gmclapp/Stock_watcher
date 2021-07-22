import pandas as pd
import pandas_datareader.data as web
import datetime as dt

ticker = "TSLA"
source = "yahoo-dividends"
today = dt.date.today()

df = web.DataReader(ticker,source,today)
print(df.head())
