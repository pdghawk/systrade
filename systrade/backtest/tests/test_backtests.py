import pytest

import numpy as np
import pandas as pd

from systrade.backtest.backtests import ParamGrid
from systrade.backtest.backtests import SingleStrategyBackTest
from systrade.backtest.backtests import MultiStrategyBackTest
from systrade.backtest.backtests import ParameterScanBackTest

# from systrade.models.strategies import SimpleStrategy
# from systrade.models.signals import ZeroCrossBuyUpSellDown
# from systrade.models.indicators import MACrossOver
#
# from systrade.trading import brokers

from systrade.models.base import BaseStrategy,BaseSignal

import copy

# ------------------------------------------------------------------------------
# stub classes

#check_strat = SimpleStrategy({'sig':ZeroCrossBuyUpSellDown(MACrossOver(1,2),None)},'tick0')

TIME_START = pd.to_datetime('2019/07/10-09:30:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
TIME_END   = pd.to_datetime('2019/07/10-09:40:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
TIMEINDEX = pd.date_range(start=TIME_START,end=TIME_END,freq='1min')
DATA_DF   = pd.DataFrame(data={'tick0':np.arange(len(TIMEINDEX))},index=TIMEINDEX)

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

FAKE_BROKER   = FakeBroker(DATA_DF)
#
class SimpleStrategy(BaseStrategy):
    def __init__(self,signal_dict,ticker_list,resampling=5):
        self.resampling = resampling
        super().__init__(signal_dict,ticker_list)

    def get_order_list(self,stocks_df):
        return []

class SimpleSignal(BaseSignal):
    def request_historical(self):
        pass

SIMPLE_STRATEGY = SimpleStrategy({'sig':SimpleSignal(1)},['tick0'])

FAKE_PORTFOLIO_DF = pd.DataFrame(data={'stock':[10,11,12,13],
                                       'cash':[4,3,2,5],
                                       'fees':[-1,-2,-3,-4]})

class FakeAccount:
    def __init__(self):
        self.total_trades = 0
        self.portfolio_df = FAKE_PORTFOLIO_DF

    def get_portfolio_df(self):
        return self.portfolio_df

class FakeAccountFactory:
    def make_account(self, broker, t0, t1):
        return FakeAccount()

FAKE_ACCOUNT_FACTORY = FakeAccountFactory()

class FakeStrategy:
    def run_historical(self,account):
        pass

    def clone(self):
        return copy.deepcopy(self)

FAKE_STRATEGY = FakeStrategy()
# ------------------------------------------------------------------------------
# testing

class TestParamGrid:

    def test_init(self):
        with pytest.raises(TypeError):
            grid = ParamGrid(1)

    def test_check_and_create(self):
        params = {'a':2,'b':[1,1]}
        with pytest.raises(TypeError):
            grid = ParamGrid.check_and_create(params,SIMPLE_STRATEGY)
        params = {'a':[2],'b':[1,2]}
        with pytest.raises(ValueError):
            grid = ParamGrid.check_and_create(params,SIMPLE_STRATEGY)
        params = {'resampling':[3,5],'sig__indicator':[1,2]}
        grid = ParamGrid.check_and_create(params,SIMPLE_STRATEGY)
        grid_as_list = list(grid)
        assert grid_as_list == [{'resampling':3,'sig__indicator':1},
                                {'resampling':3,'sig__indicator':2},
                                {'resampling':5,'sig__indicator':1},
                                {'resampling':5,'sig__indicator':2}]

class TestSingleStrategyBacktest:

    def test_make_times_valid(self):
        bt = SingleStrategyBackTest(FAKE_BROKER,FAKE_ACCOUNT_FACTORY,FAKE_STRATEGY)
        with pytest.raises(ValueError):
            t0,t1 = bt._make_times_valid(TIME_START+pd.DateOffset(minutes=-1),TIME_END)
        with pytest.raises(ValueError):
            t0,t1 = bt._make_times_valid(TIME_START,TIME_END+pd.DateOffset(minutes=1))
        t0,t1 = bt._make_times_valid(TIME_START+pd.DateOffset(minutes=2),TIME_END+pd.DateOffset(minutes=-1))
        assert t0==TIME_START+pd.DateOffset(minutes=2)
        assert t1==TIME_END+pd.DateOffset(minutes=-1)
        t0,t1 = bt._make_times_valid(None,TIME_END+pd.DateOffset(minutes=-1))
        assert t0==TIME_START
        assert t1==TIME_END+pd.DateOffset(minutes=-1)
        t0,t1 = bt._make_times_valid(TIME_START+pd.DateOffset(minutes=2),None)
        assert t0==TIME_START+pd.DateOffset(minutes=2)
        assert t1==TIME_END
        t0,t1 = bt._make_times_valid(None,None)
        assert t0==TIME_START
        assert t1==TIME_END

    def test__create_account(self):
        bt = SingleStrategyBackTest(FAKE_BROKER,FAKE_ACCOUNT_FACTORY,FAKE_STRATEGY)
        bt._create_account(TIME_START,TIME_END)

    def test__run_strategy(self):
        bt = SingleStrategyBackTest(FAKE_BROKER,FAKE_ACCOUNT_FACTORY,FAKE_STRATEGY)
        bt._run_strategy(TIME_START,TIME_END)

    def test_portfolio_to_returns(self):
        bt = SingleStrategyBackTest(FAKE_BROKER,FAKE_ACCOUNT_FACTORY,FAKE_STRATEGY)
        rets = bt.portfolio_to_returns(FAKE_PORTFOLIO_DF)
        assert np.array_equal(rets,np.array([-1,-1,3]))
