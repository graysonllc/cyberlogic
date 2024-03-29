import argparse
import heapq
import configparser
import os
import sys
import redis
import memcache
import ccxt

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
    'verbose': False,  # switch it to Fal_se if you don't want the HTTP log
	})
	return(exchange)

def fetch_prices(exchange, symbol):
	ticker = exchange.fetch_ticker(symbol.upper())
	return(ticker)


def replace_last(source_string, replace_what, replace_with):
    head, _sep, tail = source_string.rpartition(replace_what)
    return head + replace_with + tail


def work_units(symbol,budget):

	symbol=symbol.upper()
	ticker_symbol=symbol

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
	
	if trade_to=='ETH':
		tickers=fetch_prices(exchange,'ETH/USDT')
		trade_to_price=float(tickers['close'])
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])
		fraction_to_budget=budget/trade_to_price
		units=fraction_to_budget/pair_price	
	elif trade_to=='BTC':
		tickers=fetch_prices(exchange,'BTC/USDT')
		trade_to_price=float(tickers['close'])
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])
		fraction_to_budget=budget/trade_to_price
		units=fraction_to_budget/pair_price
	elif trade_to=='BNB':
		tickers=fetch_prices(exchange,'BNB/USDT')
		trade_to_price=float(tickers['close'])
		tickers=fetch_prices(exchange,symbol)
		pair_price=float(tickers['close'])
		fraction_to_budget=budget/trade_to_price
		units=fraction_to_budget/pair_price
	else:
		units=budget/pair_price
	
	print("Trading From: "+str(trade_from))
	print("Trade To: "+str(trade_to))
	print(str(trade_to)+ "Price: "+str(trade_to_price))
	print("Pair Price: "+str(pair_price))
	print("Fraction Of "+str(trade_to)+" To "+str(budget)+" is: "+str(fraction_to_budget))
	print("Units to Execute is: "+str(units))	
	
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
