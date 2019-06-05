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
import nickbot

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib'
sys.path.append(root + '/python')

import talib
import numpy as np
import ccxt  # noqa: E402

r = redis.Redis(host='localhost', port=6379, db=0)

symbol='HC/ETH'
exchange=nickbot.get_exchange()
print(nickbot.fetch_last_buy_order(exchange,symbol))
sys.exit("die")

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

def fetch_prices(exchange, symbol):
	ticker = exchange.fetch_ticker(symbol.upper())
	return(ticker)


def replace_last(source_string, replace_what, replace_with):
    head, _sep, tail = source_string.rpartition(replace_what)
    return head + replace_with + tail

def volume24h_in_usd(symbol):

	exchange=get_exchange()

	symbol=symbol.upper()
	ticker_symbol=symbol
	tickers=fetch_prices(exchange,ticker_symbol)

	v24=tickers['quoteVolume']

	if symbol.endswith('BTC'):
		tickers=fetch_prices(exchange,'BTC/USDT')
		trade_to_price=float(tickers['close'])
	elif symbol.endswith('ETH'):
		tickers=fetch_prices(exchange,'ETH/USDT')
		trade_to_price=float(tickers['close'])
	elif symbol.endswith('BNB'):
		tickers=fetch_prices(exchange,'BNB/USDT')
		trade_to_price=float(tickers['close'])
	else:
		trade_to_price=1

	p24=v24*trade_to_price
	p24=float(p24)
	
	return(p24)

def price_usd(symbol):

	symbol=symbol.upper()
	ticker_symbol=symbol

	exchange=get_exchange()

	if symbol.endswith('BTC'):
		ticker_symbol = replace_last(ticker_symbol, '/BTC', '')
		trade_to='BTC'
	elif symbol.endswith('USDT'):
		ticker_symbol = replace_last(ticker_symbol, '/USDT', '')
		trade_to='USDT'
	elif symbol.endswith('BNB'):
		ticker_symbol = replace_last(ticker_symbol, '/BNB', '')
		trade_to='BNB'
	elif symbol.endswith('TUSD'):
		ticker_symbol = replace_last(ticker_symbol, '/TUSD', '')
		trade_to='TUSD'
	elif symbol.endswith('USD'):
		ticker_symbol = replace_last(ticker_symbol, '/USD', '')
		trade_to='USD'
	elif symbol.endswith('USDC'):
		ticker_symbol = replace_last(ticker_symbol, '/USDC', '')
		trade_to='USDC'
	elif symbol.endswith('PAX'):
		ticker_symbol = replace_last(ticker_symbol, '/PAX', '')
		trade_to='PAX'
	elif symbol.endswith('USDS'):
		ticker_symbol = replace_last(ticker_symbol, '/USDS', '')
		trade_to='USDS'
	elif symbol.endswith('ETH'):
		ticker_symbol = replace_last(ticker_symbol, '/ETH', '')
		trade_to='ETH'
	
	trade_from=ticker_symbol
	exchange=get_exchange()
	
	pair_price=0
	budget=1
	if trade_to=='ETH':
		tickers=fetch_prices(exchange,'ETH/USDT')
		trade_to_price=float(tickers['close'])
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])
		fraction_to_budget=budget/trade_to_price
		units=fraction_to_budget/pair_price
		pair_price=budget/units
	elif trade_to=='BTC':
		tickers=fetch_prices(exchange,'BTC/USDT')
		trade_to_price=float(tickers['close'])
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])
		fraction_to_budget=budget/trade_to_price
		units=fraction_to_budget/pair_price
		pair_price=budget/units
	elif trade_to=='BNB':
		tickers=fetch_prices(exchange,'BNB/USDT')
		trade_to_price=float(tickers['close'])
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])
		fraction_to_budget=budget/trade_to_price
		units=fraction_to_budget/pair_price
		pair_price=budget/units
	else:
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])

	print(tickers)
	pair_price=float(pair_price)
	return(pair_price)

exchange=get_exchange()
def get_price(exchange,symbol):
	
	symbol=symbol.upper()	
	ticker = exchange.fetch_ticker(symbol.upper())
	print(str(ticker))
	price=float(ticker['last'])
	return(price)

print(get_price('ONE/USDT'))
sys.exit("die")

def wall_pos(symbol,stoploss,usd_limit):
	
	pusd=float(price_usd(symbol))
	print(pusd)
	exchange=get_exchange()
	message=""
	buy_book=exchange.fetch_order_book(symbol,100)
	#print(buy_book)
	pos=int(0)
	book=buy_book['bids']

	book.reverse()
	tv_usd=0
	for line in book:
		k=line[0]
		v=line[1]
		v_usd=round(float(v)*pusd,2)
		tv_usd=round(float(tv_usd+v_usd),2)
		if k>=float(stoploss):
			print("woop")
			message=message+"BOOK POS: "+str(pos)+"\tPRICE: "+str(k)+"\tVOLUME: "+str(v)+"\tVOLUME USD: "+str(v_usd)+"\tTOTAL VOLUME USD: "+str(tv_usd)+"\n"
			if tv_usd>=usd_limit:
				print(message)
				return(pos)		
		pos+=1
		
	print(message)

symbol='BTG/BTC'
print(volume24h_in_usd(symbol))
sys.exit("die")
	
sl_pos=wall_pos('ATOM/USDT','5.8',100000)
print(sl_pos)
sys.exit("die")

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