import os
import sys, argparse
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
import redis
import configparser
from datetime import datetime
import subprocess
import heapq

r = redis.Redis(host='localhost', port=6379, db=0)

config = configparser.ConfigParser()

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib'
sys.path.append(root + '/python')

import talib
import numpy as np
import ccxt  # noqa: E402

def log_db(symbol,rsi_symbol,trade_from,trade_to,buy_price,units,bid,last,ask,open,close,high,low):

	key=str(symbol)+'-SYSTEM-STOPLOSS'
	if mc.get(key):
		stoploss_price=float(mc.get(key))
	
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')

	mysql_username=config['mysql']['MYSQL_USERNAME']
	mysql_password=config['mysql']['MYSQL_PASSWORD']
	mysql_hostname=config['mysql']['MYSQL_HOSTNAME']
	mysql_database=config['mysql']['MYSQL_DATABASE']

	market_price=float(close)
	
	profit_per_unit=market_price-buy_price
	profit=float(profit_per_unit*units)
	profit=round(profit,8)
	prices = [buy_price,market_price]
	for a, b in zip(prices[::1], prices[1::1]):
		profit_percent=100 * (b - a) / a
		profit_percent=round(profit_percent,2)

	total_invest=units*buy_price
	total_now=units*market_price	

	total_now=float(total_now)
	total_now=round(total_now,8)

	db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysql_database)
	cursor = db.cursor()
	
	sql = """
		INSERT INTO at_history(date,date_time,timestamp,symbol,rsi_symbol,trade_from,trade_to,buy_price,units,stoploss_price,profit,profit_percent,total_invest,total_now,bid,last,ask,open,close,high,low)
		VALUES (CURRENT_DATE(),NOW(),UNIX_TIMESTAMP(),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
	"""
	print(sql)
	cursor.execute(sql,(symbol,rsi_symbol,trade_from,trade_to,buy_price,units,stoploss_price,profit,profit_percent,total_invest,total_now,bid,last,ask,open,close,high,low))
	db.close()
	
def log_redis(redis_key,message,c):

	if c>10000:
		print(r.lpop(redis_key))
		
	now = datetime.now()
	ts = datetime.timestamp(now)
	running=datetime.fromtimestamp(ts).strftime("%Y-%m-%d %I:%M:%S")

	message=str(running)+"\t"+str(message)
	print("Writing to redis: "+str(redis_key))
	print(message)
	r.rpush(redis_key,message)

def fetch_wall_book(exchange,symbol,type,qlimit):
	limit = 1000
	ret=exchange.fetch_order_book(symbol, limit)

	if type=='bids':
		bids=ret['bids']
		return bids
	else:
		asks=ret['asks']
		return asks

def walls(symbol):
	
	symbol=symbol.upper()
	exchange=get_exchange()
	buy_book=fetch_wall_book(exchange,symbol,'bids','500')
	sell_book=fetch_wall_book(exchange,symbol,'asks','500')

	
	buy_dic={}
	sell_dic={}
	
	for k,v in buy_book:
		buy_dic[k]=v

	for k,v in sell_book:
		sell_dic[k]=v
				
	buy_walls=heapq.nlargest(20, buy_dic.items(), key=itemgetter(1))
	sell_walls=heapq.nlargest(20, sell_dic.items(), key=itemgetter(1))
	
	message="<b>INFO:: - "+str(symbol)+"WALL INTEL:</b>\n\n"
	
	message=message+"<b>BUY WALLS ('SUPPORT')</b>\n"
	
	for k,v in sorted(buy_walls):
		message=message+"<b>PRICE:</b> "+str(k)+"\t<b>VOLUME:</b> "+str(v)+"\n"

	message=message+"\n<b>SELL WALLS ('RESISTANCE')</b>'\n"
	for k,v in sorted(sell_walls):
		message=message+"<b>PRICE:</b> "+str(k)+"\t<b>VOLUME:</b> "+str(v)+"\n"
		
	broadcast(message)

def get_exchange():
	
	#Read in our apikeys and accounts
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')
	conf=config['binance']
	
	binance_api_key=config['binance']['API_KEY']
	binance_api_secret=config['binance']['API_SECRET']
	
	members=r.smembers("botlist")
	sizeof=len(members)
	throttle=sizeof*1200

	exchange = ccxt.binance({
    'apiKey': binance_api_key,
    'secret': binance_api_secret,
    'enableRateLimit': True,
    'rateLimit': throttle,
    'verbose': False,  # switch it to False if you don't want the HTTP log
	})
	return(exchange)

exchange=get_exchange()

def delete_bot(symbol):
	bot_name=symbol
	r.srem("botlist", bot_name)
	r.delete(bot_name)
	redis_key="bconfig-"+bot_name
	all_keys = list(r.hgetall(redis_key).keys())
	r.hdel(redis_key, "*")	
	config = configparser.ConfigParser()
	config_file='/home/crypto/cryptologic/pid-configs/init.ini'
	config.read(config_file)
	
	bot_section='watcher:'+str(bot_name)
	config.remove_section(bot_section)
	
	for line in config:
		print(line)
	with open(config_file, 'w') as configfile:
	
		print("debug")
		print(config)
		config.write(configfile)
		
		print("Write Config File to: "+str(config_file))
		print("Wrote: "+str(configfile))
	
	subprocess.run(["/usr/bin/circusctl", "reloadconfig"])

def broadcast(text):

	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')
	telegram_id=config['binance']['TELEGRAM_ID']
	chatid=config['binance']['TRADES_CHANNEL']
	print(chatid)
	token = telegram_id
	timestamp=time.time()
	date_time=datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
	text="<b>"+str(date_time)+"</b>\t"+str(text)
	url = "https://api.telegram.org/"+ token + "/sendMessage?chat_id=" + chatid+"&text="+text+"&parse_mode=HTML"
	r=requests.get(url)
	html = r.content
	print(html)
	
def fetch_prices(exchange, symbol):
	ticker = exchange.fetch_ticker(symbol.upper())
	return(ticker)
   

def fetch_last_order(exchange,symbol):
	print("passed: "+str(symbol))
	ret=exchange.fetch_closed_orders (symbol, 1);
	print(ret)
	if ret:
		
		data=ret[-1]['info']
		side=data['side']
		price=float(data['price'])
		print("returning: 1")
		return data
	else:
		print("returning: 0")
		data=0
		return data

def die():
	sys.exit("fuck")


def get_rsi(pair,interval):

	try:
		arr = []
		out = []
		fin = []
		url="https://api.binance.com/api/v1/klines?symbol="+pair+"&interval="+interval+"&limit=100"
		print(url)
		r=requests.get(url)
		res = (r.content.strip())
		status = r.status_code
		rsi_status=''
		trades = json.loads(res.decode('utf-8'))

		for trade in trades:
			open_price=float(trade[0])
			close_price=float(trade[4])
			high_price=float(trade[2])
			low_price=float(trade[3])
			if close_price>0:
				arr.append(close_price)
			

		np_arr = np.array(arr,dtype=float)
		output=talib.RSI(np_arr,timeperiod=14)

		for chkput in output:
			if chkput>0:
				fin.append(chkput)
		
		rsi=float(fin[-1])
		rsi=round(rsi)
		return(rsi)
	except:
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
		
def main(exchange,symbol,c):
	
	mc = memcache.Client(['127.0.0.1:11211'], debug=0)

	conn = redis.Redis('127.0.0.1')

	redis_log="LOG-"+symbol
	redis_trade_log="TRADELOG-"+symbol
	redis_key="bconfig-"+symbol
	redis_rsi_log="RSILOG-"+symbol
	ret=0
	trading_on=conn.hget(redis_key,"trading_on")
	trading_on=trading_on.decode('utf-8')
	rsi_symbol=conn.hget(redis_key,"rsi_symbol")
	rsi_symbol=rsi_symbol.decode('utf-8')
	symbol=conn.hget(redis_key,"symbol")
	symbol=symbol.decode('utf-8')
	units=conn.hget(redis_key,"units")
	units=units.decode('utf-8')
	trade_from=conn.hget(redis_key,"trade_from")
	trade_from=trade_from.decode('utf-8')
	trade_to=conn.hget(redis_key,"trade_to")
	trade_to=trade_to.decode('utf-8')
	buy_pos=conn.hget(redis_key,"buy_pos")
	buy_pos=buy_pos.decode('utf-8')	
	sell_pos=conn.hget(redis_key,"sell_pos")
	sell_pos=sell_pos.decode('utf-8')
	stoploss_percent=conn.hget(redis_key,"stoploss_percent")
	stoploss_percent=stoploss_percent.decode('utf-8')
	safeguard_percent=conn.hget(redis_key,"safeguard_percent")
	safeguard_percent=safeguard_percent.decode('utf-8')
	use_stoploss=conn.hget(redis_key,"use_stoploss")
	use_stoploss=use_stoploss.decode('utf-8')
	candle_size=conn.hget(redis_key,"candle_size")
	candle_size=candle_size.decode('utf-8')
	rsi_buy=conn.hget(redis_key,"rsi_buy")
	rsi_buy=rsi_buy.decode('utf-8')
	rsi_sell=conn.hget(redis_key,"rsi_sell")
	rsi_sell=rsi_sell.decode('utf-8')
	live=conn.hget(redis_key,"live")
	live=live.decode('utf-8')
	enable_safeguard=conn.hget(redis_key,"enable_safeguard")
	enable_safeguard=enable_safeguard.decode('utf-8')
	enable_buybacks=conn.hget(redis_key,"enable_buybacks")
	if enable_buybacks:
		enable_buybacks=enable_buybacks.decode('utf-8')
	rsi_sell=float(rsi_sell)
	rsi_buy=float(rsi_buy)
	stoploss_percent=float(stoploss_percent)
	safeguard_percent=float(safeguard_percent)
	use_stoploss=str(use_stoploss)
	if use_stoploss=='1':
		use_stoploss=str('yes')
	units=float(units)
	sell_pos=int(sell_pos)
	buy_pos=int(buy_pos)
	message="Exchange: "+trading_on+"\tExchange: "+trading_on+"\tTrade Pair: "+str(symbol)+"\tUnits: "+str(units)+"\tBuy Book Scrape Position: "+str(buy_pos)+"\tSell Book Scrape Position: "+str(sell_pos)+"\tRSI Buy: "+str(rsi_buy)+"\tRSI Sell: "+str(rsi_sell)+"\tStoploss Percent: "+str(stoploss_percent)+"\tSafeguard Percent: "+str(safeguard_percent)+"\tEnable Safeguard: "+str(enable_safeguard)+"\tCandle Size: "+candle_size+"\tUse Stoploss: "+str(use_stoploss)+"\tLive Trading Enabled: "+live

	if c==0:
		log_redis(redis_log,message,c)
		print(message)

	key=str(symbol)+'-ORIGINAL-SL'	
	r.setex(key,3600,stoploss_percent)

	ignore_rsi=0
	sleep_for_after_stoploss_executed=600
	
	#If the manual bot is doing sell off then dont interfere
	key=str(symbol)+'-PAUSED'	
	if(mc.get(key)):
		#time.sleep(30)
		return(1)
	
	key=str(symbol)+'-SL'	
	if(mc.get(key)):
		ignore_rsi=1
		print("Got Stoploss key\n")
		mc.delete(key)
	
	original_stoploss_price=0
	key=str(symbol)+'-ORIGINAL-STOPLOSS-PRICE'	
	if(mc.get(key)):
		original_stoploss_price=float(mc.get(key))
		print(original_stoploss_price)
		
	exchange_cut=0.007500;
	
	tkey="seen"+str(symbol)
	orders = exchange.fetch_open_orders(symbol,1)
	
	open_order=len(orders)
	
	ticker = exchange.fetch_ticker(symbol.upper())
	bid=float(ticker['bid'])
	last=float(ticker['last'])
	ask=float(ticker['ask'])
	open=float(ticker['open'])
	close=float(ticker['close'])
	high=float(ticker['high'])
	low=float(ticker['low'])
	
	key=str(symbol)+'-LAST-PRICE'	
	#mc.set(key,close,86400)
	r.setex(key,3600,close)

	lo_key="last_order-"+str(symbol)
	if mc.get(lo_key):
		last_array=mc.get(lo_key)
		last_price=float(last_array['price'])
		last_type=last_array['side']
		buy_price=last_price
	else:
		#Cache last order in ram for 60 seconds to speed up api calls
		print("Db: lT: "+str(symbol))
		last_array=fetch_last_order(exchange,symbol)
		if last_array!=0:
			last_price=float(last_array['price'])
			last_type=last_array['side']
			buy_price=last_price
			mc.set(lo_key,last_array,60)
		else:
			last_type='NULL'

	if open_order:
		for order in orders:
			order_symbol=order['info']['symbol']
			if order_symbol==rsi_symbol:
				open_type=order['info']['side']
				open_price=order['price']
				open_filled=order['filled']
				open_remaining=order['remaining']
				open_fee=order['fee']
				order_id=order['info']['orderId']				
				order_timestamp=order['timestamp']/1000
				start_time=order_timestamp
				elapsed = time.time() - start_time
				elapsed=round(elapsed)
				
				message="<b>ALERT:: - "+str(symbol)+" OPEN ORDER\tTYPE:</b> " +str(open_type)+"\n<b>OPEN FOR: </b> "+str(elapsed)+" Seconds\n"+"<b>PRICE:</b> "+str(open_price)+ "\n<b>FILLED:</b> "+str(open_filled)+"/"+str(open_remaining)+"\n<b>ORDER ID:</b> "+str(order_id)+"\t<b>TICKER\tLAST:</b> "+str(last)+" <b>BID:</b> "+str(bid)+" <b>ASK:</b> "+str(ask)
				if open_type=='BUY' and float(elapsed)>1200:
					exchange.cancelOrder(order_id,symbol)
					delete_bot(symbol)		
					message=message+"\n\n<b>CANCELLING ORDER TO MUCH TIME ELAPSED</b>\n"
					broadcast(message)
				
				oo_key=str(symbol)+'-OOssTMPS'	
				if not (mc.get(oo_key)):
					mc.set(oo_key,1,1800)			
					broadcast(message)
					log_redis(redis_log,message,c)
					print(message)
		return("open")

	print("LT: "+str(last_type))
	if use_stoploss=="yes" or use_stoploss==1:
			
		if last_type=='BUY':
					
			stoploss=last_price/100*stoploss_percent
			stoploss_price=last_price-stoploss

			print("Debug SL: "+str(stoploss_percent))
			print("Debug SLP: "+str(stoploss_price))
			print("Debug LP: "+str(last_price))
			print("Debug OSL: "+str(original_stoploss_price))
						
			### ADD SMART STOPLOSS CODE
			key=str(symbol)+'-SYSTEM-STOPLOSS'
			if mc.get(key):
				stoploss_price=float(mc.get(key))
				sell_price=stoploss_price
			else:
				book=fetch_order_book(exchange,symbol,'bids',1)
				sell_price=float(book[0][0])

			message="Last buy price: "+str(last_price)+"\tStoploss price: "+str(stoploss_price)+"\tmarket price: "+str(last)
			log_redis(redis_log,message,c)
			log_db(symbol,rsi_symbol,trade_from,trade_to,buy_price,units,bid,last,ask,open,close,high,low)
			print(message)

			if last <= stoploss_price or last <= original_stoploss_price:

				book=fetch_order_book(exchange,symbol,'bids',1)
				sell_price=float(book[0][0])

				mc.delete(key)
				print("creating stoploss order: "+str(sell_price))
				message="<b>ALERT:: - "+str(symbol)+" STOPLOSS HIT</b>, <b>SELLING:</b> "+str(units)+"UNITS\t<b>SELL @:</b> "+str(sell_price)+" <b>LAST BUY @:</b>"+str(last_price)
				broadcast(message)
				print(message)
				log_redis(redis_trade_log,message,c)
							
				if live=="yes":
					ret=exchange.create_order (symbol, 'limit', 'sell', units, sell_price)
					broadcast(message)

					message="Killing Bot"
					log_redis(redis_trade_log,message,c)
					if enable_buybacks=='no':
						delete_bot(symbol)			
						print("killing bot/deleting it")	
						return("kill")
						key=str(symbol)+'-SL'	
						mc.set(key,1,86400)			
	else:
				
		rsikey="rsi"+str(symbol)
		rsi=get_rsi(rsi_symbol,candle_size)
		print("RSI")
		print(rsi)
		rsi=float(rsi)
	
		lo_key="last_order-"+str(symbol)
		mc.delete(lo_key)
		if mc.get(lo_key):
			last_array=mc.get(lo_key)
			last_price=float(last_array['price'])
			last_type=last_array['side']
		else:
			#Cache last order in ram for 60 seconds to speed up api calls
			print("Db: lT: "+str(symbol))
			last_array=fetch_last_order(exchange,symbol)
			last_price=float(last_array['price'])
			last_type=last_array['side']
			mc.set(lo_key,last_array,60)
		
		print(last_array)
		if last_price==0.00:
			#Was a market buy so we didn't pass a buy price work it out by cummulativeQuoteQty/aka fee / units
			market_fee=float(last_array['cummulativeQuoteQty'])
			market_units=float(last_array['origQty'])
			last_price=market_fee/market_units
			print("Debug LA: ")
			print(last_price)
			print(last_array)
	
		if last_type=='BUY':
			trade_action='selling'
		else:
			trade_action='buying'

		#Added forcebuy usefull if u wanna force a buy on rsi without instant buy @ market
		fbkey=symbol+"-FORCE-BUY"
		if mc.get(fbkey):
			trade_action='buying'
			mc.delete(fbkey)

		fskey=symbol+"-FORCE-SELL"
		if mc.get(fskey):
			trade_action='selling'
			mc.delete(fskey)

		message="No open orders Currently RSI: "+str(rsi)	
		log_redis(redis_log,message,c)
		print(message)

		if ticker:
			message=str(symbol)+"\t"+str(bid)+"\t"+str(ask)+"\t"+str(last)+"\t"+str(high)+"\t"+str(low)+"\t"+str(rsi)
			log_redis(redis_rsi_log,message,c)
	
		got_key=int(0)
		key=str(symbol)+'-SYSTEM-BUYBACK'
		if mc.get(key):
			got_key=0

		if trade_action=="buying" and rsi<=rsi_buy or trade_action=="buying" and ignore_rsi==1 or trade_action=="buying" and got_key==1:
			
			if use_stoploss=="yes":
				stoploss=last_price/100*stoploss_percent
				stoploss_price=last_price-stoploss
		
				print("Debug: "+str(stoploss_percent))
				print("Last Price: "+str(last_price))
			
				### ADD SMART STOPLOSS CODE
				key=str(symbol)+'-SYSTEM-STOPLOSS'
				if mc.get(key):
					stoploss_price=float(mc.get(key))	
						
				print("last buy price: "+str(last_price))
				print("stoploss price: "+str(stoploss_price))
				print("market price: "+str(last))
					
				message="Last buy price: "+str(last_price)+"\tStoploss price: "+str(stoploss_price)+"\tmarket price: "+str(last)
				log_redis(redis_log,message,c)
				print(message)

				if last <= stoploss_price or last <= original_stoploss_price:		
					mc.delete(key)
					book=fetch_order_book(exchange,symbol,'bids',1)
					sell_price=float(book[0][0])
					print("creating stoploss order: "+str(sell_price))
					message="<b>ALERT:: - "+str(symbol)+" STOPLOSS HIT</b> <b>SELLING:</b> "+str(units)+"UNITS\t<b>SELL @:</b> "+str(sell_price)+" <b>LAST BUY @:</b>"+str(last_price)
					broadcast(message)
					log_redis(redis_trade_log,message,c)
					if live=="yes":
						ret=exchange.create_order (symbol, 'limit', 'sell', units, sell_price)
							
					if enable_buybacks=='no':
						message="killing script no buyback here :"+str(sleep_for_after_stoploss_executed)+ "seconds now giving market time to adjust our dough is tethered"
						delete_bot(symbol)
						broadcast(message)	
						return("kill")
						
						key=str(symbol)+'-KILL'	
						mc.set(key,1,86400)			
						
						key=str(symbol)+'-SL'	
						mc.set(key,1,86400)	
						
			if enable_safeguard=='yes':
				safeguard=last_price/100*safeguard_percent
				price=last_price-safeguard
			else:
				book=fetch_order_book(exchange,symbol,'bids',1)
				price=float(book[buy_pos][0])
				
			exchange_cut=price/100*0.007500
			price=price-exchange_cut
			print("Making buyorder for "+str(units)+" price: "+str(price)+"\n")	
	
			message="<b>ALERT:: - "+str(symbol)+" BUYING</b> "+str(units)+"UNITS\t<b>BUY @:</b> "+str(price)+"\t<b>LAST SELL @:</b> "+str(last_price)
			log_redis(redis_trade_log,message,c)

			broadcast(message)
			print(ret)
			message="Live Ticker:\nBid: "+str(bid)+" Ask: "+str(ask)+ " Last: "+str(last)+ "\nHigh: "+str(high)+" Low: "+str(low)+"\nOpen: "+str(open)+" Close: "+str(close)+"\n"
			if live=="yes":
				ret=exchange.create_order (symbol, 'limit', 'buy', units, price)
				print(ret)

			log_redis(redis_trade_log,message,c)
			print(message)
		elif trade_action=="selling" and rsi>=rsi_sell:
			book=fetch_order_book(exchange,symbol,'asks',1)
			price=float(book[sell_pos][0])
		
			if price < last_price and enable_safeguard=='yes':
				message=str(price)+" is under: "+str(last_price)
				log_redis(redis_trade_log,message,c)
				safeguard=last_price/100*safeguard_percent
				price=last_price+safeguard
				message="Using safeguard price is now: "+str(price)
				log_redis(redis_trade_log,message,c)
				print(message)
				
			exchange_cut=price/100*0.007500
			price=price+exchange_cut
			
			print("Making sell order for "+str(units)+" price: "+str(price)+"\n")

			message="<b>ALERT:: - "+str(symbol)+" SELLING</b> "+str(units)+"UNITS\t<b>SELL @:</b> "+str(price)+"\t<b>LAST BUY:</b> "+str(last_price)
			broadcast(message)
			log_redis(redis_trade_log,message,c)

			if live=="yes":
				ret=exchange.create_order (symbol, 'limit', 'sell', units, price)
				print(ret)
			message="\nLive Ticker:\nBid: "+str(bid)+" Ask: "+str(ask)+ " Last: "+str(last)+ "\nHigh:"+str(high)+" Low: "+str(low)+"\nOpen: "+str(open)+" Close: "+str(close)+"\n"
			
			log_redis(redis_trade_log,message,c)
			if enable_buybacks=='no':
				message="killing script no buyback here success sell without stoploss hitting"
				delete_bot(symbol)
				broadcast(message)	
				return("kill")
		
			message="<b>ALERT:: - "+str(symbol)+"</b>\nThe market Conditions are not right for a buy or sell <b>RSI is:</b> "+str(rsi)+" Our next action is -> "+str(trade_action)
			print(message)
			tm_key=str(symbol)+'-TMPS'	
			if not (mc.get(tm_key)):
				mc.set(tm_key,1,600)			
				broadcast(message)
				#walls(symbol)
				log_redis(redis_log,message,c)

		return(1)

mc = memcache.Client(['127.0.0.1:11211'], debug=0)

parser = argparse.ArgumentParser()

parser.add_argument('--trading_pair', help='Trading pair i.e BTC/USDT')
args = parser.parse_args()

symbol=str(args.trading_pair)
print(symbol)

if r.sismember('botlist',symbol)==0:
	delete_bot(symbol)			
	sys.exit("bot not in list")
	print("bot not in list")
c=0

message="<b>ALERT:: SPAWNED A NEW BOT FOR: "+str(symbol)+"</b>"
print(message)
#broadcast(message)

while True:
	ret="meh"
	
	#try:
	#print("tying")
	ret=main(exchange,symbol,c)
	#except:
	#print("threw error sleeping for 3 seconds")
	#time.sleep(5)
	
	if ret=="kill":
		print("killing")
		delete_bot(symbol)			
		sys.exit("die")
	c+=1
	time.sleep(0.5)