import pytest

import numpy as np
import pandas as pd

from systrade.trading.holdings import AssetManager
from systrade.trading.holdings import Holdings
from systrade.trading.holdings import CashHoldingConstantRate

TIME0 = pd.to_datetime('2019/07/10-09:30:00:000000',
                       format='%Y/%m/%d-%H:%M:%S:%f')

TIME_START = pd.to_datetime('2019/07/10-09:30:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
TIME_END   = pd.to_datetime('2019/07/10-09:40:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
TIMEINDEX = pd.date_range(start=TIME_START,end=TIME_END,freq='1min')
DATA_DF   = pd.DataFrame(data={'tick0':np.arange(len(TIMEINDEX)) ,
                               'tick1':np.arange(len(TIMEINDEX)-1,-1,-1)},
                                index=TIMEINDEX)

# ------------------------------------------------------------------------------

# useful mock/stub classes

class FakeBroker:
    def get_unslipped_price(self,ticker,time):
        price = DATA_DF.loc[time][ticker]
        return price


FAKE_BROKER = FakeBroker()

SECONDS_IN_FULL_YEAR = 3600.0*24.0*365.0

class SimpleHoldings:
    def __init__(self):
        self.holds = dict()

    def add_asset(self,time,ticker,quantity):
        if ticker not in self.holds:
            self.holds[ticker]=quantity
        else:
            self.holds[ticker] += quantity

    def get_holdings(self,time):
        return self.holds

class SimpleCash:

    def __init__(self):
        self.cash = 0

    def add_asset(self,amount,time):
        self.cash += amount

    def set_adjustments_to_now(self,time):
        return self.cash

    def get_cash_no_new_vals_check(self,time):
        return self.cash


# ------------------------------------------------------------------------------

class TestAssetManager:
    def test_buy_ticker(self):
        manager = AssetManager(['tick0','tick1'],TIME0,0.0,
                            stock_holding=SimpleHoldings(),
                            cash_holding=SimpleCash(),
                            fee_holding=SimpleCash())
        manager.buy_ticker(TIME0,'tick0',10,2,2)
        assert manager.stock_holding.holds['tick0']==10
        assert manager.cash_holding.cash == -20
        assert manager.fee_holding.cash == -2

    def test_sell_ticker(self):
        manager = AssetManager(['tick0','tick1'],TIME0,0.0,
                            stock_holding=SimpleHoldings(),
                            cash_holding=SimpleCash(),
                            fee_holding=SimpleCash())
        manager.sell_ticker(TIME0,'tick0',10,2,2)
        assert manager.stock_holding.holds['tick0']==-10
        assert manager.cash_holding.cash == 20
        assert manager.fee_holding.cash == -2

    def simple_buysell(self):
        manager = AssetManager(['tick0','tick1'],TIME_START,0.0,
                            stock_holding=SimpleHoldings(),
                            cash_holding=SimpleCash(),
                            fee_holding=SimpleCash())
        manager.buy_ticker(TIME_START,'tick0',10,2,2)
        manager.buy_ticker(TIME_START,'tick1',4,3,2)
        manager.sell_ticker(TIME_START,'tick1',5,3,2)
        return manager

    def test_update_stock_time(self):
        manager = self.simple_buysell()
        manager.update_stock_to_time(TIME_END)
        assert manager._current_stock == {'tick0':10,'tick1':-1}

    def test_update_cash_to_time(self):
        manager = self.simple_buysell()
        manager.update_cash_to_time(TIME_END)
        assert manager.cash_holding.cash == -17

    def test_update_fee_to_time(self):
        manager = self.simple_buysell()
        manager.update_fee_to_time(TIME_END)
        assert manager.fee_holding.cash == -6

    def test_get_stock_portfolio_value(self):
        manager = self.simple_buysell()

        # values not updated
        value = manager.get_stock_portfolio_value(FAKE_BROKER,TIME_START)
        assert value == 0

        # update values
        manager.update_to_time(TIME_START)
        value = manager.get_stock_portfolio_value(FAKE_BROKER,TIME_START)
        assert value == -10

        manager.update_to_time(TIME_END)
        value = manager.get_stock_portfolio_value(FAKE_BROKER,TIME_END)
        assert value == 100

    def test_add_to_history(self):
        manager = self.simple_buysell()
        manager.update_to_time(TIME_START)
        manager.add_to_history(FAKE_BROKER,TIME_START)
        manager.update_to_time(TIME_END)
        manager.add_to_history(FAKE_BROKER,TIME_END)
        assets = manager.asset_history
        assert assets[0] == {'time':TIME_START,
                             'cash':-17,
                             'fees':-6,
                             'stock':-10}
        assert assets[1] == {'time':TIME_END,
                             'cash':-17,
                             'fees':-6,
                             'stock':100}
        stocks = manager.stock_history
        assert stocks[0] == {'time':TIME_START,'tick0':10,'tick1':-1}
        assert stocks[1] == {'time':TIME_END,'tick0':10,'tick1':-1}

class TestHoldings:

    def test_init(self):
        # single string for single tick
        myticks = 'tick'
        hold = Holdings(myticks,TIME0)
        ticks_time = [myticks,'time']
        assert set(hold.adjustments.columns)==set(ticks_time)
        assert len(hold.adjustments)==1
        holds0 = hold.adjustments[[myticks]].iloc[0]
        assert all(h==0 for h in holds0)

    def test_init_list(self):
        # list of ticks
        myticks = ['tick0','tick1']
        hold = Holdings(myticks,TIME0)
        ticks_time = myticks+['time']
        assert set(hold.adjustments.columns)==set(ticks_time)
        assert len(hold.adjustments)==1
        holds0 = hold.adjustments[myticks].iloc[0]
        assert all(h==0 for h in holds0)

    def test_init_holds(self):
        # with a dictionary of initial holdings
        myticks = ['tick0','tick1']
        hold_dict = {'tick0':5,'tick1':5}
        hold = Holdings(myticks,TIME0,holdings_dictionary=hold_dict)
        ticks_time = myticks+['time']
        assert set(hold.adjustments.columns)==set(ticks_time)
        assert len(hold.adjustments)==1
        holds0 = hold.adjustments[myticks].iloc[0]
        assert holds0['tick0']==5
        assert holds0['tick1']==5

    def test_init_miniholds(self):
        # more in holdings_dict than in list of tickers
        myticks=['tick0','tick1','tick2']
        hold_dict = {'tick0':5,'tick1':5}
        hold = Holdings(myticks,TIME0,holdings_dictionary=hold_dict)
        ticks_time = myticks+['time']
        assert set(hold.adjustments.columns)==set(ticks_time)
        assert len(hold.adjustments)==1
        holds0 = hold.adjustments[myticks].iloc[0]
        #print(holds0)
        assert holds0['tick0']==5
        assert holds0['tick1']==5
        assert holds0['tick2']==0

    def test_init_err(self):
        # mor ein hold_dict than in ticker list
        myticks = ['tick0']
        hold_dict = {'tick0':5,'tick1':5}
        with pytest.raises(RuntimeError):
            hold = Holdings(myticks,TIME0,holdings_dictionary=hold_dict)

    def test_add_hold_0init(self):
        myticks = ['tick0','tick1']
        hold = Holdings(myticks,TIME0)
        new_t = TIME0+pd.DateOffset(minutes=1)
        new_holds = {'tick0':3.0,'tick1':5.0}
        hold.add_holdings(new_t,new_holds)
        hold1 = hold.adjustments.iloc[1]
        assert hold1['tick0']==3.0
        assert hold1['tick1']==5.0
        new_holds2 = {'tick2':3.0,'tick1':5.0}
        new_t = TIME0+pd.DateOffset(minutes=2)
        with pytest.raises(ValueError):
            hold.add_holdings(new_t,new_holds2)

    def test_add_hold_nonzeroinit(self):
        myticks=['tick0','tick1','tick2']
        hold_dict = {'tick0':5,'tick1':5}
        hold = Holdings(myticks,TIME0,holdings_dictionary=hold_dict)
        new_t = TIME0+pd.DateOffset(minutes=1)
        new_holds = {'tick0':3,'tick2':5}
        hold.add_holdings(new_t,new_holds)
        hold1 = hold.adjustments.iloc[1]
        assert hold1['tick0']==3
        #assert hold1['tick1']==0.0
        assert hold1['tick2']==5
        hold_sum = hold.adjustments.sum()
        assert hold_sum['tick0']==8
        assert hold_sum['tick1']==5
        assert hold_sum['tick2']==5
        new_holds2 = {'tick3':3,'tick1':5}
        new_t = TIME0+pd.DateOffset(minutes=2)
        with pytest.raises(ValueError):
            hold.add_holdings(new_t,new_holds2)

    def test_add_asset(self):
        myticks = ['tick0','tick1']
        hold = Holdings(myticks,TIME0)
        new_t = TIME0+pd.DateOffset(minutes=1)
        tick='tick1'
        hold.add_asset(new_t,tick,1)
        hold1 = hold.adjustments.iloc[1]
        #print(hold1)
        assert hold1['tick1']==1
        hold_sum = hold.adjustments.sum()
        assert hold_sum['tick0']==0
        assert hold_sum['tick1']==1
        with pytest.raises(ValueError):
            hold.add_asset(new_t,'tick2',1)

    def test_get_holdings_0init(self):
        myticks=['tick0','tick1','tick2']
        hold_dict = {'tick0':5,'tick1':5}
        hold = Holdings(myticks,TIME0,holdings_dictionary=hold_dict)

        new_t = TIME0+pd.DateOffset(minutes=1)
        new_holds = {'tick0':1,'tick2':2}

        hold.add_holdings(new_t,new_holds)

        new_t = new_t+pd.DateOffset(minutes=1)
        new_holds = {'tick1':1,'tick2':-3}

        hold.add_holdings(new_t,new_holds)

        holds_end = hold.get_holdings(new_t+pd.DateOffset(minutes=1))

        assert set(holds_end.keys())==set(myticks)
        assert holds_end['tick0'] == 6
        assert holds_end['tick1'] == 6
        assert holds_end['tick2'] == -1

class TestCashHoldingConstantRate:
    def test_init(self):
        with pytest.raises(TypeError):
            cash = CashHoldingConstantRate(0.01,1.0,0.0)
        with pytest.raises(TypeError):
            cash = CashHoldingConstantRate(0.01,TIME0,np.arange(2))
        with pytest.raises(TypeError):
            cash = CashHoldingConstantRate(1.0+1.0j,TIME0,1.0)

    def test_add_asset(self):
        cash = CashHoldingConstantRate(0.01,TIME0,0.0)
        t=TIME0+pd.DateOffset(minutes=1)
        cash.add_asset(2.0,t)
        cashadj = cash.adjustments.iloc[0]
        assert cashadj['amount'] == 2.0
        cash.add_asset(4.0,t)
        cashadj = cash.adjustments.iloc[1]
        assert cashadj['amount'] == 4.0
        with pytest.raises(TypeError):
            cash.add_asset(2.0,1.0)
        with pytest.raises(ValueError):
            cash.add_asset(1.0,TIME0+pd.DateOffset(minutes=-1))
        with pytest.raises(TypeError):
            cash.add_asset(np.arange(3),TIME0+pd.DateOffset(minutes=5))

    def test_set_adjustments_to_now(self):
        cash = CashHoldingConstantRate(0.0,TIME0,1.0)
        t1=TIME0+pd.DateOffset(minutes=1)
        cash.add_asset(2.0,t1)
        t2=TIME0+pd.DateOffset(minutes=2)
        cash.add_asset(4.0,t2)
        t3=TIME0+pd.DateOffset(minutes=3)
        cash.add_asset(1.0,t3)
        cash.set_adjustments_to_now(t2)
        cash_adj_now = cash.adjustments_to_now
        assert cash_adj_now['amount'].to_list() == [2,4]
        assert cash_adj_now['amount'].sum() == 6

    def test_get_cash_no_new_vals_check(self):
        cash = CashHoldingConstantRate(0.0,TIME0,1.0)
        with pytest.raises(TypeError):
            cash.get_cash_no_new_vals_check(1.0)
        val = cash.get_cash_no_new_vals_check(TIME0+pd.DateOffset(minutes=3))
        assert val == 1.0
        r = 0.1
        cash = CashHoldingConstantRate(r,TIME0,2.0)
        t_check = TIME0+pd.DateOffset(minutes=3)
        val = cash.get_cash_no_new_vals_check(t_check)
        delt=3*60/SECONDS_IN_FULL_YEAR
        assert val == pytest.approx(2.0*np.exp(r*delt))
        t_check = TIME0+pd.DateOffset(days=100)
        val = cash.get_cash_no_new_vals_check(t_check)
        delt=100*24*60*60/SECONDS_IN_FULL_YEAR
        assert val == pytest.approx(2.0*np.exp(r*delt))

        t1=TIME0+pd.DateOffset(minutes=10)
        cash.add_asset(2.0,t1)
        t2=TIME0+pd.DateOffset(days=1)
        cash.add_asset(4.0,t2)
        t3=TIME0+pd.DateOffset(days=3)
        cash.add_asset(1.0,t3)

        with pytest.raises(RuntimeError):
            cash.get_cash_no_new_vals_check(t2)

        cash.set_adjustments_to_now(t2)

        val = cash.get_cash_no_new_vals_check(t2)
        delt0 = 1*24*60*60/SECONDS_IN_FULL_YEAR
        delt1 = (1*24*60*60-10*60)/SECONDS_IN_FULL_YEAR
        true_val = 2.0*np.exp(r*delt0) + 2.0*np.exp(r*delt1) + 4.0
        assert val==pytest.approx(true_val)
        t2_5=TIME0+pd.DateOffset(days=2)
        val = cash.get_cash_no_new_vals_check(t2_5)
        delt0 = 2*24*60*60/SECONDS_IN_FULL_YEAR
        delt1 = (2*24*60*60-10*60)/SECONDS_IN_FULL_YEAR
        delt2 = 1*24*60*60/SECONDS_IN_FULL_YEAR
        true_val = 2.0*np.exp(r*delt0) + 2.0*np.exp(r*delt1) + 4.0*np.exp(r*delt2)
        assert val==pytest.approx(true_val)

    def test_get_cash_value(self):
        r=0.1
        cash = CashHoldingConstantRate(r,TIME0,1.0)
        t1=TIME0+pd.DateOffset(minutes=10)
        cash.add_asset(2.0,t1)
        t2=TIME0+pd.DateOffset(days=1)
        cash.add_asset(4.0,t2)
        t3=TIME0+pd.DateOffset(days=3)
        cash.add_asset(-1.0,t3)

        t_check = TIME0+pd.DateOffset(minutes=5)
        delt0 = 5*60/SECONDS_IN_FULL_YEAR
        val = cash.get_cash_value(t_check)
        true_val = 1.0*np.exp(r*delt0)
        assert val==pytest.approx(true_val)

        t_check = TIME0+pd.DateOffset(days=2)
        delt0 = 2*24*60*60/SECONDS_IN_FULL_YEAR
        delt1 = (2*24*60*60 - 10*60)/SECONDS_IN_FULL_YEAR
        delt2 = (1*24*60*60)/SECONDS_IN_FULL_YEAR
        val = cash.get_cash_value(t_check)
        true_val = 1.0*np.exp(r*delt0) + 2.0*np.exp(r*delt1) + 4.0*np.exp(r*delt2)
        assert val==pytest.approx(true_val)

        t_check = TIME0+pd.DateOffset(days=50)
        delt0 = 50*24*60*60/SECONDS_IN_FULL_YEAR
        delt1 = (50*24*60*60 - 10*60)/SECONDS_IN_FULL_YEAR
        delt2 = (49*24*60*60)/SECONDS_IN_FULL_YEAR
        delt3 = (47*24*60*60)/SECONDS_IN_FULL_YEAR
        val = cash.get_cash_value(t_check)
        true_val = 1.0*np.exp(r*delt0) + 2.0*np.exp(r*delt1) + \
                   4.0*np.exp(r*delt2) - 1.0*np.exp(r*delt3)
        assert val==pytest.approx(true_val)
