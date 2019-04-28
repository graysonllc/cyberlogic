# Crypto Logic

Crypto Logic Is a Next Generation Crypto Bot Platform	

Requires following dependencies:

Python Modules:

	gparse, json, itemgetter, re, memcache, codecs, logging, sys, pymysql, time, requests, redis, configparser, datetime, talib, numpty, ccxt

*Nix
	memcached
	circus
	redis

r = redis.Redis(host='localhost', port=6379, db=0)

config = configparser.ConfigParser()

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib'
sys.path.append(root + '/python')

import talib
import numpy as np
import ccxt  # noqa: E402