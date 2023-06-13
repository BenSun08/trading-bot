from alpaca.trading.client import TradingClient
from alpaca.trading.stream import TradingStream
from alpaca.trading.requests import GetAssetsRequest, MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import AssetClass, OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, CryptoLatestQuoteRequest,\
    StockBarsRequest, CryptoBarsRequest
from alpaca.data.live import StockDataStream, CryptoDataStream
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
from config import API_KEY, SECRET_KEY
from .. import socketio


class AlpacaTradeBot:
    def __init__(self):
        self.trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

    def get_account(self):
        account = self.trading_client.get_account()
        for property_name, value in account:
            print(f"\"{property_name}\": {value}")
        return account

    def get_asset_types(self):
        asset_types = [a.value for a in AssetClass] # "us_equity", "crypto"
        print(asset_types) 
        print([s.value for s in OrderSide]) # "buy", "sell"
        return asset_types
    
    def get_all_assets(self, type="crypto"):
        search_params = GetAssetsRequest(asset_class=type)
        assets = self.trading_client.get_all_assets(search_params)
        # print(assets[0])
        parsed_assets = list(map(lambda a: { "id": a.id, "name": a.name,
        "symbol": a.symbol, "tradable": a.tradable }, assets))
        return parsed_assets
    
    def get_asset(self, id_or_symbol):
        asset = self.trading_client.get_asset(id_or_symbol)
        print(asset)
        return asset
    
    def make_order(self, symbol, qty, side="buy"):
        # preparing orders
        market_order_data = MarketOrderRequest(
                            symbol=symbol,
                            qty=qty,
                            side=side,
                            time_in_force=TimeInForce.DAY
                            )

        # Market order
        market_order = self.trading_client.submit_order(
                        order_data=market_order_data
                    )
        print(market_order)
        return market_order
        
    def get_orders(self, **kwargs):
        # params to filter orders by
        request_params = GetOrdersRequest(**kwargs)
        orders = self.trading_client.get_orders(filter=request_params)
        print(orders)
        return orders
    
    def cancel_all_orders(self):
        cancel_statuses = self.trading_client.cancel_orders()
        print(cancel_statuses)
        return cancel_statuses
    
    def cancel_order(self, id):
        cancel_status = self.trading_client.cancel_order_by_id(id)
        return cancel_status


class AlpacaDataBot:
    def __init__(self, type="crypto"): #type = "stock", "crypto"; 
        self.client = CryptoHistoricalDataClient(API_KEY, SECRET_KEY) if type == "crypto" \
            else StockHistoricalDataClient(API_KEY, SECRET_KEY)
        self.type = type
    
    def get_latest_quote(self, symbol_or_symbols):
        if self.type == "crypto":
            request_params = CryptoLatestQuoteRequest(symbol_or_symbols=symbol_or_symbols)
            latest_quote = self.client.get_crypto_latest_quote(request_params)
        else:
            request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol_or_symbols)
            latest_quote = self.client.get_stock_latest_quote(request_params)
        print(latest_quote)
        return latest_quote
    
    def get_history(self, symbol_or_symbols, start, end):
        if self.type == "crypto":
            request_params = CryptoBarsRequest(
                            symbol_or_symbols=["BTC/USD", "ETH/USD"],
                            timeframe=TimeFrame.Day,
                            start=datetime(start),
                            end=datetime(end)
                        )
            bars = self.client.get_crypto_bars(request_params)
            # convert to dataframe
            bars.df
        else:
            request_params = StockBarsRequest(
                            symbol_or_symbols=symbol_or_symbols,
                            timeframe=TimeFrame.Day,
                            start=datetime(start),
                            end=datetime(end)
                        )
            bars = self.client.get_stock_bars(request_params)
            # convert to dataframe
            bars.df

#paper trading:  wss://paper-api.alpaca.markets/stream 
#live trading:   wss://api.alpaca.markets/stream
class AlpacaRealTimeBot:
    def __init__(self, type="crypto"):
        self.data_stream = CryptoDataStream(api_key=API_KEY, secret_key=SECRET_KEY, feed="us")  \
            if type == "crypto" else StockDataStream(API_KEY, SECRET_KEY)
        self.trading_stream = TradingStream(API_KEY, SECRET_KEY, paper=True)

        self.type = type

    def subscribe(self, symbols):
        print(symbols)
        async def quote_handler(data):
            print(data.json())
            socketio.emit('data', data.json())

        async def trade_handler(data):
            print(data.json())
            socketio.emit('data', data.json())
        
        async def updated_bar_handler(data):
            print(data.json())
            socketio.emit('data', data.json())

        self.data_stream.subscribe_quotes(quote_handler, *symbols)
        self.data_stream.subscribe_trades(trade_handler, *symbols)
        self.data_stream.subscribe_updated_bars(updated_bar_handler, *symbols)

        self.data_stream.run()
    
    def unsubscribe(self, symbols):
        self.data_stream.unsubscribe_quotes(*symbols)
        self.data_stream.unsubscribe_trades(*symbols)
        self.data_stream.unsubscribe_updated_bars(*symbols)

        self.data_stream.stop()


    def subscribe_trade_updates(self):
        # async handler
        async def update_handler(data):
            # trade updates will arrive here
            print(data)

        self.trading_stream.subscribe_trade_updates(update_handler)

        self.trading_stream.run()