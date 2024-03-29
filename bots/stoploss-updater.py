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
import datetime
import heapq
import nickbot

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib'
sys.path.append(root + '/python')

mc = memcache.Client(['127.0.0.1:11211'], debug=0)

#checkposts

r = redis.Redis(host='localhost', port=6379, db=0)

botlist=r.smembers("botlist")

print(":::STOPLOSS/MOVER Polling Running Bots\n")

import ccxt  # noqa: E402
				
exchange=nickbot.get_exchange()

def loop_bots():
	
	exchange=nickbot.get_exchange()
	botlist=r.smembers("botlist")
	
	for bot_name in botlist:
	
		buy_array=float(0.0)
		new_stoploss=float(0.0)
		last_stoploss=float(0.0)
		market_price=float(0.0)

		bot_name=bot_name.decode('utf-8')
		symbol=bot_name.upper()
		print(str(symbol))

		orders = exchange.fetch_open_orders(symbol,1)

		#IF theres still an open order no bot shit here
		open_order=len(orders)
		if open_order:
			continue

		ts=float(r.get(bot_name))
		running=datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
		redis_key="bconfig-"+symbol		
		last_stoploss=0
		all=r.hgetall(redis_key)
		
		trade_from=r.hget(redis_key,'trade_from').decode('utf-8')
		trade_to=r.hget(redis_key,'trade_to').decode('utf-8')
		bot_id=r.hget(redis_key,'id').decode('utf-8')
		
		revkey='REVERSE-'+str(bot_id)
		#print("Debut Setting "+str(revkey)+"to: "+str(symbol))
		r.set(revkey,symbol)				

		ts=float(r.get(bot_name).decode('utf-8'))				
		running=datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")				
		
		key=str(symbol)+'-TRADES'	
		
		key=str(symbol)+'-LAST-PRICE'
		if r.get(key):
			market_price=float(r.get(key))
			print("SLDB MP: "+str(market_price))
		
		t_key="TTT-"+str(symbol)
		
		if mc.get(t_key):
			buy_array=mc.get(t_key)
		else:
			#Cache last order in ram for 60 seconds to speed up api calls
			buy_array=nickbot.fetch_last_buy_order(exchange,symbol)
		#if r.get(t_key):
		#	buy_array=r.get(t_key)
		#else:
		#Cache last order in ram for 60 seconds to speed up api calls
		#buy_array=nickbot.fetch_last_buy_order(exchange,symbol)
		#r.set(t_key,buy_array)
		
		print("BA: ")
		print(buy_array)
		print(str(symbol)+":::START!!!!!!!!!!!!\n\n")
		
		if buy_array!='NULL':
			units=float(buy_array['executedQty'])
			
			if buy_array['type']=='MARKET':
				print(buy_array)	
				buy_price=float(buy_array['cummulativeQuoteQty'])/units
				print("BUY PRICE: "+str(buy_price))
			else:
				buy_price=float(buy_array['price'])
				print("BUY PRICE: "+str(buy_price))

			print("MARKET PRICE: "+str(market_price))
			profit_per_unit=float(market_price)-float(buy_price)
			profit_total=float(profit_per_unit*units)
			profit_total=round(profit_total,8)
			prices = [buy_price,market_price]
			for a, b in zip(prices[::1], prices[1::1]):
				percent=100 * (b - a) / a
				percent=round(percent,2)

			investment_start=units*buy_price
			investment_now=units*market_price	
		
			investment_now=float(investment_now)
			investment_now=round(investment_now,8)
			
			#Stoploss Stuff
			#
			#original_stoploss_percent=r.hget(redis_key,'stoploss_percent').decode('utf-8')
			#original_stoploss_price_ded=buy_price/100*float(original_stoploss_percent)
			#original_stoploss_price=float(buy_price-original_stoploss_price_ded)
			#original_stoploss_price=round(original_stoploss_price,8)
			#key=str(symbol)+'-ORIGINAL-STOPLOSS-PRICE'
			#mc.set(key,original_stoploss_price,86400)
			
			#key=str(symbol)+'-ORIGINAL-STOPLOSS-PRICE'	
			#if(mc.get(key)):
			#	original_stoploss_price=float(mc.get(key))
			#else:
			#	if mc.get(key):
			#		last_stoploss=mc.get(key)		
				
			message=":::BOT " +str(symbol)+"\nSTARTED: "+str(running)+str("\nBUY PRICE: ")+str(buy_price)+"\nPRICE NOW: "+str(market_price)+"\nUNITS: "+str(units)
			message=message+"\nVALUE START "+'('+str(trade_to)+'): '+str(investment_start)
			message=message+"\nVALUE NOW "+'('+str(trade_to)+'): '+str(investment_now)
			message=message+"\nP&L: "+str(profit_total)+' ('+str(percent)+'%)'
			message=message+"\nBOT ID: "+str(bot_id)
	
			message_tg="<b>:::BOT " +str(symbol)+"</b>\n<b>STARTED:</b> "+str(running)+str("\n<b>BUY PRICE:</b> ")+str(buy_price)+"\n<b>PRICE NOW:</b> "+str(market_price)+"\n<b>UNITS:</b> "+str(units)
			message_tg=message_tg+"\n<b>VALUE START "+'('+str(trade_to)+'):</b> '+str(investment_start)
			message_tg=message_tg+"\n<b>VALUE NOW "+'('+str(trade_to)+'):</b> '+str(investment_now)
			message_tg=message_tg+"\n<b>P&L:</b> "+str(profit_total)+' ('+str(percent)+'%)'
			message_tg=message_tg+"\n<b>BOT ID:</b> "+str(bot_id)
	
			key=str(symbol)+'-SYSTEM-STOPLOSS'
			
			if mc.get(key):
				last_stoploss=mc.get(key)		
			else:
				last_stoploss=int(0)
				
			new_stoploss=float(nickbot.wall_magic(symbol,last_stoploss))
			print("NEW SL ADD: "+str(new_stoploss))
			print(new_stoploss)
							
			print("FUCKINGDB NSL: "+str(symbol)+" "+str(new_stoploss))
			print("FUCKINGDB LSL: "+str(symbol)+" "+str(last_stoploss))	
			
			
			diff=nickbot.diff_percent(last_stoploss,new_stoploss)
			diff_abs=abs(diff)

			if new_stoploss>last_stoploss and diff>=0.05:
			
				rkt=symbol+"TTT"
				sl_pos=int(r.get(rkt))
				r.hset(redis_key, 'book_pos',sl_pos)

				ikey=str(bot_id)+'-GOALPOSTS'
				cycles=r.incr(ikey)
					
				gkey=str(bot_id)+'-GOALPOST-STOPLOSS'
				r.set(gkey,new_stoploss)				
	
				print(str(symbol)+":::STOPLOSS/MOVER MOVED GOAL POST: "+str(cycles)+" Times!\n")
				
				print("Goal Post Move Set :"+str(key)+" Stoploss to "+str(new_stoploss))
				
				key=str(symbol)+'-SYSTEM-STOPLOSS'
				mc.set(key,new_stoploss,86400)	
					
				ckey=str(bot_id)+'-CPS'
				r.hincrby(ckey, 'checkpoints',1)
				r.hset(ckey, 'checkpoint_stoploss',new_stoploss)

				ckey=str(bot_id)+'-CPS'
				if r.hget(ckey,"checkpoints"):
					checkpoints=int(r.hget(ckey, 'checkpoints').decode('utf-8'))
					message=message+"\nLAST CHECKPOINT: "+str(new_stoploss)
					message=message+"\nCHECKPOINTS: "+str(checkpoints)
			
					message_tg=message_tg+"\n<b>LAST CHECKPOINT:</b> "+str(new_stoploss)
					message_tg=message_tg+"\n<b>CHECKPOINTS:</b> "+str(checkpoints)
		
					bkey=str(symbol)+'-UPDATE'
					r.setex(bkey,1,"N")
					time.sleep(1)

					print("Db Deleting: "+str(bkey))
					r.set(bkey,message_tg)		

					print(message_tg)
					
			elif last_stoploss==0:
				
				#come back to this			
				#original_stoploss_price=float(nickbot.wall_magic(symbol,0))

				original_stoploss_price=float(nickbot.wall_magic(symbol,0))
				print("First Time Set :"+str(key)+" Stoploss to "+str(original_stoploss_price))
				key=str(symbol)+'-SYSTEM-STOPLOSS'
				mc.set(key,original_stoploss_price,864000)	

				ckey=str(bot_id)+'-CPS'
				if r.hget(ckey,"checkpoints"):
		
					checkpoint_stoploss=float(r.hget(ckey, 'checkpoint_stoploss').decode('utf-8'))
					checkpoints=int(r.hget(ckey, 'checkpoints').decode('utf-8'))
					message=message+"\nLAST CHECKPOINT: "+str(checkpoint_stoploss)
					message=message+"\nCHECKPOINTS: "+str(checkpoints)
			
					message_tg=message_tg+"\n<b>LAST CHECKPOINT:</b> "+str(checkpoint_stoploss)
					message_tg=message_tg+"\n<b>CHECKPOINTS:</b> "+str(checkpoints)
		
					bkey=str(symbol)+'-UPDATE'
					r.setex(key,1,bkey)
					time.sleep(1)

					print("Db Deleting: "+str(bkey))
					r.set(bkey,message_tg)		

					print(message_tg)
			print(str(symbol)+":::END !!!!!!!!!!!!!\n\n")
while True:
	#try:
	loop_bots()
	print("STOPLOSS UPDATER")
	#except:
	#	print("")
	time.sleep(5)		


		