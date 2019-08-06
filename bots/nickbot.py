import os
from collections import OrderedDict
import requests
import json
from operator import itemgetter
import re
import memcache
import codecs
import logging
import sys
import pymysql
import talib
import numpy as np
import ccxt
import redis
import datetime
import configparser
import subprocess
import time
import shlex
import argparse
import heapq

config = configparser.ConfigParser()
config.read('/root/akeys/b.conf')
mysql_username=config['mysql']['MYSQL_USERNAME']
mysql_password=config['mysql']['MYSQL_PASSWORD']
mysql_hostname=config['mysql']['MYSQL_HOSTNAME']
mysql_database='cmc'
telegram_id=config['binance']['TEEGRAM_ID_EMBED']

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib'
sys.path.append(root + '/python')
	
r = redis.Redis(host='localhost', port=6379, db=0)

mc = memcache.Client(['127.0.0.1:11211'], debug=0)

redis_server = redis.Redis(host='localhost', port=6379, db=0)

def broadcast_tether_trade(chatid,text):
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')
	telegram_id=config['binance']['AUTO_TETHERBOT_TELEGRAM_ID']
	token = telegram_id
	url = "https://api.telegram.org/"+ token + "/sendMessage?chat_id=" + chatid+"&text="+str(text)+"&parse_mode=HTML"
	r=requests.get(url)
	html = r.content	

def broadcast_tether(chatid,text):
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')
	telegram_id=config['binance']['TETHERBOT_TELEGRAM_ID']
	token = telegram_id
	url = "https://api.telegram.org/"+ token + "/sendMessage?chat_id=" + chatid+"&text="+str(text)+"&parse_mode=HTML"
	r=requests.get(url)
	html = r.content	

def broadcast_moon(chatid,text):
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')
	telegram_id=config['binance']['MOON_TELEGRAM_ID']
	token = telegram_id
	url = "https://api.telegram.org/"+ token + "/sendMessage?chat_id=" + chatid+"&text="+str(text)+"&parse_mode=HTML"
	r=requests.get(url)
	html = r.content	

def log_alert(symbol,price,percent,spread,sent_buys_percent,sent_sells_percent,sent_price_up_ratio,alerts,percent_15m,percent_1h,percent_3h,percent_6h,percent_12h,link):
	
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')

	mysql_username=config['mysql']['MYSQL_USERNAME']
	mysql_password=config['mysql']['MYSQL_PASSWORD']
	mysql_hostname=config['mysql']['MYSQL_HOSTNAME']
	mysql_database=config['mysql']['MYSQL_DATABASE']

	db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysql_database)
	cursor = db.cursor()
	
	sql = str("""
		INSERT INTO at_alerts(date,date_time,timestamp,symbol,price,percent,spread,sent_buys_percent,sent_sells_percent,sent_price_up_ratio,alerts,percent_15m,percent_1h,percent_3h,percent_6h,percent_12h,link) 
		VALUES (CURRENT_DATE(),NOW(),UNIX_TIMESTAMP(),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
	""")

	cursor.execute(sql,(symbol,price,percent,spread,sent_buys_percent,sent_sells_percent,sent_price_up_ratio,alerts,percent_15m,percent_1h,percent_3h,percent_6h,percent_12h,link))
	db.close()

def log_autotether_trades(symbol,price,units,percent,action,reason):
	
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')

	mysql_username=config['mysql']['MYSQL_USERNAME']
	mysql_password=config['mysql']['MYSQL_PASSWORD']
	mysql_hostname=config['mysql']['MYSQL_HOSTNAME']
	mysql_database=config['mysql']['MYSQL_DATABASE']

	db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysql_database)
	cursor = db.cursor()
	
	sql = str("""
		INSERT INTO autotether_trades(date,date_time,timestamp,symbol,price,units,percent,action,reason) 
		VALUES (CURRENT_DATE(),NOW(),UNIX_TIMESTAMP(),%s,%s,%s,%s,%s,%s)
	""")

	cursor.execute(sql,(symbol,price,units,percent,action,reason))
	db.close()

def log_autotether_stats(symbol,price,percent_1min,percent_2min,percent_3min,percent_5min,percent_10min,percent_15min,percent_30min,percent_1hour,percent_3hour,percent_6hour,percent_12hour,percent_24hour,rsi):
	
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')

	mysql_username=config['mysql']['MYSQL_USERNAME']
	mysql_password=config['mysql']['MYSQL_PASSWORD']
	mysql_hostname=config['mysql']['MYSQL_HOSTNAME']
	mysql_database=config['mysql']['MYSQL_DATABASE']

	db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysql_database)
	cursor = db.cursor()
	
	sql = str("""
		INSERT INTO autotether_stats(date,date_time,timestamp,symbol,price,percent_1min,percent_2min,percent_3min,percent_5min,percent_10min,percent_15min,percent_30min,percent_1hour,percent_3hour,percent_6hour,percent_12hour,percent_24hour,rsi) 
		VALUES (CURRENT_DATE(),NOW(),UNIX_TIMESTAMP(),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
	""")

	cursor.execute(sql,(symbol,price,percent_1min,percent_2min,percent_3min,percent_5min,percent_10min,percent_15min,percent_30min,percent_1hour,percent_3hour,percent_6hour,percent_12hour,percent_24hour,rsi))
	db.close()
	
	
def log_binance(symbol,price,percent,spread,low,high,volume,btc_price,btc_percent):
	
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')

	mysql_username=config['mysql']['MYSQL_USERNAME']
	mysql_password=config['mysql']['MYSQL_PASSWORD']
	mysql_hostname=config['mysql']['MYSQL_HOSTNAME']
	mysql_database=config['mysql']['MYSQL_DATABASE']

	db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysql_database)
	cursor = db.cursor()
	
	sql = str("""
		INSERT INTO binance_stats(date,date_time,timestamp,symbol,price,percent,spread,low,high,volume,btc_price,btc_percent) 
		VALUES (CURRENT_DATE(),NOW(),UNIX_TIMESTAMP(),%s,%s,%s,%s,%s,%s,%s,%s,%s)
	""")

	cursor.execute(sql,(symbol,price,percent,spread,low,high,volume,btc_price,btc_percent))
	db.close()

def log_order(exchange,bot_id,order_id,order_type,symbol,rsi_symbol,trade_from,trade_to,sell_price,units):
	
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')

	mysql_username=config['mysql']['MYSQL_USERNAME']
	mysql_password=config['mysql']['MYSQL_PASSWORD']
	mysql_hostname=config['mysql']['MYSQL_HOSTNAME']
	mysql_database=config['mysql']['MYSQL_DATABASE']

	order_array=fetch_last_buy_order(exchange,symbol)
	buy_price=float(order_array['price'])
	
	profit_per_unit=sell_price-buy_price
	profit=float(profit_per_unit*units)
	profit=round(profit,8)
	prices = [buy_price,sell_price]
	for a, b in zip(prices[::1], prices[1::1]):
		profit_percent=100 * (b - a) / a
		profit_percent=round(profit_percent,2)

	db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysql_database)
	cursor = db.cursor()
	
	sql = str("""
		INSERT INTO at_orders(date,date_time,timestamp,bot_id,order_id,symbol,rsi_symbol,trade_from,trade_to,units,buy_price,sell_price,profit,profit_percent) 
		VALUES (CURRENT_DATE(),NOW(),UNIX_TIMESTAMP(),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
	""")

	print(bot_id,order_id,symbol,rsi_symbol,trade_from,trade_to,units,buy_price,sell_price,profit,profit_percent)

	cursor.execute(sql,(bot_id,order_id,symbol,rsi_symbol,trade_from,trade_to,units,buy_price,sell_price,profit,profit_percent))
	db.close()
	
def get_exchange():
	
	#Read in our apikeys and accounts
	blist=r.smembers("botlist")
	rlimit=int(len(blist))*1200
	
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')
	conf=config['binance']
	
	binance_api_key=config['binance']['API_KEY']
	binance_api_secret=config['binance']['API_SECRET']
	
	exchange = ccxt.binance({
    'apiKey': binance_api_key,
    'secret': binance_api_secret,
    'enableRateLimit': True,
    'rateLimit': rlimit,
    'verbose': False,  # switch it to Fal_se if you don't want the HTTP log
	})
	return(exchange)

def fetch_prices(exchange, symbol):
	ticker = exchange.fetch_ticker(symbol.upper())
	return(ticker)


def replace_last(source_string, replace_what, replace_with):
    head, _sep, tail = source_string.rpartition(replace_what)
    return head + replace_with + tail

def diff_percent(low,high):
	low=float(low)
	high=float(high)
	if high>0 and low>0:
		prices = [low,high]
		
		for a, b in zip(prices[::1], prices[1::1]):
			pdiff=100 * (b - a) / a
			pdiff=round(pdiff,4)

		return(pdiff)
	else:
		return(0)

def get_price(exchange,symbol):
	
	symbol=symbol.upper()	
	ticker = exchange.fetch_ticker(symbol.upper())
	print(str(ticker))
	price=float(ticker['last'])
	return(price)

def price_when(symbol,secs):

	symbol=symbol.replace('/','')
	ksymbol=symbol
	ts_now = datetime.datetime.now()
	ts_now_ts=int(time.mktime(ts_now.timetuple()))	
	ts_now_human=datetime.datetime.fromtimestamp(ts_now_ts).strftime("%Y-%m-%d %H:%M:%S")

	ts_before = ts_now - datetime.timedelta(seconds=secs)
	ts_end = ts_before + datetime.timedelta(seconds=60)
	#print(ts_before)

	ts_before_ts=int(time.mktime(ts_before.timetuple()))
	ts_end_ts=int(time.mktime(ts_end.timetuple()))
	tsd=datetime.datetime.fromtimestamp(ts_before_ts).strftime("%Y-%m-%d %H:%M:%S")
	#print("C")
	#print(tsd)	
	redis_key=str(symbol)+'-HISTORY'
	#print(redis_key)
	#print(ts_before_ts)
	#print(ts_end_ts)
	
	#redis_server.zrangebyscore(redis_key,symbol,ts_before_ts,ts_end_ts)
	ret=redis_server.zrangebyscore(redis_key,ts_before_ts,ts_end_ts,0,1000)
	size=len(ret)
	if size>0:
		data=ret[0].decode('utf-8')
		ts,price,volume = data.split(":")

		data={}
		price=round(float(price),8)
		volume=round(float(volume),2)
				
		data['price']=float(price)
		data['volume']=float(volume)
		return(data)
	else:	
		return("ERROR")

def our_prices(pair,price_now,volume_now):

	redis_key=str(pair)+"-HISTORY"
	ts_now = datetime.datetime.now()
	ts_now=int(time.mktime(ts_now.timetuple()))	
	#print(ts_now)
	ts_now=str(ts_now)
	
	#print(str(volume_now))
	price_set={}
	store=str(ts_now+':'+str(price_now)+':'+str(volume_now))
	price_set[store]=ts_now
	redis_server.zadd(redis_key,price_set)
	#print("Setting: "+str(redis_key)+" -> "+str(price_set))

def get_rsi(pair,interval):
	rsi_symbol=pair
	rsi_symbol=rsi_symbol.replace('/','')
	
	arr = []
	out = []
	fin = []
	url="https://api.binance.com/api/v1/klines?symbol="+rsi_symbol+"&interval="+interval+"&limit=500"
	#print(url)
	r=requests.get(url)
	res = (r.content.strip())
	status = r.status_code
	#print("Status: "+str(status))
	rsi_status=''
	trades = json.loads(res.decode('utf-8'))

	lp=0
	for trade in trades:
		open_price=float(trade[0])
		close_price=float(trade[4])
		high_price=float(trade[2])
		low_price=float(trade[3])
		if close_price>0 and close_price!=lp:
			arr.append(close_price)	
		lp=close_price

	np_arr = np.array(arr,dtype=float)
	output=talib.RSI(np_arr,timeperiod=15)

	for chkput in output:
		if chkput>0:
			fin.append(chkput)
		
	rsi=float(fin[-1])
	rsi=round(rsi)
	return(rsi)

def store_prices(symbol,price,volume):
	#1Minute
	data=price_when(symbol,60)
	if data!='ERROR':
		price_1min=data['price']
		volume_1min=data['volume']
		good=int(1)
		price_percent_1min=diff_percent(price_1min,price)
		volume_percent_1min=diff_percent(volume_1min,volume)
	else:
		price_percent_1min=0
		volume_percent_1min=0
		price_1min=0
		volume_1min=0

	#2Minute
	data=price_when(symbol,120)
	if data!='ERROR':
		price_2min=data['price']
		volume_2min=data['volume']
		good=int(1)
		price_percent_2min=diff_percent(price_2min,price)
		volume_percent_2min=diff_percent(volume_2min,volume)
	else:
		price_percent_2min=0
		volume_percent_2min=0	
		price_2min=0
		volume_2min=0


	#3Minute
	data=price_when(symbol,180)
	if data!='ERROR':
		price_3min=data['price']
		volume_3min=data['volume']
		good=int(1)
		price_percent_3min=diff_percent(price_3min,price)
		volume_percent_3min=diff_percent(volume_3min,volume)
	else:
		price_percent_3min=0
		volume_percent_3min=0
		price_3min=0
		volume_3min=0

	
	#5Minute
	data=price_when(symbol,300)
	if data!='ERROR':
		price_5min=data['price']
		volume_5min=data['volume']
		good=int(1)
		price_percent_5min=diff_percent(price_5min,price)
		volume_percent_5min=diff_percent(volume_5min,volume)
	else:
		price_percent_5min=0
		volume_percent_5min=0
		price_5min=0
		volume_5min=0

	#10Minute
	data=price_when(symbol,600)
	if data!='ERROR':
		price_10min=data['price']
		volume_10min=data['volume']
		good=int(1)
		price_percent_10min=diff_percent(price_10min,price)
		volume_percent_10min=diff_percent(volume_10min,volume)
	else:
		price_percent_10min=0
		volume_percent_10min=0
		price_10min=0
		volume_10min=0

	#15Minute
	data=price_when(symbol,900)
	if data!='ERROR':
		price_15min=data['price']
		volume_15min=data['volume']
		good=int(1)
		price_percent_15min=diff_percent(price_15min,price)
		volume_percent_15min=diff_percent(volume_15min,volume)
	else:
		price_percent_15min=0
		volume_percent_15min=0
		price_15min=0
		volume_15min=0

	
	#30Minute
	data=price_when(symbol,1800)
	if data!='ERROR':
		price_30min=data['price']
		volume_30min=data['volume']
		good=int(1)
		price_percent_30min=diff_percent(price_30min,price)
		volume_percent_30min=diff_percent(volume_30min,volume)
	else:
		price_percent_30min=0
		volume_percent_30min=0
		price_30min=0
		volume_30min=0

	#1Hour
	price_1hour=int(0)
	volume_1hour=int(0)
	
	price_2hour=int(0)
	volume_2hour=int(0)

	price_3hour=int(0)
	volume_3hour=int(0)
		
	price_6hour=int(0)
	volume_6hour=int(0)
	
	price_12hour=int(0)
	volume_12hour=int(0)

	price_24hour=int(0)
	volume_24hour=int(0)
	
	data=price_when(symbol,3600)
	if data!='ERROR':
		price_1hour=data['price']
		volume_1hour=data['volume']
		good=int(1)
		price_percent_1hour=diff_percent(price_1hour,price)
		volume_percent_1hour=diff_percent(volume_1hour,volume)
	else:
		price_percent_1hour=0
		volume_percent_1hour=0
		price_1hour=0
		
	#1Hour
	data=price_when(symbol,7200)
	if data!='ERROR':
		price_2hour=data['price']
		volume_2hour=data['volume']
		good=int(1)
		price_percent_2hour=diff_percent(price_2hour,price)
		volume_percent_2hour=diff_percent(volume_2hour,volume)
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
		price_percent_3hour=diff_percent(price_3hour,price)
		volume_percent_3hour=diff_percent(volume_3hour,volume)
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
		price_percent_6hour=diff_percent(price_6hour,price)
		volume_percent_6hour=diff_percent(volume_6hour,volume)
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
		price_percent_12hour=diff_percent(price_12hour,price)
		volume_percent_12hour=diff_percent(volume_12hour,volume)
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
		price_percent_24hour=diff_percent(price_24hour,price)
		volume_percent_24hour=diff_percent(volume_24hour,volume)
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
	return(prices)
	
def v24_usd_alerts_cached(exchange,symbol,v24):

	symbol=symbol.upper()


	if symbol.endswith('BTC'):
		key=str(symbol)+'-BTC-USDT-PRICE'
		if r.get(key):
			trade_to_price=r.get(key)
		else:
			tickers=fetch_prices(exchange,'BTC/USDT')
			trade_to_price=float(tickers['close'])
			r.setex(key,120,trade_to_price)
	elif symbol.endswith('ETH'):
		key=str(symbol)+'-ETH-USDT-PRICE'
		if r.get(key):
			trade_to_price=r.get(key)
		else:
			tickers=fetch_prices(exchange,'ETH/USDT')
			trade_to_price=float(tickers['close'])
			r.setex(key,120,trade_to_price)
	elif symbol.endswith('BNB'):
		key=str(symbol)+'-BNB-USDT-PRICE'
		if r.get(key):
			trade_to_price=r.get(key)
		else:
			tickers=fetch_prices(exchange,'BNB/USDT')
			trade_to_price=float(tickers['close'])
			r.setex(key,120,trade_to_price)
	else:
		trade_to_price=1
	trade_to_price=float(trade_to_price)
	p24=v24*trade_to_price
	p24=float(p24)
	
	return(p24)

def volume24h_in_usd(symbol):

	exchange=get_exchange()

	symbol=symbol.upper()
	ticker_symbol=symbol
	tickers=fetch_prices(exchange,ticker_symbol)

	v24=tickers['quoteVolume']

	if symbol.endswith('BTC'):
		tickers=fetch_prices(exchange,'BTC/USDT')
		trade_to_price=float(tickers['close'])
	elif symbol.endswith('ETH'):
		tickers=fetch_prices(exchange,'ETH/USDT')
		trade_to_price=float(tickers['close'])
	elif symbol.endswith('BNB'):
		tickers=fetch_prices(exchange,'BNB/USDT')
		trade_to_price=float(tickers['close'])
	else:
		trade_to_price=1

	p24=v24*trade_to_price
	p24=float(p24)
	
	return(p24)
	
def price_usd(symbol):

	symbol=symbol.upper()
	ticker_symbol=symbol

	if symbol.endswith('BTC'):
		ticker_symbol = replace_last(ticker_symbol, '/BTC', '')
		trade_to='BTC'
	elif symbol.endswith('USDT'):
		ticker_symbol = replace_last(ticker_symbol, '/USDT', '')
		trade_to='USDT'
	elif symbol.endswith('BNB'):
		ticker_symbol = replace_last(ticker_symbol, '/BNB', '')
		trade_to='BNB'
	elif symbol.endswith('TUSD'):
		ticker_symbol = replace_last(ticker_symbol, '/TUSD', '')
		trade_to='TUSD'
	elif symbol.endswith('USD'):
		ticker_symbol = replace_last(ticker_symbol, '/USD', '')
		trade_to='USD'
	elif symbol.endswith('USDC'):
		ticker_symbol = replace_last(ticker_symbol, '/USDC', '')
		trade_to='USDC'
	elif symbol.endswith('PAX'):
		ticker_symbol = replace_last(ticker_symbol, '/PAX', '')
		trade_to='PAX'
	elif symbol.endswith('USDS'):
		ticker_symbol = replace_last(ticker_symbol, '/USDS', '')
		trade_to='USDS'
	elif symbol.endswith('ETH'):
		ticker_symbol = replace_last(ticker_symbol, '/ETH', '')
		trade_to='ETH'
	
	trade_from=ticker_symbol
	exchange=get_exchange()
	
	pair_price=0
	budget=1
	if trade_to=='ETH':
		tickers=fetch_prices(exchange,'ETH/USDT')
		trade_to_price=float(tickers['close'])
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])
		fraction_to_budget=budget/trade_to_price
		units=fraction_to_budget/pair_price
		pair_price=budget/units
	elif trade_to=='BTC':
		tickers=fetch_prices(exchange,'BTC/USDT')
		trade_to_price=float(tickers['close'])
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])
		fraction_to_budget=budget/trade_to_price
		units=fraction_to_budget/pair_price
		pair_price=budget/units
	elif trade_to=='BNB':
		tickers=fetch_prices(exchange,'BNB/USDT')
		trade_to_price=float(tickers['close'])
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])
		fraction_to_budget=budget/trade_to_price
		units=fraction_to_budget/pair_price
		pair_price=budget/units
	else:
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])

	pair_price=float(pair_price)
	return(pair_price)

def wall_magic(symbol,last_stoploss):
	
	exchange=get_exchange()
	book=fetch_order_book(exchange,symbol,'bids','1000')
	#New JEdimaster shit lets have at least $100k above us in buy order book set our dynamic stoploss @ that position in the book
	
	vol24=float(volume24h_in_usd(symbol))
	if vol24>100000000:
		vlimit=vol24/100*0.2
	elif vol24>50000000 and vol24<100000000:
		vlimit=vol24/100*0.5
	elif vol24>25000000 and vol24<50000000:
		vlimit=vol24/100*1
	else:
		vlimit=vol24/100*1
	print(symbol)
		
	sl_pos=wall_pos(symbol,vlimit)
	
	print("LAST STOPLOSS: "+str(last_stoploss))
	print("STOPLOSS POSITION: "+str(sl_pos))
	
	rkt=symbol+"TTT"
	r.setex(rkt,15,sl_pos)
	
	redis_key="bconfig-"+symbol
	wall_stoploss=float(book[sl_pos][0])
	if not wall_stoploss:
		sl_pos=wall_pos(symbol,100000)		
		wall_stoploss=float(book[sl_pos][0])
	print("WSL: "+str(wall_stoploss))
	print("VOLUME V24: "+str(vol24))
	print("VLIMIT: "+str(vlimit))
	
	r.hset(redis_key, 'wall_stoploss',wall_stoploss)
	
	return(wall_stoploss)


def wall_pos(symbol,usd_limit):
	
	#Fucking jedi master shit, lets make sure that theres usd_limit above us in the buy book @ set our dynamic stoploss at that
	usd_limit=float(usd_limit)
	pusd=float(price_usd(symbol))
	exchange=get_exchange()
	message=""
	buy_book=exchange.fetch_order_book(symbol,1000)
	pos=int(0)
	book=buy_book['bids']
	tv_usd=0
	got=0
	print("USD LIMIT: "+str(usd_limit))
	for line in book:
		k=line[0]
		v=line[1]
		v_usd=round(float(v)*pusd,2)
		tv_usd=round(float(tv_usd+v_usd),2)
		#print("DEBUG K: "+str(k))
		#print("DEBUG TVUSD: "+str(tv_usd))
		#print("DEBUG USDLIMIT: "+str(usd_limit))
		#if k>=float(stoploss):
		#message=message+"BOOK POS: "+str(pos)+"\tPRICE: "+str(k)+"\tVOLUME: "+str(v)+"\tVOLUME USD: "+str(v_usd)+"\tTOTAL VOLUME USD: "+str(tv_usd)+"\n"
		#print(message)
		if tv_usd>=usd_limit:
			print(message)
			return(pos)
			got=1	
		
		if got!=1:
			pos+=1
			
	return(pos)		
	print(message)
	
def broadcast(chatid,text):
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')
	telegram_id=config['binance']['TELEGRAM_ID']
	token = telegram_id
	url = "https://api.telegram.org/"+ token + "/sendMessage?chat_id=" + chatid+"&text="+str(text)+"&parse_mode=HTML"
	r=requests.get(url)
	html = r.content
	print(html)

def work_units(symbol,budget):

	symbol=symbol.upper()
	ticker_symbol=symbol

	if symbol.endswith('BTC'):
		ticker_symbol = replace_last(ticker_symbol, '/BTC', '')
		trade_to='BTC'
	elif symbol.endswith('USDT'):
		ticker_symbol = replace_last(ticker_symbol, '/USDT', '')
		trade_to='USDT'
	elif symbol.endswith('BNB'):
		ticker_symbol = replace_last(ticker_symbol, '/BNB', '')
		trade_to='BNB'
	elif symbol.endswith('TUSD'):
		ticker_symbol = replace_last(ticker_symbol, '/TUSD', '')
		trade_to='TUSD'
	elif symbol.endswith('USD'):
		ticker_symbol = replace_last(ticker_symbol, '/USD', '')
		trade_to='USD'
	elif symbol.endswith('USDC'):
		ticker_symbol = replace_last(ticker_symbol, '/USDC', '')
		trade_to='USDC'
	elif symbol.endswith('PAX'):
		ticker_symbol = replace_last(ticker_symbol, '/PAX', '')
		trade_to='PAX'
	elif symbol.endswith('USDS'):
		ticker_symbol = replace_last(ticker_symbol, '/USDS', '')
		trade_to='USDS'
	elif symbol.endswith('ETH'):
		ticker_symbol = replace_last(ticker_symbol, '/ETH', '')
		trade_to='ETH'
	
	trade_from=ticker_symbol
	exchange=get_exchange()
	
	pair_price=0
	if trade_to=='ETH':
		tickers=fetch_prices(exchange,'ETH/USDT')
		trade_to_price=float(tickers['close'])
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])
		fraction_to_budget=budget/trade_to_price
		units=fraction_to_budget/pair_price	
	elif trade_to=='BTC':
		tickers=fetch_prices(exchange,'BTC/USDT')
		trade_to_price=float(tickers['close'])
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])
		fraction_to_budget=budget/trade_to_price
		units=fraction_to_budget/pair_price
	elif trade_to=='BNB':
		tickers=fetch_prices(exchange,'BNB/USDT')
		trade_to_price=float(tickers['close'])
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])
		fraction_to_budget=budget/trade_to_price
		units=fraction_to_budget/pair_price
	else:
		trade_to_price=int(1)
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])
		fraction_to_budget=budget/trade_to_price
		units=fraction_to_budget/pair_price
		
	#print("Trading From: "+str(trade_from))
	#print("Trade To: "+str(trade_to))
	#print(str(trade_to)+ "Price: "+str(trade_to_price))
	#print("Pair Price: "+str(pair_price))
	#print("Fraction Of "+str(trade_to)+" To "+str(budget)+" is: "+str(fraction_to_budget))
	#print("Units to Execute is: "+str(units))	
	
	bankinfo = {"units":str(units),
	"balance_needed":str(fraction_to_budget)}
	
	return(bankinfo)

def fetch_last_buy_order(exchange,symbol):
	
	ret=exchange.fetch_closed_orders (symbol, 10);
	if ret:
		for order in ret:
			data=order['info']
			side=data['side']
			price=float(data['price'])
			if side=="BUY":
				bdata=data
		return(bdata)
	else:
		print("returning: NULL")
		return("NULL")

def trade_time(exchange,symbol):
	
	trades=exchange.fetchTrades (symbol)
	
	c=0
	for dat in trades:
		ts=dat['timestamp']	
		if c==0:
			start_ts=ts/1000
	last_ts=ts/1000
	c+=1
	elapsed = last_ts - start_ts
	elapsed=float(elapsed)/60
	return(elapsed)

def fetch_last_order(exchange,symbol):
	#print("passed: "+str(symbol))
	ret=exchange.fetch_closed_orders (symbol, 1);
	#print(ret)
	if ret:
		
		data=ret[-1]['info']
		side=data['side']
		price=float(data['price'])
		print("returning: 1")
		return data
	else:
		print("returning: NULL")
		return("NULL")

def spawn_bot(symbol):
	
	config = configparser.ConfigParser()
	
	bfn=str(symbol.lower())+'.ini'
	bfn=bfn.replace("/", "-")
	
	bot_name='watcher:'+str(symbol)
	bot_file='/home/crypto/cryptologic/pid-configs/init.ini'
	args='--trading_pair '+str(symbol)

	#If we allready have this bot in the circus ini don't add it again
	config.read(bot_file)

	if not config.has_section(bot_name):
	
		config.add_section(bot_name)
		config.set(bot_name, 'cmd', '/usr/bin/python3.6 /home/crypto/cryptologic/bots/autotrader.py')
		config.set(bot_name, 'args', args)
		config.set(bot_name, 'warmup_delay', '0')
		config.set(bot_name, 'numprocesses', '1')

		with open(bot_file, 'w') as configfile:
			configfile.write("\n")
			config.write(configfile)
			print("Write Config File to: "+str(bot_file))
			print("Wrote: "+str(configfile))

		subprocess.run(["/usr/bin/circusctl", "reloadconfig"])

def fetch_order_book(exchange,symbol,type,qlimit):
	#limit = 1000
	ret=exchange.fetch_l2_order_book(symbol, qlimit)

	if type=='bids':
		bids=ret['bids']
		return bids
	else:
		asks=ret['asks']
		return asks

def auto_spawn(trading_on,rsi_symbol, symbol, units, trade_from, trade_to, buy_pos, sell_pos, stoploss_percent, use_stoploss, candle_size, safeguard_percent, rsi_buy, rsi_sell, instant_market_buy, enable_buybacks, enable_safeguard, force_buy, force_sell, live):

	bot_name=symbol

	r = redis.Redis(host='localhost', port=6379, db=0)
	
	bot_ts=time.time()
	bot_config = {"trading_on":str(trading_on),
	"rsi_symbol":str(rsi_symbol), 
	"symbol":str(bot_name), 
	"units":float(units), 
	"trade_from":str(trade_from), 
	"trade_to":str(trade_to), 
	"buy_pos":int(buy_pos),
	"sell_pos":int(sell_pos),
	"stoploss_percent":float(stoploss_percent),
	"use_stoploss":use_stoploss,
	"candle_size":str(candle_size),
	"safeguard_percent":float(safeguard_percent),
	"rsi_buy":float(rsi_buy),
	"rsi_sell":float(rsi_sell),
	"instant_market_buy":str(instant_market_buy),
	"enable_buybacks":str(enable_buybacks),
	"enable_safeguard":str(enable_safeguard),
	"force_buy":str(force_buy),
	"force_sell":str(force_sell),
	"bot_ts":str(bot_ts),
	"live":str(live)}
	
	all=bot_config
	print(bot_config)
	ksymbol=str(symbol)

	redis_key="bconfig-tmp"
	r.hmset(redis_key, bot_config)
	
	bot_name=symbol
		
	r.sadd("botlist", bot_name)
	timestamp=time.time()

	r.set(symbol,timestamp)
	running=datetime.datetime.fromtimestamp(timestamp).strftime("%A, %B %d, %Y %I:%M:%S")

	timestamp=time.time()
	ts_raw=timestamp
	running=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
			
	redis_key="bconfig-"+symbol
		
	r.hmset(redis_key, all)
	bid=r.incr("bids")
	r.hset(redis_key,"id",bid)

	if force_buy=="yes":
		mc = memcache.Client(['127.0.0.1:11211'], debug=0)	
		key=symbol+"-FORCE-BUY"
		mc.set(key,force_buy,86400)			

	elif force_sell=="yes":
		mc = memcache.Client(['127.0.0.1:11211'], debug=0)	
		key=symbol+"-FORCE-SELL"
		mc.set(key,force_sell,86400)			

	if instant_market_buy=="yes":
		exchange=get_exchange()
		buy_book=fetch_order_book(exchange,symbol,'asks','1000')
		buy_pos=int(buy_pos)
		buy_price=float(buy_book[buy_pos][0])
		print(symbol+" Units Buy Price"+str(buy_price))
		
		redis_order_log="ORDERLOG-"+symbol

		ret=exchange.create_order (symbol, 'limit', 'buy', units, buy_price)
		
		order_id=int(ret['info']['orderId'])

		m=str(bid)+"\t"+str(order_id)+"\tBUY\t"+str(symbol)+"\t"+str(rsi_symbol)+"\t"+str(trade_from)+"\t"+str(trade_to)+"\t"+str(buy_price)+"\t"+str(units)
		print(ret)			
	spawn_bot(symbol)
