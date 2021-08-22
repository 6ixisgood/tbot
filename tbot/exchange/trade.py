
class Trade():
    def __init__(self, *, ccxt_order):
        for k, v in ccxt_order.items():
            setattr(self, k, v)

    def start_amount(self):
        return self.cost if self.side == 'buy' else self.filled

    def end_amount(self):
        return self.filled if self.side == 'buy' else self.cost

    def start_symbol(self):
        return self.symbol.split('/')[1 if self.side == 'buy' else 0]

    def end_symbol(self):
        return self.symbol.split('/')[0 if self.side == 'buy' else 1]

    def rate(self):
        return 1/self.price if self.side == 'buy' else self.price
