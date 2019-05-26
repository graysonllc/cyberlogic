import redis

def gotbot(symbol):
	
	redis_server = redis.Redis(host='localhost', port=6379, db=0)
	botlist=redis_server.smembers("botlist")
	print(len(botlist))	
	seen=0
	for bot in botlist:
		bot=bot.decode('utf-8')
		if bot==symbol:
			seen=1
	print("Seen: "+str(seen))
	return(seen)

coin='PHB/BTC'
if gotbot(coin)==1:
	print("Got it")
#print gotbot(coin)
