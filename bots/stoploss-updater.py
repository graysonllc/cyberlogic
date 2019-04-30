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
import redis
import configparser

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib'
sys.path.append(root + '/python')

mc = memcache.Client(['127.0.0.1:11211'], debug=0)

#checkposts

r = redis.Redis(host='localhost', port=6379, db=0)

botlist=r.smembers("botlist")

print(":::STOPLOSS/MOVER Polling Running Bots\n")

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

def fetch_last_order(exchange,symbol):
	ret=exchange.fetch_closed_orders (symbol, 1);
	if ret:
		data=ret[-1]['info']
		side=data['side']
		price=float(data['price'])
		return data
	else:
		print("returning: 0")
		data=0
		return data

def loop_bots():
	
	for bot_name in botlist:
		bot_name=bot_name.decode('utf-8')
		symbol=bot_name.upper()
		ts=float(r.get(bot_name))

		key=str(symbol)+'-LAST-PRICE'	
		if mc.get(key):
			market_price=float(mc.get(key))

			buy_array=fetch_last_order(exchange,symbol)
			buy_price=float(buy_array['price'])
			units=float(buy_array['executedQty'])
			
			print(symbol+str(":::STOPLOSS/MOVER Last Buy Price: "+str(buy_price)+" Market Price: "+str(market_price))+" Units: "+str(units))		
		
			profit=market_price-buy_price
			profit=profit*units
			prices = [buy_price,market_price]
			for a, b in zip(prices[::1], prices[1::1]):
				percent=100 * (b - a) / a
				percent=round(percent,2)
				profit=round(profit,2)

			message=str(symbol)+":::STOPLOSS/MOVER Profit STATS: Profit: "+str(profit)+' ('+str(percent)+'%)'
			print(message)

			key=str(symbol)+'-ORIGINAL-SL'	
			if mc.get(key):
				original_stoploss=mc.get(key)
				original_stoploss_price_ded=buy_price/100*original_stoploss
				original_stoploss_price=buy_price-original_stoploss_price_ded

			print(symbol+str(":::STOPLOSS/MOVER ORIGINAL STOPLOSS PRICE: "+str(original_stoploss_price)))

			key=str(symbol)+'-SYSTEM-STOPLOSS'
			
			if profit>0:

				dec=buy_price/100*original_stoploss
				stoploss=market_price-dec
				
				print(symbol+":::STOPLOSS/MOVER Market Price Now:"+str(market_price)+" is above last buy lets move the goal posts\n")
				
				if mc.get(key):
					goalpost_stoploss=mc.get(key)
					print(symbol+str(":::STOPLOSS/MOVER GOALPOST STOPLOSS PRICE: "+str(goalpost_stoploss)))

				#If we allready moved goal posts once increment counter only if higher than last goal post move
				key=str(symbol)+'-SYSTEM-STOPLOSS'
				if mc.get(key):
					last_cycle_inc=mc.get(key)
						
					if stoploss>last_cycle_inc:
						key=str(symbol)+'-GOALPOSTS'
						cycles=r.incr(key)
						print(str(symbol)+":::STOPLOSS/MOVER MOVED GOAL POST: "+str(cycles)+" Times!\n")
						key=str(symbol)+'-SYSTEM-STOPLOSS'
						mc.set(key,stoploss,86400)			
				else:
					key=str(symbol)+'-SYSTEM-STOPLOSS'
					mc.set(key,stoploss,86400)			

while True:
	try:
		loop_bots()
		#print("STOPLOSS UPDATER")
	except:
		print("")
	time.sleep(5)		


		