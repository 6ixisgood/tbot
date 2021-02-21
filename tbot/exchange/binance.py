import ccxt
import logging
from tbot.exchange.exchange import Exchange
import websockets
from collections import defaultdict
import json

log = logging.getLogger('tbot.exchange.binance')


class Binance(Exchange):
    def __init__(self, **kwargs):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'apiKey': kwargs.get('apiKey', ''),
            'secret': kwargs.get('apiSecret', '')
        })
        self.load_markets()
        self.order_book = defaultdict(dict)

    def load_order_book(self, pairs=None):
        pairs = pairs if pairs is not None else self.exchange.load_markets()
        for pair in pairs:
            # get the orderbook for the pair
            book = self.exchange.fetch_order_book(pair)
            # index properly in self.order_book
            self.order_book[pair.replace('/','')] = {
                "symbol": pair,
                "ask": book['asks'][0][0],
                "askAmount": book['asks'][0][1],
                "bid": book['bids'][0][0],
                "bidAmount": book['bids'][0][1]
            }

    def get_order_book(self):
        return self.order_book

    async def run_orderbook_stream(self):
        url = 'wss://stream.binance.com:9443/ws/!bookTicker'
        async with websockets.connect(url) as websocket:
            while True:
                res = await websocket.recv()
                res_dict = json.loads(res)
                self.order_book[res_dict['s']].update({
                    "symbol": res_dict['s'],
                    "ask": float(res_dict['a']),
                    "askAmount": float(res_dict['A']),
                    "bid": float(res_dict['b']),
                    "bidAmount": float(res_dict['B'])
                })


if __name__ == '__main__':
    pass
