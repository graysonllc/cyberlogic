import redis
import sys
import argparse

#This app, takes the configuration for a new bot from the command line, and stores it in REDIS/RAM ready for the auto trader to read back and spawn a new process.

conn = redis.Redis('127.0.0.1')

cleaned={}

parser = argparse.ArgumentParser()
parser.add_argument('--exchange', help='Exchange name i.e binance')
parser.add_argument('--rsi_symbol', help='RSI SYMBOL pair i.e IOTAUSDT')
parser.add_argument('--trading_pair', help='Trading pair i.e BTC/USDT')
parser.add_argument('--units', help='Number of coins to trade')
parser.add_argument('--trade_from', help='I.E BTC')
parser.add_argument('--trade_to', help='I.E USDT')
parser.add_argument('--buy_position', help='Buy book position to clone')
parser.add_argument('--sell_position', help='Sell book position to clone')
parser.add_argument('--use_stoploss', help='1 to enable, 0 to disable')
parser.add_argument('--candle_size', help='i.e 5m for 5 minutes')
parser.add_argument('--safeguard_percent', help='safeguard percent if buying back cheaper')
parser.add_argument('--stoploss_percent', help='stoploss percent')
parser.add_argument('--rsi_buy', help='Rsi Number under to trigger a buy, i.e 20')
parser.add_argument('--rsi_sell', help='Rsi Number over to trigger a sell, i.e 80')
parser.add_argument('--live', help='1 for Live trading, 0 for dry testing.')
args = parser.parse_args()

bot_config = {"exchange":str(args.exchange),
"rsi_symbol":str(args.rsi_symbol), 
"symbol":str(args.trading_pair), 
"units":float(args.units), 
"trade_from":str(args.trade_from), 
"trade_to":str(args.trade_to), 
"buy_pos":int(args.buy_position),
"sell_position":int(args.buy_position),
"stoploss_percent":float(args.buy_position),
"use_stoploss":int(args.use_stoploss),
"candle_size":str(args.candle_size),
"safeguard_percent":float(args.safeguard_percent),
"rsi_buy":float(args.rsi_buy),
"rsi_sell":float(args.rsi_sell),
"live":float(args.live)}

redis_key="bconfig-".str(symbol)
conn.hmset(redis_key, bot_config)
bot_config_readback=conn.hgetall(redis_key)

trading_on=conn.hget(redis_key,"exchange")
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

print("READ Back:")
print("trading_on: "+str(trading_on))
print("rsi_symbol: "+str(rsi_symbol))
print("symbol: "+str(symbol))
print("units: "+str(units))
print("trade_from: "+str(trade_from))
print("trade_to: "+str(trade_to))
print("buy_pos: "+str(buy_pos))
print("sell_pos: "+str(sell_pos))
print("stoploss_percent: "+str(stoploss_percent))
print("safeguard_percent: "+str(safeguard_percent))
print("use_stoploss: "+str(use_stoploss))
print("candle_size: "+str(candle_size))
print("rsi_buy: "+str(rsi_buy))
print("live: "+str(live))
