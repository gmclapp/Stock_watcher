import tkinter as tk
from tkinter import ttk
import json
from stock_watcher import *

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
    
        self.master.geometry("610x290")
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

        # Place elements
        self.ticker_label.grid(column=0,row=0,padx=2,pady=2)
        self.ticker.grid(column=1,row=0,padx=2,pady=2)
        
    def transaction_frame(self):
        self.trans_frame = tk.LabelFrame(self.master,
                                         text="Transactions")
        self.transaction_labels = ttk.Label(self.trans_frame,
                                            text="Date                 B/S  Shares Price")

        
        self.transactions = tk.StringVar()
        # Create elements
        self.trans_list=tk.Listbox(self.trans_frame,
                                   listvariable=self.transactions,
                                   height=6,
                                   width=36,
                                   selectmode='browse')
        self.update_listboxes()
        # Place elements
        self.transaction_labels.grid(column=0,row=0,padx=2,pady=2,sticky='w')
        self.trans_list.grid(column=0,row=1,padx=2,pady=2,sticky='w')

    def update_listboxes(self):
        self.tran = []
        for pos in self.watch_list.position_list:
            if pos["ticker"] == self.current_ticker.get():
                for t in pos["transactions"]:
                    self.tran.append("{:12}     {}       {}       ${}".format(t['date'],
                                                                                      t['b/s'].upper(),
                                                                                      t['shares'],
                                                                                      t['price']))
                                        
                    
        self.transactions.set(self.tran)
        self.trans_list.configure()
        
    def dividend_frame(self):
        self.div_frame = tk.LabelFrame(self.master,
                                       text="Dividends")
    def action_frame(self):
        self.act_frame = tk.LabelFrame(self.master,
                                       text="Actions")
    def save(self):
        pass
    def open_about_popup(self):
        pass

    def ticker_changed(self,event):
        self.current_ticker.set(self.ticker.get())
        self.update_listboxes()
        
        print("Changed symbol to: {}".format(self.current_ticker.get()))

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
    last_modified = "20-June-2022"

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
