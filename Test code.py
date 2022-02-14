import pandas as pd
import pandas_datareader.data as web
import datetime as dt
import readchar

ticker = "TSLA"
source = "yahoo-dividends"
today = dt.date.today()

try:
    df = web.DataReader(ticker,source,today)
    print(df.head())
except KeyError as err:
    print("{}, market may not be open.".format(err))
    
while True:
    keypress = readchar.readkey()
    print(keypress)
