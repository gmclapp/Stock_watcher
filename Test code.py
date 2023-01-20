import pandas as pd
import pandas_datareader.data as web
import datetime as dt
import readchar
import requests
import time

session=requests.Session()
session.verify = False # SSL verification turned off, requests will give an InsecureRequestWarning
ticker = "TSLA"
source = "yahoo-dividends"
today = dt.date.today()

try:
    df = web.DataReader(ticker,source,today,session=session)
    print(df.head())
except KeyError as err:
    print("{}, market may not be open.".format(err))
time.sleep(60)
while True:
    keypress = readchar.readkey()
    print(readchar.key.UP)
    print(keypress)
