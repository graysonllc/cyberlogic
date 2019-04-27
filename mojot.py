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
from datetime import date
import configparser

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib'
sys.path.append(root + '/python')

import talib
import numpy as np
import ccxt  # noqa: E402

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
	print("got "+str(text))
	
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')
	telegram_id=config['binance']['TELEGRAM_ID']
	token = telegram_id
	url = "https://api.telegram.org/"+ token + "/sendMessage?chat_id=" + chatid+"&text="+text
	print(url)
	r=requests.get(url)
	print(r)
	html = r.content

def style(s, style):
    return style + s + '\033[0m'


def green(s):
    return style(s, '\033[92m')


def blue(s):
    return style(s, '\033[94m')


def yellow(s):
    return style(s, '\033[93m')


def dump(*args):
    print(' '.join([str(arg) for arg in args]))
    
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

def get_price(pair,ts):

	try:
		url="https://api.binance.com/api/v1/klines?symbol="+pair+"&startTime="+ts+"&interval=1m"
		r=requests.get(url)
		res = (r.content.strip())
		status = r.status_code
		rsi_status=''
		trades = json.loads(res.decode('utf-8'))
		data=trades[0]
		price=float(data[4])
		return(price)
	except:
		return("error")

def diff_percent(low,high):
	prices = [low,high]
	for a, b in zip(prices[::1], prices[1::1]):
		pdiff=100 * (b - a) / a
	pdiff=round(pdiff,2)

	return(pdiff)

def mojo(pair,price_now):

	mc = memcache.Client(['127.0.0.1:11211'], debug=0)

	print("Running Mojo: "+str(pair))
	try:
		ts_now = int(round(time.time() * 1000))
		ts_now=ts_now+1
		ts_1hour=ts_now-3600*1000

		key=str(pair)+str("pkey-1hour")
		if(mc.get(key)):
			mc.delete(key)
		
		price_1_hours_ago=float(get_price(pair,str(ts_1hour)))
		if price_1_hours_ago!="error":
			price_now=float(price_now)
			price_diff=diff_percent(price_1_hours_ago,price_now)
			if price_diff>0:
				

				mc.set(key,price_diff,86400)
				print("db: set key to: "+str(key)+"->"+str(price_diff))
				print("Price Now: "+str(price_now)+" 1 Hour Ago: "+str(price_1_hours_ago)+" Diff %: "+str(price_diff))
	except:
		print("")
	
	time.sleep(0.5)

	try:
		ts_now = int(round(time.time() * 1000))
		ts_now=ts_now+1
		ts_2hour=ts_now-7200*1000
		
		key=str(pair)+str("pkey-2hour")
		if(mc.get(key)):
			mc.delete(key)

		price_2_hours_ago=get_price(pair,str(ts_2hour))
		if price_2_hours_ago!="error":
			price_diff=diff_percent(price_2_hours_ago,price_now)
			if price_diff>0:
				mc.set(key,price_diff,86400)

				print("Price Now: "+str(price_now)+" 2 Hour Ago: "+str(price_2_hours_ago)+" Diff %: "+str(price_diff))
	except:
		print("")

	time.sleep(0.5)
	
	try:
		ts_now = int(round(time.time() * 1000))
		ts_now=ts_now+1
		ts_3hour=ts_now-10800*1000

		key=str(pair)+str("pkey-3hour")
		if(mc.get(key)):
			mc.delete(key)		
		
		price_3_hours_ago=get_price(pair,str(ts_3hour))
		if price_3_hours_ago!="error":
			price_diff=diff_percent(price_3_hours_ago,price_now)
			if price_diff>0:
				mc.set(key,price_diff,86400)
				print("Price Now: "+str(price_now)+" 3 Hour Ago: "+str(price_3_hours_ago)+" Diff %: "+str(price_diff))
	except:
		print("")
	
	time.sleep(0.5)
	
	try:
		ts_now = int(round(time.time() * 1000))
		ts_now=ts_now+1
		ts_4hour=ts_now-14400*1000

		key=str(pair)+str("pkey-4hour")
		if(mc.get(key)):
			mc.delete(key)
			
		price_4_hours_ago=get_price(pair,str(ts_4hour))
		if price_4_hours_ago!="error":
			price_diff=diff_percent(price_4_hours_ago,price_now)
			if price_diff>0:							
				mc.set(key,price_diff,86400)
				print("Price Now: "+str(price_now)+" 4 Hour Ago: "+str(price_4_hours_ago)+" Diff %: "+str(price_diff))
	except:	
		print("")

	time.sleep(0.5)
	
	try:
		ts_now = int(round(time.time() * 1000))
		ts_now=ts_now+1
		ts_5hour=ts_now-18000*1000

		key=str(pair)+str("pkey-5hour")
		if(mc.get(key)):
			mc.delete(key)

		price_5_hours_ago=get_price(pair,str(ts_5hour))
		if price_5_hours_ago!="error":
			price_diff=diff_percent(price_5_hours_ago,price_now)
			if price_diff>0:
							
				mc.set(key,price_diff,86400)

				print("Price Now: "+str(price_now)+" 5 Hour Ago: "+str(price_5_hours_ago)+" Diff %: "+str(price_diff))
	except:
		print("")
	
	time.sleep(0.5)	
	
	try:
		ts_now = int(round(time.time() * 1000))
		ts_now=ts_now+1
		ts_6hour=ts_now-21600*1000

		key=str(pair)+str("pkey-6hour")
		if(mc.get(key)):
			mc.delete(key)

		price_6_hours_ago=get_price(pair,str(ts_6hour))
		if price_6_hours_ago!="error":
			price_diff=diff_percent(price_6_hours_ago,price_now)
			if price_diff>0:			
				mc.set(key,price_diff,86400)
				print("Price Now: "+str(price_now)+" 6 Hour Ago: "+str(price_6_hours_ago)+" Diff %: "+str(price_diff))
	except:
		print("")
	
	time.sleep(0.5)
	
	try:
		ts_now = int(round(time.time() * 1000))
		ts_now=ts_now+1
		ts_12hour=ts_now-43200*1000
		price_12_hours_ago=get_price(pair,str(ts_12hour))
		
		key=str(pair)+str("pkey-12hour")
		if(mc.get(key)):
			mc.delete(key)

		
		if price_6_hours_ago!="error":
			price_diff=diff_percent(price_12_hours_ago,price_now)
			if price_diff>0:
				mc.set(key,price_diff,86400)
				print("Price Now: "+str(price_now)+" 12 Hour Ago: "+str(price_12_hours_ago)+" Diff %: "+str(price_diff))
	except:
		print("")

	time.sleep(0.5)
	
	try:
		ts_now = int(round(time.time() * 1000))
		ts_now=ts_now+1
		ts_5min=ts_now-300*1000
		
		key=str(pair)+str("pkey-5mins")
		if(mc.get(key)):
			mc.delete(key)

		price_5_min_ago=get_price(pair,str(ts_5min))
		if price_5_min_ago!="error":
			price_diff=diff_percent(price_5_min_ago,price_now)
			if price_diff>0:
				mc.set(key,price_diff,86400)
				print("Price Now: "+str(price_now)+" 5 Min Ago: "+str(price_5_min_ago)+" Diff %: "+str(price_diff))
	except:
		print("")

	time.sleep(0.5)
	
	try:
		ts_now = int(round(time.time() * 1000))
		ts_now=ts_now+1
		ts_10min=ts_now-600*1000

		key=str(pair)+str("pkey-10mins")
		if(mc.get(key)):
			mc.delete(key)

		price_10_min_ago=get_price(pair,str(ts_10min))
		if price_10_min_ago!="error":
			price_diff=diff_percent(price_10_min_ago,price_now)
			if price_diff>0:
				mc.set(key,price_diff,86400)
				print("Price Now: "+str(price_now)+" 10 Min Ago: "+str(price_10_min_ago)+" Diff %: "+str(price_diff))
	except:
		print("")
	
	time.sleep(0.5)
	
	try:
		ts_now = int(round(time.time() * 1000))
		ts_now=ts_now+1
		ts_15min=ts_now-900*1000

		key=str(pair)+str("pkey-15mins")
		if(mc.get(key)):
			mc.delete(key)

		price_15_min_ago=get_price(pair,str(ts_15min))
		if price_15_min_ago!="error":
			price_diff=diff_percent(price_15_min_ago,price_now)
			if price_diff>0:
				mc.set(key,price_diff,86400)
				print("Price Now: "+str(price_now)+" 15 Min Ago: "+str(price_15_min_ago)+" Diff %: "+str(price_diff))
	except:
		ts_now = int(round(time.time() * 1000))
		ts_now=ts_now+1
	
	time.sleep(0.5)	
	
	try:
		ts_30min=ts_now-1800*1000
		price_30_min_ago=get_price(pair,str(ts_30min))

		key=str(pair)+str("pkey-30mins")
		if(mc.get(key)):
			mc.delete(key)

		if price_30_min_ago!="error":
			price_diff=diff_percent(price_30_min_ago,price_now)
			if price_diff>0:
				mc.set(key,price_diff,86400)

				print("Price Now: "+str(price_now)+" 30 Min Ago: "+str(price_30_min_ago)+" Diff %: "+str(price_diff))
	except:
		print("")

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
		print("Today: "+str(today))
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
			
		if skip!=1:
		
			mc.set(key,close,86400)
	
			if qv >=min_vol:
				prices = [low,high]
				#print(prices)
				for a, b in zip(prices[::1], prices[1::1]):
					pdiff=100 * (b - a) / a
			
				pdiff=round(pdiff,2)
				if pdiff>2.5 and percent>1:
				
					pair=symbol

					if percent>1 and percent<2:
						key = str(date.today())+str('DDdadda2new')+str(csymbol)
						if mc.get(key):
							print("seen p1-key")
						else:
							det=int(1)
							mc.set(key,1,3600)

							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
							
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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
							
					if percent>2 and percent<3:
						key = str(date.today())+str('DD3')+str(csymbol)
						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)						
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)
							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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
					
					if percent>3 and percent<4:
						key = str(date.today())+str('DD4')+str(csymbol)
						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)
							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
							
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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

					if percent>4 and percent<5:
						key = str(date.today())+str('ddd4')+str(csymbol)
						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)
							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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

							
					elif percent>5 and percent<6:
					
						key = str(date.today())+str('djdhdhjjdh')+str(csymbol)
						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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

					elif percent>6 and percent<7:
						key = str(date.today())+str('dddiduiiudyud')+str(csymbol)
						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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

					elif percent>7 and percent<8:
						key = str(date.today())+str('djdhdhdddjjdh')+str(csymbol)
						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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


					elif percent>8 and percent<9:
						key = str(date.today())+str('djdhdhssjjdh')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)

							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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


					elif percent>9 and percent<10:
						key = str(date.today())+str('DALEdjdjjdjdRT3')+str(csymbol)
						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)

							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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


					elif percent>10 and percent<11:
						key = str(date.today())+str('DALEddjdjjdjdRT3')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							print(data)
							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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

	
					elif percent>11 and percent<12:
						key = str(date.today())+str('dddihsjkhhkjddhkj')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
													
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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

	
					elif percent>12 and percent<13:
						key = str(date.today())+str('DALEdjddddjjdjdRT3')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							print(data)
							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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


					elif percent>13 and percent<14:
						key = str(date.today())+str('ddkdkkhjdkj33')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)
							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							print(data)
							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
							
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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

	
					elif percent>14 and percent<15:
						key = str(date.today())+str('dkdhjkdhkjdkjh333d')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)
							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
							
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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


					elif percent>16 and percent<17:
						key = str(date.today())+str('adhjkhdjhjhkj')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)
							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							print(data)
							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
													
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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

	
					elif percent>15 and percent<16:
						key = str(date.today())+str('dkdjkdkh234')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)

							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							print(data)
							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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

	
					elif percent>16 and percent<17:
						key = str(date.today())+str('djdjhg3ujdhd')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)

							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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

	
					elif percent>17 and percent<18:
						key = str(date.today())+str('djdjhg3uddn39jdhd')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)
							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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


					elif percent>17 and percent<18:
						key = str(date.today())+str('djdhdhh33')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
													
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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


					elif percent>18 and percent<19:
						key = str(date.today())+str('djdh8838383dhh33')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)

							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0

							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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

	

					elif percent>18 and percent<19:
						key = str(date.today())+str('djd383838hdhh33')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)
							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0
							print(data)
							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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


					elif percent>19 and percent<20:
						key = str(date.today())+str('djd383dddd838hdhh33')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)

							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0
							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
														
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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

					elif percent>20:
						key = str(date.today())+str('m0000ned')+str(csymbol)

						if mc.get(key):
							print("")
						else:
							det=int(1)
							mc.set(key,1,3600)
							rsi_3m=get_rsi(symbol,'3m')
							rsi_5m=get_rsi(symbol,'5m')
							rsi_stats="RSI 3M: "+str(rsi_3m)+" RSI 5M: "+str(rsi_5m)
							mojo(symbol,close)
							key=str(pair)+str("pkey-1hour")
							if mc.get(key):
								one_hours=mc.get(key)
							else:
								one_hours=0

							key=str(pair)+str("pkey-2hour")
							if mc.get(key):
								two_hours=mc.get(key)
							else:
								two_hours=0
						
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
						
							key=str(pair)+str("pkey-5hour")
							if mc.get(key):
								five_hours=mc.get(key)
							else:
								five_hours=0
							
							key=str(pair)+str("pkey-6hour")
							if mc.get(key):
								six_hours=mc.get(key)
							else:
								six_hours=0
						
							key=str(pair)+str("pkey-5mins")

							if mc.get(key):
								five_mins=mc.get(key)
							else:
								five_mins=0
						
							key=str(pair)+str("pkey-10mins")
							if mc.get(key):
								ten_mins=mc.get(key)
							else:
								ten_mins=0
						
							key=str(pair)+str("pkey-15mins")
							if mc.get(key):
								fifteen_mins=mc.get(key)
							else:
								fifteen_mins=0	
						
							key=str(pair)+str("pkey-30mins")
							if mc.get(key):
								thirty_mins=mc.get(key)
							else:
								thirty_mins=0

							key=str(pair)+str("pkey-12hour")
							if mc.get(key):
								twelve_hours=mc.get(key)
							else:
								twelve_hours=0
							link='https://www.binance.com/en/trade/pro/'+csymbol
							alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
												
							data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
							data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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
						time.sleep(3)
						if rsi_3m>53 and rsi_3m<65:
							key = str(date.today())+str('rsi53')+str(csymbol)
							if mc.get(key):
								print("")
							else:
								mc.set(key,1,86400)
								link='https://www.binance.com/en/trade/pro/'+csymbol
								alert_type=' ::Price Alert Up: '+str(percent)+'%:: '					
							
								data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
								data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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
								print("")
							else:
								key=str(pair)+str("pkey-1hour")
								mc.set(key,1,86400)
								link='https://www.binance.com/en/trade/pro/'+csymbol
								alert_type=' ::EXTREME RSI ALERT + '+str(percent)+'%:: '					
							
								data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
								data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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
								print("")
							else:
								mc.set(key,1,86400)
								link='https://www.binance.com/en/trade/pro/'+csymbol
								alert_type=' ::RSI Alert + '+str(percent)+'%:: '					
							
								data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
								data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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
								print("")
							else:
								mc.set(key,1,86400)
								link='https://www.binance.com/en/trade/pro/'+csymbol
								alert_type=' ::EXTREME RSI ALERT + '+str(percent)+'%:: '					
							
								data_add="5 Mins: "+str(five_mins)+"%, 10 Mins: "+str(ten_mins)+"%, 15 Mins: "+str(fifteen_mins)+"%, 30 Mins: "+str(thirty_mins)+"%, 1H: "+str(one_hours)+str('%')+", 2H: "+str(two_hours)+str('%')+", 3H: "+str(three_hours)+str('%')+"\n4H: "+str(four_hours)+str('%')+", 5H: "+str(five_hours)+" 6H: "+str(six_hours)+", 12H: "+str(twelve_hours)+str('. %')
								data=str(symbol)+str(alert_type)+"\nPrice: "+str(close)+' ('+str(percent)+'%)' + "\nSpread: "+str(pdiff)+"%\nBTC Price: "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)
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

				else:	
					print("no conditions met: "+str(symbol))

while True:
	try:
		main()
		print("Ended cycle\n")
		quit()
		time.sleep(60)
	except:
		print("error")
		time.sleep(30)
