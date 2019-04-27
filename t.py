import argparse
import shlex

parser = argparse.ArgumentParser()
parser.add_argument('--trading_on', help='Exchange name i.e binance')
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

argstr = "--trading_on Binance --rsi_symbol BCHABCUSDT --units 0.1 --trade_from BCHABC --trade_to USDT --buy_position 5 --sell_position 5 --use_stoploss 1 --candle_size 5m --safeguard_percent 1 --stoploss_percent 1 --rsi_buy 20 --rsi_sell 20 --live yes"
args = parser.parse_args(shlex.split(argstr))
print(args)
