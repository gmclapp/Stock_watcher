import tkinter as tk
from tkinter import ttk
import json
from stock_watcher import *
import datetime as dt

class GUI:
    def __init__(self,master,version,mod_date):
        self.version = version
        self.mod_date = mod_date
        self.master = master
        self.get_config()

        self.watch_list = positions()

        self.watch_list.load_positions()
        self.watch_list.calc_cost_basis()
        self.watch_list.sort_open_positions()
        self.watch_list.calc_portfolio_value()
        self.watch_list.calc_average_yield()

        for pos in self.watch_list.position_list:
            if pos["ticker"] == self.current_ticker.get():
                self.current_pos_data = pos
                
        self.transactions = tk.StringVar()
        self.dividends = tk.StringVar()
        self.last_price = tk.DoubleVar()
        self.current_shares = tk.IntVar()
        self.cost_basis = tk.DoubleVar()
        self.avg_buy = tk.DoubleVar()
        self.avg_sell = tk.DoubleVar()
        self.watching = tk.BooleanVar()
        
        self.master.geometry("400x525")
        self.master.title("Stockwatcher The Empire Strikes Back")

        self.ticker_frame()
        self.transaction_frame()
        self.dividend_frame()
        self.action_frame()

        self.tick_frame.grid(column=0,row=0,padx=2,pady=2,sticky='W')
        self.trans_frame.grid(column=0,row=1,padx=2,pady=2,sticky='W')
        self.div_frame.grid(column=0,row=2,padx=2,pady=2,sticky='W')
        self.act_frame.grid(column=0,row=3,padx=2,pady=2,sticky='W')

        # Create a menubar
        self.menubar = tk.Menu(self.master)

        # Create the file menu
        self.filemenu = tk.Menu(self.menubar,tearoff=0)
        self.filemenu.add_command(label="Save",command=self.save)
        
        # Create the help menu
        self.helpmenu = tk.Menu(self.menubar,tearoff=0)
        self.helpmenu.add_command(label="About",command=self.open_about_popup)

        # Add cascading menus to the menubar
        self.menubar.add_cascade(label="File",menu=self.filemenu)
        self.menubar.add_cascade(label="Help",menu=self.helpmenu)
        self.master.config(menu=self.menubar)

    def ticker_frame(self):
        self.tick_frame = tk.LabelFrame(self.master,
                                        text="Ticker")

        # Create elements
        self.ticker_label = ttk.Label(self.tick_frame,
                                      text="Symbol")
        self.ticker = ttk.Combobox(self.tick_frame,
                                   textvariable=self.current_ticker)
        self.ticker['values'] = self.watch_list.list_positions()
        self.ticker.bind('<<ComboboxSelected>>',self.ticker_changed)

        self.last_price_label = ttk.Label(self.tick_frame,
                                          text="Last price: ")
        self.lp = ttk.Label(self.tick_frame,
                            textvariable=self.last_price)

        # Place elements
        self.ticker_label.grid(column=0,row=0,padx=2,pady=2)
        self.ticker.grid(column=1,row=0,padx=2,pady=2)
        self.last_price_label.grid(column=2,row=0,padx=2,pady=2)
        self.lp.grid(column=3,row=0,padx=2,pady=2,sticky='e')
        
    def transaction_frame(self):
        self.trans_frame = tk.LabelFrame(self.master,
                                         text="Transactions")
        self.transaction_labels = ttk.Label(self.trans_frame,
                                            text="Date\t\t      B/S\t        Shares     Price")

        # Create elements
        self.trans_list=tk.Listbox(self.trans_frame,
                                   listvariable=self.transactions,
                                   height=6,
                                   width=36,
                                   font="Courier",
                                   selectmode='extended')
        self.update_listboxes()
        # Place elements
        self.transaction_labels.grid(column=0,row=0,padx=2,pady=2,sticky='w')
        self.trans_list.grid(column=0,row=1,padx=2,pady=2,sticky='w')
        
    def dividend_frame(self):
        self.div_frame = tk.LabelFrame(self.master,
                                       text="Dividends")

        # Create elements
        self.dividend_labels = ttk.Label(self.div_frame,
                                         text="Date\t\t\tShares\t     Amount\t         Total")
        
        self.divs_list=tk.Listbox(self.div_frame,
                                  listvariable=self.dividends,
                                  height=6,
                                  width=36,
                                  font="Courier",
                                  selectmode='extended')
        self.update_listboxes()
        
        # Place elements
        self.dividend_labels.grid(row=0,column=0,padx=2,pady=2,sticky='w')
        self.divs_list.grid(row=1,column=0,padx=2,pady=2,sticky='w')
        
    def action_frame(self):
        self.act_frame = tk.LabelFrame(self.master,
                                       text="Actions")

        # Create elements
        self.current_shares_label = ttk.Label(self.act_frame,
                                              text="Current Shares: ")
        self.cost_basis_label = ttk.Label(self.act_frame,
                                          text="Cost Basis: ")
        self.avg_buy_label = ttk.Label(self.act_frame,
                                       text="Average Buy: ")
        self.avg_sell_label = ttk.Label(self.act_frame,
                                        text="Average Sell: ")
        self.watching_label = ttk.Label(self.act_frame,
                                        text="Watching?")

        self.cs = ttk.Label(self.act_frame,
                           textvariable=self.current_shares)
        self.cb = ttk.Label(self.act_frame,
                            textvariable=self.cost_basis)
        self.avgb = ttk.Label(self.act_frame,
                              textvariable=self.avg_buy)
        self.avgs = ttk.Label(self.act_frame,
                              textvariable=self.avg_sell)
        self.watch = ttk.Label(self.act_frame,
                               textvariable=self.watching)

        self.trade_pb = ttk.Button(self.act_frame,text="Trade")
        self.edit_pb = ttk.Button(self.act_frame,text="Edit")
        self.other_pb = ttk.Button(self.act_frame,text="Other")
        self.indicators_pb = ttk.Button(self.act_frame,text="Indicators")

        # Place elements
        self.current_shares_label.grid(column=0,row=0,padx=2,pady=2,sticky='w')
        self.cost_basis_label.grid(column=0,row=1,padx=2,pady=2,sticky='w')
        self.avg_buy_label.grid(column=0,row=2,padx=2,pady=2,sticky='w')
        self.avg_sell_label.grid(column=0,row=3,padx=2,pady=2,sticky='w')
        self.watching_label.grid(column=0,row=4,padx=2,pady=2,sticky='w')

        self.cs.grid(column=1,row=0,padx=2,pady=2,sticky='e')
        self.cb.grid(column=1,row=1,padx=2,pady=2,sticky='e')
        self.avgb.grid(column=1,row=2,padx=2,pady=2,sticky='e')
        self.avgs.grid(column=1,row=3,padx=2,pady=2,sticky='e')
        self.watch.grid(column=1,row=4,padx=2,pady=2,sticky='e')
        self.update_listboxes()

        self.trade_pb.grid(column=2,row=0)
        self.edit_pb.grid(column=2,row=1)
        self.other_pb.grid(column=2,row=2)
        self.indicators_pb.grid(column=2,row=3)
        
    def save(self):
        pass
    def open_about_popup(self):
        child = tk.Toplevel(self.master)
        child.geometry("360x60")
        child.title("About")
        child.grid_columnconfigure(0,weight=1)
        
        version_txt = "Version: {}".format(self.version)
        versionLabel = ttk.Label(child,text=version_txt)
        authorLabel = ttk.Label(child,text="Glenn Clapp")
        date_txt = "Created: 20-June-2022, Modified: {}".format(self.mod_date)
        dateLabel = ttk.Label(child,text=date_txt)

        authorLabel.grid(row=0,column=0)
        versionLabel.grid(row=1,column=0)
        dateLabel.grid(row=2,column=0)

    def trade_popup(self):
        child = tk.Toplevel(self.master)
        child.geometry("360x60")
        child.title("Trade")
        child.grid_columnconfigure(0,weight=1)

        # Create widgets
        
        # Place widgets

    def ticker_changed(self,event=None):
        self.current_ticker.set(self.ticker.get())
        for pos in self.watch_list.position_list:
            if pos["ticker"] == self.current_ticker.get():
                self.current_pos_data = pos
                
        df = get_quoteDF(self.current_ticker,
                         self.current_pos_data,
                         dt.date.today(),
                         force=True)
        
        self.update_listboxes()
        
        print("Changed symbol to: {}".format(self.current_ticker.get()))

    def update_listboxes(self):
        # Update transactions listbox
        tran = []
        div = []
        
        self.last_price.set(self.current_pos_data["last price"])
        self.current_shares.set(self.current_pos_data["current shares"])
        self.cost_basis.set(self.current_pos_data["cost basis"])
        self.avg_buy.set(self.current_pos_data["avg buy"])
        self.avg_sell.set(self.current_pos_data["avg sell"])
        self.watching.set(self.current_pos_data["track"])
        
        for t in self.current_pos_data["transactions"]:
            tran.append("{:11} {}  {:5}  ${}".format(t['date'],
                                                     t['b/s'].upper(),
                                                     t['shares'],
                                                     t['price']))
        for d in self.current_pos_data["dividends"]:
            div.append("{:11} {:5} x ${:.2f} = ${:.2f}".format(d['date'],
                                                     d['shares'],
                                                     d['amount'],
                                                     d['total']))
                                        
                    
        self.transactions.set(tran)
        self.dividends.set(div)
        try:
            self.trans_list.configure()
            self.divs_list.configure()
            self.cs.configure()
            self.cb.configure()
            self.avgb.configure()
            self.avgs.configure()
            self.watch.configure()
            self.lp.configure()
        except AttributeError:
            pass

        

    def get_config(self):
        with open("config.txt","r") as f:
            self.config = json.load(f)

        self.current_ticker = tk.StringVar(value=self.config["current ticker"])

    def save_config(self):
        self.config["current ticker"] = self.current_ticker.get()

        with open("config.txt","w") as f:
            json.dump(self.config,f,indent=4)
            
if __name__ == '__main__':

    __version__ = "1.0.0"
    last_modified = "22-June-2022"

    root = tk.Tk()
    try:
        f = open("config.txt","r")
        f.close()
    except FileNotFoundError:
        with open("config.txt","w") as f:
            # Default config
            defaultConfig = {"current ticker":"STX"}
            json.dump(defaultConfig,f,indent=4)
            
    app = GUI(root,__version__,last_modified)
    root.mainloop()
    root.destroy()
