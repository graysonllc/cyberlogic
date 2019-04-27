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

r = redis.Redis(host='localhost', port=6379, db=0)

timestamp=time.time()
ts_raw=timestamp
date_time=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %I:%M:%S")
date_today=datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

pump_key=str(date_today+"-ALERTLIST")
pump_coins=r.smembers(pump_key)

for coin in pump_coins:
	coin=coin.decode('utf-8')
	r.sort(coin+'-IDS')
	coin_ids=r.smembers(coin+'-IDS')
	message=":: Alerts For: "+str(coin)
	for cid in coin_ids:
		cid=cid.decode('utf-8')
		#print(cid)
		rkey=str(coin)+'-'+str(cid)
		coin_hash=r.hgetall(rkey)
		if coin_hash:
			date_time=r.hget(rkey,"date_time").decode('utf-8')
			price=r.hget(rkey,"price").decode('utf-8')
			percent=r.hget(rkey,"percent").decode('utf-8')
			spread=r.hget(rkey,"percent").decode('utf-8')
			high=r.hget(rkey,"high").decode('utf-8')
			low=r.hget(rkey,"low").decode('utf-8')
			btc_price=r.hget(rkey,"btc_price").decode('utf-8')
			btc_percent=r.hget(rkey,"btc_percent").decode('utf-8')
			message=message+"\n"+str(date_time)+"\tPrice: "+str(price)+' Change %:'+str(percent)+" Spread: "+str(spread)
			print(message)
		#print(date_time+"\tPrice: "+str(price)+' \('+str(percent)+'\%)')
		
	
