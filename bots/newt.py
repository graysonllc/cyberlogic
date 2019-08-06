import os
import sys
import json
from operator import itemgetter
import re
import memcache
import codecs
import logging
import sys
import pymysql
import time
import requests
import re
import configparser
import datetime
import redis
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib'
sys.path.append(root + '/python')

import talib
import numpy as np
import ccxt  # noqa: E402
import nickbot

redis_server = redis.Redis(host='localhost', port=6379, db=0)

def price_when(symbol,secs):

	symbol=symbol.replace('/','')
	ksymbol=symbol
	ts_now = datetime.datetime.now()
	ts_now_ts=int(time.mktime(ts_now.timetuple()))	
	ts_now_human=datetime.datetime.fromtimestamp(ts_now_ts).strftime("%Y-%m-%d %H:%M:%S")

	ts_before = ts_now - datetime.timedelta(seconds=secs)
	ts_end = ts_before + datetime.timedelta(seconds=20)
	print(ts_before)

	ts_before_ts=int(time.mktime(ts_before.timetuple()))
	ts_end_ts=int(time.mktime(ts_end.timetuple()))
	tsd=datetime.datetime.fromtimestamp(ts_before_ts).strftime("%Y-%m-%d %H:%M:%S")
	print("C")
	print(tsd)	
	redis_key=str(symbol)+'HISTORY'
	print(redis_key)
	print(ts_before_ts)
	print(ts_end_ts)
	
	#redis_server.zrangebyscore(redis_key,symbol,ts_before_ts,ts_end_ts)
	ret=redis_server.zrangebyscore('BTCUSDT-HISTORY',ts_before_ts,ts_end_ts,0,1000)
	size=len(ret)
	if size>0:
		data=ret[0].decode('utf-8')
		ts,price,volume = data.split(":")

		data={}
		data['price']=float(price)
		data['volume']=float(volume)
		return(data)
	else:	
		return("ERROR")
symbol='BTC/PAX'
exchange=nickbot.get_exchange()

tickers=exchange.fetchTickers()
mc = memcache.Client(['127.0.0.1:11211'], debug=0)
#for coin in tickers:
price=float(tickers['BTC/USDT']['close'])
volume=float(tickers['BTC/USDT']['quoteVolume'])

def sell(symbol,percent,stablecoin):
	symbol=symbol.upper()
	balances=exchange.fetch_balance ()
	balance=float(format(balances['BTC']['total'],'.8f'))
	units=units=balance/100*float(percent)
	
	print("Selling: "+str(symbol)+" Units: "+str(units)+" To Stable coin: "+str(stablecoin))
	
sell('BTC','75','PAX')
sys.exit("die")
def store_prices(symbol,price,volume):
	#1Minute
	data=price_when(symbol,60)
	if data!='ERROR':
		price_1min=data['price']
		volume_1min=data['volume']
		good=int(1)
		price_percent_1min=nickbot.diff_percent(price_1min,price)
		volume_percent_1min=nickbot.diff_percent(volume_1min,volume)
	else:
		price_percent_1min=0
		volume_percent_1min=0

	#2Minute
	data=price_when(symbol,120)
	if data!='ERROR':
		price_2min=data['price']
		volume_2min=data['volume']
		good=int(1)
		price_percent_2min=nickbot.diff_percent(price_2min,price)
		volume_percent_2min=nickbot.diff_percent(volume_2min,volume)
	else:
		price_percent_2min=0
		volume_percent_2min=0	

	#3Minute
	data=price_when(symbol,180)
	if data!='ERROR':
		price_3min=data['price']
		volume_3min=data['volume']
		good=int(1)
		price_percent_3min=nickbot.diff_percent(price_3min,price)
		volume_percent_3min=nickbot.diff_percent(volume_3min,volume)
	else:
		price_percent_3min=0
		volume_percent_3min=0
	
	#5Minute
	data=price_when(symbol,300)
	if data!='ERROR':
		price_5min=data['price']
		volume_5min=data['volume']
		good=int(1)
		price_percent_5min=nickbot.diff_percent(price_5min,price)
		volume_percent_5min=nickbot.diff_percent(volume_5min,volume)
	else:
		price_percent_5min=0
		volume_percent_5min=0

	#10Minute
	data=price_when(symbol,600)
	if data!='ERROR':
		price_10min=data['price']
		volume_10min=data['volume']
		good=int(1)
		price_percent_10min=nickbot.diff_percent(price_10min,price)
		volume_percent_10min=nickbot.diff_percent(volume_10min,volume)
	else:
		price_percent_10min=0
		volume_percent_10min=0
	
	#15Minute
	data=price_when(symbol,900)
	if data!='ERROR':
		price_15min=data['price']
		volume_15min=data['volume']
		good=int(1)
		price_percent_15min=nickbot.diff_percent(price_15min,price)
		volume_percent_15min=nickbot.diff_percent(volume_15min,volume)
	else:
		price_percent_15min=0
		volume_percent_15min=0
	
	#30Minute
	data=price_when(symbol,1800)
	if data!='ERROR':
		price_30min=data['price']
		volume_30min=data['volume']
		good=int(1)
		price_percent_30min=nickbot.diff_percent(price_30min,price)
		volume_percent_30min=nickbot.diff_percent(volume_30min,volume)
	else:
		price_percent_30min=0
		volume_percent_30min=0

	#1Hour
	data=price_when(symbol,3600)
	if data!='ERROR':
		price_1hour=data['price']
		volume_1hour=data['volume']
		good=int(1)
		price_percent_1hour=nickbot.diff_percent(price_1hour,price)
		volume_percent_1hour=nickbot.diff_percent(volume_1hour,volume)
	else:
		price_percent_1hour=0
		volume_percent_1hour=0
		
	#1Hour
	data=price_when(symbol,7200)
	if data!='ERROR':
		price_2hour=data['price']
		volume_2hour=data['volume']
		good=int(1)
		price_percent_2hour=nickbot.diff_percent(price_2hour,price)
		volume_percent_2hour=nickbot.diff_percent(volume_2hour,volume)
	else:
		price_percent_2hour=0
		volume_percent_2hour=0
		price_2hour=0
		volume_2hour=0
	
	#3Hour
	data=price_when(symbol,10800)
	if data!='ERROR':
		price_3hour=data['price']
		volume_3hour=data['volume']
		good=int(1)
		price_percent_3hour=nickbot.diff_percent(price_3hour,price)
		volume_percent_3hour=nickbot.diff_percent(volume_3hour,volume)
	else:
		price_percent_3hour=0
		volume_percent_3hour=0
		price_3hour=0
		volume_3hour=0
		
	#6Hour
	data=price_when(symbol,21600)
	if data!='ERROR':
		price_6hour=data['price']
		volume_6hour=data['volume']
		good=int(1)
		price_percent_6hour=nickbot.diff_percent(price_6hour,price)
		volume_percent_6hour=nickbot.diff_percent(volume_6hour,volume)
	else:
		price_percent_6hour=0
		volume_percent_6hour=0
		price_6hour=0
		volume_6hour=0
	
	#12Hour
	data=price_when(symbol,43200)
	if data!='ERROR':
		price_12hour=data['price']
		volume_12hour=data['volume']
		good=int(1)
		price_percent_12hour=nickbot.diff_percent(price_12hour,price)
		volume_percent_12hour=nickbot.diff_percent(volume_12hour,volume)
	else:
		price_percent_12hour=0
		volume_percent_12hour=0
		price_12hour=0
		volume_12hour=0
	
	#24hour
	data=price_when(symbol,86400)
	if data!='ERROR':
		price_24hour=data['price']
		volume_24hour=data['volume']
		good=int(1)
		price_percent_24hour=nickbot.diff_percent(price_24hour,price)
		volume_percent_24hour=nickbot.diff_percent(volume_24hour,volume)
	else:
		price_percent_24hour=0
		volume_percent_24hour=0
		price_24hour=0
		volume_24hour=0
	
	prices = {
		"price-1min":str(price_1min),
		"price-percent-1min":str(price_percent_1min), 
		"volume-1min":str(volume_1min),
		"volume-percent-1min":str(volume_percent_1min),			
		"price-2min":str(price_2min),
		"price-percent-2min":str(price_percent_2min), 
		"volume-2min":str(volume_2min),
		"volume-percent-2min":str(volume_percent_2min),
		"price-3min":str(price_3min),
		"price-percent-3min":str(price_percent_3min), 
		"volume-3min":str(volume_3min),
		"volume-percent-3min":str(volume_percent_3min),
		"price-5min":str(price_5min),
		"price-percent-5min":str(price_percent_5min), 
		"volume-5min":str(volume_5min),
		"volume-percent-5min":str(volume_percent_5min),
		"price-10min":str(price_10min),
		"price-percent-10min":str(price_percent_10min), 
		"volume-10min":str(volume_10min),
		"volume-percent-10min":str(volume_percent_10min),
		"price-15min":str(price_15min),
		"price-percent-15min":str(price_percent_15min), 
		"volume-15min":str(volume_15min),
		"volume-percent-15min":str(volume_percent_15min),
		"price-30min":str(price_30min),
		"price-percent-30min":str(price_percent_30min), 
		"volume-30min":str(volume_30min),
		"volume-percent-30min":str(volume_percent_30min),
		"price-1hour":str(price_1hour),
		"price-percent-1hour":str(price_percent_1hour), 
		"volume-1hour":str(volume_1hour),
		"volume-percent-1hour":str(volume_percent_1hour),
		"price-2hour":str(price_2hour),
		"price-percent-2hour":str(price_percent_2hour), 
		"volume-2hour":str(volume_2hour),
		"volume-percent-2hour":str(volume_percent_2hour),
		"price-3hour":str(price_3hour),
		"price-percent-3hour":str(price_percent_3hour), 
		"volume-3hour":str(volume_3hour),
		"volume-percent-3hour":str(volume_percent_3hour),
		"price-6hour":str(price_6hour),
		"price-percent-6hour":str(price_percent_6hour), 
		"volume-6hour":str(volume_6hour),
		"volume-percent-6hour":str(volume_percent_6hour),
		"price-12hour":str(price_12hour),
		"price-percent-12hour":str(price_percent_12hour), 
		"volume-12hour":str(volume_12hour),
		"volume-percent-12hour":str(volume_percent_12hour),
		"price-24hour":str(price_24hour),
		"price-percent-24hour":str(price_percent_24hour), 
		"volume-24hour":str(volume_24hour),
		"volume-percent-24hour":str(volume_percent_24hour)}
	redis_key=symbol+'-STATS'
	redis_server.hmset(redis_key, prices)
print(prices)
