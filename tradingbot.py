from lumibot.brokers import Alpaca # the broker
from lumibot.backtesting import YahooDataBacktesting # frame work for back testing
from lumibot.strategies.strategy import Strategy # the trading bot
from lumibot.traders import Trader # delpoyment capability for running live
from datetime import datetime

API_KEY = "PKFI2YEDDK32ILJ49DK2"
API_SECRET = "NaPGvSelWmrwnNxTKvEYBVMTckMQzKN6lxIwUP57"
BASE_URL = "https://paper-api.alpaca.markets/v2"

ALPACA_CREDS = {
    "API_KEY":API_KEY,
    "API_SECRET":API_SECRET,    
    "PAPER":True 
}
class MLTrader(Strategy):
    def initialize(self, symbol:str="SPY"):
        self.symbol = symbol
        self.sleeptime = "24H" # frequency of trade
        self.last_trade = None # capture last trade
    def on_trading_iteration(self):
        if self.last_trade == None:
            order = self.create_order(
                self.symbol,
                10,
                "buy",
                type="market"
            )
            self.submit_order(order)
            self.last_trade = "buy"
    
start_date = datetime(2023,12,15)
end_date = datetime(2023,12,31)

broker = Alpaca(ALPACA_CREDS)
strategy = MLTrader(name='Trading Bot', broker=broker, 
                    parameters={"symbol":"SPY"})
strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbol":"SPY"}
)