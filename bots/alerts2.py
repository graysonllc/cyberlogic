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

redis_server = redis.Redis(host='localhost', port=6379, db=0)

def get_exchange():
	
	#Read in our apikeys and accounts
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')
	conf=config['binance']
	
	binance_api_key=config['binance']['API_KEY']
	binance_api_secret=config['binance']['API_SECRET']
	
	exchange = ccxt.binance({
    'apiKey': binance_api_key,
    'secret': binance_api_secret,
    'enableRateLimit': True,
    'rateLimit': 3600,
    'verbose': False,  # switch it to False if you don't want the HTTP log
	})
	return(exchange)

exchange=get_exchange()	

def broadcast(chatid,text):
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')
	telegram_id=config['binance']['TELEGRAM_ID']
	token = telegram_id
	url = "https://api.telegram.org/"+ token + "/sendMessage?chat_id=" + chatid+"&text="+str(text)+"&parse_mode=HTML"
	r=requests.get(url)
	html = r.content

def fetch_prices(exchange, symbol):
	ticker = exchange.fetch_ticker(symbol.upper())
	return(ticker)
   

def fetch_last_order(exchange,symbol):
	ret=exchange.fetch_closed_orders (symbol, 1,"");
	#print(ret)
	if ret:
		data=ret[-1]['info']
		side=data['side']
		price=data['price']
		print("returning: 1")
	else:
		print("returning: 0")
		data=0
	return data

def die():
	sys.exit("fuck")

def get_price(pair,start_ts,end_ts):

	p=0
	#try:
	start_ts=start_ts+"000"
	url="https://api.binance.com/api/v1/klines?symbol="+pair+"&startTime="+str(start_ts)+"&interval=1m"
	print(url)
	r=requests.get(url)
	res = (r.content.strip())
	status = r.status_code
	print(status)
	rsi_status=''
	print(res)
	trades = json.loads(res.decode('utf-8'))
	data=trades[0]
	price=float(data[4])
	return(price)
	#except:
	#	p=1

def diff_percent(low,high):
	prices = [low,high]
	for a, b in zip(prices[::1], prices[1::1]):
		pdiff=100 * (b - a) / a
	pdiff=round(pdiff,2)

	return(pdiff)

def mojo(pair,price_now):

	mc = memcache.Client(['127.0.0.1:11211'], debug=0)

	blank=1
	
	ts_now = datetime.datetime.now()
	ts_now_ts=int(time.mktime(ts_now.timetuple()))	
	ts_now_human=datetime.datetime.fromtimestamp(ts_now_ts).strftime("%Y-%m-%d %H:%M:%S")

	key=str(pair)+str("pkey-1hour")
	if(mc.get(key)):
		mc.delete(key)
	
	ts_1hour = ts_now - datetime.timedelta(seconds=3600)
	ts_1hour_ts=int(time.mktime(ts_1hour.timetuple()))
	tsd=datetime.datetime.fromtimestamp(ts_1hour_ts).strftime("%Y-%m-%d %H:%M:%S")
	
	price_1_hours_ago=get_price(pair,str(ts_1hour_ts),str(ts_now_ts))
	if price_1_hours_ago:
		price_1_hours_ago=float(price_1_hours_ago)
		print("P1HA")
		print(price_1_hours_ago)
		price_now=float(price_now)
		price_diff=diff_percent(price_1_hours_ago,price_now)
		if price_diff:		
			mc.set(key,price_diff,86400)
			print("ALERTS::: Price Now: "+str(ts_now_human)+" "+str(price_now)+" 1 Hour Ago "+str(tsd)+" : "+str(price_1_hours_ago)+" Diff %: "+str(price_diff))
	
	key=str(pair)+str("pkey-3hour")
	if(mc.get(key)):
		mc.delete(key)
	
	ts_3hour = ts_now - datetime.timedelta(seconds=10800)
	ts_3hour_ts=int(time.mktime(ts_3hour.timetuple()))
	tsd=datetime.datetime.fromtimestamp(ts_3hour_ts).strftime("%Y-%m-%d %H:%M:%S")
		
	price_3_hours_ago=get_price(pair,str(ts_3hour_ts),str(ts_now_ts))
	if price_3_hours_ago:
		price_3_hours_ago=float(price_3_hours_ago)
		print("P3HA")
		print(price_3_hours_ago)
		price_now=float(price_now)
		price_diff=diff_percent(price_3_hours_ago,price_now)
		if price_diff:		
			mc.set(key,price_diff,86400)
			print("ALERTS::: Price Now: "+str(ts_now_human)+" "+str(price_now)+" 3 Hour Ago: "+str(tsd)+" : "+str(price_3_hours_ago)+" Diff %: "+str(price_diff))
	
	key=str(pair)+str("pkey-6hour")
	if(mc.get(key)):
		mc.delete(key)
	
	ts_6hour = ts_now - datetime.timedelta(seconds=21600)
	ts_6hour_ts=int(time.mktime(ts_6hour.timetuple()))
	tsd=datetime.datetime.fromtimestamp(ts_6hour_ts).strftime("%Y-%m-%d %H:%M:%S")
		
	price_6_hours_ago=get_price(pair,str(ts_6hour_ts),str(ts_now_ts))
	if price_6_hours_ago:
		price_6_hours_ago=float(price_6_hours_ago)
		print("P6HA")
		print(price_6_hours_ago)
		price_now=float(price_now)
		price_diff=diff_percent(price_6_hours_ago,price_now)
		if price_diff:		
			mc.set(key,price_diff,86400)
			print("ALERTS::: Price Now: "+str(ts_now_human)+" "+str(price_now)+" "+str(price_now)+" 6 Hour Ago: "+str(tsd)+" : "+str(price_6_hours_ago)+" Diff %: "+str(price_diff))
	
	key=str(pair)+str("pkey-12hour")
	if(mc.get(key)):
		mc.delete(key)
	
	ts_12hour = ts_now - datetime.timedelta(seconds=43200)
	ts_12hour_ts=int(time.mktime(ts_12hour.timetuple()))

	tsd=datetime.datetime.fromtimestamp(ts_12hour_ts).strftime("%Y-%m-%d %H:%M:%S")
		
	price_12_hours_ago=get_price(pair,str(ts_12hour_ts),str(ts_now_ts))
	if price_12_hours_ago:
		price_12_hours_ago=float(price_12_hours_ago)
		
		print("P12HA")
		print(price_12_hours_ago)
		price_now=float(price_now)
		price_diff=diff_percent(price_12_hours_ago,price_now)
		if price_diff:		
			mc.set(key,price_diff,86400)
			print("ALERTS::: Price Now: "+str(ts_now_human)+" "+str(price_now)+" 12 Hour Ago: "+str(tsd)+" : "+str(price_12_hours_ago)+" Diff %: "+str(price_diff))
	#except:
	#	print("")
	#sys.exit("Die")

def get_rsi(pair,interval):

	arr = []
	out = []
	fin = []
	url="https://api.binance.com/api/v1/klines?symbol="+pair+"&interval="+interval+"&limit=500"
	print(url)
	r=requests.get(url)
	res = (r.content.strip())
	status = r.status_code
	print("Status: "+str(status))
	rsi_status=''
	print("DBRSI: "+str(res))
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

def fetch_order_book(exchange,symbol,type,qlimit):
	limit = 1000
	ret=exchange.fetch_order_book(symbol, limit)

	if type=='bids':
		bids=ret['bids']
		return bids
	else:
		asks=ret['asks']
		return asks

def main():
	
	from datetime import date
	tickers=exchange.fetchTickers()
	mc = memcache.Client(['127.0.0.1:11211'], debug=0)
	for coin in tickers:

		first=0
		skip=1
		broadcast_message=0
		price_jump=0
		coin=str(coin)
		rsi=100
		btc_price=float(tickers['BTC/USDT']['close'])
		btc_percent=float(tickers['BTC/USDT']['percentage'])

		symbol=tickers[coin]['info']['symbol']
		csymbol=coin
		csymbol=csymbol.replace("/","_",1)
		det=int(0)
		today = str(date.today())
		
		if 'USDT' in symbol:
			min_vol=1000000
			skip=0
		elif 'BTC' in symbol:
			min_vol=500
			skip=0
		elif 'BNB' in symbol:
			min_vol=50000
			
		key = str(date.today())+str('ALERTS-LAST_PRICE')+str(csymbol)
		
		last_price=0
		if mc.get(key):
			last_price=mc.get(key)
			#print("ALERTS DB: GOT LP: "+str(last_price))
		else:
			first=1
			
		data=str()
		row=tickers[coin]
		symbol=row['info']['symbol']
		close=row['close']
		percent=row['percentage']
		low=row['low']
		high=row['high']
		qv=row['quoteVolume']
		price=close
		dprint=1
		pair=symbol
		our_percent=0
		last_price=0
		
		if skip!=1 and qv >=min_vol:
			
			prices = [low,high]
			for a, b in zip(prices[::1], prices[1::1]):
				pdiff=100 * (b - a) / a
			
			pdiff=round(pdiff,2)
				
			spread=pdiff

			pair=symbol

			if last_price>0:
				print("DBLP: "+str(last_price))
				print("PRICE: "+str(price))
				darr = [last_price,price]
				for a, b in zip(darr[::1], darr[1::1]):
					price_jump=100 * (b - a) / a
					price_jump=round(price_jump,2)

			if percent>1 and price_jump>0.10 or percent>1 and first==1:
	
				key = str(date.today())+str('ALERTSDB')+str(csymbol)
				if mc.get(key):
					dprint=2
				else:
					print("ALERTS DEBUG::: LP: "+str(last_price)+" P: "+str(price)+" D: "+str(price_jump))
	
					det=int(1)
					mc.set(key,1,120)
					
					try:
						rsi_3m=get_rsi(symbol,'3m')
						rsi_5m=get_rsi(symbol,'5m')
						rsi_stats="<b>RSI 3M:</b> "+str(rsi_3m)+" <b>RSI 5M:</b> "+str(rsi_5m)
						mojo(symbol,close)
														
						key=str(pair)+str("pkey-1hour")
						if mc.get(key):
							one_hours=mc.get(key)
						else:
							one_hours=0

						key=str(pair)+str("pkey-3hour")
						if mc.get(key):
							three_hours=mc.get(key)
						else:
							three_hours=0
							
						key=str(pair)+str("pkey-6hour")
						if mc.get(key):
							six_hours=mc.get(key)
						else:
							six_hours=0
						
						key=str(pair)+str("pkey-12hour")
						if mc.get(key):
							twelve_hours=mc.get(key)
						else:
							twelve_hours=0
				
						link='https://www.binance.com/en/trade/pro/'+csymbol
						alert_type=':::PRICE ALERT: '+str(percent)+'%:::'					
							
						data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+"%, <b>12H:</b> "+str(twelve_hours)+str('%')
						data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)

						timestamp=time.time()
						ts_raw=timestamp
						date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
						date_today=str(date.today())							
						alert_key_all=str(date_today)+'-NALERTS'
						alert_key_symbol=str(date_today)+str(symbol)+'-NALERTS'
						alert_list_today=str(date_today)+'-NALERTLIST'
						symbol_ids=str(symbol)+'-NIDS'
						symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
								
						data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
						pdata=str(date_time)+"\t"+str(price)+"\t"+str(percent)
						redis_server.rpush(alert_key_all,pdata)
														
						redis_server.sadd(alert_list_today,symbol)

						#Add Unique Timestamp to list for this symbol, will use as identifer for hash later
						redis_server.sadd(symbol_ids,ts_raw)
							
						detail_hash = {"date":str(date_today),
						"date_time":str(date_time), 
						"symbol":str(symbol), 
						"alert_type":str(alert_type), 
						"price":float(price), 
						"percent":float(percent), 
						"high":str(high), 
						"low":str(low), 
						"volume":int(qv),
						"spread":float(spread),
						"rsi_3mins":float(rsi_3m),
						"rsi_5mins":float(rsi_5m),
						"btc_price":str(btc_price),
						"btc_percent":str(btc_percent),
						"link":str(link),
						}
		
						print("Writing detailed alert hash data to: "+str(symbol_hash_detailed))
						print(detail_hash)
						redis_server.hmset(symbol_hash_detailed, detail_hash)

						print("Pushing coin to todays alert list: "+str(symbol))
						print(data)

						key = str(date.today())+str('ALERTS-LAST_PRICE')+str(csymbol)
						mc.set(key,price,86400)

						#broadcast('693711905',data)	
						#broadcast('420441454',data)	
						#broadcast('446619309',data)	
						#broadcast('490148813',data)	
						#broadcast('110880375',data)	
						#broadcast('699448304',data)	
						#broadcast('593213791',data)	
						#broadcast('506872080',data)	
						#broadcast('543018578',data)
						#broadcast('503482955',data)
						time.sleep(10)	
						#broadcast('429640253',data)
					except:
						print("threw error")
						time.sleep(5)
				
while True:
	#try:
	main()
	#except:
	#print("error")
	time.sleep(5)
