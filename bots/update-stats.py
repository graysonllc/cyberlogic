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

try:
	db=pymysql.connect(mysql_hostname,mysql_username,mysql_password,mysql_database)
except Exception:
	print("Error in MySQL connexion")
else:
	cur = db.cursor()
	
	subcur = db.cursor()

	subquery="truncate at_analysis";
	subcur.execute(subquery)
	
	#try:
	query='select * from at_orders'
	cur.execute(query)
	##except Exception:
	#	print("Error with query: " + query)
	#else:
	db.commit()
	result = cur.fetchall()
	for row in result:
		id=row[0]
		date=row[1]
		end_date_time=str(row[2])
		end_timestamp=int(row[3])
		bot_id=row[4]
		order_id=row[5]
		symbol=row[6]
		rsi_symbol=row[7]
		trade_from=row[8]
		trade_to=row[9]
		units=row[10]
		buy_price=row[11]
		sell_price=row[12]
		profit=row[13]
		profit_percent=row[14]
		
		subquery="select date_time,timestamp,total_invest from at_history where bot_id="+str(bot_id)+" limit 1"
		subcur.execute(subquery)
		subresult = subcur.fetchall()
		for srow in subresult:
			start_date_time=str(srow[0])
			start_timestamp=srow[1]
			invest_start=srow[2]
			invest_end=invest_start+profit
	
		subquery="select profit,profit_percent from at_history where bot_id="+str(bot_id)+" order by profit_percent desc limit 1";
		subcur.execute(subquery)
		subresult = subcur.fetchall()
		for srow in subresult:
			bot_profit_high=srow[0]
			bot_profit_high_percent=srow[1]
			
		print("Start Date: "+str(start_date_time))
		print("End Date: "+str(end_date_time))
		
		day1=str(start_date_time)
		day2=str(end_date_time)
		day1=datetime.datetime(*time.strptime(day1, "%Y-%m-%d %H:%M:%S")[:6])
		day2=datetime.datetime(*time.strptime(day2, "%Y-%m-%d %H:%M:%S")[:6])
		duration_secs=str(abs(day2-day1).seconds)
		print(duration_secs)

		sql = str("""INSERT INTO at_analysis(date,start_date_time,end_date_time,start_timestamp,end_timestamp,duration_secs,bot_id,order_id,symbol,rsi_symbol,trade_from,trade_to,units,buy_price,sell_price,profit,profit_percent,bot_profit_high,bot_profit_high_percent,invest_start,invest_end) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""")
		subcur.execute(sql,(date,start_date_time,end_date_time,start_timestamp,end_timestamp,duration_secs,bot_id,order_id,symbol,rsi_symbol,trade_from,trade_to,units,buy_price,sell_price,profit,profit_percent,bot_profit_high,bot_profit_high_percent,invest_start,invest_end))


	db.close() 
