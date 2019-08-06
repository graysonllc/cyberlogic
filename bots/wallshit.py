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

def log_db(symbol,rsi_symbol,trade_from,trade_to,buy_price,units,bid,last,ask,open,close,high,low,bot_id):

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
		INSERT INTO at_history(date,date_time,timestamp,symbol,rsi_symbol,trade_from,trade_to,buy_price,units,stoploss_price,profit,profit_percent,total_invest,total_now,bid,last,ask,open,close,high,low,bot_id)
		VALUES (CURRENT_DATE(),NOW(),UNIX_TIMESTAMP(),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
	"""
	print(sql)
	cursor.execute(sql,(symbol,rsi_symbol,trade_from,trade_to,buy_price,units,stoploss_price,profit,profit_percent,total_invest,total_now,bid,last,ask,open,close,high,low,bot_id))
	db.close()

def log_order(exchange,bot_id,order_id,order_type,symbol,rsi_symbol,trade_from,trade_to,sell_price,units):
	
	config = configparser.ConfigParser()
	config.read('/root/akeys/b.conf')

	mysql_username=config['mysql']['MYSQL_USERNAME']
	mysql_password=config['mysql']['MYSQL_PASSWORD']
	mysql_hostname=config['mysql']['MYSQL_HOSTNAME']
	mysql_database=config['mysql']['MYSQL_DATABASE']

	order_array=nickbot.fetch_last_buy_order(exchange,symbol)
	buy_price=float(order_array['price'])
	
	profit_per_unit=sell_price-buy_price
	profit=float(profit_per_unit*units)
	profit=round(profit,8)
	prices = [buy_price,sell_price]
	for a, b in zip(prices[::1], prices[1::1]):
		profit_percent=100 * (b - a) / a
		profit_percent=round(profit_percent,2)

	db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysql_database)
	cursor = db.cursor()
	
	sql = str("""
		INSERT INTO at_orders(date,date_time,timestamp,bot_id,order_id,symbol,rsi_symbol,trade_from,trade_to,units,buy_price,sell_price,profit,profit_percent) 
		VALUES (CURRENT_DATE(),NOW(),UNIX_TIMESTAMP(),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
	""")

	print(bot_id,order_id,symbol,rsi_symbol,trade_from,trade_to,units,buy_price,sell_price,profit,profit_percent)

	cursor.execute(sql,(bot_id,order_id,symbol,rsi_symbol,trade_from,trade_to,units,buy_price,sell_price,profit,profit_percent))
	db.close()
	
r = redis.Redis(host='localhost', port=6379, db=0)

def fetch_prices(exchange, symbol):
	ticker = exchange.fetch_ticker(symbol.upper())
	return(ticker)


def replace_last(source_string, replace_what, replace_with):
    head, _sep, tail = source_string.rpartition(replace_what)
    return head + replace_with + tail

def volume24h_in_usd(symbol):

	exchange=nickbot.get_exchange()

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

	exchange=nickbot.get_exchange()

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
	exchange=nickbot.get_exchange()
	
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

#exchange=get_exchange()
def get_price(exchange,symbol):
	
	symbol=symbol.upper()	
	ticker = exchange.fetch_ticker(symbol.upper())
	print(str(ticker))
	price=float(ticker['last'])
	return(price)

def wall_pos2(symbol,usd_limit):
	
	#Fucking jedi master shit, lets make sure that theres usd_limit above us in the buy book @ set our dynamic stoploss at that
	usd_limit=float(usd_limit)
	pusd=float(price_usd(symbol))
	exchange=nickbot.get_exchange()
	message=""
	buy_book=exchange.fetch_order_book(symbol,1000)
	print(buy_book)
	pos=int(0)
	book=buy_book['bids']
	print(book)
	#book.reverse()
	tv_usd=0
	got=0
	print("USD LIMIT: "+str(usd_limit))
	for line in book:
		k=line[0]
		v=line[1]
		v_usd=round(float(v)*pusd,2)
		tv_usd=round(float(tv_usd+v_usd),2)
		#print("DEBUG K: "+str(k))
		#print("DEBUG TVUSD: "+str(tv_usd))
		#print("DEBUG USDLIMIT: "+str(usd_limit))
		#if k>=float(stoploss):
		message=message+"BOOK POS: "+str(pos)+"\tPRICE: "+str(k)+"\tVOLUME: "+str(v)+"\tVOLUME USD: "+str(v_usd)+"\tTOTAL VOLUME USD: "+str(tv_usd)+"\n"
		print(message)
		if tv_usd>=usd_limit:
			print(message)
			return(pos)
			got=1	
		
		if got!=1:
			pos+=1
			
	return(pos)		
	print(message)


exchange=nickbot.get_exchange()

blist=r.smembers("botlist")
print(len(blist))

sys.exit("fucker")
#nickbot.wall_pos('BTC/USDT','100000')
#print("BNB/USDT:")
#new_stoploss=float(nickbot.wall_magic('BNB/USDT','11000'))
#print("ETH/USDT:")
#new_stoploss=float(nickbot.wall_magic('ETH/USDT','11000'))
print("LINK/USDT:")
new_stoploss=float(nickbot.wall_magic('LINK/USDT','11000'))
trades=exchange.fetchTrades ('LINK/USDT')
c=0
for dat in trades:
	ts=dat['timestamp']	
	if c==0:
		start_ts=ts/1000
	last_ts=ts/1000
	c+=1
elapsed = last_ts - start_ts
elapsed=elapsed/60
print(elapsed)
#print(trades)
sys.exit("die")
def walls(symbol):
	
	#symbol=args[0].upper()
	exchange=nickbot.get_exchange()
	
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