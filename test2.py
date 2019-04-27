import time
import requests
from datetime import datetime
import sys, argparse
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

conn = redis.Redis('127.0.0.1')

def log_redis(redis_key,message,c):

	if c>100:
		print(r.lpop(redis_key))
		
	now = datetime.now()
	ts = datetime.timestamp(now)
	running=datetime.fromtimestamp(ts).strftime("%Y-%m-%d %I:%M:%S")

	message="LOG\t"+str(running)+"\t"+str(message)
	r.rpush(redis_key,message)
		
parser = argparse.ArgumentParser()
parser.add_argument('--trading_pair', help='Trading pair i.e BTC/USDT')
args = parser.parse_args()

symbol=str(args.trading_pair)
redis_key="BOTLOG-"+symbol

c=0
while True:
	try:
		now = datetime.now()
		ts = datetime.timestamp(now)
	
		running=datetime.fromtimestamp(ts).strftime("%Y-%m-%d %I:%M:%S")
		message=":::Bot "+str(symbol)+" Running"
		print(message)
		log_redis(redis_key,message,c)
		time.sleep(0.1)
	except:
		print("threw error sleeping for 3 seconds")
		time.sleep(3)
	
	c+=1