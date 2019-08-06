import os
import sys, argparse
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
from datetime import datetime
import subprocess
import heapq
import nickbot

redis_key="bconfig-"+bot_name
	


all_keys = list(r.hgetall(redis_key))
bot_id=all_keys["id"].decode('utf-8')

#r.delete(ckey)
#r.hdel(ckey)
