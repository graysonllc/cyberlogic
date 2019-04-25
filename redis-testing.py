import redis
import sys
import argparse

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

#python3.6 redis-testing.py --exchange "Binance" --rsi_symbol='BTCUSDT' --trading_pair='BTC/USDT' --units '0.001' --trade_from 'BTC' --trade_to 'USDT' --buy_position '1' --sell_position '1' --use_stoploss '1' --candle_size '5m' --safeguard_percent '2' --stoploss_percent '1' --rsi_buy '20' --rsi_sell '80' --live '1'
{'exchange': 'Binance', 'rsi_symbol': 'BTCUSDT', 'symbol': 'BTC/USDT', 'units': 0.001, 'trade_from': 'BTC', 'trade_to': 'USDT', 'buy_pos': 1, 'sell_position': 1, 'stoploss_percent': 1.0, 'use_stoploss': 1, 'candle_size': '5m', 'safeguard_percent': 2.0, 'rsi_buy': 20.0, 'rsi_sell': 80.0, 'live': 1.0}

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

print(bot_config)
sys.exit("die")

conn.hmset("bconfig", bot_config)

bot_config_readback=conn.hgetall("bconfig")

print(conn.hget("bconfig","exchange"))

trading_on=conn.hget("bconfig","exchange")
trading_on=trading_on.decode('utf-8')
rsi_symbol=conn.hget("bconfig","rsi_symbol")
rsi_symbol=rsi_symbol.decode('utf-8')
symbol=conn.hget("bconfig","symbol")
symbol=symbol.decode('utf-8')
units=conn.hget("bconfig","units")
units=units.decode('utf-8')
trade_from=conn.hget("bconfig","trade_from")
trade_from=trade_from.decode('utf-8')
trade_to=conn.hget("bconfig","trade_to")
trade_to=trade_to.decode('utf-8')
buy_pos=conn.hget("bconfig","buy_pos")
buy_pos=buy_pos.decode('utf-8')
sell_pos=conn.hget("bconfig","sell_pos")
sell_pos=sell_pos.decode('utf-8')
stoploss_percent=conn.hget("bconfig","stoploss_percent")
stoploss_percent=stoploss_percent.decode('utf-8')
safeguard_percent=conn.hget("bconfig","safeguard_percent")
safeguard_percent=safeguard_percent.decode('utf-8')
use_stoploss=conn.hget("bconfig","use_stoploss")
use_stoploss=use_stoploss.decode('utf-8')
candle_size=conn.hget("bconfig","candle_size")
candle_size=candle_size.decode('utf-8')
rsi_buy=conn.hget("bconfig","rsi_buy")
rsi_buy=rsi_buy.decode('utf-8')
rsi_sell=conn.hget("bconfig","rsi_sell")
rsi_sell=rsi_sell.decode('utf-8')
live=conn.hget("bconfig","live")
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

#print(str(trading_on))

#print(conn.hgetall("bconfig"))
