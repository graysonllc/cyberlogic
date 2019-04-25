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

config = configparser.ConfigParser()
config.read('/root/akeys/b.conf')
mysql_username=config['mysql']['MYSQL_USERNAME']
mysql_password=config['mysql']['MYSQL_PASSWORD']
mysql_hostname=config['mysql']['MYSQL_HOSTNAME']
mysql_database=config['mysql']['MYSQL_DATABASE']
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
	

def get_rsi(bot, update, args):

	try:
		pair=args[0]
		interval=args[1]
		pair=pair.upper()
		arr = []
		url="https://api.binance.com/api/v1/klines?symbol="+pair+"&interval="+interval+"&limit=30"
		r=requests.get(url)
		res = (r.content.strip())
		status = r.status_code
		trades = json.loads(res.decode('utf-8'))
		n=0
		for trade in trades:
			open_price=float(trade[0])
			close_price=float(trade[4])
			high_price=float(trade[2])
			low_price=float(trade[3])
			arr.append(close_price)
			n += 1
			
		np_arr = np.array(arr,dtype=float)
		output=talib.RSI(np_arr,timeperiod=14)
		rsi=output[-1]
		if rsi<30:
			status='Oversold'
		elif rsi>70:
			status="Overbought"
		else:
			status='Neutral'
		rsi=round(rsi)

		ret1=("Binance RSI (Relative Strength Monitor: "+str(pair)+")\n")
		ret2=("RSI :"+str(rsi)+"\tStatus: "+str(status)+"\n")
		ret3=("Candlestick Timeframe: "+interval)
		out=ret1+ret2+ret3
		bot.send_message(chat_id=update.message.chat_id, text=out)	
	except:
		error_message=("Error: something went wrong syntax is /rsi PAIR interval i.e /rsi ETHUSDT INTERVAL\nValid Intervals are 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8 h, 12h, 1d, 3d, 1w, 1m")
		error_message = str(error_message)
		bot.send_message(chat_id=update.message.chat_id, text=error_message)	

def get_articles(ftype):
	
	db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysl_database)
	cursor = db.cursor(pymysql.cursors.DictCursor)
	
	sql = """SELECT datetime,user,coin,score,link from news_reviews where date>=%s and ftype=%s order by datetime desc limit 5"""
	try:
		from datetime import date, timedelta                   
		yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

		cursor.execute(sql,(yesterday,ftype))
		
		data = ""

		for row in cursor:
			datetime=str(row['datetime'])
			score=str(row['score'])
			link=str(row['link'])
			user=str(row['user'])
			coin=str(row['coin'])
			data+=datetime+"\t submitted by: "+user+"\tcoin:"+str(coin)+"\tlink: "+link+" Score: "+score+"\n"
	
	except:
		# Rollback in case there is any error
		db.rollback()

		# disconnect from server
		db.close()
	return(data)

def query_ath(name):

	try:
		db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysl_database)
		cursor = db.cursor()
		sql = """SELECT ath_date,price from aths where coin=%s"""
		cursor.execute(sql,(name))
		for row in cursor:
			ath_date=row[0]	
			ath_price=row[1]
			ath_price='${:,.2f}'.format(ath_price)
			ret="\n"+str(name)+("\nAth Date: "+str(ath_date)+ "\n"+ str(name)+" Ath Price: "+str(ath_price))
		return(ret)
	except:
		print("some error")
	db.close()

def get_score(ftype):
	db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysl_database)	
	cursor = db.cursor(pymysql.cursors.DictCursor)
	
	sql = """
	SELECT avg(score) as score from news_reviews where date=current_date() and ftype=%s
	"""

	try:
		cursor.execute(sql,(ftype))
		for row in cursor:
			score=(row['score'])

	#Commit your changes in the database
	except:
	# Rollback in case there is any error
		db.rollback()

	# disconnect from server
	db.close()
	
	return score

def fud(bot, update, args):
	
	try:
		coin=args[0]
		link=args[1]
		score=args[2]
		coin=coin.upper()
	except:
		error_message=("Error: something went wrong syntax is /fud coin link score")
		error_message = str(error_message)
		bot.send_message(chat_id=update.message.chat_id, text=error_message)
		return 0
	
	ftype=str('fud')
	
	username = update.message.from_user.first_name
	
	db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysl_database)
	cursor = db.cursor()

	sql = """
		INSERT INTO news_reviews(datetime,date,user,ftype,coin,score,link)
		VALUES (now(),current_date(),%s,%s,%s,%s,%s)
		"""

	try:
		cursor.execute(sql,(username,ftype,coin,score,link))
		#Commit your changes in the database
		db.commit()
	except:
		# Rollback in case there is any error
		db.rollback()

		# disconnect from server
		db.close()
	
		
	fud_score=get_score('fud')
	fud_articles=get_articles('fud')
	fud_message=("\nTodays fud score is: " + str(fud_score)+"\nFud Articles: \n"+fud_articles)

	message = username.upper() + ": You said Fud score for " +coin.upper()+" is at Level: "+score+" Link: "+link+fud_message
	message = str(message)
	bot.send_message(chat_id=update.message.chat_id, text=message)
	

def fomo(bot, update, args):
	
	try:
		coin=args[0]
		coin=coin.upper()
		link=args[1]
		score=args[2]
		score_int=int(score)
	except:
		error_message=("Error: something went wrong syntax is /fomo coin link score")
		error_message = str(error_message)
		bot.send_message(chat_id=update.message.chat_id, text=error_message)
		return 0
	
	if score_int<1 or score_int>10:
		error_message=("Error: score has to be between 1 and 10 syntax is /fomo coin link score")
		error_message = str(error_message)
		bot.send_message(chat_id=update.message.chat_id, text=error_message)
		return 0
	
	try:
		coin
	except:
		error_message=("Coin cant be empty syntax is /fomo coin link score")
		error_message = str(error_message)
		bot.send_message(chat_id=update.message.chat_id, text=error_message)
		return 0
	
	ftype=str('fomo')
	
	username = update.message.from_user.first_name
	
	db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysl_database)
	cursor = db.cursor()

	sql = """
		INSERT INTO news_reviews(datetime,date,user,ftype,coin,score,link)
		VALUES (now(),current_date(),%s,%s,%s,%s,%s)
		"""

	try:
		cursor.execute(sql,(username,ftype,coin,score,link))
		#Commit your changes in the database
		db.commit()
	except:
		# Rollback in case there is any error
		db.rollback()

		# disconnect from server
		db.close()
	
		error_message=("Error: something went wrong syntax is /fomo coin link score")
		error_message = str(error_message)
		bot.send_message(chat_id=update.message.chat_id, text=error_message)
		return 0

		
	fomo_score=get_score('fomo')
	fomo_articles=get_articles('fomo')
	fomo_message=("\nTodays Fomo score is: " + str(fomo_score)+"\nFomo Articles: \n"+fomo_articles)

	message = username.upper() + ": You said Fomo score for " +coin.upper()+" is at Level: "+score+" Link: "+link+fomo_message
	message = str(message)
	bot.send_message(chat_id=update.message.chat_id, text=message)

def fomoscore(bot,update,args):
	username = update.message.from_user.first_name

	fomo_score=get_score('fomo')
	fomo_articles=get_articles('fomo')
	fomo_message=("\nTodays Fomo score is: " + str(fomo_score)+"\nFomo Articles: \n"+fomo_articles)

	bot.send_message(chat_id=update.message.chat_id, text=fomo_message)
	
	
def fudscore(bot,update,args):
	username = update.message.from_user.first_name
	fud_score=get_score('fud')
	fud_articles=get_articles('fud')
	fud_message=("\nTodays Fud score is: " + str(fud_score)+"\nFud Articles: \n"+fud_articles)

	bot.send_message(chat_id=update.message.chat_id, text=fud_message)

def is_moon():
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
			#print(row_data)
			p_1h=row_data['percent_change_1h']
			p_24h=row_data["percent_change_24h"]
			p_7d=row_data["percent_change_7d"]
			if p_1h > 5:
				plus_1h += 1
			if p_24h > 0:
				plus_24h += 1
			if p_7d > 0:
				plus_7d += 1
		
		minus_1h = int(100) - plus_1h
		minus_24h = int(100) - plus_24h
		minus_7d = int(100) - plus_7d

		
		try:
			ath=query_ath(name)
		except:
			ath=""
			
		ret=("Market Health For Top 100\n1 Hr Green: "+str(plus_1h)+"% Red: "+str(minus_1h)+ "%\n24 Hr Green: "+str(plus_24h)+"% Red: "+str(minus_24h)+ "%\n7 Day Green: "+str(plus_7d)+"% Red: "+str(minus_7d)+ "%"+str(ath)) 
	except:
		print("some error")
	return(ret)


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

				ret=str(ticker.upper()) +" #"+str(rank)+"\nPrice: $"+str(price_usd)+" BTC: "+str(price_btc)+"\n1hr ("+change_1h+ "%) 24hr("	+change_24h+ "%) 7D("	+change_7d+ "%)""\nMarket Cap "+str(market_cap)+ "\nMax Supply: "+str(total_supply)+"\nCirculating Supply: "+str(circulating+str(ath))

				
	if ret=='':
		return("not found")
	else:
		return(ret)

def start(bot, update):
	help="I am T800, i can do the following commands:\n\n/market to get global market data, and market health!\n/ticker SYMBOL to get coin Ticker and ATH\n/fomo coinname  link score to report a fomo article and score it\n/fud coinname link score to report a fud article and score it\n/fomoscore to see todays fomo score and articles\n/fudscore to see todays fud score and articles\n/rsi ETHUSDT INTERVAL (Valid Intervals are 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8 h, 12h, 1d, 3d, 1w, 1m)\nThis is binance RSI Only, replace ETHUSDT with the pair u want";
	bot.send_message(chat_id=update.message.chat_id, text=help)
	
def help(bot, update):
	help="I am T800, i can do the following commands:\n\n/market to get global market data, and market health!\n/ticker SYMBOL to get coin Ticker and ATH\n/fomo coinname  link score to report a fomo article and score it\n/fud coinname link score to report a fud article and score it\n/fomoscore to see todays fomo score and articles\n/fudscore to see todays fud score and articles\n/rsi ETHUSDT INTERVAL (Valid Intervals are 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8 h, 12h, 1d, 3d, 1w, 1m)\nThis is binance RSI only, replace ETHUSDT with the pair u want";

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
	redis_key="bconfig-"+bot_name

	r.hdel(redis_key,'*')
	bot.send_message(chat_id=update.message.chat_id, text=ret)

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
		bot_name=symbol
		
		r.sadd("botlist", bot_name)
		now = datetime.now()
		timestamp = datetime.timestamp(now)
		r.set(symbol,timestamp)
		running=datetime.fromtimestamp(timestamp).strftime("%A, %B %d, %Y %I:%M:%S")
	
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
		ret=ret+"\n\nIf you ever want to kill it issue /deletebot "+str(symbol)
		bot.send_message(chat_id=update.message.chat_id, text=ret)	

	else:
		
		trading_on=args[0]
		rsi_symbol=args[1]
		trading_pair=args[2]
		units=args[3]
		trade_from=args[4]
		trade_to=args[5]
		buy_pos=args[6]
		sell_pos=args[7]
		stoploss_percent=args[8]
		use_stoploss=args[9]
		candle_size=args[10]
		safeguard_percent=args[11]
		rsi_buy=args[12]
		rsi_sell=args[13]
		live=args[14]
		bot_name=trading_pair
		symbol=bot_name
		if r.sismember("botlist", trading_pair):
			ts=float(r.get(bot_name).decode('utf-8'))
			print(ts)
			running=datetime.fromtimestamp(ts).strftime("%A, %B %d, %Y %I:%M:%S")
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
			ret=ret+"\n::TA Candle Size: "+candle_size
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
			"live":str(live)}
			
			print(bot_config)
			ksymbol=str(symbol)

			redis_key="bconfig-tmp"
			conn.hmset(redis_key, bot_config)
			bot.send_message(chat_id=update.message.chat_id, text=ret)
	
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
news_handler = CommandHandler('news', news)
fud_handler = CommandHandler('fud', fud,pass_args=True)
fomo_handler = CommandHandler('fomo', fomo,pass_args=True)
fomoscore_handler = CommandHandler('fomoscore', fomoscore,pass_args=True)
fudscore_handler = CommandHandler('fudscore', fudscore,pass_args=True)
rsi_handler = CommandHandler('rsi', get_rsi,pass_args=True)
sell_handler=CommandHandler('sell', sell,pass_args=True)
price_handler=CommandHandler('price', price,pass_args=True)
stoploss_handler=CommandHandler('stoploss', stoploss,pass_args=True)
list_bots_handler=CommandHandler('listbots', list_bots,pass_args=True)
add_bot_handler=CommandHandler('addbot', add_bot,pass_args=True)
delete_bot_handler=CommandHandler('deletebot', delete_bot,pass_args=True)

dispatcher.add_handler(delete_bot_handler)
dispatcher.add_handler(add_bot_handler)
dispatcher.add_handler(rsi_handler)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(stoploss_handler)
dispatcher.add_handler(list_bots_handler)
dispatcher.add_handler(ticker_handler)
dispatcher.add_handler(market_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(news_handler)
dispatcher.add_handler(fud_handler)
dispatcher.add_handler(fomo_handler)
dispatcher.add_handler(fudscore_handler)
dispatcher.add_handler(fomoscore_handler)
dispatcher.add_handler(sell_handler)
dispatcher.add_handler(price_handler)
dispatcher.add_handler(p_handler)

updater.start_polling()
