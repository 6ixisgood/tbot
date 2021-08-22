import ccxt
import statistics as stats
import logging
import time
from tbot.exchange.base_exchange import BaseExchange

log = logging.getLogger('tbot.exchange.exchange')


class Exchange(BaseExchange):
    """
    Abstract CCXT-like exchange implementation
    """
    class Decorators:
        """
        Helpful decorators
        """
        @classmethod
        def ccxt_exception_handler(cls, f):
            """
            decorator for handling basic CCXT request errors
            :param f:
            :return:
            """
            def wrapper(self, *args, **kwargs):
                try:
                    return f(self, *args, **kwargs)
                except ccxt.DDoSProtection as e:
                    log.info(f'{self._exchange} {f.__name__} too many requests in timeframe')
                    time.sleep(10)
                    # try again after some time
                except ccxt.NetworkError as e:
                    log.exception(f'{self._exchange} {f.__name__} failed due to a network error')
                except ccxt.InsufficientFunds as e:
                    log.exception(f'{self._exchange} {f.__name__} insufficient funds to complete transaction')
                    # raise
                except ccxt.ExchangeError as e:
                    log.exception(f'{self._exchange} {f.__name__} failed due to exchange error')
                except Exception as e:
                    log.exception(f'{self._exchange} {f.__name__} failed')

            return wrapper

    def __init__(self, **kwargs):
        self._exchange: ccxt.Exchange = None
        super(Exchange, self).__init__(**kwargs)

    def startup(self, **kwargs):
        self.load_market()
        self.load_fees()

    ##############################
    # Create Orders
    ##############################

    @Decorators.ccxt_exception_handler
    def create_order(self, sym, type, side, amount, price=None, params={}):
        return self._exchange.create_order(sym, type, side, amount, price, params)

    def create_market_buy_order(self, sym, amount, params={}):
        return self.create_order(sym, 'market', 'buy', amount, params=params)

    def create_market_sell_order(self, sym, amount, price, params={}):
        return self.create_order(sym, 'market', 'sell', amount, params=params)

    def create_limit_buy_order(self, sym, amount, price, params={}):
        return self.create_order(sym, 'limit', 'buy', amount, price, params=params)

    def create_limit_sell_order(self, sym, amount, price, params={}):
        return self.create_order(sym, 'limit', 'sell', amount, price, params=params)

    ##############################
    # Order Book
    ##############################

    @Decorators.ccxt_exception_handler
    def load_order_book(self, *args):
        for sym in args:
            # try to handle exceptions per symbol
            try:
                self._order_book[sym] = self._exchange.fetch_order_book(sym)
            except ccxt.BaseError:
                log.info(f'Error fetching order book for {sym}')

    def get_bid_ask(self, sym):
        """
        Get high, low and avg bid/ask for a given trading pair
        """
        self.load_order_book(sym)
        book = self._order_book(sym)
        return {
            'bids': {
                'high': book['bids'][0],
                'low': book['bids'][-1],
                'avg': [stats.mean(bid[0] for bid in book['bids']),
                        stats.mean(bid[1] for bid in book['bids'])]
            },
            'asks': {
                'high': book['asks'][0],
                'low': book['asks'][-1],
                'avg': [stats.mean(ask[0] for ask in book['asks']),
                        stats.mean(ask[1] for ask in book['asks'])]
            }
        }

    ##############################
    # Tickers
    ##############################

    @Decorators.ccxt_exception_handler
    def load_ticker(self, *args):
        tickers = self._exchange.fetch_tickers(list(args))
        for ticker, info in tickers.items():
            if ticker != 'info':
                self._ticker[ticker] = info

    ##############################
    # Markets
    ##############################

    @Decorators.ccxt_exception_handler
    def load_market(self):
        self._market = self._exchange.load_markets()

    ##############################
    # Account Info
    ##############################

    @Decorators.ccxt_exception_handler
    def get_balance(self, sym=None):
        return self._exchange.fetch_balance() if sym is None else self._exchange.fetch_balance()[sym]

    def get_free_balance(self, sym=None):
        return self.get_balance(sym)['free']

    def get_total_balance(self, sym=None):
        return self.get_balance(sym)['total']

    def get_used_balance(self, sym=None):
        return self.get_balance(sym)['used']

    ##############################
    # Fees
    ##############################

    @Decorators.ccxt_exception_handler
    def load_fees(self):
        self.fees = self._exchange.fetch_trading_fees()

    @Decorators.ccxt_exception_handler
    def estimate_trade_fees(self, sym, type, side, amount, price=None, params={}):
        return self._exchange.calculate_fee(sym, type, side, amount, price, params=params)

    @Decorators.ccxt_exception_handler
    def get_trade_fee(self, sym, params={}):
        return self._exchange.fetch_trading_fee(sym, params)

    @Decorators.ccxt_exception_handler
    def get_trade_fees(self, params={}):
        return self._exchange.fetch_trading_fees(params)



