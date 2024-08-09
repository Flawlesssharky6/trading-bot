# MIT License
#
# Original work Copyright (c) 2024 Nick Renotte
# Modifications Copyright (c) 2024 Kyle Chengqiang Lin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from lumibot.brokers import Alpaca  # the broker
from lumibot.backtesting import YahooDataBacktesting  # framework for backtesting
from lumibot.strategies.strategy import Strategy  # the trading bot
from lumibot.traders import Trader  # deployment capability for running live
from datetime import datetime
from alpaca_trade_api import REST
from timedelta import Timedelta
from finbert_utils import estimate_sentiment  # the machine learning model
import logging

# Setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = "PK0Z7OFHYCECN28DT91L"
API_SECRET = "wbPxNsTrcoHlRRKbP2cm3USeH1JThOcg4lwG6TNW"
BASE_URL = "https://paper-api.alpaca.markets/v2"

ALPACA_CREDS = {
    "API_KEY": API_KEY,
    "API_SECRET": API_SECRET,
    "PAPER": True
}

class MLTrader(Strategy):
    def initialize(self, symbols: list = ["SPY"], cash_at_risk: float = .5, sentiment_threshold: float = .999):
        self.symbols = symbols
        self.sleeptime = "24H"  # frequency of trade
        self.last_trades = {symbol: None for symbol in symbols}  # capture last trade for each symbol
        self.cash_at_risk = cash_at_risk
        self.sentiment_threshold = sentiment_threshold
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)
        self.last_trade_dates = {symbol: None for symbol in symbols}  # Store last trade date for each symbol

    def position_sizing(self, symbol):
        try:
            cash = self.get_cash()
            last_price = self.get_last_price(symbol)
            quantity = round(cash * self.cash_at_risk / last_price, 0)
            return cash, last_price, quantity
        except Exception as e:
            logger.error(f"Error in position_sizing: {e}")
            return 0, 0, 0

    def get_dates(self):
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def get_sentiment(self, symbol):
        try:
            today, three_days_prior = self.get_dates()
            news = self.api.get_news(symbol=symbol, start=three_days_prior, end=today)
            news = [ev.__dict__["_raw"]["headline"] for ev in news]
            probability, sentiment = estimate_sentiment(news)
            return probability, sentiment
        except Exception as e:
            logger.error(f"Error in get_sentiment: {e}")
            return 0, "neutral"

    def on_trading_iteration(self):
        today = self.get_datetime().date()
        for symbol in self.symbols:
            try:
                cash, last_price, quantity = self.position_sizing(symbol)
                probability, sentiment = self.get_sentiment(symbol)

                last_trade_date = self.last_trade_dates.get(symbol)

                if last_trade_date == today:
                    logger.info(f"Skipping trade for {symbol} to avoid day trading.")
                    continue

                if cash > last_price:
                    if sentiment == "positive" and probability > self.sentiment_threshold:
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
                        self.last_trade_dates[symbol] = today
                    elif sentiment == "negative" and probability > self.sentiment_threshold:
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
                        self.last_trade_dates[symbol] = today
            except Exception as e:
                logger.error(f"Error in on_trading_iteration for {symbol}: {e}")

start_date = datetime(2020, 1, 1)
end_date = datetime(2023, 12, 31)

broker = Alpaca(ALPACA_CREDS)

strategy = MLTrader(name='Trading Bot', broker=broker, 
                    parameters={"symbols": ["SPY", "AAPL", "GOOGL"],  
                                "cash_at_risk": .5,  
                                "sentiment_threshold": .999 
                                })

strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbols": ["SPY", "AAPL", "GOOGL"],
                "cash_at_risk": .5,
                "sentiment_threshold": .999
                }
)

# Uncomment the lines below to deploy the strategy for live trading

# Create a Trader instance
# trader = Trader()

# Add the strategy to the trader
# trader.add_strategy(strategy)

# Deploy the strategy for live trading
# trader.run_all()
