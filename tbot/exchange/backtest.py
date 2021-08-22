import json
import asyncio
from tbot.exchange.base_exchange import BaseExchange

class Backtest(BaseExchange):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass

    def startup(self, **kwargs):
        self._set_initial_funds(kwargs.get('initial_funds', {}))


    async def _sleep(self):
        await asyncio.sleep(.1)

    ##############################
    # Create Orders
    #############################

    def create_order(self, sym, type, side, amount, price=None, params={}):
        # let a little bit of time go by to let the orderbook stream update a bit
        book = self._ticker[sym.replace('/', '')]
        price = book['ask'] if side == 'buy' else book['bid']

        # return an order
        order = {
            'id':                '12345-67890:09876/54321',
            'clientOrderId':     'abcdef-ghijklmnop-qrstuvwxyz',
            'datetime':          '2017-08-17 12:42:48.000',
            'timestamp':          1502962946216,
            'lastTradeTimestamp': 1502962956216,
            'status':     'closed',
            'symbol':     sym,
            'type':       type,
            'side':       side,
            'price':      price,
            'amount':      amount if side == 'sell' else amount/price,
            'filled':      amount if side == 'sell' else amount/price,
            'remaining':   0.0,
            'cost':        price * (amount if side == 'sell' else amount/price),
            'fee': {
                'currency': 'BTC',
                'cost': 0.0009,
                'rate': 0.002,
            }
        }
        # check if you have enough balance to make trade
        if self._check_sufficient_balance(order=order):
            # update your new balance if so
            self._update_balance_from_order(order=order)

        return order


    ##############################
    # Order Book
    ##############################

    ##############################
    # Tickers
    ##############################

    async def fetch_ticker_async(self, *args):
        filename = '/home/andrew/Lab/trader/tbot/tbot/exchange/2021-02-23 11:01:18.128222binance-bookTicker.txt'

        with open(filename, 'r') as f:
            while True:
                res = f.readline()
                res_dict = json.loads(res)
                self._ticker[res_dict['s']].update({
                    "symbol": res_dict['s'],
                    "ask": float(res_dict['a']),
                    "askAmount": float(res_dict['A']),
                    "bid": float(res_dict['b']),
                    "bidAmount": float(res_dict['B'])
                })
                print(res_dict)
                await asyncio.sleep(.0001)


    ##############################
    # Markets
    ##############################

    def load_market(self, *args):
        with open('/home/andrew/Lab/trader/tbot/tbot/exchange/markets.json', 'r') as f:
            self._market = json.load(f)

    ##############################
    # Account Info
    ##############################

    def _update_balance_from_order(self, *, order):
        pos_sym, neg_sym = order['symbol'].split('/')[0 if order['side'] == 'buy' else 1]
        pos_bal, neg_bal = (order['filled'], order['cost']) if order['side'] == 'buy' else \
            (order['cost'], order['filled'])
        self._update_balance(pos_sym, pos_bal)
        self._update_balance(neg_sym, -neg_bal)

    def _update_balance(self, sym, delta):
        types = ['free']
        for t in types:
            self._balance.get(sym, {})[t] += delta

    def _check_sufficient_balance(self, *, order):
        pos_sym, neg_sym = order['symbol'].split('/')[0 if order['side'] == 'buy' else 1]
        pos_bal, neg_bal = (order['filled'], order['cost']) if order['side'] == 'buy' else \
            (order['cost'], order['filled'])
        return self._balance[neg_sym]['free'] - neg_bal >= 0

    def _set_initial_funds(self, pairs):
        for sym, amt in pairs.items():
            self._balance[sym]['free'] = amt

if __name__ == '__main__':
    import time
    import json
    b = Backtest()

    async def create_order():
        await asyncio.sleep(1)
        order = b.create_order('BTC/USDT', 'market', 'sell', .0003)
        print(json.dumps(order, indent=2))
        time.sleep(50)

    async def test():
        await asyncio.gather(create_order(), b.run_bookticker_stream())

    asyncio.run(test())



