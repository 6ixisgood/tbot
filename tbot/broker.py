import time
import logging
from collections import defaultdict
from pprint import pprint
import json
import asyncio

log = logging.getLogger('tbot.broker')


class Broker():
    def __init__(self, strategies, **kwargs):
        self.strategies = strategies
        self.required_funds = defaultdict(dict)

    def broker(self):
        # determine if there are enough funds to run the strategies
        self.update_required_funds()
        if not self.check_funds():
            log.error("Not enough funds to run all strategies")
            return

        # run strategies
        while True:
            for name, strategy in self.strategies.items():
                asyncio.run(strategy.trade())
                # if trade is not None:
                #     self.register_trade(trade)
                #     self.check_funds()

    def check_funds(self):
        for exchange, pair in self.required_funds.items():
            for sym, amount in pair.items():
                if not exchange.get_free_balance(sym) >= amount:
                    return False
        return True

    def update_required_funds(self):
        for name, strategy in self.strategies.items():
            for sym, amount in strategy.get_required_funds().items():
                self.required_funds[strategy.exchange][sym] = \
                    self.required_funds[strategy.exchange].get(sym, 0) + amount

    def register_trade(self, trade):
        """
        Somehow make note of a trade
        """
        pass


