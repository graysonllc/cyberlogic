import configparser
config = configparser.ConfigParser()
config.read('/root/akeys/b.conf')
conf=config['binance']

print(config['binance']['API_KEY'])