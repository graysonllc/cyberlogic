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
import heapq

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib'
sys.path.append(root + '/python')

import talib
import numpy as np
import ccxt  # noqa: E402

r = redis.Redis(host='localhost', port=6379, db=0)


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

def walls(symbol):
	
	#symbol=args[0].upper()
	exchange=get_exchange()
	
	buy_book=exchange.fetch_l2_order_book(symbol,500)
	sell_book=exchange.fetch_l2_order_book(symbol,500)
	print(buy_book)
	buy_dic={}
	sell_dic={}
	
	for k,v in buy_book:
		buy_dic[k]=v
		print(v)
		print("Key: "+str(k)+" v: "+str(v))

	for k,v in sell_book:
		sell_dic[k]=v
				
	buy_walls=heapq.nlargest(20, buy_dic.items(), key=itemgetter(1))
	print(buy_walls)
	sell_walls=heapq.nlargest(20, sell_dic.items(), key=itemgetter(1))
	
	message="<b>WALL INTEL:</b>\n\n"
	
	message=message+"<b>BUY WALLS ('SUPPORT')</b>\n"
	
	for k,v in sorted(buy_walls):
		message=message+"<b>PRICE:</b> "+str(k)+"\t<b>VOLUME:</b> "+str(v)+"\n"

	message=message+"\n<b>SELL WALLS ('RESISTANCE')</b>'\n"
	for k,v in sorted(sell_walls):
		message=message+"<b>PRICE:</b> "+str(k)+"\t<b>VOLUME:</b> "+str(v)+"\n"
	
	print(message)
		
walls('BTC/PAX')