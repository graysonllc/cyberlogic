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

def replace_last(source_string, replace_what, replace_with):
    head, _sep, tail = source_string.rpartition(replace_what)
    return head + replace_with + tail

exchange=nickbot.get_exchange()	

config = configparser.ConfigParser()

config.read('/root/akeys/b.conf')
mysql_username=config['mysql']['MYSQL_USERNAME']
mysql_password=config['mysql']['MYSQL_PASSWORD']
mysql_hostname=config['mysql']['MYSQL_HOSTNAME']
mysql_database=config['mysql']['MYSQL_DATABASE']

print(mysql_hostname)
print(mysql_username)
print(mysql_password)
print(mysql_database)

db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysql_database)
cur = db.cursor()
	
query='select * from at_analysis'
cur.execute(query)
db.commit()
result = cur.fetchall()
for row in result:
	id=row[0]
	date=row[1]
	start_date_time=row[2]
	end_date_time=row[3]
	start_timestamp=int(row[4])
	end_timestamp=int(row[5])
	duration_secs=int(row[6])
	bot_id=int(row[7])
	order_id=str(row[8])
	symbol=str(row[9])	
	rsi_symbol=str(row[10])
	trade_from=str(row[11])
	trade_to=str(row[12])
	units=int(row[13])
	buy_price=int(row[14])
	sell_price=int(row[15])
	profit=float(row[16])
	profit_percent=float(row[17])
	bot_profit_high=float(row[18])			
	bot_profit_high_percent=float(row[19])			
	invest_start=float(row[20])
	invest_end=float(row[21])
	
	message=":::BOT " +str(symbol)
	message=message+"\nSTART TIME: "+str(start_date_time)
	message=message+"\nEND TIME: "+str(end_date_time)
	message=message+"\nRAN FOR: "+str(duration_secs)+" SECS"	
	message=message+str("\nBUY PRICE: ")+str(buy_price)+"\nSELL PRICE: "+str(sell_price)+"\nUNITS: "+str(units)
	message=message+"\nVALUE START: "+str(invest_end)
	message=message+"\nVALUE NOW: "+str(invest_end)
	message=message+"\nP&L: "+str(profit)+' ('+str(profit_percent)+'%)'
	message=message+"\nP&L HIGHS: "+str(bot_profit_high)+' ('+str(bot_profit_high_percent)+'%)'
	message=message+"\nBOT ID: "+str(bot_id)
	print(message)
db.close() 
