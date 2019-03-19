import datetime as dt
import time
import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
import pandas as pd
import pandas_datareader.data as web
import json
import sys
import os
import sanitize_inputs as si

__version__ = '0.7.2'
#os.system("mode con cols=60 lines=60")

# Hide all warnings
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")
    
class positions():
    def __init__(self):
        self.position_list = []
        self.meta_data = {}
    def list_positions(self):
        plist = []
        for pos in self.position_list:
            plist.append(pos['ticker'])
        return(plist)
    
    def enter_order(self, buysell, date, ticker, shares, price,
                    commission=4.95, fees=0):
        '''buysell = 'buy' or 'sell', date of order(str), stock ticker (not case
        sensitive), price of order, number of shares transacted,
        commission, and fees if applicable.'''
        exists_flag = False
        ticker = ticker.upper()
        for pos in self.position_list:
            if ticker == pos['ticker']:
                exists_flag = True
                print("Position is already on watch list")
                pos['transactions'].append({'b/s':buysell,
                                            'date':date,
                                            'price':price,
                                            'commission':commission,
                                            'fees':fees,'shares':shares})
        if exists_flag:
            pass
        else:
            self.position_list.append({'ticker':ticker,
                                       'transactions':[{'b/s':buysell,'date':date,'price':price,'commission':commission,'fees':fees,'shares':shares}],
                                       'dividends':[],
                                       'cost basis':shares*price + commission + fees,
                                       'current shares':shares,
                                       'last price':price,
                                       'last price date':date,
                                       'last dividend':0,
                                       'last yield date':date})

    def enter_dividend(self, ticker, date, amount, shares):
        exists_flag = False
        ticker = ticker.upper()
        for pos in self.position_list:
            if ticker == pos['ticker']:
                exists_flag = True
                total = amount*shares
                print("Shares: {}; Dividend: ${:<7.2f}; Total: ${:<7.2f}"\
                      .format(shares,amount,total))
                pos['dividends'].append({'date': date,
                                         'amount':amount,
                                         'shares':shares,
                                         'total':total})

    def enter_ticker(self, ticker):
        self.position_list.append({'ticker':ticker,
                                   'transactions':[],
                                   'dividends':[],
                                   'cost basis':0,
                                   'current shares':0})
    def sort_open_positions(self):
        self.position_list.sort(key=lambda x: x['ticker'], reverse=False)
        
    def calc_cost_basis(self):
        print("Calculating cost basis...")
        for pos in self.position_list:
            accum = 0
            shares = 0
            pos['transactions'].sort(key=lambda x: parse_date(x['date']), reverse=False)
            # in place sort of transactions list by date
            
            for transaction in pos['transactions']:
                if transaction['b/s'] == 'b':
                    shares += transaction['shares']
                    accum += transaction['price']*transaction['shares']\
                             + transaction['commission'] + transaction['fees']
                elif transaction['b/s'] == 's':
                    shares -= transaction['shares']
                    accum -= transaction['price']*transaction['shares']\
                             + transaction['commission'] + transaction['fees']
                    
            pos['dividends'].sort(key=lambda x: parse_date(x['date']), reverse=False)
            # in place sort of dividends list by date
            for d in pos['dividends']:
                accum -= d['total']
                    

            try:        
                pos['cost basis'] = accum/shares
            except ZeroDivisionError:
                pos['cost basis'] = 0
            pos['current shares'] = shares

    def calc_average_yield(self):
        # position value weighted average of dividend yield
        # this calculation assumes that dividends are paid quarterly
        accum = 0
        for pos in self.position_list:
            position_value = pos["current shares"]*pos["last price"]
            try:
                annual_yield = (pos["last dividend"]/pos["last price"])*4
            except KeyError:
                annual_yield = 0
                print("No dividend data for {}".format(pos["ticker"]))
            accum += position_value*annual_yield        
        self.meta_data["average yield"] = accum/self.meta_data["portfolio value"]
        
        
    def calc_portfolio_value(self):
        self.meta_data["portfolio value"] = 0
        for pos in self.position_list:
            if pos["current shares"] != 0:
                pos_value = pos["last price"] * pos["current shares"]
                self.meta_data["portfolio value"] += pos_value
                
    def shares_at_date(self, ticker, date):
        '''takes a ticker symbol, and a datetime.date() and returns the number
        of shares of that symbol held at the given date.'''
        shares = 0
        for pos in self.position_list:
            if pos['ticker'] == ticker:
                for transaction in pos['transactions']:
                    if int((date - parse_date(transaction['date'])).days) >= 0:
                        if transaction['b/s'] == 'b':
                            shares += transaction['shares']
                           
                        elif transaction['b/s'] == 's':
                            shares -= transaction['shares']
        return(shares)            

    def save_positions(self):
        with open("watchlist.stk",'w') as f:
            json.dump([self.meta_data, self.position_list], f,sort_keys=False,indent=4,default=default)

    def load_positions(self):
        print("Loading trading data...")
        with open("watchlist.stk","r") as f:
            self.meta_data, self.position_list = json.load(f)
def default(o):
    if isinstance(o, np.int64): return(int(o))
    raise TypeError

def order(watch_list):
    today = dt.date.today()
    orders = ['Buy',
              'Sell',
              'Back']
    date_options = ['Today',
                    'Enter date',
                    'Back']
    print("What kind of order?")

    order = orders[si.select(orders)]
    if order == 'Back':
        print("\n",end='')
        return()
    print("When was this order?")
    date_selection = date_options[si.select(date_options)]
    if date_selection == 'Today':
        date = today
        year = today.year
        month = today.month
        day = today.day
    elif date_selection == 'Enter date':
        year = si.get_integer("Enter year.\n>>>",
                              upper=today.year+1,lower=1970)
        month = si.get_integer("Enter month.\n>>>",upper=13,lower=0)
        day = si.get_integer("Enter day.\n>>>",upper=32,lower=0)
    elif date_selection == 'Back':
        print("\n",end='')
        return()
    date_str = str(year)+'-'+str(month)+'-'+str(day)
        
    tick = input("Enter stock ticker.\n>>>").upper()
    shares = si.get_integer("Enter number of shares.\n>>>",lower=0)
    price = si.get_real_number("Enter share price.\n>>>",lower=0)
    comm = si.get_real_number("Enter commission.\n>>>",lower=-0.0001)
    fee = si.get_real_number("Enter fees.\n>>>",lower=-0.0001)

    watch_list.enter_order(order[0].lower(),
                           date_str, tick,
                           shares,
                           price,
                           comm,
                           fee)
    watch_list.calc_cost_basis()

def view(pos):
    try:
        pos_yield = (pos["last dividend"]/pos["last price"])*4
    except KeyError:
        pos_yield = 0
    print("Ticker: {}".format(pos["ticker"]))
    print("Shares: {}".format(pos["current shares"]))
    print("Current cost basis: ${:<7.2f}".format(pos["cost basis"]))
    print("Annual dividend yield: {:<7.2f}%".format(pos_yield*100))
    today = dt.date.today()

    df = get_quoteDF(pos["ticker"],pos,today,force=True)
    
    if df is None:
        print("Current price: No data")
    else:
        
        last_close = pos["last price"]
        print("Current price: ${:<7.2f}\n".format(last_close))
        
    print("Transactions:")
    for t in pos["transactions"]:
        print("{}: {} {} @ ${:<7.4f}".format(t['date'],t['b/s'].upper(),
                                             t['shares'],t['price']))
    print("\nDividends:")
    for d in pos['dividends']:
        print("{}: {} x ${:<7.2f} = ${:<7.2f}"\
              .format(d['date'],d['shares'],d['amount'],d['total']))
    print("\n",end='')
    
def edit(watch_list):
    print("\n",end='')
    edit_list = ['Transactions',
                 'Dividends',
                 'Tickers',
                 'Back']
    viewlist = watch_list.list_positions() # used in several options
    viewlist.append('Back')
    edit_sel = edit_list[si.select(edit_list)]
    if edit_sel == 'Transactions':
        print("\n",end='')
        print("For which position would you like to edit a transaction?")
        
        edit_pos = viewlist[si.select(viewlist)]
        print("\nEditing",edit_pos,"\n")
        for pos in watch_list.position_list:
            if pos["ticker"] == edit_pos:
                print("Which transaction would you like to edit?")
                tran_list = []
                for t in pos["transactions"]:
                    trans_str = "{}: {} {} @ ${:<7.4f}"\
                                .format(t['date'],
                                        t['b/s'].upper(),
                                        t['shares'],
                                        t['price'])
                    tran_list.append(trans_str)
                t_sel = tran_list[si.select(tran_list)]
                for i,t in enumerate(tran_list): # get index of transaction
                    if t_sel == t:
                        break
                    
                print("What would you like to edit?")
                edit_choices = ['Date',
                                'Buy/Sell',
                                'Shares',
                                'Price',
                                'Commission',
                                'Fees',
                                'Delete transaction',
                                'Back']
                e_choice = edit_choices[si.select(edit_choices)]
                
                if e_choice == 'Date':
                    today = dt.date.today()
                    year = si.get_integer("Enter year.\n>>>",
                                          upper=today.year+1,lower=1970)
                    month = si.get_integer("Enter month.\n>>>",
                                           upper=13,lower=0)
                    day = si.get_integer("Enter day.\n>>>",
                                         upper=32,lower=0)
                    date_str = str(year)+'-'+str(month)+'-'+str(day)
                    
                    pos["transactions"][i]['date'] = date_str
                    
                elif e_choice == 'Buy/Sell':
                    orders = ['Buy',
                              'Sell']
                    print("What kind of order?")
                    order = orders[si.select(orders)]
                    
                    pos["transactions"][i]['b/s'] = order[0].lower()
                    
                elif e_choice == 'Shares':
                    shares = si.get_integer("Enter number of shares.\n>>>",
                                            lower=0)
                    
                    pos["transactions"][i]['shares'] = shares
                    
                elif e_choice == 'Price':
                    price = si.get_real_number("Enter share price.\n>>>",
                                               lower=0)

                    pos["transactions"][i]['price'] = price
                elif e_choice == 'Commission':
                    commission = si.get_real_number("Enter commission.\n>>>",
                                                    lower=0)
                    pos["transactions"][i]['commission'] = commission
                elif e_choice == 'Fees':
                    fees = si.get_real_number("Enter fees.\n>>>",
                                                    lower=0)
                    pos["transactions"][i]['fees'] = fees
                elif e_choice == 'Delete transaction':
                    pos["transactions"].pop(i)
                elif e_choice == 'Back':
                    pass
                
    elif edit_sel == 'Dividends':
        print("For which position would you like to edit a dividend?")
        edit_pos = viewlist[si.select(viewlist)]
        for pos in watch_list.position_list:
            if pos["ticker"] == edit_pos:
                print("Which dividend would you like to edit?")
                div_list = []
                for d in pos["dividends"]:
                    div_str = "{}: {} x ${:<7.2f} = ${:<7.2f}"\
                                .format(d['date'],
                                        d['shares'],
                                        d['amount'],
                                        d['total'])
                    
                    div_list.append(div_str)
                div_list.append('Back')
                d_sel = div_list[si.select(div_list)]
                if d_sel == 'Back':
                    print("\n",end='')
                    return()
                
                for i,d in enumerate(div_list): # get index of transaction
                    if d_sel == d:
                        break
                    
                print("What would you like to edit?")
                edit_choices = ['Date',
                                'Amount',
                                'Shares',
                                'Total',
                                'Delete dividend',
                                'Back']
                
                e_choice = edit_choices[si.select(edit_choices)]
                if e_choice == 'Date':
                    today = dt.date.today()
                    year = si.get_integer("Enter year.\n>>>",
                                          upper=today.year+1,lower=1970)
                    month = si.get_integer("Enter month.\n>>>",
                                           upper=13,lower=0)
                    day = si.get_integer("Enter day.\n>>>",
                                         upper=32,lower=0)
                    date_str = str(year)+'-'+str(month)+'-'+str(day)
                    
                    pos["dividends"][i]['date'] = date_str
                    
                elif e_choice == 'Amount':
                    amount = si.get_real_number("Enter dividend amount.\n>>>",
                                               lower=0)
                    pos["dividends"][i]['amount'] = amount
                elif e_choice == 'Shares':
                    shares = si.get_integer("Enter number of shares.\n>>>",
                                            lower=0)
                    
                    pos["dividends"][i]['shares'] = shares
                    
                elif e_choice == 'Total':
                    price = si.get_real_number("Enter total dividend.\n>>>",
                                               lower=0)
                    pos["dividends"][i]['total'] = price

                elif e_choice == 'Delete dividend':
                    pos["dividends"].pop(i)

                elif e_choice == 'Back':
                    pass
                
    elif edit_sel == 'Tickers':
        tick_options = ['Edit symbol',
                        'Delete symbol',
                        'Back']
        
        print("Which ticker would you like to edit?")
        edit_pos = viewlist[si.select(viewlist)]
        if edit_pos != 'Back':
            print("What would you like to do with this position?")
            edit_sel = tick_options[si.select(tick_options)]
            for i,pos in enumerate(watch_list.position_list):
                if pos["ticker"] == edit_pos:
                    if edit_sel == 'Edit symbol':
                        tick = input("Enter stock ticker.\n>>>").upper()
                        pos["ticker"] = tick
                        # There will need to be logic here to merge two identical
                        # symbols.
                        
                    elif edit_sel == 'Delete symbol':
                        watch_list.position_list.pop(i)
                    elif edit_sel == 'Back':
                        pass
    elif edit_sel == 'Back':
        return()
    watch_list.calc_cost_basis()
    
                                
def last_transaction_indicator(watch_list, ind_dict):
    indicator = False
    score = 0
    today = dt.date.today()

    for index, position in enumerate(watch_list.position_list):
        # The next few lines print progress indication
        print("\033[1A\033[K", end='')
        # \033[K = Erase to the end of line
        # \033[1A = moves the cursor up 1 line.
        print("{}/{}".format(index,len(watch_list.position_list),end=''))
        
        indicator = False
        score = 0
        try:
            #df = get_quoteDF(position["ticker"],position,today)
            get_quoteDF(position["ticker"],position,today)
            last_close = position["last price"]

            last_t = position["transactions"][-1]

            # test for indicator
            if last_t['b/s'].lower() == 'b':
                # Note that this logic assumes a $4.95 commission and $0 fee.
                if (float(last_t['price'])
                    +(4.95/last_t['shares']) < float(last_close)):
                    
                    indicator = True
                    score = (last_close - last_t['price']) * last_t['shares']
                    direction = last_t['b/s']
                else:
                    direction = 'N/A'
   
            elif last_t['b/s'].lower() == 's':
                # Note that this logic assumes a $4.95 commission and $0 fee.
                if (float(last_t['price']) > float(last_close)
                    +(4.95/last_t['shares'])):
                    
                    indicator = True
                    score = (last_t['price'] - last_close) * last_t['shares']
                    direction = last_t['b/s']
                else:
                    direction = 'N/A'
            if direction.lower() == 'b':
                direction = 'SELL'
            elif direction.lower() == 's':
                direction = 'BUY'
            else:
                pass
                
        except:
            print("Indicator failed.")
        if indicator:
            ind_dict["Last Transaction"].append \
                           ({"Ticker":position['ticker'],
                             "Score":score,
                             "Direction":direction.upper()})
        else:
            pass

    print("\033[1A\033[K", end='')
    print("\033[1A\033[K", end='')
    return(watch_list, ind_dict)

def over_exposure_indicator(watch_list, ind_dict):
    indicator = False
    score = 0
    direction = 's'
    
    for index,position in enumerate(watch_list.position_list):
        # The next few lines print progress indication
        print("\033[1A\033[K", end='')
        # \033[K = Erase to the end of line
        # \033[1A = moves the cursor up 1 line.
        print("{}/{}".format(index,len(watch_list.position_list),end=''))

        pos_exp = (position["current shares"] * position["last price"])\
                  /watch_list.meta_data["portfolio value"]
        score = watch_list.meta_data["exposure target"] - pos_exp
        if score > 0:
            direction = 'BUY'
        elif score < 0:
            direction = 'SELL'
        else:
            direction = 'N/A'
        ind_dict["Over-exposure"].append \
                       ({"Ticker":position['ticker'],
                         "Score":score,
                         "Direction":direction.upper()})
        
    print("\033[1A\033[K", end='')
    print("\033[1A\033[K", end='')
    return(watch_list, ind_dict)

def div_yield_indicator(watch_list, ind_dict):
    indicator = False
    score = 0
    direction = 'b'
    today = dt.date.today()
    last_year = dt.date(today.year-1,1,1)

    for index,position in enumerate(watch_list.position_list):
        # The next few lines print progress indication
        print("\033[1A\033[K", end='')
        # \033[K = Erase to the end of line
        # \033[1A = moves the cursor up 1 line.
        print("{}/{}".format(index,len(watch_list.position_list),end=''))
    
        try:
            last_close = position["last price"]

            dividend = get_last_dividend(position)

            score = (dividend/last_close)*4 # assumes quarterly dividend.
            # Score is compared to the dividend target.
            score = score - watch_list.meta_data["dividend target"]
            if score > 0:
                direction = 'BUY'
            elif score < 0:
                direction = 'SELL'
            else:
                direction = 'N/A'
            ind_dict["High Dividend Yield"].append \
                           ({"Ticker":position['ticker'],
                             "Score":score,
                             "Direction":direction.upper()})
        except KeyError:
            print("No dividend fetch date for {}\n".format(position["ticker"]))
            score = 0 - watch_list.meta_data["dividend target"]
            direction = 'SELL'
            ind_dict["High Dividend Yield"].append \
                           ({"Ticker":position['ticker'],
                             "Score":score,
                             "Direction":direction.upper()})
            continue
        except TypeError:
            print("No dividends for this position")
            continue
        except:
            #pass
            raise

    print("\033[1A\033[K", end='')
    print("\033[1A\033[K", end='')
    return(watch_list, ind_dict)

def parse_date(date):
    year,month,day = [int(x) for x in date.split('-')]
    d = dt.date(year,month,day)
    return(d)

def unpack_date(date):
    year=date.year
    month=date.month
    day=date.day
    return(year,month,day)

def get_dividends(watch_list, force_all=False):
    '''This function gets a list of historical dividends for the given symbol,
    determines how many shares were held at each dividend date and adds a
    dividend transaction for each one to the position data. This function
    need only be run for dates after the most recent dividend transaction.
    force_all will find dividends for positions for which no shares are
    currently held.'''
    for pos in watch_list.position_list:
        div_exists = False
        n = 0
        if len(pos['dividends']) == 0:
            print("No dividends have been recorded for {}."\
                  .format(pos['ticker']))
            # if no dividends have been recorded, find the earliest dated
            # transaction.
            date = parse_date(pos['transactions'][0]['date'])
        else:
            div_exists = True
            latest = parse_date(pos['transactions'][0]['date'])
            for d in pos['dividends']:
                date = parse_date(d['date'])
                test = int((date-latest).days)
                if test > 0:
                    latest = date
            latest_str = unpack_date(latest)
            print("{}: Latest recorded dividend was {}"\
                    .format(pos['ticker'],latest_str))
            date = latest

        if pos['current shares'] > 0 or force_all:
            try:
                div_df=get_divDF(pos['ticker'],pos,date)
                for stamp in div_df.index:
                    year,month,day = unpack_date(stamp)

                    date_str = str(year)+'-'+str(month)+'-'+str(day)
                    d = dt.date(year,month,day)
                    delta = int((date - d).days)
                    if delta < 0 or not div_exists:
                        print("processing dividend.")
                        n+=1
                        shares = watch_list.shares_at_date(pos['ticker'],d)
                        dividend = float(div_df.loc[stamp]['value'])
                        
                        watch_list.enter_dividend(pos['ticker'],
                                                  date_str, dividend, shares)
                    else:
                        print("{}: dividends are up to date.".format(pos['ticker']))
            except AttributeError:
                print("No recent dividends")
            except TypeError:
                print("No dividends for this position")
        else:
            pass
        print("processed {} dividends.".format(n))

def get_last_dividend(position):
    ticker=position['ticker']
    source = "yahoo-dividends"
    today = dt.date.today()
    last_year = dt.date(today.year-1,1,1)
    delta = int((today - parse_date(position["last yield date"])).days)
    if delta == 0:
        #print("Already fetched dividend yield today.\n")
        dividend = position["last dividend"]
    else:
        div_df=get_divDF(ticker,position,last_year)
        dividend = div_df['value'][0]

    return(dividend)

def get_divDF(ticker,position,date):
    source = "yahoo-dividends"
    today = dt.date.today()
    try:
        div_df = web.DataReader(ticker,source,date)
        dividend = div_df['value'][0]
        position["last dividend"] = dividend # last dividend in dollars
        year,month,day = unpack_date(today)
        position["last yield date"] = \
                       str(year)+'-'+str(month)+'-'+str(day)
        # Preceding line is the last date on which the yield was fetched.
        return(div_df)
    except IndexError:
        print("No dividends for",position["ticker"],'\n')
        return(None)
    except Exception as ex:
        print(ex)
        print("No response from yahoo-finance.")
        return(None)
    
def timeout_timer():
    time.sleep(15)
    return(True)

def get_quoteDF(ticker, position, date, force=False):
    source = "yahoo"
    today = dt.date.today()
    delta = int((today - parse_date(position["last price date"])).days)
    if (delta == 0 and not force):
        #print("Already priced today\n")
        last_close = position["last price"]
        return(last_close)
    else:
        try:
            df = web.DataReader(ticker,source,date)
            last_close = df["Close"][0]
            position["last price"] = last_close
            year,month,day = unpack_date(today)

            position["last price date"] = \
                           str(year)+'-'+str(month)+'-'+str(day)
            return(last_close)
        except:
            print("No response from yahoo-finance")
            return(None)
        
watch_list = positions()

#style.use("fivethirtyeight")

print('\033[2J') # Clear the terminal
watch_list.load_positions()
watch_list.calc_cost_basis()
watch_list.sort_open_positions()
watch_list.calc_portfolio_value()
watch_list.calc_average_yield()
today = dt.date.today()

while(True):
    try:
        selections = ['Order',
                      'View',
                      'Indicators',
                      'Edit',
                      'Other',
                      'Save',
                      'Quit']
        selection = selections[si.select(selections)]
        if selection == 'Order':
            order(watch_list)
            
        elif selection == 'View':
            print("\n",end='')# Add whitespace between this and previous menu.
            viewlist = ["Portfolio"]+watch_list.list_positions()
            viewlist.append('Back')
            view_pos = viewlist[si.select(viewlist)]
            if view_pos == "Portfolio":
                for pos in watch_list.position_list:
                    if pos["current shares"] != 0:
                        pos_value = pos["last price"] * pos["current shares"]
                        print("{:<6} Shares: {:<5} @ ${:<7.2f} = Value: ${:<7.2f}"\
                              .format(pos["ticker"], pos["current shares"],
                                      pos["last price"], pos_value))
                watch_list.calc_portfolio_value()
                print("Total value: ${:<7.2f}".format\
                      (watch_list.meta_data["portfolio value"]))
                print("Average dividend yield: {:<7.2f}%\n".format\
                      (watch_list.meta_data["average yield"]*100))
            elif view_pos == 'Back':
                print("\n",end='')
                pass
            else:
                for pos in watch_list.position_list:
                    if pos["ticker"] == view_pos:
                        view(pos)
                    else:
                        pass
                
        elif selection == 'Indicators':
            ind_dict = {"Last Transaction":[], # Looks for opportunities to reverse the last transaction recorded
                        "Matched Transactions":[], # Looks for opportunities to improve cost-basis
                        "High Dividend Yield":[], # Looks for high dividend yields with respect to a specified target
                        "Portfolio Yield":[], # Looks for opportunities to increase the average dividend yield of the portfolio
                        "Recent Passed Dividend":[], # Looks for opportunities in response to recent or upcoming ex-dates
                        "Over-exposure":[]} # Looks for opportunities to improve exposure with respect to a specified target
                
            print("\nWorking on \"Last Transaction\" indicator.\n")
            watch_list, ind_dict = last_transaction_indicator(watch_list,
                                                              ind_dict)
            print("\033[1A\033[K", end='')    
            print("Done checking.\n")

            ind_dict["Last Transaction"].sort(key=lambda x: x["Score"],
                                              reverse=True)
            for i,indicator in enumerate(ind_dict["Last Transaction"]):
                if i > 9:
                    break
                else:
                    print("{:<6} Score: ${:<7.2f} Advise: {}".format\
                          (indicator["Ticker"],
                           indicator["Score"],
                           indicator["Direction"].upper()))

            print("\nWorking on \"Over-exposure\" indicator.\n")
            watch_list, ind_dict = over_exposure_indicator(watch_list,
                                                           ind_dict)
            ind_dict["Over-exposure"].sort(key=lambda x: abs(x["Score"]),
                                           reverse=True)
            print("Exposure target: {:<7.2f}% (Position value: ${:<7.2f})".format\
                  (watch_list.meta_data["exposure target"]*100,
                   watch_list.meta_data["portfolio value"]*watch_list.meta_data["exposure target"]))
            for i,indicator in enumerate(ind_dict["Over-exposure"]):
                if i > 9:
                    break
                else:
                    print("{:<6} Score: {:<7.2f}% Advise: {}".format\
                          (indicator["Ticker"],
                           indicator["Score"]*100,
                           indicator["Direction"].upper()))
            
            print("\nWorking on \"Dividend Yield\" indicator.\n")
            watch_list, ind_dict = div_yield_indicator(watch_list,ind_dict)
            
            ind_dict["High Dividend Yield"].sort(key=lambda x: abs(x["Score"]),
                                                 reverse=True)
            print("Dividend target: {:<7.2f}%".format(watch_list.meta_data["dividend target"]*100))
            for i,indicator in enumerate(ind_dict["High Dividend Yield"]):
                if i > 9:
                    break
                else:
                    print("{:<6} Score: {:<7.2f}% Advise: {}".format\
                          (indicator["Ticker"],
                           indicator["Score"]*100,
                           indicator["Direction"].upper()))
            print("\n",end='')
            
            for indicator in ind_dict["Recent Passed Dividend"]:
                pass
        elif selection == 'Edit':
            edit(watch_list)

        elif selection == 'Other':
            print('\n',end='')
            selections = ['Get all dividends',
                          'Get dividends for current positions',
                          'Edit target exposure',
                          'Edit dividend target',
                          'Clear console']
            selection = selections[si.select(selections)]
            if selection == 'Get all dividends':
                get_dividends(watch_list, force_all=True)

            elif selection == 'Get dividends for current positions':
                get_dividends(watch_list)

            elif selection == 'Edit target exposure':
                print("Current target: {:<7.2f}%".format\
                      (watch_list.meta_data["exposure target"]*100))
                new_target = si.get_real_number("Enter new target (0-100).\n>>>",
                                               lower=0, upper=100)
                watch_list.meta_data["exposure target"] = new_target/100
                print("New target: {:<7.2f}%".format\
                      (watch_list.meta_data["exposure target"]*100))

            elif selection == 'Edit dividend target':
                print("Current target: {:<7.2f}%".format\
                      (watch_list.meta_data["dividend target"]*100))
                new_target = si.get_real_number("Enter new target (0-100).\n>>>",
                                               lower=0, upper=100)
                watch_list.meta_data["dividend target"] = new_target/100
                print("New target: {:<7.2f}%".format\
                      (watch_list.meta_data["dividend target"]*100))
                
            elif selection == 'Clear console':
                print('\033[2J')
                # console command to clear console and return to (0,0)

        elif selection == 'Save':
            watch_list.save_positions()
            print("Saving...\n")
            
        elif selection == 'Quit':
            print("Save changes?")
            yn = ['Yes','No']
            sav = yn[si.select(yn)]
            if sav == 'Yes':
                watch_list.save_positions()
            else:
                pass
            break
        
    except:
        print("Unexpected error:",sys.exc_info())
##        time.sleep(60)
        continue
##        raise
