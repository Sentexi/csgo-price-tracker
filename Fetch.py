import numpy as np
import os
import argparse
from bs4 import BeautifulSoup
import requests
import re
import csv
from tqdm import tqdm
import time
import json
import pickle

#Some random paths to test the script
path = 'https://steamcommunity.com/market/listings/730/Sticker%20%7C%20Virtus.Pro%20%28Holo%29%20%7C%20Krakow%202017'
paths = ["https://steamcommunity.com/market/listings/730/Sticker%20%7C%20Astralis%20%28Foil%29%20%7C%20Cologne%202016",
         "https://steamcommunity.com/market/listings/730/Sticker%20%7C%20Team%20Dignitas%20%28Foil%29%20%7C%20Cologne%202016",
         "https://steamcommunity.com/market/listings/730/Sticker%20%7C%20Virtus.Pro%20%28Foil%29%20%7C%20Cologne%202016",
         "https://steamcommunity.com/market/listings/730/Sticker%20%7C%20friberg%20%7C%20Cologne%202016"]

#Get the Exchange from cached file
#Load from API if there is no cached file
def get_exchange_rate():
    #Checks if cache file exists
    if os.path.isfile('rate.p'):
        with open("rate.p","rb") as file:
            data = pickle.load(file)
        #Compares time to timestamp
        DeltaT = int(time.time()) - int(data["timestamp"])
        #Request a new value each day
        if DeltaT < 86400:
            eurusd = data["eurusd"]
        else:
            eurusd  = get_exchange_rate_from_api()
    else:
        eurusd  = get_exchange_rate_from_api()
    return eurusd

#Loads the Exchange rate from an API         
def get_exchange_rate_from_api():      
    rates = requests.get("https://api.exchangeratesapi.io/latest")
    rates = json.loads(rates.text)
    eurusd = rates["rates"]["USD"]
    Dump = {"eurusd":eurusd,"timestamp":time.time()}
    with open('rate.p', 'wb') as handle:
         pickle.dump(Dump, handle)
    print('Updating exchange rate, now: {}'.format(eurusd))
    return eurusd

#Gets the sticker price from a custom URL
def get_sticker_price(url):
    #load HTML and create soup
    request = requests.get(url)
    soup = BeautifulSoup(request.text, 'html.parser')

    #Find relevant scripts
    scripts = soup.find_all('script', attrs={'type':'text/javascript','src':False}) 
    
    #sample through scripts and regexp relevant part
    for script in scripts:
        content = script.contents
        for parts in content:
            m = re.search('price":([0-9]*),"fee":([0-9]*)',parts)
            if m == None:
                pass
            else:
                price = int(m.group(1))+int(m.group(2))
    return price

#Finds individual Sticker ID from URL    
def get_sticker_id(url):
    #load HTML and create soup
    request = requests.get(url)
    soup = BeautifulSoup(request.text, 'html.parser')

    #Find relevant scripts
    scripts = soup.find_all('script', attrs={'type':'text/javascript','src':False}) 

    #Find individual sticker ID
    for script in scripts:
        content = script.contents
        for parts in content:
            m = re.search('Market_LoadOrderSpread\( ([0-9]*)',parts)
            if m == None:
                pass
            else:
                id = int(m.group(1))
                if args.v == True:
                    print('id: {}'.format(id))
    return id

#Gets sticker price from custom URL via custom ID    
def get_sticker_price2(url):
    #Steam tends to refuse scraping if page is called to often
    try:
        id = get_sticker_id(url)
    except UnboundLocalError:
        print("to many attempts at scraping, waiting 120s")
        time.sleep(180)
        id = 0
        try:
            id = get_sticker_id(url)
        except:
            ("Second try rejected, aborting")
    #from individual sticker ID load HTML as text
    request = requests.get("https://steamcommunity.com/market/itemordershistogram?&language=english&currency=1&item_nameid={}".format(id))
    #Regex relevant part
    m = re.search(r'highest_buy_order\":\"([0-9]*)\",\"lowest_sell_order\":\"([0-9]*)',request.text)
    bid = int(m.group(1))
    ask = int(m.group(2))
    return bid,ask

#Same as get_sticker_price2 but without scraping the id first    
def get_sticker_price_from_id(id):
    #from individual sticker ID load HTML as text
    request = requests.get("https://steamcommunity.com/market/itemordershistogram?&language=english&currency=1&item_nameid={}".format(id))
    #Regex relevant part
    m = re.search(r'highest_buy_order\":\"([0-9]*)\",\"lowest_sell_order\":\"([0-9]*)',request.text)
    bid = int(m.group(1))
    ask = int(m.group(2))
    return bid,ask

#gets average price from a list of URLs
def get_average(paths):
    bids = np.zeros(len(paths))
    asks = np.zeros(len(paths))
    for i in range(len(paths)):
        bid,ask = get_sticker_price2(paths[i])
        bids[i] = bid
        asks[i] = ask
    bid = np.average(bids)
    ask = np.average(asks)
    return int(bid),int(ask)

#Gets price of investment asset from a Textfile with the format 'URL' \t 'amount'    
def get_value(Textfile):
    paths = []
    with open(Textfile, 'r') as file:
        if args.l == True:
            reader = csv.reader(file, delimiter='\t')
        if args.i == True:
            reader = csv.reader(file, delimiter=',')
        for row in reader:
            paths.append(row)
    Price = np.zeros((len(paths),2))
    for i in tqdm(range(len(paths))):
        if args.l == True:
            time.sleep(wait_time)
            bid,ask = get_sticker_price2(paths[i][0])
        if args.i == True:
            if args.v == True:
                print(paths[i][0])
            try:
                bid,ask = get_sticker_price_from_id(paths[i][0])
            except:
                print("to many attempts at price updating, waiting 180s")
                time.sleep(180)
                try:
                    bid,ask = F.get_sticker_euro_price_from_id(int(paths[i][0]))
                except:
                    ("Second try rejected, aborting")
        if args.v == True:
            print("Bid: {} \t Ask: {}".format(bid,ask))
        Price[i][0] = bid*int(paths[i][1])
        Price[i][1] = ask*int(paths[i][1])
    Price = np.sum(Price,axis=0)
    return int(Price[0]),int(Price[1])

#Formats price from US cents to Euro minus 13% tax
def format_price(price):
    price = (price/eurusd)/100
    price = round(price*0.87,2)
    return price

#Gets prices either library of IDs or List of Links and writes them to a csv    
def write_asset_to_csv(Textfile):
    bid,ask = get_value(Textfile)
    bid = format_price(bid)
    ask = format_price(ask)
    timestamp = time.asctime(  time.localtime( time.time() )  )
    Filename = os.path.splitext(Textfile)[0]
    rows = []
    if os.path.isfile('{}.csv'.format(Filename)):
        with open('{}.csv'.format(Filename),'r') as file:
             reader = csv.reader(file, delimiter=',')
             for row in reader:
                 rows.append(row)
        rows = rows[1:]
    rows.append([timestamp,bid,ask])
    if args.v == True:
        print(rows)
    if len(rows) > maxrows:
        rows = rows[-maxrows:]
        if args.v == True:
            print(rows)
    with open('{}.csv'.format(Filename),'w',newline='') as file:
        writer = csv.writer(file, delimiter=",",quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Date","Bid","Ask"])
        for i in range(len(rows)):
            writer.writerow(rows[i])

#Creates a library of IDs based on a Textfile            
def create_library(Textfile):
    paths = []
    with open(Textfile, 'r') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            paths.append(row)
    IDs = np.zeros(len(paths))
    #Efficiency for small batches
    if len(paths) < 24:
        wait_time = 1
    #Else take the long way and wait x seconds as defined per cmd line
    else:
        wait_time = args.wait
    for i in tqdm(range(len(paths))):
        time.sleep(wait_time)
        #Steam tends to refuse scraping if page is called to often
        try:
            IDs[i] = get_sticker_id(paths[i][0])
        except UnboundLocalError:
            print("to many attempts at scraping, waiting 180s")
            time.sleep(180)
            id = 0
            try:
                IDs[i] = get_sticker_id(paths[i][0])
            except:
                ("Second try rejected, aborting")   
    Filename = os.path.splitext(Textfile)[0]
    with open('{}.lib'.format(Filename),'w',newline='') as file:
        writer = csv.writer(file, delimiter=",",quoting=csv.QUOTE_MINIMAL)
        for i in range(len(IDs)):
            writer.writerow([int(IDs[i]),paths[i][1]])
            
#Grab the USD to EUR exchange rate
eurusd = get_exchange_rate()
    
if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description='Scrapes steam for sticker prices and pregenerated assets')

    parser.add_argument('--textfile', type=str,  help='Textfile from which assets are accumulated',required=False)
    parser.add_argument('-v', action='store_true', help='Verbose')
    parser.add_argument('-b', action='store_true', help='Build Library of IDs from list of paths')
    parser.add_argument('-l', action='store_true', help='Use Links to scrape for ID')
    parser.add_argument('-i', action='store_true', help='Use ID Library to get prices')
    parser.add_argument('--maxrows', type=int, default=1000000,  help='Maximum amount of rows in csv')
    parser.add_argument('--wait', type=int, default=6, help='Waiting time between requests')

    args = parser.parse_args()

    Textfile = args.textfile
    wait_time = args.wait
    maxrows = args.maxrows

    #Writes Timestamp and Bid/Ask values from a Textfile of Links
    if args.l == True:
        if args.v == True:
            print("Writing to csv from Links")
        write_asset_to_csv(Textfile)

    #Creates a library of IDs based on a Textfile of links    
    if args.b == True:
        print("Creating Library from {}".format(Textfile))
        create_library(Textfile)

    #Writes Timestamp and Bid/Ask values from a Library of IDs    
    if args.i == True:
        if args.v == True:
            print("Writing to csv from library")
        write_asset_to_csv(Textfile)        
 
'''    
print("Wert des Assets auf dem Steam Markt: {}€".format(value))
'''


'''
bid,ask = get_average(paths)
print("Bid = {} \t Ask = {}".format(bid,ask))
'''        
