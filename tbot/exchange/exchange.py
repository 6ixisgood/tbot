import ccxt
import statistics as stats
import logging
import time

log = logging.getLogger('tbot.exchange.exchange')


class Exchange:
    class Decorators:
        @classmethod
        def ccxt_exception_handler(cls, f):
            def wrapper(self, *args, **kwargs):
                try:
                    return f(self, *args, **kwargs)
                except ccxt.DDoSProtection as e:
                    log.info(f'{self.exchange} {f.__name__} too many requests in timeframe')
                    time.sleep(10)
                    # try again after some time
                except ccxt.NetworkError as e:
                    log.exception(f'{self.exchange} {f.__name__} failed due to a network error')
                except ccxt.InsufficientFunds as e:
                    log.exception(f'{self.exchange} {f.__name__} insufficient funds to complete transaction')
                    # raise
                except ccxt.ExchangeError as e:
                    log.exception(f'{self.exchange} {f.__name__} failed due to exchange error')
                except Exception as e:
                    log.exception(f'{self.exchange} {f.__name__} failed')

            return wrapper

    def __init__(self):
        self.exchange: ccxt.Exchange = None
        self.fees = {}
        self.load_markets()

    @Decorators.ccxt_exception_handler
    def get_book(self, sym):
        """
        Fetch the order book for a given symbol
        """
        return self.exchange.fetch_order_book(sym)

    def get_bid_ask(self, sym):
        """
        Get high, low and avg bid/ask for a given trading pair
        """
        book = self.get_book(sym)
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

    @Decorators.ccxt_exception_handler
    def get_ticker(self, sym, params={}):
        return self.exchange.fetch_ticker(sym, params)

    @Decorators.ccxt_exception_handler
    def get_tickers(self, sym: list, params={}):
        return self.exchange.fetch_tickers(sym, params)

    @Decorators.ccxt_exception_handler
    def create_order(self, sym, type, side, amount, price=None, params={}):
        """
        Create an order to the exchange
        """
        return self.exchange.create_order(sym, type, side, amount, price, params)

    def create_market_buy_order(self, sym, amount, params={}):
        return self.create_order(sym, 'market', 'buy', amount, params=params)

    def create_market_sell_order(self, sym, amount, price, params={}):
        return self.create_order(sym, 'market', 'sell', amount, params=params)

    def create_limit_buy_order(self, sym, amount, price, params={}):
        return self.create_order(sym, 'limit', 'buy', amount, price, params=params)

    def create_limit_sell_order(self, sym, amount, price, params={}):
        return self.create_order(sym, 'limit', 'sell', amount, price, params=params)

    @Decorators.ccxt_exception_handler
    def estimate_trade_fees(self, sym, type, side, amount, price=None, params={}):
        return self.exchange.calculate_fee(sym, type, side, amount, price, params=params)

    @Decorators.ccxt_exception_handler
    def get_trade_fee(self, sym, params={}):
        return self.exchange.fetch_trading_fee(sym, params)

    @Decorators.ccxt_exception_handler
    def get_trade_fees(self, params={}):
        return self.exchange.fetch_trading_fees(params)

    @Decorators.ccxt_exception_handler
    def get_markets(self):
        """
        Create an order to the exchange
        """
        return self.exchange.fetch_markets()

    @Decorators.ccxt_exception_handler
    def load_markets(self):
        if self.exchange is not None:
            self.exchange.load_markets()

    @Decorators.ccxt_exception_handler
    def get_balance(self, sym=None):
        return self.exchange.fetch_balance() if sym is None else self.exchange.fetch_balance()[sym]

    def get_free_balance(self, sym=None):
        return self.get_balance(sym)['free']

    def get_total_balance(self, sym=None):
        return self.get_balance(sym)['total']

    def get_used_balance(self, sym=None):
        return self.get_balance(sym)['used']

    @Decorators.ccxt_exception_handler
    def load_fees(self):
        self.exchange.fetch_trading_fees()



