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
    def initialize(self, symbol:str="SPY", cash_at_risk:float=.5):
        #attributes
        self.symbol = symbol
        self.sleeptime = "24H" # frequency of trade
        self.last_trade = None # capture last trade
        self.cash_at_risk = cash_at_risk
        
    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        # ex: cash_at_risk=.5 means use 50% of our remaining cash balance
        quantity = round(cash * self.cash_at_risk / last_price, 0)
        return cash, last_price, quantity
            
    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        
        if cash > last_price:
            if self.last_trade == None:
                order = self.create_order(
                    self.symbol,
                    quantity,
                    "buy",
                    type="bracket",
                    take_profit_price=last_price*1.20,
                    stop_loss_price=last_price*.95
                )
                self.submit_order(order)
                self.last_trade = "buy"
    
start_date = datetime(2023,12,15)
end_date = datetime(2023,12,31)

broker = Alpaca(ALPACA_CREDS)
strategy = MLTrader(name='Trading Bot', broker=broker, 
                    parameters={"symbol":"SPY",
                                "cash_at_risk":.5 # higher number means more cash per trade
                                })
strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbol":"SPY",
                "cash_at_risk":.5}
)