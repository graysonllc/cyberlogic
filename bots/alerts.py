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
	rsi_status=''
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
	
	#try:
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

	try:
		arr = []
		out = []
		fin = []
		url="https://api.binance.com/api/v1/klines?symbol="+pair+"&interval="+interval+"&limit=100"
		r=requests.get(url)
		res = (r.content.strip())
		status = r.status_code
		rsi_status=''
		trades = json.loads(res.decode('utf-8'))

		#print(trades)
		for trade in trades:
			open_price=float(trade[0])
			close_price=float(trade[4])
			high_price=float(trade[2])
			low_price=float(trade[3])
			if close_price>0:
				arr.append(close_price)	

		np_arr = np.array(arr,dtype=float)
		output=talib.RSI(np_arr,timeperiod=20)

		for chkput in output:
			if chkput>0:
				fin.append(chkput)
		
		#sys.exit("fuck")
		rsi=float(fin[-1])

		rsi=round(rsi)
		print(rsi)

		return(rsi)
	except:
		time.sleep(2)
		print("rsi is the problem")

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
	
	only_broadcast_up=1
	broadcast_message=0
	
	from datetime import date
	tickers=exchange.fetchTickers()
	mc = memcache.Client(['127.0.0.1:11211'], debug=0)
	for coin in tickers:

		skip=1
		coin=str(coin)
		rsi=100
		btc_price=float(tickers['BTC/USDT']['close'])
		btc_percent=float(tickers['BTC/USDT']['percentage'])

		symbol=tickers[coin]['info']['symbol']
		csymbol=coin
		csymbol=csymbol.replace("/","_",1)
		det=int(0)
		today = str(date.today())
		key = str(date.today())+str('last_price')+str(csymbol)
		
		last_price=0
		if 'USDT' in symbol:
			min_vol=1000000
			skip=0
		elif 'BTC' in symbol:
			min_vol=500
			skip=0
		elif 'BNB' in symbol:
			min_vol=50000
			
			skip=0
		if mc.get(key):
			last_price=mc.get(key)
			
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
		
		if skip!=1:
			
			key=str(pair)+str("pkey-12hour")
			if mc.get(key):
				our_percent=mc.get(key)

			key=str(pair)+str("LAST_PRICE_KEY")
			if mc.get(key):
				last_price=float(mc.get(key))
				
				if(last_price>=float(close)):
					alert_direction="UP"
				else:
					alert_direction="DOWN"	
			else:
				alert_direction="UP"			
			
			mc.set(key,close,86400)

			if qv >=min_vol:
				prices = [low,high]
				#print(prices)
				for a, b in zip(prices[::1], prices[1::1]):
					pdiff=100 * (b - a) / a
			
				pdiff=round(pdiff,2)
				
				spread=pdiff

				if percent>1:
				
					pair=symbol

					if percent>1 and percent<2 or our_percent>1 and our_percent<2:
						key = str(date.today())+str('newkey-sd1dddddasssasdspddsajja')+str(csymbol)
						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)

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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
							
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)

							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							redis_server.rpush(alert_key_all,data)
							#print("Pushing coin to todays alert list: "+str(symbol))
														
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)

							
					if percent>2 and percent<3 or our_percent>2 and our_percent<3:
						key = str(date.today())+str('DfffD3')+str(csymbol)
						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)						
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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
														
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)

					if percent>3 and percent<4 or our_percent>3 and our_percent<4:
						key = str(date.today())+str('DdddD4')+str(csymbol)
						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)
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
							
							key=str(pair)+str("pkey-4hour")
							if mc.get(key):
								four_hours=mc.get(key)
							else:
								four_hours=0
						
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
							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
							
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)

							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)


					if percent>4 and percent<5 or our_percent>4 and our_percent<5:
						key = str(date.today())+str('ddddddd4')+str(csymbol)
						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)
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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
														
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)

							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)
							
					elif percent>5 and percent<6 or our_percent>5 and our_percent<6:
					
						key = str(date.today())+str('djdhdhjjdh')+str(csymbol)
						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)
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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
														
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)


							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							
							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)

					elif percent>6 and percent<7 or our_percent>6 and our_percent<7:
						key = str(date.today())+str('dddddiduiiudyud')+str(csymbol)
						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)
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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
														
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)

							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)

					elif percent>7 and percent<8 or our_percent>7 and our_percent<8:
						key = str(date.today())+str('djdhdhdddjjdh')+str(csymbol)
						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)
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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
														
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)

					elif percent>8 and percent<9 or our_percent>8 and our_percent<9:
						key = str(date.today())+str('djdhdhssjjdh')+str(csymbol)

						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)

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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
														
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)

							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
														
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							
							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)


					elif percent>9 and percent<10 or our_percent>9 and our_percent<10:
						key = str(date.today())+str('DALEdjdjjdjdRT3')+str(csymbol)
						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)

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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
														
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)


					elif percent>10 and percent<11 or our_percent>10 and our_percent<11:
						key = str(date.today())+str('DALEddjdjjdjdRT3')+str(csymbol)

						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)
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

							print(data)
							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
														
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)
	
					elif percent>11 and percent<12 or our_percent>11 and our_percent<12:
						key = str(date.today())+str('dddihsjkhhkjddhkj')+str(csymbol)

						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)
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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
													
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)

							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)
	
					elif percent>12 and percent<13 or our_percent>12 and our_percent<13:
						key = str(date.today())+str('DALEdjddddjjdjdRT3')+str(csymbol)

						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)
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

							print(data)
							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
														
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)

					elif percent>13 and percent<14 or our_percent>13 and our_percent<14:
						key = str(date.today())+str('ddkdkkhjdkj33')+str(csymbol)

						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)
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

							print(data)
							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
							
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)
	
					elif percent>14 and percent<15 or our_percent>14 and our_percent<15:
						key = str(date.today())+str('dkdhjkdhkjdkjh333d')+str(csymbol)

						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)
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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
							
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)

	
					elif percent>15 and percent<16 or our_percent>15 and our_percent<16:
						key = str(date.today())+str('dkdjkdkh234')+str(csymbol)

						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)

							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="<b>RSI 3M:</b> "+str(rsi_3m)+" <b>RSI 5M:</b> "+str(rsi_5m)

							print(data)
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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
														
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)


	
					elif percent>16 and percent<17 or our_percent>16 and our_percent<17:
						key = str(date.today())+str('djdjhg3ujdhd')+str(csymbol)

						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)

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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
														
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)


	
					elif percent>17 and percent<18 or our_percent>17 and our_percent<18:
						key = str(date.today())+str('djdjhg3uddn39jdhd')+str(csymbol)

						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)
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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
														
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)

							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)

					elif percent>17 and percent<18 or our_percent>17 and our_percent<18:
						key = str(date.today())+str('djdhdhh33')+str(csymbol)

						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)
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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
										
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)

							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)

					elif percent>18 and percent<19 or our_percent>18 and our_percent<19:
						key = str(date.today())+str('djdh8838383dhh33')+str(csymbol)

						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)

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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
														
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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
							
							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)

					elif percent>19 and percent<20 or our_percent>19 and our_percent<20:
						key = str(date.today())+str('m0000ned')+str(csymbol)

						if mc.get(key):
							dprint=2
						else:
							det=int(1)
							mc.set(key,1,3600)
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
							alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
												
							data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
							data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)

							
							timestamp=time.time()
							ts_raw=timestamp
							date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
							date_today=str(date.today())
							
							alert_key_all=str(date_today)+'-ALERTS'
							alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
							alert_list_today=str(date_today)+'-ALERTLIST'
							symbol_ids=str(symbol)+'-IDS'
							symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
							data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
							#Push the whole Alert to redis
							redis_server.rpush(alert_key_all,data)
							print("Pushing coin to todays alert list: "+str(symbol))
							print(data)
							
							#Add Unique Coin to Alerts list for today
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

							if only_broadcast_up==1 and alert_direction=='UP':
								broadcast_message=1
							elif only_broadcast_up==0:
								broadcast_message=1
							
							if broadcast_message==1:
								broadcast('693711905',data)	
								broadcast('420441454',data)	
								broadcast('446619309',data)	
								broadcast('490148813',data)	
								broadcast('110880375',data)	
								broadcast('699448304',data)	
								broadcast('593213791',data)	
								broadcast('506872080',data)	
								broadcast('543018578',data)
								broadcast('503482955',data)
								broadcast('429640253',data)
				
					if det==1:
						time.sleep(30)
						if rsi_3m>53 and rsi_3m<65:
							key = str(date.today())+str('rsi53')+str(csymbol)
							if mc.get(key):
								dprint=2
							else:
								mc.set(key,1,86400)
								link='https://www.binance.com/en/trade/pro/'+csymbol
								alert_type=':::PRICE ALERT '+str(alert_direction)+': '+str(percent)+'%:::'					
							
								data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
								data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
								
								timestamp=time.time()
								ts_raw=timestamp
								date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
								date_today=str(date.today())
							
								alert_key_all=str(date_today)+'-ALERTS'
								alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
								alert_list_today=str(date_today)+'-ALERTLIST'
								symbol_ids=str(symbol)+'-IDS'
								symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
								data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
								#Push the whole Alert to redis
								redis_server.rpush(alert_key_all,data)
								print("Pushing coin to todays alert list: "+str(symbol))
								print(data)
							
								#Add Unique Coin to Alerts list for today
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

								if only_broadcast_up==1 and alert_direction=='UP':
									broadcast_message=1
								elif only_broadcast_up==0:
									broadcast_message=1
							
								if broadcast_message==1:
									broadcast('693711905',data)	
									broadcast('420441454',data)	
									broadcast('446619309',data)	
									broadcast('490148813',data)	
									broadcast('110880375',data)	
									broadcast('699448304',data)	
									broadcast('593213791',data)	
									broadcast('506872080',data)	
									broadcast('543018578',data)
									broadcast('503482955',data)
									broadcast('429640253',data)
	
						elif rsi_3m>80:
							key = str(date.today())+str('rsi70')+str(csymbol)
							if mc.get(key):
								dprint=2
							else:
								key=str(pair)+str("pkey-1hour")
								mc.set(key,1,86400)
								link='https://www.binance.com/en/trade/pro/'+csymbol
								alert_type=':::EXTREME RSI ALERT + '+str(percent)+'%:::'					
							
								data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
								data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
									
								timestamp=time.time()
								ts_raw=timestamp
								date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
								date_today=str(date.today())
							
								alert_key_all=str(date_today)+'-ALERTS'
								alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
								alert_list_today=str(date_today)+'-ALERTLIST'
								symbol_ids=str(symbol)+'-IDS'
								symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
								data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
								#Push the whole Alert to redis
								redis_server.rpush(alert_key_all,data)
								print("Pushing coin to todays alert list: "+str(symbol))
								print(data)
							
								#Add Unique Coin to Alerts list for today
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

								if only_broadcast_up==1 and alert_direction=='UP':
									broadcast_message=1
								elif only_broadcast_up==0:
									broadcast_message=1
							
								if broadcast_message==1:
									broadcast('693711905',data)	
									broadcast('420441454',data)	
									broadcast('446619309',data)	
									broadcast('490148813',data)	
									broadcast('110880375',data)	
									broadcast('699448304',data)	
									broadcast('593213791',data)	
									broadcast('506872080',data)	
									broadcast('543018578',data)
									broadcast('503482955',data)
									broadcast('429640253',data)


						elif rsi_3m>70 and rsi_3m<80:
							key = str(date.today())+str('rsi70')+str(csymbol)
							if mc.get(key):
								dprint=2
							else:
								mc.set(key,1,86400)
								link='https://www.binance.com/en/trade/pro/'+csymbol
								alert_type=':::RSI Alert + '+str(percent)+'%::'					
							
								data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
								data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)

								
								timestamp=time.time()
								ts_raw=timestamp
								date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
								date_today=str(date.today())
							
								alert_key_all=str(date_today)+'-ALERTS'
								alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
								alert_list_today=str(date_today)+'-ALERTLIST'
								symbol_ids=str(symbol)+'-IDS'
								symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
								data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
								#Push the whole Alert to redis
								redis_server.rpush(alert_key_all,data)
								print("Pushing coin to todays alert list: "+str(symbol))
								print(data)
							
								#Add Unique Coin to Alerts list for today
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

								if only_broadcast_up==1 and alert_direction=='UP':
									broadcast_message=1
								elif only_broadcast_up==0:
									broadcast_message=1
							
								if broadcast_message==1:
									broadcast('693711905',data)	
									broadcast('420441454',data)	
									broadcast('446619309',data)	
									broadcast('490148813',data)	
									broadcast('110880375',data)	
									broadcast('699448304',data)	
									broadcast('593213791',data)	
									broadcast('506872080',data)	
									broadcast('543018578',data)
									broadcast('503482955',data)
									broadcast('429640253',data)


						elif rsi_3m>80 and rsi<100:
							key = str(date.today())+str('rsi70')+str(csymbol)
							if mc.get(key):
								dprint=2
							else:
								mc.set(key,1,86400)
								link='https://www.binance.com/en/trade/pro/'+csymbol
								alert_type=':::EXTREME RSI ALERT + '+str(percent)+'%:::'					
							
								data_add="<b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+", <b>12H:</b> "+str(twelve_hours)+str('. %')
								data='<b>'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(percent)+'%)' + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)

								
								timestamp=time.time()
								ts_raw=timestamp
								date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
								date_today=str(date.today())
							
								alert_key_all=str(date_today)+'-ALERTS'
								alert_key_symbol=str(date_today)+str(symbol)+'-ALERTS'
								alert_list_today=str(date_today)+'-ALERTLIST'
								symbol_ids=str(symbol)+'-IDS'
								symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
							
								data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
							
								#Push the whole Alert to redis
								redis_server.rpush(alert_key_all,data)
								print("Pushing coin to todays alert list: "+str(symbol))
								print(data)
							
								#Add Unique Coin to Alerts list for today
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

								if only_broadcast_up==1 and alert_direction=='UP':
									broadcast_message=1
								elif only_broadcast_up==0:
									broadcast_message=1
							
								if broadcast_message==1:
									broadcast('693711905',data)	
									broadcast('420441454',data)	
									broadcast('446619309',data)	
									broadcast('490148813',data)	
									broadcast('110880375',data)	
									broadcast('699448304',data)	
									broadcast('593213791',data)	
									broadcast('506872080',data)	
									broadcast('543018578',data)
									broadcast('503482955',data)
									broadcast('429640253',data)

				#else:	
				#	print("no conditions met: "+str(symbol))

while True:
	try:
		main()
	except:
		print("error")
	time.sleep(30)
