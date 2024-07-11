from lumibot.brokers import Alpaca  # the broker
from lumibot.backtesting import YahooDataBacktesting  # framework for backtesting
from lumibot.strategies.strategy import Strategy  # the trading bot
from lumibot.traders import Trader  # deployment capability for running live
from datetime import datetime
from alpaca_trade_api import REST
from timedelta import Timedelta
from finbert_utils import estimate_sentiment  # the machine learning model

API_KEY = "PK0Z7OFHYCECN28DT91L"
API_SECRET = "wbPxNsTrcoHlRRKbP2cm3USeH1JThOcg4lwG6TNW"
BASE_URL = "https://paper-api.alpaca.markets/v2"

ALPACA_CREDS = {
    "API_KEY": API_KEY,
    "API_SECRET": API_SECRET,
    "PAPER": True
}

class MLTrader(Strategy):
    def initialize(self, symbols: list = ["SPY"], cash_at_risk: float = .5):
        self.symbols = symbols
        self.sleeptime = "24H"  # frequency of trade
        self.last_trades = {symbol: None for symbol in symbols}  # capture last trade for each symbol
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)

    def position_sizing(self, symbol):
        cash = self.get_cash()
        last_price = self.get_last_price(symbol)
        # ex: cash_at_risk=.5 means use 50% of our remaining cash balance
        quantity = round(cash * self.cash_at_risk / last_price, 0)
        return cash, last_price, quantity

    def get_dates(self):
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def get_sentiment(self, symbol):
        today, three_days_prior = self.get_dates()
        news = self.api.get_news(symbol=symbol,
                                 start=three_days_prior,
                                 end=today)
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment

    def on_trading_iteration(self):
        for symbol in self.symbols:
            cash, last_price, quantity = self.position_sizing(symbol)
            probability, sentiment = self.get_sentiment(symbol)

            if cash > last_price:
                if sentiment == "positive" and probability > .999:
                    if self.last_trades[symbol] == "sell":
                        self.sell_all()
                    order = self.create_order(
                        symbol,
                        quantity,
                        "buy",
                        type="bracket",
                        take_profit_price=last_price * 1.20,
                        stop_loss_price=last_price * .95
                    )
                    self.submit_order(order)
                    self.last_trades[symbol] = "buy"
                elif sentiment == "negative" and probability > .999:
                    if self.last_trades[symbol] == "buy":
                        self.sell_all()
                    order = self.create_order(
                        symbol,
                        quantity,
                        "sell",
                        type="bracket",
                        take_profit_price=last_price * .8,
                        stop_loss_price=last_price * 1.05
                    )
                    self.submit_order(order)
                    self.last_trades[symbol] = "sell"

start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 12, 31)

broker = Alpaca(ALPACA_CREDS)

strategy = MLTrader(name='Trading Bot', broker=broker, 
                    parameters={"symbols": ["SPY", "AAPL", "GOOGL"],  # List of symbols
                                "cash_at_risk": .5  # higher number means more cash per trade
                                })

strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbols": ["SPY", "AAPL", "GOOGL"],
                "cash_at_risk": .5}
)
'''
# Create a Trader instance
trader = Trader()

# Add the strategy to the trader
trader.add_strategy(strategy)

# Deploy the strategy for live trading
trader.run_all()
'''