def replace_last(source_string, replace_what, replace_with):
    head, _sep, tail = source_string.rpartition(replace_what)
    return head + replace_with + tail

symbol=str('btc/usdt')
symbol=symbol.upper()
ticker_symbol=symbol
if symbol.endswith('BTC'):
	ticker_symbol = replace_last(ticker_symbol, 'BTC', '')
elif symbol.endswith('USDT'):
	ticker_symbol = replace_last(ticker_symbol, '/USDT', '')
elif symbol.endswith('BNB'):
	ticker_symbol = replace_last(ticker_symbol, '/BNB', '')
elif symbol.endswith('TUSD'):
	ticker_symbol = replace_last(ticker_symbol, '/TUSD', '')
elif symbol.endswith('USD'):
	ticker_symbol = replace_last(ticker_symbol, '/USD', '')
elif symbol.endswith('USDC'):
	ticker_symbol = replace_last(ticker_symbol, '/USDC', '')
elif symbol.endswith('PAX'):
	ticker_symbol = replace_last(ticker_symbol, '/PAX', '')
elif symbol.endswith('USDS'):
	ticker_symbol = replace_last(ticker_symbol, '/USDS', '')
elif symbol.endswith('ETH'):
	ticker_symbol = replace_last(ticker_symbol, '/ETH', '')
print(ticker_symbol)