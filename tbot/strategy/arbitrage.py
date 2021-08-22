from tbot.exchange.binance import Binance
from tbot.exchange.exchange import Exchange
from tbot.strategy.strategy import Strategy
from tbot.exchange.trade import Trade
import logging
import asyncio
import time
from datetime import datetime
from tabulate import tabulate

log = logging.getLogger('tbot.strategy.arbitrage')


class TriangleNode:
    """
    Node of a Triangular Arbitrage triangle
    """
    def __init__(self, market, side, ticker):
        self.market = market
        self.symbol = market['symbol']
        self.base = market['base']
        self.quote = market['quote']
        self.side = side
        self.ticker = ticker
        self.start = self.quote if side == 'buy' else self.base
        self.end = self.base if side == 'buy' else self.quote
        self.rate = 0
        self.fees = {}

    def set_market(self, market):
        self.market = market


class Triangle:
    """
    Representation of Triangular Arbitrage triangle.
    Consists of 3 TriangleNodes 
    """
    def __init__(self, a, b, c, exchange):
        self.trades = {'a': a, 'b': b, 'c': c}
        self.exchange: Exchange = exchange
        self.rate = 0
        self.last_trade_time = datetime.min
        self.score = 0

    def get_fees(self):
        return 0.001

    def expand(self):
        """
        Supplement triangle with detailed info on markets
        """
        tickers = self.exchange.ticker()
        try:
            for step, node in self.trades.items():
                # get the current ticker info for given market
                node.ticker = tickers[node.symbol]
        except KeyError as e:
            log.exception(f"Error expanding triangle: couldn't save ticker data")

    def update_rate(self):
        """
        Get the rate of return for trading with a given triangle
        """
        try:
            rate = self.rate = 1
            for step, node in self.trades.items():
                rate *= node.ticker['ask'] if node.side == 'buy' else 1 / node.ticker['bid']
            fees = self.get_fees()
            self.rate = 1 - rate - fees if rate != 0 else 0
        except (KeyError, ZeroDivisionError):
            # we don't care
            self.rate = None
        except Exception:
            log.exception('Error calculating triangle rate')
        return self.rate

    def update_score(self):
        return self.score


class Arbitrage(Strategy):
    def __init__(self, exchange, **kwargs):
        self.exchange: Binance = exchange
        self.triangles = []
        self.trade_unit = kwargs.get('trade_unit', 0)
        self.init_currency = kwargs.get('init_currency', 'BTC')
        self.min_rate = kwargs.get('min_rate', 0)
        self.min_rate = -1
        self._startup()

    def _startup(self):
        # create all the triangles
        self.create_triangles()
        log.debug("Arbitrage created all triangles")
        # TODO: probably remove below
        # # load all tickers in exchange
        # self.exchange.load_order_book(['BTC/USDT'])
        # log.info("Loaded exchange's orderbook")

    async def trade(self):
        # run the stream update and execute trades at same time
        await asyncio.gather(self.find_arbitrage(), self.exchange.fetch_ticker_async())

    async def find_arbitrage(self):
        """
        Attempt to execute a trade. Find a possible triangle,
        calculate its rate, determine whether to buy, and
        execute the appropriate trade
        """
        # sleep a bit to start
        await asyncio.sleep(1)
        while True:
            # go through all triangles, update and evaluate

            for triangle in self.triangles:
                triangle.update_rate()
                print(triangle.rate)
                if triangle.rate is not None and triangle.rate > self.min_rate and self.is_valid_trade(triangle) \
                        and (datetime.now() - triangle.last_trade_time).seconds > 10:
                    log.info(f"""Trades: {''.join(f"{node.symbol} "
                                                  for step, node in triangle.trades.items())} Rate: {triangle.rate}""")
                    # orders = self.execute_trade(triangle)
                    # self.evaluate_trade(triangle, orders)
                    # await asyncio.sleep(.1)
                    # triangle.update_rate()
                    # print(triangle.rate)
                    #
                    # triangle.last_trade_time = datetime.now()
            time.sleep(10)
            # let the exchange update
            await asyncio.sleep(1)

    def execute_trade(self, triangle):
        """
        Execute the trade.  Should be validated prior to reduce chance of error.
        If something goes wrong, just bail out and go back to the default currency.

        TODO: some error handling when a trade goes wrong
        TODO: convert to market-like limit order
        """
        orders = []
        amount = self.trade_unit
        for step, node in triangle.trades.items():
            order = None
            amount_att = amount / node.ticker['ask'] if node.side == 'buy' else amount
            log.info(f"Attempting to {node.side} {amount_att} of {node.base} for "
                     f"{amount_att * node.ticker['ask'] if node.side == 'buy' else amount_att * node.ticker['bid']}"
                     f"{node.quote}")
            # try to create the order
            # if it's a 'buy', binance exchange will flip to 'quoteOrderQty'
            order = self.exchange.create_order(node.symbol,
                                               'market',
                                               node.side,
                                               amount,
                                               1 if node.side == 'buy' else None)
            orders.append(Trade(ccxt_order=order))

            amount, cost = (order['filled'], order['cost']) \
                if order['side'] == 'buy' else (order['cost'], order['filled'])
            log.info(f"Received {amount} of {order['symbol'].split('/')[0 if order['side'] == 'buy' else 1]} "
                     f"for {cost} {order['symbol'].split('/')[1 if order['side'] == 'buy' else 0]} "
                     f"at {order['price'] if order['side'] == 'buy' else 1/order['price']}")
        return orders

    def evaluate_trade(self, triangle, trades):
        triangle_headers = ['Node', 'In', 'Sym', 'Out', 'Sym', 'Side', 'Dust', 'Rate']
        triangle_values = []
        total_rate = 1
        total_dust_cur = 0
        for index, trade in enumerate(trades):
            dust_cur = 0
            if index > 0:
                dust = trades[index-1].end_amount() - trade.start_amount()
                if index == 1:
                    dust_cur += dust / trades[index-1].rate()
                else:
                    dust_cur += dust * trade.rate()
            total_dust_cur += dust_cur
            triangle_values.append(['a', trade.start_amount(), trade.start_symbol(), trade.end_amount(), trade.end_symbol(), trade.side, dust_cur, trade.rate()])
            total_rate *= trade.rate()

        fee_rate = .00075
        total_rate = total_rate - fee_rate
        actual_rate = trades[-1].end_amount()/trades[0].start_amount()
        actual_dust_rate = (trades[-1].end_amount()+total_dust_cur)/trades[0].start_amount()
        triangle_values.append(['', '', '', '', '', '', 'Guess', total_rate])
        triangle_values.append(['', '', '', '', '', '', 'Actual', actual_rate])
        triangle_values.append(['', '', '', '', '', '', 'Act+Dust', actual_dust_rate])
        print(tabulate(triangle_values, headers=triangle_headers))

    def is_valid_trade(self, triangle):
        """
        "Simulate" the trade to make sure desired initial trade unit will
        be sufficient to complete all the trades
        """
        valid = True
        # starting amount of currency "A"
        funds = self.trade_unit

        for step, node in triangle.trades.items():
            try:
                if node.side == 'buy' and \
                        funds / node.ticker['ask'] >= node.market['limits']['amount']['min'] and \
                        funds >= node.market['limits']['cost']['min']:
                    # funds are now in the next currency
                    funds = funds / node.ticker['ask']
                elif node.side == 'sell' and \
                        funds * node.ticker['bid'] >= node.market['limits']['cost']['min'] and \
                        funds >= node.market['limits']['amount']['min']:
                    # funds are now in the next currency
                    funds = funds * node.ticker['bid']
                else:
                    log.debug(f"Insufficient funds to execute trade on {node.symbol}")
                    valid = False
                    break
            except (ZeroDivisionError, KeyError):
                valid = False


        return valid

    def create_triangles(self):
        # get a starting currency (step A)
        starting_currencies = [self.init_currency]
        ticker = self.exchange.ticker()
        for a in starting_currencies:
            for a_b_market in self._match_pairs(a):
                # find market that isn't step A and determine correct side of trade
                a_node = TriangleNode(a_b_market, 'sell' if a_b_market['base'] == a else 'buy',
                                      ticker[a_b_market['symbol'].replace('/','')])
                # take step B and find step C
                for b_c_market in self._match_pairs(a_node.end):
                    b_node = TriangleNode(b_c_market, 'sell' if b_c_market['base'] == a_node.end else 'buy',
                                          ticker[b_c_market['symbol'].replace('/','')])
                    # find all step C that can go back to step A
                    for c_a_market in self._match_pairs(b_node.end, a_node.start):
                        c_node = TriangleNode(c_a_market, 'sell' if c_a_market['base'] == b_node.end else 'buy',
                                              ticker[c_a_market['symbol'].replace('/','')])
                        self.triangles.append(Triangle(a_node, b_node, c_node, self.exchange))
        self._filter_triangles()

    def _match_pairs(self, sym1, sym2=None):
        """
        Get all markets where a given symbol is either the base or quote
        """
        matching_markets = []
        for symbol, market in self.exchange.market().items():
            if sym2:
                if (market['base'] == sym1 and market['quote'] == sym2) or \
                        (market['base'] == sym2 and market['quote'] == sym1):
                    matching_markets.append(market)
            else:
                if market['base'] == sym1 or market['quote'] == sym1:
                    matching_markets.append(market)
        return matching_markets

    def _filter_triangles(self):
        """
        Knock out triangles we don't want
        """
        exclude = ['USDT', 'USDC', 'TUSD']
        for triangle in self.triangles[:]:
            rem = False
            for step, node in triangle.trades.items():
                if node.base in exclude or node.quote in exclude:
                    rem = True
                elif not (node.market['active']):
                    rem = True
            if rem:
                self.triangles.remove(triangle)

    def get_required_funds(self):
        """
        Get the amount of funds required to use this strategy
        """
        return {self.init_currency: self.trade_unit}


if __name__ == '__main__':
    pass
