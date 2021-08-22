import ccxt
import logging
from tbot.exchange.exchange import Exchange
import websockets
import json

log = logging.getLogger('tbot.exchange.binance')


class Binance(Exchange):
    def __init__(self, **kwargs):
        super(Binance, self).__init__(**kwargs)

        self.load_markets()
        self.fee = .001

    def startup(self, **kwargs):
        self._exchange = ccxt.binance({
            'enableRateLimit': True,
            'apiKey': kwargs.get('apiKey', ''),
            'secret': kwargs.get('apiSecret', '')
        })
        self._exchange.set_sandbox_mode(kwargs.get('sandbox', False))

    def load_order_book(self, pairs=None):
        pairs = pairs if pairs is not None else self._exchange.markets()
        for pair in pairs:
            # get the orderbook for the pair
            book = self._exchange.fetch_order_book(pair)
            # index properly in self.order_book
            self._order_book[pair.replace('/','')] = {
                "symbol": pair,
                "ask": book['asks'][0][0],
                "askAmount": book['asks'][0][1],
                "bid": book['bids'][0][0],
                "bidAmount": book['bids'][0][1]
            }

    def get_order_book(self):
        return self.order_book

    async def fetch_ticker_async(self):
        url = 'wss://stream.binance.com:9443/ws/!bookTicker'
        # url = 'wss://testnet.binance.vision/ws/!bookTicker'
        try:
            async with websockets.connect(url) as websocket:
                while True:
                    res = await websocket.recv()
                    print(res)
                    res_dict = json.loads(res)
                    self._ticker[res_dict['s']].update({
                        "symbol": res_dict['s'],
                        "ask": float(res_dict['a']),
                        "askAmount": float(res_dict['A']),
                        "bid": float(res_dict['b']),
                        "bidAmount": float(res_dict['B'])
                    })
        except websockets.ConnectionClosedError:
            log.warning("Connection Closed.  Trying to restart")
            await self.run_orderbook_stream()


if __name__ == '__main__':
    # b = Binance(apiSecret='dMPoVu5p4g0z0G47fV0UKSQhyZ85dZuEygil6U6JXOzRx8ni1FynIPCHlYYFVe6H',
    #             apiKey='oKuOS4rQzeuko0uKSlMiE5lBIt7M1sG4bYOtcdnCtCpFfYZ2tNXv5mmVEQH1YqeD')
    b = Binance()
    import asyncio
    with open('markets.json', 'w+') as f:
        f.write(json.dumps(b.market()))
