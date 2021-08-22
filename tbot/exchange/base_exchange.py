import logging
from collections import defaultdict

log = logging.getLogger('tbot.exchange.base_exchange')


class BaseExchange:
    """
    Basic priniples of a tbot exchange.  A tbot exchange consists of ways to interact
    with real (or simulated) trade data and provides a way to make trades.

    Most "fetch" methods will fetch the newest information from their appropriate exchange
    and return the information.  They also update the instance variables (e.g. order_book,
    markets, ticker, fees, etc.) so you can interact with those directly, without forcing
    and update.

    The instance variables can be updated using other means (e.g. async websockets) for
    better connection to live data.  The variables themselves should be accessed through
    "get" methods ("get" is obmitted in method names for brevity).
    """
    def __init__(self, **kwargs):
        self._order_book = defaultdict(dict)
        self._market = defaultdict(dict)
        self._ticker = defaultdict(dict)
        self._fees = defaultdict(dict)
        self._balance = defaultdict(lambda: defaultdict(float))
        self.startup(**kwargs)

    def startup(self, **kwargs):
        """
        Execute any necessary startup commands.  Good for things like loading fees
        and markets early.
        :return:
        """

    ##############################
    # Create Orders
    ##############################

    def create_order(self, sym, type, side, amount, price=None, params={}):
        """
        Create an order. Used by strategies to place orders to the exchange.
        :param sym: Trading symbol
        :param type: Trade type (e.g. market, limit)
        :param side: Side of trade (e.g. buy, sell)
        :param amount: Amount to trade. Could be either base or quote (TODO sure this up)
        :param price: Price to execute at (for limit orders)
        :param params: Optional parameters
        :return: An order summary (CCXT-style)
        """
        pass

    ##############################
    # Order Book
    ##############################

    def fetch_order_book(self, *args):
        """
        Get the order book
        :param args: Optional list of symbols
        :return:
        """
        self.load_order_book(*args)
        book = defaultdict(dict)
        if not args:
            for symbol in args:
                try:
                    book[symbol] = self.order_book.get(symbol, None)
                except KeyError:
                    log.info(f"No symbol {symbol} in exchange order book")
        else:
            book = self.order_book
        return book

    def load_order_book(self, *args):
        """
        Load current data into exchange's order book (CCXT-style order book structure),
        updating order book dict
        :return:
        """
        pass

    def order_book(self):
        """
        Get the current order book.  No fetching data
        ""
        :return: order book
        """
        return self._order_book

    ##############################
    # Tickers
    ##############################

    def fetch_ticker(self, *args):
        """
        Get ticker info for exchange
        :param args: optional list of symbols to fetch the ticker for
        :return:
        """
        self.load_order_book()
        ticker = defaultdict(dict)
        if not args:
            for symbol in args:
                try:
                    ticker[symbol] = self.ticker.get(symbol, None)
                except KeyError:
                    log.info(f"No symbol {symbol} in exchange ticker")
        else:
            ticker = self.ticker
        return ticker

    def load_ticker(self, *args):
        """
        Load the ticker info from the exchange, updating ticker dict
        :return:
        """

    def ticker(self):
        """
        Get the current ticker.  No fetching data
        :return: ticker
        """
        return self._ticker

    ##############################
    # Markets
    ##############################

    def fetch_market(self, *args):
        """
        Get maerket info for exchange
        :param args: optional list of symbols to fetch the market for
        :return: market
        """
        self.load_market(*args)
        market = defaultdict(dict)
        if not args:
            for symbol in args:
                try:
                    market[symbol] = self._market.get(symbol, None)
                except KeyError:
                    log.info(f"No symbol {symbol} in exchange ticker")
        else:
            ticker = self.ticker
        return market

    def load_market(self, *args):
        """
        Load the market info from the exchange, updating ticker dict
        :return:
        """

    def market(self):
        """
        Get the current markets. No fetching data
        :return: market
        """
        return self._market

    ##############################
    # Account Info
    ##############################

    def fetch_balance(self, *args):
        """
        Get the current balance of a currency
        :param sym: Currency symbol
        :return:
        """
        pass

    def balance(self, sym):
        """
        Return the balance for a given symbol
        :return:
        """
        return self._balance[sym]

    def fetch_fees(self, *args):
        """
        Get the fees
        :param syms: Optional list of symbols to get fees for
        :return:
        """
        fees = defaultdict(dict)
        if not args:
            for symbol in args:
                try:
                    fees[symbol] = self.fees.get(symbol, None)
                except KeyError:
                    log.info(f"No symbol {symbol} in exchange fees")
        else:
            fees = self.order_book
        return fees

    def load_fees(self, *args):
        """
        Load the fee info to the exchange, updating "fees" dict
        {"BTC/USDT": {"feeType": amount}}
        :return:
        """

    def get_fees(self):
        """
        Get the current fees. No fetching data
        :return: fees
        """
        return self._fees