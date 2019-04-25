import redis
conn = redis.Redis('127.0.0.1')

bot_config = {"exchange":"Binance", "rsi_symbol":"BTC/USDT", "symbol":"BTCUSDT", "units":"0.005","trade_from":"BTC","trade_to":"USDT","buy_pos":"1","sell_pos":"1","stoploss_percent":"1","use_stoploss":"1","candle_size":"5m","rsi_buy":"20","rsi_sell":"80","live":"1"}


conn.hmset("bconfig", bot_config)

print(conn.hgetall("bconfig"))
