import pytest

import pandas as pd
import numpy as np

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
    def get_buy_price(self,ticker,time):
        price = DATA_DF.loc[time][ticker]
        return price,0,time

    def get_sell_price(self,ticker,time):
        price = DATA_DF.loc[time][ticker]
        return price,0,time

    def get_data_subset(self,ticker,time):
        return DATA_DF


FAKE_BROKER = FakeBroker()


class FakeOrder:
    def __init__(self):
        self.placed = False
        self.fulfilled = False
        self.type = 'buy'
        self.ticker = 'tick'
        self.time_placed = TIME_START
        self.time_executed = TIME_START

    def place_historical(self):
        self.placed = True

    def execute_historical(self,portfolio):
        self.fulfilled = True


class FakeOrderPlacer:
    def process_order(self,info,broker):
        order = FakeOrder()
        order.place_historical()
        return order

class FakePortfolio:
    def __init__(self):
        self.bought=0
        self.sold=0

    def buy_ticker(self,*args):
        self.bought+=1

    def sell_ticker(self,*args):
        self.sold+=1

class SimpleBuyOrder(orders.Order):
    def __init__(self,time,ticker,quantity):
        self.buysell=1
        super().__init__(time,ticker,quantity)

    def get_price_fee_time(self,broker):
        return 0,0,0

class SimpleSellOrder(orders.Order):
    def __init__(self,time,ticker,quantity):
        self.buysell=-1
        super().__init__(time,ticker,quantity)

    def get_price_fee_time(self,broker):
        return 0,0,0


# ------------------------------------------------------------------------------
# actual test case classes


class TestOrderPlacer:
    def test__info_to_order(self):
        new_order_info = {'time':TIME_START,
                          'type':'buy_market',
                          'ticker':'tick0',
                          'quantity':1,
                          'limit':10}
        my_placer = orders.OrderPlacer()
        the_order = my_placer._info_to_order(new_order_info)
        assert isinstance(the_order, orders.BuyMarketOrder)

        new_order_info['type'] = 'not_a_type'
        with pytest.raises(ValueError):
            the_order = my_placer._info_to_order(new_order_info)

    def test_process_order(self):
        new_order_info = {'time':TIME_START,
                          'type':'buy_market',
                          'ticker':'tick0',
                          'quantity':1,
                          'limit':10}
        my_placer = orders.OrderPlacer()
        the_order = my_placer.process_order(new_order_info,FAKE_BROKER)
        assert isinstance(the_order, orders.BuyMarketOrder)
        assert the_order.placed


class TestOrderManager:
    def test_place_order(self):
        placer = FakeOrderPlacer()
        manager = orders.OrderManager(order_placer = placer)
        id = manager.place_order(None,None)
        assert manager.orders[id].placed
        assert len(manager.orders)==1

    def test_cancel_order(self):
        placer = FakeOrderPlacer()
        manager = orders.OrderManager(order_placer = placer)
        id0 = manager.place_order(None,None)
        id1 = manager.place_order(None,None)
        print(manager.orders)
        manager.cancel_order(id0)
        print(manager.orders)
        assert len(manager.orders)==1
        assert len(manager.cancelled)==1
        assert id0 in manager.cancelled
        assert id0 not in manager.orders
        assert id1 in manager.orders
        assert id1 not in manager.cancelled

    def test_execute_order(self):
        placer = FakeOrderPlacer()
        manager = orders.OrderManager(order_placer = placer)
        id0 = manager.place_order(None,None)
        manager.execute_order(id0,None)
        assert len(manager.orders)==0
        assert len(manager.cancelled)==0
        assert len(manager.fulfilled)==1
        assert manager.fulfilled[id0].fulfilled

    def test_check_order_fulfilled(self):
        placer = FakeOrderPlacer()
        manager = orders.OrderManager(order_placer = placer)
        id0 = manager.place_order(None,None)
        bool = manager.check_order_fulfilled(id0)
        assert not bool
        manager.execute_order(id0,None)
        bool = manager.check_order_fulfilled(id0)
        assert bool

    def test_order_to_info(self):
        this_order = FakeOrder()
        placer = FakeOrderPlacer()
        manager = orders.OrderManager(order_placer = placer)
        info = manager.order_to_info(this_order)
        assert info=={'type':'buy',
                      'ticker':'tick',
                      'time_placed':TIME_START,
                      'time_executed':TIME_START}

    def test_get_open_orders(self):
        placer = FakeOrderPlacer()
        manager = orders.OrderManager(order_placer = placer)
        id0 = manager.place_order(None,None)
        id1 = manager.place_order(None,None)
        open = manager.get_open_orders_info()
        assert len(open)==2

    def test_get_fulfilled_orders_info(self):
        placer = FakeOrderPlacer()
        manager = orders.OrderManager(order_placer = placer)
        id0 = manager.place_order(None,None)
        id1 = manager.place_order(None,None)
        manager.execute_order(id0,None)
        manager.execute_order(id1,None)
        fulfilled = manager.get_fulfilled_orders_info()
        assert len(fulfilled)==2

    def test_get_cancelled_orders_info(self):
        placer = FakeOrderPlacer()
        manager = orders.OrderManager(order_placer = placer)
        id0 = manager.place_order(None,None)
        id1 = manager.place_order(None,None)
        manager.cancel_order(id0)
        manager.cancel_order(id1)
        cancelled = manager.get_cancelled_orders_info()
        assert len(cancelled)==2

    def test_merge_order_dictionaries(self):
        placer = FakeOrderPlacer()
        manager = orders.OrderManager(order_placer = placer)
        dict1 = {'a':0, 'b':1}
        dict2 = {'c':2, 'd':3}
        out = manager.merge_order_dictionaries(dict1,dict2)
        assert out == {'a':0, 'b':1, 'c':2, 'd':3}
        dict2 = {'b':3,'d':5}
        with pytest.raises(RuntimeError):
            out = manager.merge_order_dictionaries(dict1,dict2)

    def test_get_all_orders_info(self):
        placer = FakeOrderPlacer()
        manager = orders.OrderManager(order_placer = placer)
        id0 = manager.place_order(None,None)
        id1 = manager.place_order(None,None)
        id2 = manager.place_order(None,None)
        id3 = manager.place_order(None,None)
        manager.cancel_order(id0)
        manager.execute_order(id1,None)
        all_orders = manager.get_all_orders_info()
        assert len(all_orders)==4


class TestOrder:
    def test_place_historical(self):
        order = SimpleBuyOrder(TIME_START,'tick',1)
        order.place_historical(None)
        assert order.placed
        order.fulfilled=True
        with pytest.warns(RuntimeWarning):
            order.place_historical(None)

    def test_execute_historical(self):
        order = SimpleBuyOrder(TIME_START,'tick',1)
        order.place_historical(None)
        portfolio = FakePortfolio()
        order.execute_historical(portfolio)
        assert order.fulfilled
        assert portfolio.bought==1
        assert portfolio.sold==0

        order = SimpleSellOrder(TIME_START,'tick',1)
        order.place_historical(None)
        portfolio = FakePortfolio()
        order.execute_historical(portfolio)
        assert order.fulfilled
        assert portfolio.sold==1
        assert portfolio.bought==0

        order = SimpleSellOrder(TIME_START,'tick',1)
        portfolio = FakePortfolio()
        with pytest.raises(UnboundLocalError):
            order.execute_historical(portfolio)

class TestBuyLimitOrder:
    def test_get_price_fee_time(self):
        order = orders.BuyLimitOrder(TIME_START,'tick1',1,7.5)
        p,f,t = order.get_price_fee_time(FAKE_BROKER)
        assert t==TIME_START+pd.DateOffset(minutes=3)
        assert p==7

class TestSellLimitOrder:
    def test_get_price_fee_time(self):
        order = orders.SellLimitOrder(TIME_START,'tick0',1,3.5)
        p,f,t = order.get_price_fee_time(FAKE_BROKER)
        assert t==TIME_START+pd.DateOffset(minutes=4)
        assert p==4
