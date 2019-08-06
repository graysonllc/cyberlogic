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

def replace_last(source_string, replace_what, replace_with):
    head, _sep, tail = source_string.rpartition(replace_what)
    return head + replace_with + tail

exchange=nickbot.get_exchange()	

def price_when(symbol,secs):

	symbol=symbol.replace('/','')
	print(symbol)
	ts_now = datetime.datetime.now()
	ts_now_ts=int(time.mktime(ts_now.timetuple()))	
	ts_now_human=datetime.datetime.fromtimestamp(ts_now_ts).strftime("%Y-%m-%d %H:%M:%S")

	ts_before = ts_now - datetime.timedelta(seconds=secs)
	ts_end = ts_now + datetime.timedelta(seconds=secs)
	print(ts_before)

	ts_before_ts=int(time.mktime(ts_before.timetuple()))
	ts_end_ts=int(time.mktime(ts_end.timetuple()))
	tsd=datetime.datetime.fromtimestamp(ts_before_ts).strftime("%Y-%m-%d %H:%M:%S")
	print(tsd)
	p=0
	#try:
	print(ts_before_ts)
	start_ts=str(ts_before_ts)+"000"

	end_ts=str(ts_end_ts)+"000"	
	
	url="https://api.binance.com/api/v1/aggTrades?symbol="+symbol+"&startTime="+str(start_ts)+"&endTime="+str(end_ts)
	r=requests.get(url)
	res = (r.content.strip())
	status = r.status_code
	rsi_status=''
	trades = json.loads(res.decode('utf-8'))
	
	data=trades[0]
	price=data['p']
	#price=float(data[4])
	return(price)
				
def main():
	
	from datetime import date
	tickers=exchange.fetchTickers()
	mc = memcache.Client(['127.0.0.1:11211'], debug=0)
		
	for coin in tickers:
		pair=coin
		first=0
		skip=1
		broadcast_message=0
		price_jump=0
		coin=str(coin)
		rsi=100
		errors=0
		btc_price=float(tickers['BTC/USDT']['close'])
		btc_percent=float(tickers['BTC/USDT']['percentage'])
		last_price=0
		symbol=tickers[coin]['info']['symbol']
		redis_key=str(pair)+"-HISTORY"
		ts_now = datetime.datetime.now()
		ts_now=int(time.mktime(ts_now.timetuple()))	
		#print(ts_now)
		ts_now=str(ts_now)
	
		ts_now = datetime.datetime.now()
		ts_now_ts=int(time.mktime(ts_now.timetuple()))	
		ts_now_human=datetime.datetime.fromtimestamp(ts_now_ts).strftime("%Y-%m-%d %H:%M:%S")

		ts_before = ts_now - datetime.timedelta(seconds=864000)
		ts_end = ts_now - datetime.timedelta(seconds=86400)
		#print(ts_before)

		ts_before_ts=int(time.mktime(ts_before.timetuple()))
		ts_end_ts=int(time.mktime(ts_end.timetuple()))
		
		tsd=datetime.datetime.fromtimestamp(ts_before_ts).strftime("%Y-%m-%d %H:%M:%S")
		print(tsd)
		
		tsd=datetime.datetime.fromtimestamp(ts_end_ts).strftime("%Y-%m-%d %H:%M:%S")
		print(tsd)
		
		redis_log="LOG-"+symbol
		redis_server.delete(redis_log)
		
		redis_rsi_log="RSILOG-"+symbol
		redis_server.delete(redis_rsi_log)
			
		redis_key=str(symbol)+'-HISTORY'
		redis_server.zremrangebyscore(redis_key,ts_before_ts,ts_end_ts)
		
		print(str(symbol)+"\t"+str(ts_before_ts)+"\t"+str(ts_end_ts))
		
	time.sleep(0.5)
main()
sys.exit("die")	
e=0
while True:
	#try:
	main()
	print("Cycle !!!!!\n")
	#except:
	#e=1
