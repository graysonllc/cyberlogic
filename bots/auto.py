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
from datetime import datetime
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
		buy_book=fetch_order_book(exchange,symbol,'bids','1000')
		buy_pos=int(buy_pos)
		buy_price=float(buy_book[buy_pos][0])
		print(symbol+" Units Buy Price"+str(buy_price))
		ret=exchange.create_order (symbol, 'limit', 'buy', units, buy_price)
		print(ret)			
	spawn_bot(symbol)

exchange=get_exchange()

symbol='DENT/ETH'
rsi_symbol='DENTETH'
orders = exchange.fetch_open_orders(symbol,1)
open_order=len(orders)

if open_order:
	for order in orders:
		print(order)
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
			
			print("ET: ")
			print(elapsed_time)



sys.exit("die")

rsi_symbol=str('ETHUSDT')
symbol=str('ETH/USDT')
units=float(0.1)
trade_from=str('ETH')
trade_to=str('USDT')
buy_pos=int(20)
sell_pos=int(20)
stoploss_percent=float(4)
use_stoploss=int(1)
candle_size=str('5m')
safeguard_percent=float(2)
rsi_buy=float(20)
rsi_sell=float(80)
instant_market_buy=str('yes')
enable_buybacks=str('no')
enable_safeguard=str('yes')
force_buy=str('yes')
force_sell=str('no')
live=str('yes')
trading_on=str('Binance')

auto_spawn(trading_on, rsi_symbol, symbol, units, trade_from, trade_to, buy_pos, sell_pos, stoploss_percent, use_stoploss, candle_size, safeguard_percent, rsi_buy, rsi_sell, instant_market_buy, enable_buybacks, enable_safeguard, force_buy, force_sell, live)
