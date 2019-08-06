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

def gotbot(symbol):
	
	redis_server = redis.Redis(host='localhost', port=6379, db=0)
	botlist=redis_server.smembers("botlist")
	
	seen=0
	for bot in botlist:
		bot=bot.decode('utf-8')
		if bot==symbol:
			seen=1
	return(seen)
	
def broadcast_moon(chatid,text):
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')
	telegram_id=config['binance']['MOON_TELEGRAM_ID']
	token = telegram_id
	url = "https://api.telegram.org/"+ token + "/sendMessage?chat_id=" + chatid+"&text="+str(text)+"&parse_mode=HTML"
	r=requests.get(url)
	html = r.content	

def broadcast(chatid,text):
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')
	telegram_id=config['binance']['TELEGRAM_ID']
	token = telegram_id
	url = "https://api.telegram.org/"+ token + "/sendMessage?chat_id=" + chatid+"&text="+str(text)+"&parse_mode=HTML"
	r=requests.get(url)
	html = r.content
	print(html)
	
def fetch_prices(exchange, symbol):
	ticker = exchange.fetch_ticker(symbol.upper())
	return(ticker)
   

def fetch_last_order(exchange,symbol):
	ret=exchange.fetch_closed_orders (symbol, 1,"");
	if ret:
		data=ret[-1]['info']
		side=data['side']
		price=data['price']
		#print("returning: 1")
	else:
		#print("returning: 0")
		data=0
	return data

def die():
	sys.exit("fuck")

def get_price(pair,start_ts,end_ts):

	p=0
	#try:
	start_ts=start_ts+"000"
	url="https://api.binance.com/api/v1/klines?symbol="+pair+"&startTime="+str(start_ts)+"&interval=1m&limit=100"
	print(url)
	r=requests.get(url)
	res = (r.content.strip())
	print("R: "+str(res))
	status = r.status_code
	print(status)
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

def get_sentiment(symbol):
	
	exchange=nickbot.get_exchange()	
	ts_now = datetime.datetime.now()
	ts_now_ts=int(time.mktime(ts_now.timetuple()))	

	ts_5mins = ts_now - datetime.timedelta(seconds=300)
	ts_5mins_ts=int(time.mktime(ts_5mins.timetuple()))
	tsd=datetime.datetime.fromtimestamp(ts_5mins_ts).strftime("%Y-%m-%d %H:%M:%S")

	buys=0
	sells=0
	total=0
	slast_price=0
	price_up=0
	price_down=0

	trades=exchange.fetchTrades (symbol)
	for trade in trades:
		side=trade['side']
		sprice=float(trade['info']['p'])

		if side=='buy':
			buys+=1
		else:
			sells+=1

		if slast_price>0 and sprice>slast_price:
			price_up+=1
	
		if slast_price>0 and sprice<slast_price:
			price_down+=1		

		slast_price=sprice
		total+=1	
	
	trade_total=price_up+price_down
	price_up_ratio=100-abs(diff_percent(trade_total,price_up))
	price_down_ratio=100-abs(diff_percent(trade_total,price_down))
	buy_ratio=100-abs(diff_percent(total,buys))
	sell_ratio=100-abs(diff_percent(total,sells))

	sell_ratio=round(sell_ratio,2)
	buy_ratio=round(buy_ratio,2)

	redis_server.set('SENT-BUYS',str(buy_ratio))
	redis_server.set('SENT-SELLS',str(sell_ratio))
	redis_server.set('SENT-PRICE-UP-RATIO',str(price_up_ratio))

	dat="\n<b>:::SENTIMENT DATA:::\nBUYS:</b> "+str(buys)+' ('+str(buy_ratio)+'%)\n<b>SELLS:</b> '+str(sells)+' ('+str(sell_ratio)+'%)'+"\n"+'<b>PRICE UP RATIO:</b> '+str(price_up)+' ('+str(price_up_ratio)+'%)'
	return(dat)

def mojo(pair,price_now):

	mc = memcache.Client(['127.0.0.1:11211'], debug=0)

	blank=1
	
	ts_now = datetime.datetime.now()
	ts_now_ts=int(time.mktime(ts_now.timetuple()))	
	ts_now_human=datetime.datetime.fromtimestamp(ts_now_ts).strftime("%Y-%m-%d %H:%M:%S")

	key=str(pair)+str("pkey-30secs")
	if(mc.get(key)):
		mc.delete(key)

	ts_30secs = ts_now - datetime.timedelta(seconds=30)
	ts_30secs_ts=int(time.mktime(ts_30secs.timetuple()))
	tsd=datetime.datetime.fromtimestamp(ts_30secs_ts).strftime("%Y-%m-%d %H:%M:%S")
	
	price_30_secs_ago=get_price(pair,str(ts_30secs_ts),str(ts_now_ts))
	if price_30_secs_ago:
		price_30_secs_ago=float(price_30_secs_ago)
		print("P30SA")
		print(price_30_secs_ago)
		price_now=float(price_now)
		price_diff=diff_percent(price_30_secs_ago,price_now)
		if price_diff:		
			mc.set(key,price_diff,86400)
			print("ALERTS::: Price Now: "+str(ts_now_human)+" "+str(price_now)+" 30 Seconds Ago "+str(tsd)+" : "+str(price_30_secs_ago)+" Diff %: "+str(price_diff))

	key=str(pair)+str("pkey-1mins")
	if(mc.get(key)):
		mc.delete(key)
	
	ts_1mins = ts_now - datetime.timedelta(seconds=60)
	ts_1mins_ts=int(time.mktime(ts_1mins.timetuple()))
	tsd=datetime.datetime.fromtimestamp(ts_1mins_ts).strftime("%Y-%m-%d %H:%M:%S")
	
	price_1_mins_ago=get_price(pair,str(ts_1mins_ts),str(ts_now_ts))
	if price_1_mins_ago:
		price_1_mins_ago=float(price_1_mins_ago)
		print("P1MA")
		print(price_1_mins_ago)
		price_now=float(price_now)
		price_diff=diff_percent(price_1_mins_ago,price_now)
		if price_diff:		
			mc.set(key,price_diff,86400)
			print("ALERTS::: Price Now: "+str(ts_now_human)+" "+str(price_now)+" 1 Mins Ago "+str(tsd)+" : "+str(price_1_mins_ago)+" Diff %: "+str(price_diff))

	key=str(pair)+str("pkey-3mins")
	if(mc.get(key)):
		mc.delete(key)

	ts_3mins = ts_now - datetime.timedelta(seconds=180)
	ts_3mins_ts=int(time.mktime(ts_3mins.timetuple()))
	tsd=datetime.datetime.fromtimestamp(ts_3mins_ts).strftime("%Y-%m-%d %H:%M:%S")
	
	price_3_mins_ago=get_price(pair,str(ts_3mins_ts),str(ts_now_ts))
	if price_3_mins_ago:
		price_3_mins_ago=float(price_3_mins_ago)
		print("P3MA")
		print(price_3_mins_ago)
		price_now=float(price_now)
		price_diff=diff_percent(price_3_mins_ago,price_now)
		if price_diff:		
			mc.set(key,price_diff,86400)

	key=str(pair)+str("pkey-5mins")
	if(mc.get(key)):
		mc.delete(key)
		print("ALERTS::: Price Now: "+str(ts_now_human)+" "+str(price_now)+" 3 Mins Ago "+str(tsd)+" : "+str(price_3_mins_ago)+" Diff %: "+str(price_diff))

	ts_5mins = ts_now - datetime.timedelta(seconds=300)
	ts_5mins_ts=int(time.mktime(ts_5mins.timetuple()))
	tsd=datetime.datetime.fromtimestamp(ts_5mins_ts).strftime("%Y-%m-%d %H:%M:%S")
	
	price_5_mins_ago=get_price(pair,str(ts_5mins_ts),str(ts_now_ts))
	if price_5_mins_ago:
		price_5_mins_ago=float(price_5_mins_ago)
		print("P5MA")
		print(price_5_mins_ago)
		price_now=float(price_now)
		price_diff=diff_percent(price_5_mins_ago,price_now)
		if price_diff:		
			mc.set(key,price_diff,86400)
			print("ALERTS::: Price Now: "+str(ts_now_human)+" "+str(price_now)+" 5 Mins Ago "+str(tsd)+" : "+str(price_5_mins_ago)+" Diff %: "+str(price_diff))

	key=str(pair)+str("pkey-15mins")
	if(mc.get(key)):
		mc.delete(key)
	
	ts_15mins = ts_now - datetime.timedelta(seconds=900)
	ts_15mins_ts=int(time.mktime(ts_15mins.timetuple()))
	tsd=datetime.datetime.fromtimestamp(ts_15mins_ts).strftime("%Y-%m-%d %H:%M:%S")
	
	price_15_mins_ago=get_price(pair,str(ts_15mins_ts),str(ts_now_ts))
	if price_15_mins_ago:
		price_15_mins_ago=float(price_15_mins_ago)
		print("P15MA")
		print(price_15_mins_ago)
		price_now=float(price_now)
		price_diff=diff_percent(price_15_mins_ago,price_now)
		if price_diff:		
			mc.set(key,price_diff,86400)
			print("ALERTS::: Price Now: "+str(ts_now_human)+" "+str(price_now)+" 1 Hour Ago "+str(tsd)+" : "+str(price_15_mins_ago)+" Diff %: "+str(price_diff))
	
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
			threee_hour_up_perc=price_diff
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

mojo('WTCBTC','0.0002012')
sys.exit("c")
def get_rsi(pair,interval):

	arr = []
	out = []
	fin = []
	url="https://api.binance.com/api/v1/klines?symbol="+pair+"&interval="+interval+"&limit=500"
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
		errors=0
		btc_price=float(tickers['BTC/USDT']['close'])
		btc_percent=float(tickers['BTC/USDT']['percentage'])
		last_price=0
		symbol=tickers[coin]['info']['symbol']
		print("SDBS: "+str(coin))
		csymbol=coin
		csymbol=csymbol.replace("/","_",1)
		det=int(0)
		today = str(date.today())
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
		rsi_3m=0
		rsi_5m=0
		price_jump=0
		alerts=""
		
		#if 'USD' in symbol:
		#	min_vol=1000000
		#	skip=0
		#elif 'PAX' in symbol:
		#	min_vol=1000000
		#	skip=0
		#elif 'BTC' in symbol:
		#	min_vol=500
		#	skip=0
		#elif 'BNB' in symbol:
		#	min_vol=50000
		#	skip=0
		#elif 'ETH' in symbol:
		#	min_vol=1000	
		#	skip=0
		vol24=float(nickbot.v24_usd_alerts_cached(exchange,coin,qv))
		vol24=round(vol24,2)

		if vol24>500000:
			skip=0
		else:
			skip=1
			print(symbol+" VOL TO LOW: "+str(vol24))
		#	timetrades=float(nickbot.trade_time(exchange,coin))
		#	if timetrades>60:
		#		print(str(symbol)+"TRADES TOOK TO LONG")
		#		skip=1
		#else:
		#	print(symbol+" VOL TO LOW: "+str(vol24))
		#	skip=1
		#skip=0
		if 'BCHSV' in symbol:
			continue
			
		if low==0 or high==0:
			print("Skipping LH")
			continue
		print(symbol)
		
		redis_key="ASLASTPRICE-"+symbol
		if redis_server.get(redis_key):
			last_price=float(redis_server.get(redis_key))
			first=0
			darr = [last_price,price]
			for a, b in zip(darr[::1], darr[1::1]):
				price_jump=100 * (b - a) / a
				price_jump=round(price_jump,2)
		else:
			first=1
		
		prices = [low,high]
		for a, b in zip(prices[::1], prices[1::1]):
			pdiff=100 * (b - a) / a
			
		pdiff=round(pdiff,2)
				
		spread=pdiff
			
		nickbot.log_binance(symbol,price,percent,spread,low,high,qv,btc_price,btc_percent)

		print("DBPercent: "+str(percent)+" Price jump: "+str(price_jump)+" Price: "+str(price)+" Last Price: "+str(last_price)+" BTC PRICE: "+str(btc_price)+" BTC PER: "+str(btc_percent))
			
		if skip!=1:
			
			pair=symbol
			
			#if percent>1 and last_price>0 and price_jump>0.01 and price>last_price or percent>1 and first==1:
			if percent>1 and last_price>0 and price>last_price or percent>1 and first==1:

				print("ALERTS DEBUG::: LP: "+str(last_price)+" P: "+str(price)+" D: "+str(price_jump))
	
				key = str(date.today())+str('ALERTSDBN2')+str(csymbol)
				if mc.get(key):
					#print("Seen Ignoring it")
					dprint=2
				else:	
					det=int(1)
					mc.set(key,1,60)
					
					try:
						rsi_3m=get_rsi(symbol,'3m')
						rsi_5m=get_rsi(symbol,'5m')
						rsi_stats="<b>RSI 3M:</b> "+str(rsi_3m)+" <b>RSI 5M:</b> "+str(rsi_5m)
					except:
						print("Rsi is the issue")
						errors=1					
					
					#try:
					mojo(symbol,close)
					#except:
					#	#print("Error getting Trades")
					#	errors=1
									
					#print("DBERRORS: "+str(errors))		
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
				
					key=str(pair)+str("pkey-15mins")
					if mc.get(key):
						fifteen_mins=mc.get(key)
					else:
						fifteen_mins=0

					key=str(pair)+str("pkey-30secs")
					if mc.get(key):
						thirty_secs=mc.get(key)
					else:
						thirty_secs=0

					key=str(pair)+str("pkey-1mins")
					if mc.get(key):
						one_mins=mc.get(key)
					else:
						one_mins=0
						
					key=str(pair)+str("pkey-3mins")
					if mc.get(key):
						three_mins=mc.get(key)
					else:
						three_mins=0
						
					key=str(pair)+str("pkey-5mins")
					if mc.get(key):
						five_mins=mc.get(key)
					else:
						five_mins=0
					
					#Lets log the price every 60 seconds to look for jumps
					redis_key="ASLASTPRICE-"+symbol
					if redis_server.get(redis_key):
						last_price=redis_server.get(redis_key)
						
					if errors==0 and one_hours>0.05 and float(price)>float(last_price) or errors==0 and one_hours>0.05 and first==1:
						
						redis_key="ASLASTPRICE-"+symbol
						redis_server.setex(redis_key,3600,price)
											
						link='https://www.binance.com/en/trade/pro/'+csymbol
						alert_type=' PRICE ALERT: '+str(twelve_hours)+'%:::'					
							
						data_add="<b>30S:</b> "+str(thirty_secs)+str('%')+", <b>1M:</b> "+str(one_mins)+str('%')+", <b>3M:</b> "+str(three_mins)+str('%')+",<b>5M:</b> "+str(five_mins)+str('%')+", <b>15M:</b> "+str(fifteen_mins)+str('%')+", <b>1H:</b> "+str(one_hours)+str('%')+", <b>3H:</b> "+str(three_hours)+str('%')+", <b>6H:</b> "+str(six_hours)+"%, <b>12H:</b> "+str(twelve_hours)+str('%')
						data='<b>:::'+str(symbol)+str(alert_type)+"\nPrice: </b>"+str(close)+' ('+str(twelve_hours)+'%)'+"\n<b>Volume 24H: </b>"+str(vol24) + "\n<b>Spread:</b> "+str(pdiff)+"%\n<b>BTC Price:</b> "+str(btc_price)+' ('+str(btc_percent)+'%'+')'+"\n"+str(rsi_stats)+"\n"+str(data_add)+"\n"+str(link)

						timestamp=time.time()
						ts_raw=timestamp
						date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
						date_today=str(date.today())							
						alert_key_all=str(date_today)+'-NALERTddsSKdNNBNS'+str(symbol)
						alert_list_today=str(date_today)+'-ALERTLIST'

						symbol_ids=str(symbol)+'-IDS'
						symbol_hash_detailed=str(symbol)+'-'+str(ts_raw)
						
						a=0
						lp=0
								
						alerts=redis_server.lrange(alert_key_all,0,1000)
												
						adata=""
						for alert in alerts:
							alert=alert.decode('utf-8')
							vDate, vPrice, vPer = alert.split("\t")
							if float(vPrice)>float(lp):
								adata=adata+"\n"+str(vDate)+"\t<b>"+str(vPrice)+"</b>\t<b>"+str(vPer)+"</b>"							
								lp=vPrice
							else:
								adata=adata+"\n"+str(vDate)+"\t<i>"+str(vPrice)+"</i>\t"+str(vPer)
							a=1
						
						alerts_key=str(symbol)+str(date_today)+'-ALERTCYCLES'
						alerts_today=redis_server.incr(alerts_key)
						
						#Lets also make a memcache # of alerts so we can have auto expiry time, lets set expiry to two hours "7200 seconds rolling"
						mckey=str(pair)+str("MCALERTS")
						mc.incr(mckey,10800)
						
						grab_mc_counter=0
						
						if mc.get(mckey):
							grab_mc_counter=mc.get(mckey)

						moon=0
						if grab_mc_counter>=5 and percent>3 and fifteen_mins>2:
							mooning=str(symbol)+'-MOONING'
							moon=1
							
						sent=get_sentiment(coin)
						data=data+"\n"+str(sent)
						if a==1:
							data=data+"\n\n<b>TODAYS ALERTS:</b>"+str(adata)

						data=str(data)+"\n\n<b>ALERTS TODAY:</b> "+str(alerts_today)

						data=str(data)+"\n\nThis Alert Was Sent AT: "+str(date_time)+" GMT";
						
						
						sent_buys_percent=float(redis_server.get('SENT-BUYS'))
						sent_sells_percent=float(redis_server.get('SENT-SELLS'))
						sent_price_up_ratio=float(redis_server.get('SENT-PRICE-UP-RATIO'))
						
						nickbot.log_alert(symbol,price,percent,spread,sent_buys_percent,sent_sells_percent,sent_price_up_ratio,alerts_today,fifteen_mins,one_hours,three_hours,six_hours,twelve_hours,link)
							
						#print("DBBBBB")
						#print("LP: ")
						#print(last_price)
						#print("DBBBBB:")
						#print(price)
						pdata=str(date_time)+"\t"+str(price)+"\t"+'('+str(twelve_hours)+'%)'
						
						alert_key_nd=str(coin)+'-ALL-ALERTS'
						redis_server.rpush(alert_key_all,pdata)
						redis_server.rpush(alert_key_nd,pdata)
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
		
						#print("Writing detailed alert hash data to: "+str(symbol_hash_detailed))
						#print(detail_hash)
						redis_server.hmset(symbol_hash_detailed, detail_hash)

						#print("Pushing coin to todays alert list: "+str(symbol))
						#print(data)
						
						#print("DB RED: set "+str(redis_key)+' last_price'+str(price))
						
						#Blacklist from rebuying a coin for 30 minutes
						blacklisted=0
						blacklisted_key=redis_key+"-BLACKLIST"
						
						rk="bconfig-"+symbol
						blacklisted_key=rk+"-BLACKLIST"

						if redis_server.get(blacklisted_key):
							blacklisted=1
	
						if one_mins>=0.3 or fifteen_mins>1:
							dtoday=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
							moonkey=str(dtoday)+'-mooning'
							broadcast_moon('506872080',data)	
							broadcast_moon('446619309',data)
							print("Sent a moon shot alert: key:"+str(moonkey))
							redis_server.sadd(moonkey, symbol)
							
							symbol=symbol.upper()
							ticker_symbol=symbol
							if symbol.endswith('BTC'):
								ticker_symbol = replace_last(ticker_symbol, '/BTC', '')
								trading_to=str('BTC')
							elif symbol.endswith('USDT'):
								ticker_symbol = replace_last(ticker_symbol, '/USDT', '')
								trading_to=str('USDT')
							elif symbol.endswith('BNB'):
								ticker_symbol = replace_last(ticker_symbol, '/BNB', '')
								trading_to=str('BNB')
							elif symbol.endswith('TUSD'):
								ticker_symbol = replace_last(ticker_symbol, '/TUSD', '')
								trading_to=str('TUSD')
							elif symbol.endswith('USD'):
								ticker_symbol = replace_last(ticker_symbol, '/USD', '')
								trading_to=str('USD')
							elif symbol.endswith('USDC'):
								ticker_symbol = replace_last(ticker_symbol, '/USDC', '')
								trading_to=str('USDC')
							elif symbol.endswith('PAX'):
								ticker_symbol = replace_last(ticker_symbol, '/PAX', '')
								trading_to=str('PAX')
							elif symbol.endswith('USDS'):
								ticker_symbol = replace_last(ticker_symbol, '/USDS', '')
								trading_to=str('USDS')
							elif symbol.endswith('ETH'):
								ticker_symbol = replace_last(ticker_symbol, '/ETH', '')
								trading_to=str('ETH')
							trading_from=ticker_symbol
							print("Debug TS: "+str(ticker_symbol))
							#broadcast_moon('506872080',ticker_symbol)	

							moonkey2=str(dtoday)+'-mooning-np'
							redis_server.sadd(moonkey2, ticker_symbol)

							max_bots=10
							#$100 bucks budget per bot
							budget=100
							#Lets Work out the number of units here
							bankinfo=nickbot.work_units(coin,budget)
							units=float(bankinfo["units"])
							balance_needed=float(bankinfo["balance_needed"])
							#Lets check the whole bank roll to see if we got enuff dough for the trade
							balances=exchange.fetch_balance ()
							bank_balance=float(format(balances[trading_to]['total'],'.8f'))
							if bank_balance>=balance_needed:
								
								#lets check we don't have a bot allready running for this shit and that we didn't exceed max amount of bots
								botlist=redis_server.smembers("botlist")
								bots_running=int(len(botlist))
								if gotbot(coin)!=1 and bots_running<=max_bots:					
									bcdb='lets spawn an auto trader bot for '+str(coin)+' budget: '+str(budget)+' Units: '+str(units)
									broadcast_moon('506872080',bcdb)
									broadcast_moon('446619309',data)
									rsi_symbol=str(symbol)
									symbol=str(coin)
									buy_pos=int(0)
									sell_pos=int(0)
									stoploss_percent=float(4)
									use_stoploss=int(1)
									candle_size=str('5m')
									safeguard_percent=float(2)
									rsi_buy=float(20)
									rsi_sell=float(80)
									instant_market_buy=str('yes')
									enable_buybacks=str('no')
									enable_safeguard=str('no')
									force_buy=str('yes')
									force_sell=str('no')
									live=str('yes')
									trading_on=str('Binance')
									key=str(symbol)+'-SYSTEM-STOPLOSS'
									if(mc.get(key)):
										mc.delete(key)
									nickbot.auto_spawn(trading_on, rsi_symbol, symbol, units, ticker_symbol, trading_to, buy_pos, sell_pos, stoploss_percent, use_stoploss, candle_size, safeguard_percent, rsi_buy, rsi_sell, instant_market_buy, enable_buybacks, enable_safeguard, force_buy, force_sell, live)
						print("Sending!!!.."+str(data))
						broadcast('506872080',data)	
						broadcast('693711905',data)	
						broadcast('420441454',data)	
						broadcast('446619309',data)	
						broadcast('490148813',data)	
						broadcast('110880375',data)	
						broadcast('699448304',data)	
						broadcast('593213791',data)	
						broadcast('543018578',data)
						broadcast('503482955',data)
						broadcast('429640253',data)
						broadcast('862193134',data)
						
						time.sleep(0.5)	
		
e=0
while True:
	#try:
	main()
	print("Cycle !!!!!\n")
	#except:
	#e=1
	time.sleep(10)
