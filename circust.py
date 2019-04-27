from circus import get_arbiter

args=str("--trading_pair BTC/USDT")
myprogram = {"cmd": "python3.6 bots/autotrader.py","args":args, "numprocesses": 1, "background":"True","pipe_stdout":"False","close_child_stdout":"True","pid":966666}

arbiter = get_arbiter([myprogram])

try:
	arbiter.start()
finally:
	arbiter.stop()
print("We ever get here")