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
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib'
sys.path.append(root + '/python')

import talib
import numpy as np
import ccxt  # noqa: E402
import nickbot

redis_server = redis.Redis(host='localhost', port=6379, db=0)

def main(symbol,trading_from,trading_to,stop_units,stop_add,decrease_per,increase_per,stoploss_percent,percent_drop_1hour,percent_drop_15min,percent_drop_5min,percent_drop_10min):

	stablecoin=trading_to
	increase_per=float(increase_per)
	decrease_per=float(decrease_per)
	exchange=nickbot.get_exchange()
	
	print("Settings: ")
	print("P5" +str(percent_drop_5min))
	print("P15" +str(percent_drop_15min))
	print("P10" +str(percent_drop_10min))
	print("P1H" +str(percent_drop_1hour))
		

	ticker = exchange.fetch_ticker(symbol.upper())
	pair=symbol
	bid=float(ticker['bid'])
	last=float(ticker['last'])
	ask=float(ticker['ask'])
	open=float(ticker['open'])
	close=float(ticker['close'])
	high=float(ticker['high'])
	low=float(ticker['low'])
	volume=float(ticker['quoteVolume'])
	price=close
	stop_add=float(stop_add)
	stop_action=int(0)
	price_last=int(0)
	redis_key=str(pair)+str("price-last")	
	
	if redis_server.get(redis_key):
		price_last=redis_server.get(redis_key).decode('utf-8')
		price_last=float(price_last)
	redis_server.set(redis_key,price)
	
	print("Price Now: "+str(price))
	print("Price Last: "+str(price_last))
	print("Stored Symbol: "+str(symbol))
	prices=nickbot.store_prices(symbol,price,volume)
	#print(prices)
	price_1min=prices['price-1min']
	percent_1min=prices['price-percent-1min']

	price_2min=prices['price-2min']
	percent_2min=prices['price-percent-2min']

	price_3min=prices['price-3min']
	percent_3min=prices['price-percent-3min']
		
	price_5min=prices['price-5min']
	percent_5min=prices['price-percent-5min']
	
	price_10min=prices['price-10min']
	percent_10min=prices['price-percent-10min']
	
	price_15min=prices['price-15min']
	percent_15min=prices['price-percent-15min']
		
	price_30min=prices['price-30min']
	percent_30min=prices['price-percent-30min']
	
	price_1hour=prices['price-1hour']
	percent_1hour=prices['price-percent-1hour']

	price_2hour=prices['price-2hour']
	percent_2hour=prices['price-percent-2hour']
	
	price_3hour=prices['price-3hour']
	percent_3hour=prices['price-percent-3hour']
		
	price_6hour=prices['price-6hour']
	percent_6hour=prices['price-percent-6hour']
	
	price_12hour=prices['price-12hour']
	percent_12hour=prices['price-percent-12hour']
	
	price_24hour=prices['price-24hour']
	percent_24hour=prices['price-percent-24hour']
	
	stoploss_percent=float(stoploss_percent)
	new_stoploss=round(float(price-price/100*stoploss_percent))
	new_stoploss=round(new_stoploss,2)
	hard_stoploss=new_stoploss
	stop_price=new_stoploss+stop_add
	
	last_array=nickbot.fetch_last_order(exchange,symbol)
	last_price=float(last_array['price'])
	last_type=last_array['side']
	last_units=last_array['executedQty']

	redis_key=str(symbol)+str("STOP-ACTION")
	#print(last_array)
	#print("LT: "+str(last_type))

	orders = exchange.fetch_open_orders(symbol,1)
	if orders:
		data=orders[0]['info']
		order_type=data['type']
		order_id=data['orderId']
		order_timestamp=data['time']/1000
		start_time=order_timestamp
		elapsed = time.time() - start_time
		elapsed=round(elapsed)
					
		print("DB ELAPSED: "+str(elapsed))
		print("DB TYPE: "+str(order_type))
		#Watch to run away buy ins!
			
		if order_type=='LIMIT' and elapsed>=300:
			exchange.cancelOrder(order_id,symbol)

	print("LT: "+str(last_type))
	if last_type=='SELL':
		last_stop_price=last_price

		redis_key=str(symbol)+str("BROADCAST-SENT")
		if redis_server.get(redis_key):
			seen=int(1)
		else:
			data="STOPLOSS HAS HIT WE SOLD: "+str(last_units)+" AT: "+str(last_price)
			nickbot.broadcast_tether('506872080',data)	
			nickbot.broadcast_tether('446619309',data)
			nickbot.broadcast_tether('693711905',data)
			
			redis_server.set(redis_key,1)
			redis_key=str(symbol)+str("STOP-ACTION")
			redis_server.set(redis_key,1)
	
		diff=nickbot.diff_percent(last_price,price)
		diff_abs=abs(diff)
		
		if price>last_price:
			direction='increased'
		else:
			direction='decreased'
			
		if diff<-decrease_per:
			orders = exchange.fetch_open_orders(symbol,1)
			if orders:
				data=orders[0]['info']
				order_type=data['type']
				order_id=data['orderId']
				order_timestamp=data['time']/1000
				start_time=order_timestamp
				elapsed = time.time() - start_time
				elapsed=round(elapsed)
					
				print("DB ELAPSED: "+str(elapsed))
				print("DB TYPE: "+str(order_type))
				#Watch to run away buy ins!
			
				if order_type=='LIMIT' and elapsed>=300:
					exchange.cancelOrder(order_id,symbol)
			else:
				total=float(last_units)*float(last_price)
				data="STOPLOSS WE SOLD: "+str(last_units)+" AT: "+str(last_price)+" TOTAL: "+str(total)
				data=data+"\nSINCE STOPLOSS HIT PRICE HAS DECREASED BY: "+str(diff)+" % AND IS NOW: "+str(price)+" BUYING THE CUNT BACK"+" DIRECTION: "+str(direction)
				nickbot.broadcast_tether_trade('506872080',data)	
				nickbot.broadcast_tether_trade('446619309',data)
				nickbot.broadcast_tether_trade('693711905',data)				
				ret=exchange.create_order (symbol, 'limit', 'buy', last_units, price)
				#time.sleep(10)
	
		elif diff>increase_per:
			orders = exchange.fetch_open_orders(symbol,1)
			if orders:
				data=orders[0]['info']
				order_type=data['type']
			else:
				data="STOPLOSS WE SOLD: "+str(last_units)+" AT: "+str(last_price)
				data=data+"\nSINCE STOPLOSS HIT PRICE HAS INCREASED BY: "+str(diff)+" % AND IS NOW: "+str(price)+" BUYING THE CUNT BACK"+" DIRECTION: "+str(direction)
				nickbot.broadcast_tether('506872080',data)	
				nickbot.broadcast_tether('446619309',data)
				nickbot.broadcast_tether('693711905',data)
				ret=exchange.create_order (symbol, 'limit', 'buy', last_units, price)
				#time.sleep(10)
		else:
			total=float(last_units)*float(last_price)

			data="STOPLOSS WE SOLD: "+str(last_units)+" AT: "+str(last_price)+" TOTAL: "+str(total)

			buyback=float(last_units)*float(price)
			buyback=round(buyback,2)
			profit=round(float(total)-float(buyback),2)
			data=data+"\nSINCE STOPLOSS HIT PRICE DIFF IS: "+str(diff)+" % AND IS NOW: "+str(price)+" DIRECTION: "+str(direction)+" WOULD COST: "+str(buyback)+" TO BUYBACK PROFIT WOULD BE: "+str(profit)
			redis_key=str(symbol)+str("STOP-ACTION-BC")
			if redis_server.get(redis_key):		
				seen=int(1)
			else:
				nickbot.broadcast_tether('506872080',data)	
				nickbot.broadcast_tether('446619309',data)
				nickbot.broadcast_tether('693711905',data)
				redis_key=str(symbol)+str("STOP-ACTION-BC")
				redis_server.setex(redis_key,1,1)
		stop_action=1
		return(1)
			
	diff=nickbot.diff_percent(last_price,price)
	data="<b>TRADING PAIR:</b> "+str(symbol)+"\t<b>PRICE:</b> "+str(price)+" <b>LAST PRICE:</b> "+str(last_price)+"\t<b>LAST TYPE:</b> "+str(last_type)+"\t"+str(diff)+" <b>PERCENT DIFFERENCE</b>\n"
	data_add="<b>1M:</b> "+str(price_1min)+" "+str(percent_1min)+str('%')+",<b>2M:</b> "+str(price_2min)+" "+str(percent_2min)+str('%')+",<b>3M:</b> "+str(price_3min)+" "+str(percent_3min)+str('%')+",<b>5M:</b> "+str(price_5min)+" "+str(percent_5min)+str('%')+",<b>10M:</b> "+str(price_10min)+" "+str(percent_10min)+"%,<b>15M:</b> "+str(price_15min)+" "+str(percent_15min)+str('%')+",<b>30M:</b> "+str(price_30min)+" "+str(percent_30min)+str('%')+",<b>1H:</b> "+str(price_1hour)+" "+str(percent_1hour)+str('%')+",<b>3H:</b> "+str(price_3hour)+" "+str(percent_3hour)+str('%')+",<b>6H:</b> "+str(price_6hour)+" "+str(percent_6hour)+str('%')+",<b>12H:</b> "+str(price_12hour)+" "+str(percent_12hour)+str('%')+",<b>24H:</b> "+str(price_24hour)+" "+str(percent_24hour)+str('%')
	
	rsi=nickbot.get_rsi(symbol,'15m')

	print("Debug: PP2H; "+str(percent_2hour))
	percent_2hour=0
	nickbot.log_autotether_stats(symbol,price,percent_1min,percent_2min,percent_3min,percent_5min,percent_10min,percent_15min,percent_30min,percent_1hour,percent_3hour,percent_6hour,percent_12hour,percent_24hour,rsi)

	data=str(data)+"\n"+str(data_add)+"\n<b>RSI:</b> "+str(rsi)
	nickbot.broadcast_tether('506872080',data)
	nickbot.broadcast_tether('693711905',data)
	print("STOP ACTION: "+str(stop_action))
	if stop_action==0:
	#if stop_action==0 and float(percent_3min)<-0.3 or stop_action==0 and float(percent_1min)<-0.3:
	# or stop_action==0 and float(percent-30min)<-0.40:
		print(symbol+" Stop action is zero\n")
		orders = exchange.fetch_open_orders(symbol,1)
		if orders:
			data=orders[0]['info']
			order_type=data['type']
			order_id=data['orderId']
			print(data)
			order_timestamp=data['time']/1000
			start_time=order_timestamp
			elapsed = time.time() - start_time
			elapsed=round(elapsed)
					
			print("DB ELAPSED: "+str(elapsed))
			print("DB TYPE: "+str(order_type))
			#Watch to run away buy ins!
			
			if order_type=='LIMIT' and elapsed>=300:
				exchange.cancelOrder(order_id,symbol)
					
		else:
			print("Cunt are we here")
			
			diff=nickbot.diff_percent(last_price,price)
			diff_abs=abs(diff)
			print("Diff: "+str(diff))
			print("Diff ABS: "+str(diff))

			data="TRADING PAIR: "+str(symbol)+"\tPRICE: "+str(price)+" LAST PRICE: "+str(last_price)+"\tLAST TYPE: "+str(last_type)+"\t"+str(diff)+" PERCENT DIFFERENCE\n"
			data_add="1M: "+str(price_1min)+" "+str(percent_1min)+str('%')+"\t2M: "+str(price_2min)+" "+str(percent_2min)+str('%')+"\t3M: "+str(price_3min)+" "+str(percent_3min)+str('%')+"\t5M: "+str(price_5min)+" "+str(percent_5min)+str('%')+"\t10M: "+str(price_10min)+" "+str(percent_10min)+"%\t15M: "+str(price_15min)+" "+str(percent_15min)+str('%')+"\t30M: "+str(price_30min)+" "+str(percent_30min)+str('%')+"\t1H: "+str(price_1hour)+" "+str(percent_1hour)+str('%')+"\t3H: "+str(price_3hour)+" "+str(percent_3hour)+str('%')+"\t6H: "+str(price_6hour)+" "+str(percent_6hour)+str('%')+"\t12H: "+str(price_12hour)+" "+str(percent_12hour)+str('%')+"\t24H: "+str(price_24hour)+" "+str(percent_24hour)+str('%')
			print(str(data)+"\n"+str(data_add))
			if rsi>95:
				percent=50
				balances=exchange.fetch_balance ()
				balance=float(format(balances[trading_from]['total'],'.8f'))
				units=units=balance/100*float(percent)
				units=round(units,2)
				
				action='tether'
				reason='rsi over 85'
				
				book=nickbot.fetch_order_book(exchange,pair,'asks',100)
				sell_price=float(book[0][0])
				total_amount=round(sell_price*units,2)
				message="TETHERING: "+str(symbol)+" UNITS: "+str(units)+" PRICE: "+str(sell_price)+" TO STABLE COIN: "+str(stablecoin)+" TOTAL USD: "+str(total_amount)+" REASON: "+str(reason)
				print(message)
				
				nickbot.broadcast_tether_trade('506872080',message)	
				nickbot.broadcast_tether_trade('446619309',message)
				nickbot.broadcast_tether_trade('693711905',message)
				
				exchange=nickbot.get_exchange()
				ret=exchange.create_order (pair, 'limit', 'sell', units, sell_price)

				nickbot.log_autotether_trades(symbol,price,units,percent,action,reason)
			#elif float(percent_24hour)>=5:
			#	percent=50
			#	balances=exchange.fetch_balance ()
			#	balance=float(format(balances[trading_from]['total'],'.8f'))
			#	units=units=balance/100*float(percent)
			#	units=round(units,2)
				
			#	book=nickbot.fetch_order_book(exchange,pair,'bids',100)
			#	sell_price=float(book[0][0])
			#	total_amount=round(sell_price*units,2)
			#	action='tether'
			#	reason='24 hour over 5 percent'
			#	message="TETHERING: "+str(symbol)+" UNITS: "+str(units)+" PRICE: "+str(sell_price)+" TO STABLE COIN: "+str(stablecoin)+" TOTAL USD: "+str(total_amount)+" REASON: "+str(reason)

			#	print(message)
				
			#	nickbot.broadcast_tether_trade('506872080',message)	
			#	nickbot.broadcast_tether_trade('446619309',message)
			#	nickbot.broadcast_tether_trade('693711905',message)
				
			#	exchange=nickbot.get_exchange()
			#	ret=exchange.create_order (pair, 'limit', 'sell', units, sell_price)
			#	action='tether'
			#	reason='rsi over 80'
			#	nickbot.log_autotether_trades(symbol,price,units,percent,action,reason)
			
			diff=nickbot.diff_percent(last_price,price)
			print("DEBUGDIFF: "+str(diff))

			prices=nickbot.store_prices(symbol,price,volume)
			price_1min=prices['price-1min']
			percent_1min=prices['price-percent-1min']
			price_2min=prices['price-2min']
			percent_2min=prices['price-percent-2min']
			price_3min=prices['price-3min']
			percent_3min=prices['price-percent-3min']
			price_5min=prices['price-5min']
			percent_5min=prices['price-percent-5min']
			price_10min=prices['price-10min']
			percent_10min=prices['price-percent-10min']
			price_15min=prices['price-15min']
			percent_15min=prices['price-percent-15min']
			price_30min=prices['price-30min']
			percent_30min=prices['price-percent-30min']
			price_1hour=prices['price-1hour']
			percent_1hour=prices['price-percent-1hour']
			price_2hour=prices['price-2hour']
			percent_2hour=prices['price-percent-2hour']
			price_3hour=prices['price-3hour']
			percent_3hour=prices['price-percent-3hour']
			price_6hour=prices['price-6hour']
			percent_6hour=prices['price-percent-6hour']
			price_12hour=prices['price-12hour']
			percent_12hour=prices['price-percent-12hour']
			price_24hour=prices['price-24hour']
			percent_24hour=prices['price-percent-24hour']

			print("DBP5M: "+str(percent_5min))
			print("DBP5MD: "+str(percent_drop_5min))
			
			if float(percent_1min)>0.5:
				percent=20
				balances=exchange.fetch_balance ()
				balance=float(format(balances[trading_from]['total'],'.8f'))
				print(str(balance))
				units=units=balance/100*float(percent)
				units=round(units,2)
				
				book=nickbot.fetch_order_book(exchange,pair,'bids',100)
				sell_price=float(book[0][0])
				total_amount=round(sell_price*units,2)
				
				exchange=nickbot.get_exchange()
				#ret=exchange.create_order (pair, 'limit', 'sell', units, sell_price)
				action='tether'
				reason='Per 1Min<=-0.5 '
				nickbot.log_autotether_trades(symbol,price,units,percent,action,reason)

				message="TETHERING: "+str(symbol)+" UNITS: "+str(units)+" PRICE: "+str(sell_price)+" TO STABLE COIN: "+str(stablecoin)+" TOTAL USD: "+str(total_amount)+" REASON: "+str(reason)
				print(message)
				
				nickbot.broadcast_tether_trade('506872080',message)	
				nickbot.broadcast_tether_trade('446619309',message)
				nickbot.broadcast_tether_trade('693711905',message)
			if float(percent_1min)<-0.5 and diff<=-0.5:
				percent=5
				balances=exchange.fetch_balance ()
				balance=float(format(balances[trading_from]['total'],'.8f'))
				print(str(balance))
				units=units=balance/100*float(percent)
				units=round(units,2)
				
				book=nickbot.fetch_order_book(exchange,pair,'bids',100)
				sell_price=float(book[5][0])
				total_amount=round(sell_price*units,2)
				
				exchange=nickbot.get_exchange()
				#ret=exchange.create_order (pair, 'limit', 'sell', units, sell_price)
				action='tether'
				reason='Per 1Min<=-0.5 '
				nickbot.log_autotether_trades(symbol,price,units,percent,action,reason)

				message="TETHERING: "+str(symbol)+" UNITS: "+str(units)+" PRICE: "+str(sell_price)+" TO STABLE COIN: "+str(stablecoin)+" TOTAL USD: "+str(total_amount)+" REASON: "+str(reason)
				print(message)
				
				nickbot.broadcast_tether_trade('506872080',message)	
				nickbot.broadcast_tether_trade('446619309',message)
				nickbot.broadcast_tether_trade('693711905',message)
					
					
			elif float(percent_5min)<=-float(percent_drop_5min) and dif<=-float(percent_drop_5min):
				percent=5
				balances=exchange.fetch_balance ()
				balance=float(format(balances[trading_from]['total'],'.8f'))
				print(str(balance))
				units=units=balance/100*float(percent)
				units=round(units,2)
				
				book=nickbot.fetch_order_book(exchange,pair,'bids',100)
				sell_price=float(book[5][0])
				total_amount=round(sell_price*units,2)
				
				exchange=nickbot.get_exchange()
				#ret=exchange.create_order (pair, 'limit', 'sell', units, sell_price)
				action='tether'
				reason='Per 5Min<='+str(percent_drop_5min)
				nickbot.log_autotether_trades(symbol,price,units,percent,action,reason)

				message="TETHERING: "+str(symbol)+" UNITS: "+str(units)+" PRICE: "+str(sell_price)+" TO STABLE COIN: "+str(stablecoin)+" TOTAL USD: "+str(total_amount)+" REASON: "+str(reason)
				print(message)
				
				nickbot.broadcast_tether_trade('506872080',message)	
				nickbot.broadcast_tether_trade('446619309',message)
				nickbot.broadcast_tether_trade('693711905',message)
			elif float(percent_10min)<=-float(percent_drop_10min) and diff<=-float(percent_drop_10min):
				percent=5
				balances=exchange.fetch_balance ()
				balance=float(format(balances[trading_from]['total'],'.8f'))
				print(str(balance))
				units=units=balance/100*float(percent)
				units=round(units,2)
				
				book=nickbot.fetch_order_book(exchange,pair,'bids',100)
				sell_price=float(book[5][0])
				total_amount=round(sell_price*units,2)
				
				#ret=exchange.create_order (pair, 'limit', 'sell', units, sell_price)
				action='tether'
				reason='Per 10Min<='+str(percent_drop_10min)
				nickbot.log_autotether_trades(symbol,price,units,percent,action,reason)

				message="TETHERING: "+str(symbol)+" UNITS: "+str(units)+" PRICE: "+str(sell_price)+" TO STABLE COIN: "+str(stablecoin)+" TOTAL USD: "+str(total_amount)+" REASON: "+str(reason)
				print(message)
				
				nickbot.broadcast_tether_trade('506872080',message)	
				nickbot.broadcast_tether_trade('446619309',message)
				nickbot.broadcast_tether_trade('693711905',message)

			elif float(percent_15min)<=-float(percent_drop_15min) and diff<=-float(percent_drop_15min):
				percent=5
				balances=exchange.fetch_balance ()
				balance=float(format(balances[trading_from]['total'],'.8f'))
				print(str(balance))
				units=units=balance/100*float(percent)
				units=round(units,2)
				
				book=nickbot.fetch_order_book(exchange,pair,'bids',100)
				sell_price=float(book[5][0])
				total_amount=round(sell_price*units,2)
				
				#ret=exchange.create_order (pair, 'limit', 'sell', units, sell_price)
				action='tether'
				reason='Per 15Min<='+str(percent_drop_15min)
				nickbot.log_autotether_trades(symbol,price,units,percent,action,reason)

				message="TETHERING: "+str(symbol)+" UNITS: "+str(units)+" PRICE: "+str(sell_price)+" TO STABLE COIN: "+str(stablecoin)+" TOTAL USD: "+str(total_amount)+" REASON: "+str(reason)
				print(message)
				
				nickbot.broadcast_tether_trade('506872080',message)	
				nickbot.broadcast_tether_trade('446619309',message)
				nickbot.broadcast_tether_trade('693711905',message)

			elif float(percent_30min)<=-1 and diff<=-1:
				percent=5
				balances=exchange.fetch_balance ()
				balance=float(format(balances[trading_from]['total'],'.8f'))
				print(str(balance))
				units=units=balance/100*float(percent)
				units=round(units,2)
				
				book=nickbot.fetch_order_book(exchange,pair,'bids',100)
				sell_price=float(book[5][0])
				total_amount=round(sell_price*units,2)
				
				#ret=exchange.create_order (pair, 'limit', 'sell', units, sell_price)
				action='tether'
				reason='Per 30Min<=-1'
				nickbot.log_autotether_trades(symbol,price,units,percent,action,reason)

				message="TETHERING: "+str(symbol)+" UNITS: "+str(units)+" PRICE: "+str(sell_price)+" TO STABLE COIN: "+str(stablecoin)+" TOTAL USD: "+str(total_amount)+" REASON: "+str(reason)
				print(message)
				
				nickbot.broadcast_tether_trade('506872080',message)	
				nickbot.broadcast_tether_trade('446619309',message)
				nickbot.broadcast_tether_trade('693711905',message)
			elif float(percent_1hour)<=percent_drop_1hour and diff<=-float(percent_drop_1hour):
				percent=5
				balances=exchange.fetch_balance ()
				balance=float(format(balances[trading_from]['total'],'.8f'))
				print(str(balance))
				units=units=balance/100*float(percent)
				units=round(units,2)
				
				book=nickbot.fetch_order_book(exchange,pair,'bids',100)
				sell_price=float(book[5][0])
				total_amount=round(sell_price*units,2)
				
				#ret=exchange.create_order (pair, 'limit', 'sell', units, sell_price)
				action='tether'
				reason='Per 1hour <='+str(percent_drop_1hour)
				nickbot.log_autotether_trades(symbol,price,units,percent,action,reason)

				message="TETHERING: "+str(symbol)+" UNITS: "+str(units)+" PRICE: "+str(sell_price)+" TO STABLE COIN: "+str(stablecoin)+" TOTAL USD: "+str(total_amount)+" REASON: "+str(reason)
				print(message)
				
				nickbot.broadcast_tether_trade('506872080',message)	
				nickbot.broadcast_tether_trade('446619309',message)
				nickbot.broadcast_tether_trade('693711905',message)
			elif float(percent_15min)<=-percent_drop_15min and diff<=float(percent_drop_15min):
				percent=5
				balances=exchange.fetch_balance ()
				balance=float(format(balances[trading_from]['total'],'.8f'))
				print(str(balance))
				units=units=balance/100*float(percent)
				units=round(units,2)
				
				book=nickbot.fetch_order_book(exchange,pair,'bids',100)
				sell_price=float(book[5][0])
				total_amount=round(sell_price*units,2)
				
				#ret=exchange.create_order (pair, 'limit', 'sell', units, sell_price)
				action='tether'
				reason='Per 15Min<='+str(percent_drop_15min)
				nickbot.log_autotether_trades(symbol,price,units,percent,action,reason)

				message="TETHERING: "+str(symbol)+" UNITS: "+str(units)+" PRICE: "+str(sell_price)+" TO STABLE COIN: "+str(stablecoin)+" TOTAL USD: "+str(total_amount)+" REASON: "+str(reason)
				print(message)
				
				nickbot.broadcast_tether_trade('506872080',message)	
				nickbot.broadcast_tether_trade('446619309',message)
				nickbot.broadcast_tether_trade('693711905',message)
			elif float(percent_12hour)<=-2 and diff<=-float(1):
				percent=5
				balances=exchange.fetch_balance ()
				balance=float(format(balances[trading_from]['total'],'.8f'))
				print(str(balance))
				units=units=balance/100*float(percent)
				units=round(units,2)
				
				book=nickbot.fetch_order_book(exchange,pair,'bids',100)
				sell_price=float(book[5][0])
				total_amount=round(sell_price*units,2)
				
				#ret=exchange.create_order (pair, 'limit', 'sell', units, sell_price)
				action='tether'
				reason='Per 12hour<=-2'
				nickbot.log_autotether_trades(symbol,price,units,percent,action,reason)

				message="TETHERING: "+str(symbol)+" UNITS: "+str(units)+" PRICE: "+str(sell_price)+" TO STABLE COIN: "+str(stablecoin)+" TOTAL USD: "+str(total_amount)+" REASON: "+str(reason)
				print(message)
				
				nickbot.broadcast_tether_trade('506872080',message)	
				nickbot.broadcast_tether_trade('446619309',message)
				nickbot.broadcast_tether_trade('693711905',message)
			elif float(percent_24hour)>=10:
				percent=70
				balances=exchange.fetch_balance ()
				balance=float(format(balances[trading_from]['total'],'.8f'))
				print(str(balance))
				units=units=balance/100*float(percent)
				units=round(units,2)
				
				book=nickbot.fetch_order_book(exchange,pair,'bids',100)
				sell_price=float(book[5][0])
				total_amount=round(sell_price*units,2)
				
				#ret=exchange.create_order (pair, 'limit', 'sell', units, sell_price)
				action='tether'
				reason='Per 12hour<=-2'
				nickbot.log_autotether_trades(symbol,price,units,percent,action,reason)

				message="TETHERING: "+str(symbol)+" UNITS: "+str(units)+" PRICE: "+str(sell_price)+" TO STABLE COIN: "+str(stablecoin)+" TOTAL USD: "+str(total_amount)+" REASON: "+str(reason)
				print(message)
				
				nickbot.broadcast_tether_trade('506872080',message)	
				nickbot.broadcast_tether_trade('446619309',message)
				nickbot.broadcast_tether_trade('693711905',message)

		#print(prices)
	#else:
		
e=0

###THINK OF A BETTER WAY TO STORE THE KEYS MAYBE WITH TIMESTAMP GIVE 5 SECS EACH WAY ON TS RANGE X-Y
#move stoploss up if 5min 1 min etc is up by X percent step up stoploss as a division of that
#symbol,stop_units,stop_add,decrease_per,increase_per,stoploss_percent
#Think about some TA to RSI
while True:
	try:
		print("----STARTING BTC/USDT\n")
		decrease_per=float(2)
		stop_units=float(0.01)
		stop_add=float(0.5)
		increase_per=float(0.3)
		stoploss_per=float(0.75)
	
		percent_drop_15min=float(1)
		percent_drop_1hour=float(1)
		percent_drop_5min=float(0.7)
		percent_drop_10min=float(1)

		main('BTC/USDT','BTC','USDT',stop_units,stop_add,decrease_per,increase_per,stoploss_per,percent_drop_1hour,percent_drop_15min,percent_drop_5min,percent_drop_10min)

		print("----ENDING BTC/USDT\nn")

		#print("----STARTING ETH/USDT\n")
		#decrease_per=float(2)
		#stop_units=float(0.5)
		#stop_add=float(0.5)
		#increase_per=float(1)
		#stoploss_per=float(0.75)
		#percent_drop_1hour=float(1.2)
		#percent_drop_15min=float(1.2)
		#percent_drop_10min=float(0.9)
		#percent_drop_5min=float(0.9)

		#main('ETH/USDT','ETH','USDT',stop_units,stop_add,decrease_per,increase_per,stoploss_per,percent_drop_1hour,percent_drop_15min,percent_drop_5min,percent_drop_10min)
		print("----ENDING ETH/USDT\nn")
	
		print("Cycle !!!!!\n")
	except:
		e=1
	sleep(0.5)
