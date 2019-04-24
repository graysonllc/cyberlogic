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

def broadcast(text):

	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')
	telegram_id=config['binance']['TELEGRAM_ID']
	token = telegram_id
	chatid = "@ntradez"
	url = "https://api.telegram.org/"+ token + "/sendMessage?chat_id=" + chatid+"&text="+text
	r=requests.get(url)
	html = r.content

def fetch_prices(exchange, symbol):
	ticker = exchange.fetch_ticker(symbol.upper())
	return(ticker)
   

def fetch_last_order(exchange,symbol):
	ret=exchange.fetch_closed_orders (symbol, 1);
	#print(ret)
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
		
		#sys.exit("fuck")
		rsi=float(fin[-1])

		#rsi=round(rsi)

		return(rsi)
	except:
		print("rsi is the problem")


def get_rsi_old(pair,interval):

	try:
		arr = []
		out = []
		fin = []
		trades=exchange.fetch_ohlcv(pair,interval)
		for trade in trades:
			open_price=float(trade[1])
			close_price=float(trade[5])
			high_price=float(trade[3])
			low_price=float(trade[4])
			#if close_price>0:
			arr.append(close_price)
			

		np_arr = np.array(arr,dtype=float)
		output=talib.RSI(np_arr,timeperiod=14)
		for chkput in output:
			#if chkput>0:
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
def main(exchange):
	
	mc = memcache.Client(['127.0.0.1:11211'], debug=0)

	parser=argparse.ArgumentParser()
	parser.add_argument('--exchange', help='Exchange name i.e binance')
	parser.add_argument('--rsi_symbol', help='RSI SYMBOL pair i.e IOTAUSDT')
	parser.add_argument('--trading_pair', help='Trading pair i.e BTC/USDT')
	parser.add_argument('--units', help='Number of coins to trade')
	parser.add_argument('--trade_from', help='I.E BTC')
	parser.add_argument('--trade_to', help='I.E USDT')
	parser.add_argument('--buy_position', help='Buy book position to clone')
	parser.add_argument('--sell_position', help='Sell book position to clone')
	parser.add_argument('--use_stoploss', help='1 to enable, 0 to disable')
	parser.add_argument('--candle_size', help='i.e 5m for 5 minutes')
	parser.add_argument('--safeguard_percent', help='safeguard percent if buying back cheaper')
	parser.add_argument('--rsi_buy', help='Rsi Number under to trigger a buy, i.e 20')
	parser.add_argument('--rsi_sell', help='Rsi Number over to trigger a sell, i.e 80')
	parser.add_argument('--live', help='1 for Live trading, 0 for dry testing.')

	args = parser.parse_args()

	trading_on=args.exchange
	rsi_symbol=args.rsi_symbol
	symbol=args.trading_pair
	units=args.unit
	trade_from=args.trade_from
	trade_to=args.trade_to
	buy_pos=args.buy_position	
	sell_pos=args.sell_position
	stoploss_percent=args.stoploss_percent
	safeguard_percent=args.safeguard_percent
	use_stoploss=args.use_stoploss
	candle_size=args.candle_size
	rsi_buy=args.rsi_buy
	rsi_sell=args.rsi_sell
	live=args.live

	key=str(symbol)+'-ORIGINAL-SL'	
	mc.set(key,stoploss_per,864000)
	ignore_rsi=0
	sleep_for_after_stoploss_executed=600
	
	#If the manual bot is doing sell off then dont interfere
	key=str(symbol)+'-PAUSED'	
	if(mc.get(key)):
		time.sleep(30)
		return(1)
	
	key=str(symbol)+'-SL'	
	if(mc.get(key)):
		ignore_rsi=1
		print("Got Stoploss key\n")
		mc.delete(key)
					
	exchange_cut=0.007500;
	
	tkey="seen"+str(symbol)
	orders = exchange.fetch_open_orders(symbol,1)
	balances=exchange.fetch_balance ()
	pair_1_balance=float(format(balances[trade_from]['total'],'.8f'))
	pair_2_balance=float(format(balances[trade_to]['total'],'.8f'))

	open_order=len(orders)
	
	rsikey="rsi"+str(symbol)
	rsi=get_rsi(rsi_symbol,candle_size)
	print("RSI")
	print(rsi)

	rsi=float(rsi)
	ticker = exchange.fetch_ticker(symbol.upper())
	bid=float(ticker['bid'])
	last=float(ticker['last'])
	key=str(symbol)+'-LAST-PRICE'	
	mc.set(key,last,86400)
	ask=float(ticker['ask'])
	open=float(ticker['open'])
	close=float(ticker['close'])
	high=float(ticker['high'])
	low=float(ticker['low'])
	
	last_array=fetch_last_order(exchange,symbol)
	last_price=float(last_array['price'])
	last_type=last_array['side']

	if last_type=='BUY':
		trade_action='selling'
	else:
		trade_action='buying'

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
				
				print("Theres an open order\nType: " +str(open_type)+ "\nPrice: "+str(open_price)+ "\nFilled: "+str(open_filled)+"/"+str(open_remaining)+"\nRSI is: "+str(rsi)+" Order ID: "+str(order_id))
				print("Current Ticker Values- Last: "+str(last)+" Bid: "+str(bid)+" Ask: "+str(ask))
	
		if use_stoploss==1:
			
				try:
					
					if last_type=='BUY':
						stoploss=last_price/100*stoploss_per
						stoploss_price=last_price-stoploss
						
						### ADD SMART STOPLOSS CODE
						key=str(symbol)+'-SYSTEM-STOPLOSS'
						if mc.get(key):
							stoploss_price=float(mc.get(key))
							sell_price=stoploss_price
						else:
							book=fetch_order_book(exchange,symbol,'bids',1)
							#sell_price=float(last)
							sell_price=float(book[0][0])

						print("last buy price: "+str(last_price))
						print("stoploss price: "+str(stoploss_price))
						print("market price: "+str(last))
						if last < stoploss_price:

							exchange.cancelOrder(order_id,symbol)
							mc.delete(key)
							sell_price=float(book[0][0])
							print("creating stoploss order: "+str(sell_price))
							message="Alert Stoploss Hit line 260, Making Sell Order For: "+str(units)+" Price: "+str(sell_price)+" Last Buy Price"+str(last_price)
							broadcast(message)
							if live==1:
								ret=exchange.create_order (symbol, 'limit', 'sell', units, sell_price)
							message="killing script never buy back here for :"+str(sleep_for_after_stoploss_executed)+ "seconds now giving market time to adjust our dough is tethered"
							broadcast(message)	
							return("kill")				
							key=str(symbol)+'-SL'	
							mc.set(key,1,86400)			
				except:
					print("Some Error\n")
	else:
		print("\nNo open orders Currently RSI: "+str(rsi))	
		
		try:
			last_array=fetch_last_order(exchange,symbol)
			last_price=float(last_array['price'])
			last_type=last_array['side']
			print(last_type)
		except:
			#Check if there was never a trade on this pair if so force a buy or sell
			print("mook")
			last_type=str("")
			last_price=int(0)	
			print(last_price)
					
		if ticker:
		
			config = configparser.ConfigParser()
			config.read('/root/akeys/b.conf')
			mysql_username=config['mysql']['MYSQL_USERNAME']
			mysql_password=config['mysql']['MYSQL_PASSWORD']
			mysql_hostname=config['mysql']['MYSQL_HOSTNAME']
			mysql_database=config['mysql']['MYSQL_DATABASE']
			telegram_id=config['binance']['TELEGRAM_ID']

			db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysl_database)

			cursor = db.cursor()
	
			sql = """
			INSERT INTO rsi_history(pair,bid,ask,last,high,low,rsi,timestamp,datetime)
			VALUES (%s,%s,%s,%s,%s,%s,%s,now(),now())
			"""
			cursor.execute(sql,(symbol,bid,ask,last,high,low,rsi))
			db.close()	
	
		got_key=int(0)
		key=str(symbol)+'-SYSTEM-BUYBACK'
		if mc.get(key):
			got_key=0
		if trade_action=="buying" and rsi<=rsi_buy or trade_action=="buying" and ignore_rsi==1 or trade_action=="buying" and got_key==1:
			
			print(str(price)+" is over: "+str(last_price))
			safeguard=last_price/100*safeguard_percent
			price=last_price-safeguard
			print("using safeguard price is now: "+str(price))

			exchange_cut=price/100*0.007500
			price=price-exchange_cut
			print("Making buyorder for "+str(units)+" price: "+str(price)+"\n")
			add="\nBalance:"+str(trade_from)+str('=')+str(pair_1_balance)+"\nBalance: "+str(trade_to)+str('=')+str(pair_2_balance)				
			message="Making Buy Order For "+str(units)+" Price: "+str(price)+" Last Sell Price: "+str(last_price)
			broadcast(message)
			print(ret)
			print("\nLive Ticker:\nBid: "+str(bid)+" Ask: "+str(ask)+ " Last: "+str(last)+ "\nHigh: "+str(high)+" Low: "+str(low)+"\nOpen: "+str(open)+" Close: "+str(close)+"\n")
		
		elif trade_action=="selling" and rsi>=rsi_sell:
			book=fetch_order_book(exchange,symbol,'asks',1)
			price=float(book[sell_pos][0])
		
			if price < last_price:
				print(str(price)+" is under: "+str(last_price))
				safeguard=last_price/100*safeguard_percent
				price=last_price+safeguard
				print("using safeguard price is now: "+str(price))
				
			exchange_cut=price/100*0.007500
			price=price+exchange_cut
			
			print("Making sell order for "+str(units)+" price: "+str(price)+"\n")
			add="\nBalance:"+str(trade_from)+str('=')+str(pair_1_balance)+"\nBalance: "+str(trade_to)+str('=')+str(pair_2_balance)				
			message="Making Sell Order For "+str(units)+" Price: "+str(price)+" Last Buy Price: "+str(last_price)+str(add)
			broadcast(message)
			if live==1:
				ret=exchange.create_order (symbol, 'limit', 'sell', units, price)
			print(ret)
			print("\nLive Ticker:\nBid: "+str(bid)+" Ask: "+str(ask)+ " Last: "+str(last)+ "\nHigh: "+str(high)+" Low: "+str(low)+"\nOpen: "+str(open)+" Close: "+str(close)+"\n")
		else:
			if use_stoploss==1:
				last_array=fetch_last_order(exchange,symbol)
				last_price=float(last_array['price'])
				last_type=last_array['side']

				if last_type=='BUY':
					stoploss=last_price/100*stoploss_per
					stoploss_price=last_price-stoploss
					
					### ADD SMART STOPLOSS CODE
					key=str(symbol)+'-SYSTEM-STOPLOSS'
					if mc.get(key):
						stoploss_price=float(mc.get(key))	
						
					print("last buy price: "+str(last_price))
					print("stoploss price: "+str(stoploss_price))
					print("market price: "+str(last))
					if last < stoploss_price:
					
						mc.delete(key)

						book=fetch_order_book(exchange,symbol,'bids',1)
						
						sell_price=float(book[0][0])

						print("creating stoploss order: "+str(sell_price))
						message="Alert Stoploss Hit 364, Making Sell Order For: "+str(units)+" Price: "+str(sell_price)+" Last Buy Price"+str(last_price)
						broadcast(message)
						
						if live==1:
							ret=exchange.create_order (symbol, 'limit', 'sell', units, sell_price)
	
						message="killing script no buyback here :"+str(sleep_for_after_stoploss_executed)+ "seconds now giving market time to adjust our dough is tethered"
						broadcast(message)	
						return("kill")
						
						key=str(symbol)+'-KILL'	
						mc.set(key,1,86400)			
						
						key=str(symbol)+'-SL'	
						mc.set(key,1,86400)			
		
			print("The market Conditions are not right for a buy or sell rsi is: "+str(rsi))
		return(1)

mc = memcache.Client(['127.0.0.1:11211'], debug=0)

symbol='BNB/USDT'

parser=argparse.ArgumentParser()
parser.add_argument('--rsi_symbol', help='RSI SYMBOL pair i.e IOTAUSDT')
args = parser.parse_args()
symbol=args.trading_pair

while True:
	ret="meh"
	try:
		ret=main(exchange)
	except:
		print("threw error sleeping for 3 seconds")
	if ret=="kill":
		sys.exit("die bitch")