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
import datetime
import configparser
import subprocess
import time
import shlex
import argparse

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

conn = redis.Redis('127.0.0.1')

#Name of bot PyCryptoBot

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
print(telegram_id)
updater = Updater(token=telegram_id)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
		
def get_price(exchange,symbol):
	
	symbol=symbol.upper()	
	ticker = exchange.fetch_ticker(symbol.upper())
	price=float(ticker['last'])
	return(price)
	

def query_ath(name):

	try:
		db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,'cmc')
		cursor = db.cursor()
		sql = """SELECT ath_date,price from aths where coin=%s"""
		cursor.execute(sql,(name))
		for row in cursor:
			ath_date=row[0]	
			ath_price=row[1]
			ath_price='${:,.2f}'.format(ath_price)
			ret="\n"+str(name)+("\nAth Date: "+str(ath_date)+ "\n"+ str(name)+" Ath Price: "+str(ath_price))
			db.close()
		return(ret)
	except:
		print("some error")

def market_health():
	try:
		url = 'https://api.coinmarketcap.com/v2/ticker/'
		r=requests.get(url)
		res = (r.content.strip())
		status = r.status_code
		data = json.loads(res.decode('utf-8'))
	
		plus_1h=int(0)
		plus_24h=int(0)
		plus_7d=int(0)
	
		rows=data['data']
		for row in rows:
			row_data=rows[row]["quotes"]["USD"]
			p_1h=row_data['percent_change_1h']
			p_24h=row_data["percent_change_24h"]
			p_7d=row_data["percent_change_7d"]
		
			if p_1h:
				if p_1h > 0:
					plus_1h += 1
		
			if p_24h:
				if p_24h > 0:
					plus_24h += 1
			if p_7d:
				if p_7d > 0:
					plus_7d += 1
		
		minus_1h = int(100) - plus_1h
		minus_24h = int(100) - plus_24h
		minus_7d = int(100) - plus_7d

		ret=("Market Health For Top 100\n1 Hr Green: "+str(plus_1h)+"% Red: "+str(minus_1h)+ "%\n24 Hr Green: "+str(plus_24h)+"% Red: "+str(minus_24h)+ "%\n7 Day Green: "+str(plus_7d)+"% Red: "+str(minus_7d)+ "%") 
	except:
		print("some error")
	return(ret)
	

def memcache_stuff():
#Connect to memcache
	mc = memcache.Client(['127.0.0.1:11211'], debug=0)

	if mc.get("some_key2"):
		print("some key exists")
	
		#mc.set("some_key", "Some value")
		#value = mc.get("some_key")
		#mc.delete("another_key")
		#mc.incr("key")
		#mc.decr("key")
		#print(value)


def get_global():
	url ='https://api.coinmarketcap.com/v1/global/'
	r=requests.get(url)

	res = (r.content.strip())

	status = r.status_code

	data = json.loads(res.decode('utf-8'))

	market_cap			= int(data['total_market_cap_usd'])
	volume_24			= data['total_24h_volume_usd']
	btc_per				= str(data['bitcoin_percentage_of_market_cap'])
	total_currencies	= str(data['active_currencies'])
	total_assets		= str(data['active_assets'])
	active_markets		= str(data['active_markets'])
	
	market_cap='${:,.2f}'.format(market_cap)
	volume_24='${:,.2f}'.format(volume_24)

	health=market_health()
	if not health:
		health=""

	
	ret="Market Cap:\t"+str(market_cap)+"\n24 Hours:\t"+str(volume_24)+"\nBTC Dominance:\t"+btc_per+"%\nCurrencies: "+total_currencies+"\tAssets:\t"+active_markets+"\tMarkets: "+active_markets+"\n\n"+str(health)
	return ret;	

def get_ticker(ucoin):
	ucoin = ucoin.lower()
	url = 'https://api.coinmarketcap.com/v1/ticker/?limit=10000'
	r=requests.get(url)

	res = (r.content.strip())

	status = r.status_code

	data = json.loads(res.decode('utf-8'))

	coin_data = []
	#print(data)
	for row in data:
		
			coin_n=row['name']
			coin		= str(row['name'].lower())
			ticker		= str(row['symbol'].lower())
			
			if ticker==ucoin:
				rank 		= int(row['rank'])
				price_usd	= row['price_usd']
				price_btc	= float(row['price_btc'])
				market_cap	= float(row['market_cap_usd'])
				total_supply= float(row['total_supply'])
				change_1h	= row['percent_change_1h']
				change_24h	= row['percent_change_24h']
				change_7d	= row['percent_change_7d']
				circulating = float(row['available_supply'])

				market_cap='${:,.2f}'.format(market_cap)
				total_supply='{:,.2f}'.format(total_supply)
				price_btc='{:,.8f}'.format(price_btc)
				circulating='{:,.8f}'.format(circulating)

				ath=query_ath(coin_n)
				if not ath:
					ath=""
				else:
					print(ath)

				ret=str(ticker.upper()) +" #"+str(rank)+"\nPrice: $"+str(price_usd)+" BTC: "+str(price_btc)+"\n1hr ("+change_1h+ "%) 24hr("	+change_24h+ "%) 7D("	+change_7d+ "%)""\nMarket Cap "+str(market_cap)+ "\nMax Supply: "+str(total_supply)+"\nCirculating Supply: "+str(circulating+str(ath))

				
	if ret=='':
		return("not found")
	else:
		return(ret)

def start(bot, update):
	help="I am T800, i can do the following commands:\n\n/market to get global market data, and market health!\n/ticker SYMBOL to get coin Ticker and ATH\n";
	bot.send_message(chat_id=update.message.chat_id, text=help)
	
def help(bot, update):
	help="I am T800, i can do the following commands:\n\n/market to get global market data, and market health!\n/ticker SYMBOL to get coin Ticker and ATH\n";

	bot.send_message(chat_id=update.message.chat_id, text=help)

def ticker(bot, update, args):
	coin=args[0]
	data=get_ticker(coin)
	bot.send_message(chat_id=update.message.chat_id, text=data)
	
def market(bot, update):
	data=get_global()
	bot.send_message(chat_id=update.message.chat_id, text=data)
	
def news(bot, update):
	data=read_news()
	bot.send_message(chat_id=update.message.chat_id, text=data)


def sell(bot, update,args):	
	bid=update.message.from_user.id

	symbol=args[0].upper()
	
	exchange=get_exchange()

	bid=update.message.from_user.id
	price=get_price(exchange,symbol)
	
	ret=exchange.fetch_closed_orders (symbol, 1);
	if ret:
		data=ret[-1]['info']
		side=data['side']
		units=float(data['executedQty'])

		last_price=float(data['price'])
		
		profit=price-last_price
		profit=profit*units
		prices = [last_price,price]
		for a, b in zip(prices[::1], prices[1::1]):
			percent=100 * (b - a) / a

		percent=round(percent,2)
		profit=round(profit,2)

		mc = memcache.Client(['127.0.0.1:11211'], debug=0)
		key=str(symbol)+'-PAUSED'	

		mc.set(key,1,86400)			

		message=str(symbol)+"Selling Now!!! Price: "+str(price)+" Last Price: "+str(last_price)+" Units: "+str(units)+" Profit: "+str(profit)+' ('+str(percent)+'%)'

		ret=exchange.create_order (symbol, 'limit', 'sell', units, price)

		bot.send_message(chat_id=update.message.chat_id, text=message)


def delete_bot(bot, update, args):
	
	bot_name=args[0]
	print(bot_name)
	
	ret="::Crypto Logic Deleted bot: "+str(bot_name)
	r.srem("botlist", bot_name)
	r.delete(bot_name)
	r.sadd("botlist-stopped", bot_name)
	config = configparser.ConfigParser()
	config_file='/home/crypto/cryptologic/pid-configs/init.ini'
	config.read(config_file)
	
	bot_section='watcher:'+str(bot_name)
	config.remove_section(bot_section)
	
	with open(config_file, 'w+') as configfile:
		config.write(configfile)
		print("Write Config File to: "+str(config_file))
		print("Wrote: "+str(configfile))
	
		#subprocess.run(["/usr/bin/circusd", "--daemon",config_file])
		#subprocess.run(["/usr/bin/circusctl", "reloadconfig"])
		bot.send_message(chat_id=update.message.chat_id, text=ret)

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

def add_bot(bot, update, args):

	r = redis.Redis(host='localhost', port=6379, db=0)
	
	var1=args[0]
	
	if var1=="confirm":
	
		redis_key="bconfig-tmp"
		all=conn.hgetall(redis_key)
		
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
		instant_market_buy=conn.hget(redis_key,"instant_market_buy")
		instant_market_buy=instant_market_buy.decode('utf-8')
		enable_buybacks=conn.hget(redis_key,"enable_buybacks")
		enable_buybacks=enable_buybacks.decode('utf-8')
		
		bot_name=symbol
		
		r.sadd("botlist", bot_name)
		timestamp=time.time()

		r.set(symbol,timestamp)
		running=datetime.datetime.fromtimestamp(timestamp).strftime("%A, %B %d, %Y %I:%M:%S")

		timestamp=time.time()
		ts_raw=timestamp
		running=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
			
		redis_key="bconfig-"+symbol
		
		conn.hmset(redis_key, all)

		ret="::Crypto Logic new bot: "+str(symbol)+" has been spawned on - "+str(running)
		ret=ret+"\n\n::Exchange: "+trading_on
		ret=ret+"\n::Trade Pair: "+str(symbol)
		ret=ret+"\n::Units: "+str(units)
		ret=ret+"\n::Buy Book Scrape Position: "+str(buy_pos)
		ret=ret+"\n::Sell Book Scrape Position: "+str(sell_pos)
		ret=ret+"\n::RSI Buy: "+str(rsi_buy)
		ret=ret+"\n::RSI Sell: "+str(rsi_sell)
		ret=ret+"\n::Stoploss Percent: "+str(stoploss_percent)
		ret=ret+"\n::Safeguard Percent: "+str(safeguard_percent)
		ret=ret+"\n::Candle Size: "+candle_size
		ret=ret+"\n::Stoploss Enabled: "+str(use_stoploss)
		ret=ret+"\n::Live Trading Enabled: "+live
		ret=ret+"\n::TA Candle Size: "+candle_size
		ret=ret+"\n::Instant Market Buy: "+str(instant_market_buy)
		ret=ret+"\n::Enable Buy Backs After Stoploss Hit: "+str(enable_buybacks)

		ret=ret+"\n\nIf you ever want to kill it issue /deletebot "+str(symbol)

		if instant_market_buy=="yes":
			print("")
			#exchange=get_exchange()
			#ret=exchange.create_order (symbol, 'MARKET', 'BUY', units)
			#print(ret)
		spawn_bot(symbol)
		bot.send_message(chat_id=update.message.chat_id, text=ret)	

	else:
		argstr=' '.join(args[0:])
		print(argstr)
		parser = argparse.ArgumentParser()
				
		parser.add_argument('--trading_on', help='Exchange name i.e binance')
		parser.add_argument('--rsi_symbol', help='RSI SYMBOL pair i.e IOTAUSDT')
		parser.add_argument('--trading_pair', help='Trading pair i.e BTC/USDT')
		parser.add_argument('--units', help='Number of coins to trade')
		parser.add_argument('--trade_from', help='I.E BTC')
		parser.add_argument('--trade_to', help='I.E USDT')
		parser.add_argument('--buy_pos', help='Buy book position to clone')
		parser.add_argument('--sell_pos', help='Sell book position to clone')
		parser.add_argument('--use_stoploss', help='1 to enable, 0 to disable')
		parser.add_argument('--candle_size', help='i.e 5m for 5 minutes')
		parser.add_argument('--safeguard_percent', help='safeguard percent if buying back cheaper')
		parser.add_argument('--stoploss_percent', help='stoploss percent')
		parser.add_argument('--rsi_buy', help='Rsi Number under to trigger a buy, i.e 20')
		parser.add_argument('--rsi_sell', help='Rsi Number over to trigger a sell, i.e 80')
		parser.add_argument('--live', help='1 for Live trading, 0 for dry testing.')
		parser.add_argument('--instant_market_buy', help='To make the first buy instant @ market price')
		parser.add_argument('--enable_buybacks', help='If enabled will buy back cheaper after a stoploss sell')

		pargs = parser.parse_args(shlex.split(argstr))

		trading_on=str(pargs.trading_on)
		rsi_symbol=str(pargs.rsi_symbol)
		trading_pair=str(pargs.trading_pair)
		units=float(pargs.units)
		trade_from=str(pargs.trade_from)
		trade_to=str(pargs.trade_to)
		buy_pos=int(pargs.buy_pos)
		sell_pos=int(pargs.sell_pos)
		stoploss_percent=float(pargs.stoploss_percent)
		use_stoploss=str(pargs.use_stoploss)
		candle_size=str(pargs.candle_size)
		safeguard_percent=float(pargs.safeguard_percent)
		rsi_buy=float(pargs.rsi_buy)
		rsi_sell=float(pargs.rsi_sell)
		live=str(pargs.live)
		bot_name=str(trading_pair)
		instant_market_buy=str(pargs.instant_market_buy)
		enable_buybacks=str(pargs.enable_buybacks)

		symbol=bot_name
		if r.sismember("botlist", trading_pair):
			ts=float(r.get(bot_name).decode('utf-8'))
			print(ts)
			running=datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %I:%M:%S")

			txt="we allready have a bot running called: "+str(bot_name)+" Its been Running since: "+str(running)
			bot.send_message(chat_id=update.message.chat_id, text=txt)	
		else:	
			ret="::Crypto Logic Please review the settings for new bot: "+str(symbol)
			ret=ret+"\n\n::Exchange: "+trading_on
			ret=ret+"\n::Trade Pair: "+str(symbol)
			ret=ret+"\n::Units: "+str(units)
			ret=ret+"\n::Buy Book Scrape Position: "+str(buy_pos)
			ret=ret+"\n::Sell Book Scrape Position: "+str(sell_pos)
			ret=ret+"\n::RSI Buy: "+str(rsi_buy)
			ret=ret+"\n::RSI Sell: "+str(rsi_sell)
			ret=ret+"\n::Stoploss Percent: "+str(stoploss_percent)
			ret=ret+"\n::Safeguard Percent: "+str(safeguard_percent)
			ret=ret+"\n::Candle Size: "+candle_size
			ret=ret+"\n::Stoploss Enabled: "+str(use_stoploss)
			ret=ret+"\n::Live Trading Enabled: "+live
			ret=ret+"\n::Instant Market Buy: "+str(instant_market_buy)
			ret=ret+"\n::TA Candle Size: "+candle_size
			ret=ret+"\n::Enable Buybacks: "+str(enable_buybacks)

			ret=ret+"\n\nIf you have reviewed all settings carefully reply with /addbot confirm to execute!"

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
			"live":str(live)}
			
			print(bot_config)
			ksymbol=str(symbol)

			redis_key="bconfig-tmp"
			conn.hmset(redis_key, bot_config)
			bot.send_message(chat_id=update.message.chat_id, text=ret)

def replace_last(source_string, replace_what, replace_with):
    head, _sep, tail = source_string.rpartition(replace_what)
    return head + replace_with + tail


def alerts(bot,update,args):
	
	first_price=0
	
	secs=int(args[0])

	ts_now = datetime.datetime.now()
	ts_now_ts=float(time.mktime(ts_now.timetuple())	)
	ts_now_human=datetime.datetime.fromtimestamp(ts_now_ts).strftime("%Y-%m-%d %H:%M:%S")

	print("TSN: ")
	print(ts_now_ts)
	print(ts_now_human)

	timestamp=ts_now
	ts_from = ts_now - datetime.timedelta(seconds=secs)
	ts_from_ts=float(time.mktime(ts_from.timetuple()))
	ts_from_human=datetime.datetime.fromtimestamp(ts_from_ts).strftime("%Y-%m-%d %H:%M:%S")
	
	print("TSF: ")
	print(ts_from_ts)
	print(ts_from_human)

	r = redis.Redis(host='localhost', port=6379, db=0)
	
	date_time=datetime.datetime.fromtimestamp(ts_now_ts).strftime("%Y-%m-%d %H:%M:%S")
	date_today=datetime.datetime.fromtimestamp(ts_now_ts).strftime("%Y-%m-%d")

	pump_key=str(date_today+"-ALERTLIST")
	pump_coins=r.smembers(pump_key)

	exchange=get_exchange()
	
	for coin in pump_coins:
		coin=coin.decode('utf-8')
		coin_ids=r.smembers(coin+'-IDS')
		coin_ids=sorted(coin_ids)
		message="<b>:: Alerts For: "+str(coin)+str('</b>')
		c=0
		last_change=0

		seen=0

		for cid in coin_ids:
			cid=cid.decode('utf-8')
			rkey=str(coin)+'-'+str(cid)
			coin_hash=r.hgetall(rkey)
			if coin_hash:
				symbol=r.hget(rkey,"symbol").decode('utf-8')
				ticker_symbol=symbol

				if symbol.endswith('BTC'):
					ticker_symbol = replace_last(ticker_symbol, 'BTC', '')
					ticker_symbol=ticker_symbol+'/BTC'
				elif symbol.endswith('USDT'):
					ticker_symbol=symbol
					ticker_symbol = replace_last(ticker_symbol, 'USDT', '')
					ticker_symbol=ticker_symbol+'/USDT'
				elif symbol.endswith('BNB'):
					ticker_symbol = replace_last(ticker_symbol, 'BNB', '')
					ticker_symbol=ticker_symbol+'/BNB'
				elif symbol.endswith('TUSD'):
					ticker_symbol = replace_last(ticker_symbol, 'TUSD', '')
					ticker_symbol=ticker_symbol+'/TUSD'	
				elif symbol.endswith('USD'):
					ticker_symbol = replace_last(ticker_symbol, 'USD', '')
					ticker_symbol=ticker_symbol+'/USD'
				elif symbol.endswith('USDC'):
					ticker_symbol = replace_last(ticker_symbol, 'USDC', '')
					ticker_symbol=ticker_symbol+'/USDC'
				elif symbol.endswith('PAX'):
					ticker_symbol = replace_last(ticker_symbol, 'PAX', '')
					ticker_symbol=ticker_symbol+'/PAX'	
										
				cidn=float(cid)
	
				msorted={}
			
				if cidn>=ts_from_ts:
					date_time=r.hget(rkey,"date_time").decode('utf-8')
					price=float(r.hget(rkey,"price").decode('utf-8'))
					percent=r.hget(rkey,"percent").decode('utf-8')
					spread=r.hget(rkey,"spread").decode('utf-8')
					high=r.hget(rkey,"high").decode('utf-8')
					low=r.hget(rkey,"low").decode('utf-8')
					btc_price=r.hget(rkey,"btc_price").decode('utf-8')
					btc_price="{0:.8}".format(btc_price)
									
					if percent!=last_change or last_change==0:			
						if seen==0:
							first_price=price
							first_price=str(format(price, '.6f'))
							seen=1
						if 'e' in str(price):
							price=str(format(price, '.6f'))
						else:
							price=format(price, '.6f')
						if float(percent)>float(last_change):
							message=message+"\n\n<b>"+str(date_time)+"\tPrice: "+str(price)+' Change %:'+str(percent)+" Spread: "+str(spread)+'</b>'
						else:
							message=message+"\n\n<i>"+str(date_time)+"\tPrice: "+str(price)+' Change %:'+str(percent)+" Spread: "+str(spread)+'</i>'
						c+=1
					last_change=percent							
				
		if c>0:
			print(symbol)
			print(ticker_symbol)
			ticker = exchange.fetch_ticker(ticker_symbol.upper())
			tick=0
			if ticker:
				bid=float(ticker['bid'])
				last=float(ticker['last'])
				ask=float(ticker['ask'])
				open=float(ticker['open'])
				close=float(ticker['close'])
				high=float(ticker['high'])
				low=float(ticker['low'])
				tick=1
				first_price=float(first_price)
				
				if first_price>0.0 and tick==1:
					price_diff=last-first_price
					prices = [first_price,last]
				
					price_diff=str(format(price_diff, '.6f'))

					print(first_price)
					
					for a, b in zip(prices[::1], prices[1::1]):
						pdiff=100 * (b - a) / a
			
					pdiff=round(pdiff,2)

					coin_stats=''
					coin_stats=coin_stats+"\n<b>:: Current Ticker For: "+str(ticker_symbol)+'</b>'+"\n"
					coin_stats=coin_stats+'<b>:: 24 Low: '+str(low)+'</b>'+"\n"
					coin_stats=coin_stats+'<b>:: 24 High: '+str(high)+'</b>'+"\n"
					coin_stats=coin_stats+'<b>:: Bid: '+str(bid)+'</b>'+"\n"
					coin_stats=coin_stats+'<b>:: Ask: '+str(ask)+'</b>'+"\n"
					coin_stats=coin_stats+'<b>:: Last: '+str(ask)+'</b>'+"\n"
					coin_stats=coin_stats+'<b>:: First Alert Price: '+str(first_price)+'</b>'+"\n"
					coin_stats=coin_stats+'<b>:: Price Diff Since First Alert: '+str(price_diff)+'('+str(pdiff)+'%)</b>'+"\n"

					csymbol=ticker_symbol
					csymbol=csymbol.replace("/","_",1)
					link='https://www.binance.com/en/trade/pro/'+csymbol

					coin_stats=coin_stats+':: '+str(link)

					message=message+"\n"+coin_stats
					if seen==1:
						bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode= 'HTML')
	
def list_bots(bot, update, args):
	#args[0]="twat"
	#meh=args[0]
	botlist=r.smembers("botlist")

	#txt="cunt"
	#bot.send_message(chat_id=update.message.chat_id, text=txt)	
	
	for bot_name in botlist:
		bot_name=bot_name.decode('utf-8')
		ts=float(r.get(bot_name))
		running=datetime.fromtimestamp(ts).strftime("%A, %B %d, %Y %I:%M:%S")
		txt="Bot: "+str(bot_name)+" Has been running since: "+str(running)
		print(txt)
		bot.send_message(chat_id=update.message.chat_id, text=txt)
		
		#bot.send_message(chat_id=update.message.chat_id, text=message)

def stoploss(bot, update,args):	
	symbol=args[0].upper()
	action=str(args[1].lower())

	mc = memcache.Client(['127.0.0.1:11211'], debug=0)	

	if action=="execute":
	
		key=str(symbol)+'-SLTMP'
		stoploss_price=mc.get(key)			
		
		key=str(symbol)+'-BBTMP'
		buyback_price=mc.get(key)

		message=":::SYSTEM EXECUTED A STOPLOSS OF: "+str(stoploss_price)+" WITH BUYBACK PRICE OF: "+str(buyback_price)
		bot.send_message(chat_id=update.message.chat_id, text=message)

		key=str(symbol)+'-SYSTEM-STOPLOSS'
		mc.set(key,stoploss_price,86400)			
		
		#key=str(symbol)+'-SYSTEM-BUYBACK'
		#mc.set(key,buyback_price,864)			

		return(1)
	else:
		stoploss_percent=float(args[1].lower())
		buyback_percent=float(args[2].lower())

		exchange=get_exchange()
		
		if float(stoploss_percent)>0:
			bid=update.message.from_user.id
			price=get_price(exchange,symbol)
	
			ret=exchange.fetch_closed_orders (symbol, 1);
			if ret:
				data=ret[-1]['info']
				side=data['side']
				units=float(data['executedQty'])
				last_price=float(data['price'])

				profit=price-last_price
				profit=profit*units
				prices = [last_price,price]
				for a, b in zip(prices[::1], prices[1::1]):
					percent=100 * (b - a) / a

				percent=round(percent,2)
				profit=round(profit,2)
				profit=price-last_price
				profit=profit*units
				prices = [last_price,price]
				for a, b in zip(prices[::1], prices[1::1]):
					percent=100 * (b - a) / a

				percent=round(percent,2)
				profit=round(profit,2)

				stoploss=price/100*stoploss_percent
				stoploss_price=price-stoploss

				buyback=stoploss_price/100*buyback_percent
				buyback_price=stoploss_price-buyback

				message=str(symbol)+" Price: "+str(price)+" Last Price: "+str(last_price)+" Units: "+str(units)+" Profit: "+str(profit)+' ('+str(percent)+'%)'
		
				stoploss_info=("::::STOPLOSS INFO::::\nSetting a stoploss % of: "+str(stoploss_percent)+" % Would have a stoploss price of "+str(stoploss_price)+"\nReply With /stoploss execute to execute changes")
		
				buyback_info=("::::BUYBACK INFO::::\nSetting a byback % of: "+str(buyback_percent)+" % Would have a buyback price of "+str(buyback_price)+"\nReply With /stoploss execute to execute changes")

				message=str(message)+"\n"+str(stoploss_info)+str(buyback_info)
		
				key=str(symbol)+'-SLTMP'
				mc.set(key,stoploss_price,86400)			
		
				key=str(symbol)+'-BBTMP'
				mc.set(key,buyback_price,86400)			
		
				bot.send_message(chat_id=update.message.chat_id, text=message)


def price(bot, update,args):	
	symbol=args[0].upper()
	
	exchange=get_exchange()

	bid=update.message.from_user.id
	price=get_price(exchange,symbol)
	
	ret=exchange.fetch_closed_orders (symbol, 1);
	if ret:
		data=ret[-1]['info']
		side=data['side']
		units=float(data['executedQty'])
		print(data)
		last_price=float(data['price'])
		
		profit=price-last_price
		profit=profit*units
		prices = [last_price,price]
		for a, b in zip(prices[::1], prices[1::1]):
			percent=100 * (b - a) / a

		percent=round(percent,2)
		profit=round(profit,2)

		message=str(symbol)+" Price: "+str(price)+" Last Price: "+str(last_price)+" Units: "+str(units)+" Profit: "+str(profit)+' ('+str(percent)+'%)'
		bot.send_message(chat_id=update.message.chat_id, text=message)

dispatcher = updater.dispatcher
start_handler = CommandHandler('start', start)
help_handler = CommandHandler('help', help)
ticker_handler = CommandHandler('ticker', ticker,pass_args=True)
p_handler = CommandHandler('p', ticker,pass_args=True)
market_handler = CommandHandler('market', market)
sell_handler=CommandHandler('sell', sell,pass_args=True)
price_handler=CommandHandler('price', price,pass_args=True)
stoploss_handler=CommandHandler('stoploss', stoploss,pass_args=True)
list_bots_handler=CommandHandler('listbots', list_bots,pass_args=True)
add_bot_handler=CommandHandler('addbot', add_bot,pass_args=True)
delete_bot_handler=CommandHandler('deletebot', delete_bot,pass_args=True)
alerts_handler=CommandHandler('alerts', alerts,pass_args=True)

dispatcher.add_handler(delete_bot_handler)
dispatcher.add_handler(add_bot_handler)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(stoploss_handler)
dispatcher.add_handler(list_bots_handler)
dispatcher.add_handler(ticker_handler)
dispatcher.add_handler(market_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(sell_handler)
dispatcher.add_handler(price_handler)
dispatcher.add_handler(p_handler)
dispatcher.add_handler(alerts_handler)


updater.start_polling()
