import pytest

import numpy as np
import pandas as pd

from systrade.trading.brokers import PaperBroker
from systrade.trading.accounts import BasicAccount
from systrade.trading import orders

TIME_START = pd.to_datetime('2019/07/10-09:30:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
TIME_END   = pd.to_datetime('2019/07/10-09:40:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
TIMEINDEX = pd.date_range(start=TIME_START,end=TIME_END,freq='1min')
DATA_DF   = pd.DataFrame(data={'tick0':np.arange(len(TIMEINDEX)) ,
                               'tick1':np.arange(len(TIMEINDEX)-1,-1,-1)},
                                index=TIMEINDEX)

# ------------------------------------------------------------------------------

# useful mack/stub classes

class FakeBroker:

    def __init__(self,data):
        self.data=data

    def get_buy_price(self,ticker,time):
        price = self.data.loc[time][ticker]
        return price,0,time

    def get_sell_price(self,ticker,time):
        price = self.data.loc[time][ticker]
        return price,0,time

    def get_data_subset(self,ticker,time):
        pass

    def get_firstlast_times(self):
        return TIME_START,TIME_END

    def get_timeindex_subset(self,t0,t1):
        return self.data.loc[t0:t1].index

    def get_price_list(self):
        pass

    def get_unslipped_price(self):
        pass


FAKE_BROKER = FakeBroker(DATA_DF)


class FakeOrder:
    def __init__(self,type,time):
        self.placed = False
        self.fulfilled = False
        self.type = type
        self.ticker = 'tick'
        self.time_placed = time
        self.time_executed = None

    def place_historical(self):
        self.placed = True
        self.time_executed = self.time_placed

    def execute_historical(self,portfolio):
        self.fulfilled = True
        if self.type=='buy':
            portfolio.buy_ticker()
        if self.type=='sell':
            portfolio.sell_ticker()


class FakeOrderPlacer:
    def process_order(self,info,broker):
        order = FakeOrder(info['type'],info['time'])
        order.place_historical()
        return order


class FakeOrderManager:
    def __init__(self,placer):
        self.orders = dict()
        self.placer = placer
        self.last_int=0

    def place_order(self,info,broker):
        id = self.last_int + 1
        self.last_int+=1
        self.orders[id] = self.placer.process_order(info,broker)

    def cancel_order(self,id):
        self.orders.pop(id)

    def execute_order(self,id,portfolio):
        self.orders[id].execute_historical(portfolio)
        self.orders.pop(id)

    def get_open_orders_info(self):
        out = dict()
        for id,o in self.orders.items():
            out[id] = {'time_executed':o.time_executed}
        return out

FAKE_ORDER_MANAGER = FakeOrderManager(FakeOrderPlacer())

class FakePortfolio:
    def __init__(self):
        self.bought=0
        self.sold=0

    def buy_ticker(self,*args):
        self.bought+=1

    def sell_ticker(self,*args):
        self.sold+=1

    def update_to_time(self,time):
        pass

    def add_to_history(self,broker,time):
        pass


FAKE_PORTFOLIO = FakePortfolio()


# ------------------------------------------------------------------------------
# actually testing

class TestBasicAccount:
    def test_update_to_t(self):
        account = BasicAccount(FAKE_BROKER,TIME_START,TIME_END,FAKE_ORDER_MANAGER,FAKE_PORTFOLIO)
        account.place_historical_order('buy',TIME_START,'tick0',1,None)
        account.place_historical_order('sell',TIME_START+pd.DateOffset(minutes=3),'tick0',1,None)
        account.place_historical_order('buy',TIME_START+pd.DateOffset(minutes=5),'tick0',1,None)

        with pytest.raises(TypeError):
            account.update_to_t(1)

        account.update_to_t(TIME_START+pd.DateOffset(minutes=1))
        assert account.asset_manager.bought == 1
        assert account.asset_manager.sold == 0
        assert account.last_time_checked == TIME_START+pd.DateOffset(minutes=1)

        account.update_to_t(TIME_START+pd.DateOffset(minutes=2))
        assert account.asset_manager.bought == 1
        assert account.asset_manager.sold == 0

        account.update_to_t(TIME_START+pd.DateOffset(minutes=3))
        assert account.asset_manager.bought == 1
        assert account.asset_manager.sold == 1

        account.update_to_t(TIME_START+pd.DateOffset(minutes=6))
        assert account.asset_manager.bought == 2
        assert account.asset_manager.sold == 1

        assert account.total_trades == 3

    def test_cancel_order(self):
        account = BasicAccount(FAKE_BROKER,TIME_START,TIME_END,FAKE_ORDER_MANAGER,FAKE_PORTFOLIO)
        id0 = account.place_historical_order('buy',TIME_START,'tick0',1,None)
        with pytest.warns(Warning):
            account.cancel_order('j')
    
