import redis
import sys
conn = redis.Redis('127.0.0.1')

cleaned={}

bot_config = {"exchange":"Binance", 
"rsi_symbol":"BTC/USDT", 
"symbol":"BTCUSDT", 
"units":"0.005",
"trade_from":"BTC",
"trade_to":"USDT",
"buy_pos":"1",
"sell_pos":"1",
"stoploss_percent":"1",
"use_stoploss":"1",
"candle_size":"5m",
"rsi_buy":"20",
"rsi_sell":"80",
"safeguard_percent":"2",
"live":"1"}

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
