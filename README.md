# T-Bot
Automated trading bot.  Run a variety of strategies along various exchanges.

## Settings File
To run, construct a YAML settings file. Specify the exchanges and strategies to use.  
Reference the Exchange and Strategy documentation for required values. 
```yaml
exchanges:
  - name: "binance"
    type: "tbot.exchange.binance.Binance"
    options:
      apiKey: "xxxx"
      apiSecret: "xxxx"
strategies:
  - name: "arbitrage"
    type: "tbot.strategy.arbitrage.Arbitrage"
    exchange: "binance"
    options:
      trade_unit: .0003
      init_currency: "BTC"
      level: 5
      min_rate: .003
```

## Exchanges
Exchanges are mostly based off of the CCXT library, with supplement from other sources
(e.g. for websocket support).

The general setup for an exchange is as follows:
```yaml
exchanges:
  - name: "nickname for exchange"
    type: "tbot module.className"
    # all the options for the specific exchange here
    options:
      apiKey: "xxxx"
      apiSecret: "xxxx"
```

## Strategies
Multiple strategies can be ran at a time, with most having unique options.
```yaml
strategies:
  - name: "nickname for strategy"
    type: "tbot module.className"
    exchange: "exchange nickname"
    # strat specific options
    options:
      trade_unit: .0003
      init_currency: "BTC"
      level: 5
      min_rate: .003
```