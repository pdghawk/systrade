import pytest

import numpy as np
import pandas as pd

from systrade.models.base import BaseIndicator
from systrade.models.base import BaseSignal
from systrade.models.base import BaseStrategy

from systrade.trading.accounts import BasicAccount
from systrade.trading.brokers import PaperBroker
from systrade.trading import orders

# ---------------------- useful setup ------------------------------------------

T_START = pd.to_datetime('2019/07/10-09:30:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
T_END   = pd.to_datetime('2019/07/10-10:00:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')

TIMEINDEX = pd.date_range(start=T_START,end=T_END,freq='1min')

DATA_DF   = pd.DataFrame(data={'tick0':np.arange(len(TIMEINDEX)) ,
                               'tick1':np.arange(len(TIMEINDEX)-1,-1,-1)},
                               index=TIMEINDEX)
T1 = T_START+pd.DateOffset(minutes=4)
T2 = T_START+pd.DateOffset(minutes=8)
T3 = T_START+pd.DateOffset(minutes=11)

BROKER = PaperBroker(DATA_DF)

class FakeIndicator(BaseIndicator):
    def __init__(self,a):
        self.a=a
        super().__init__()

    def get_indicator(self,stock_df):
        return None

    def __eq__(self,other):
        return self.a == other.a

class FakeSignal(BaseSignal):
    def __init__(self,indicator,filter=None):
        super().__init__(indicator,filter)

    def request_historical(self,stocks_df,signal_name):
        out_dict = dict()
        if signal_name=='s1':
            out_dict['tick0'] = pd.DataFrame(index=[T1,T3],
                                             data={signal_name:[1,-1]})
            out_dict['tick1'] = pd.DataFrame(index=[T2],
                                             data={signal_name:[1]})
        else:
            out_dict['tick0'] = pd.DataFrame(index=[T2],
                                             data={signal_name:[-1]})
        return out_dict
# o1 = orders.BuyMarketOrder(T1,'tick0',1)
# o2 = orders.BuyMarketOrder(T2,'tick1',2)
# o3 = orders.SellMarketOrder(T3,'tick0',3)
# return [o1,o2,o3]

class FakeStrategy(BaseStrategy):
    def __init__(self,signal_dict,ticker_list,a=0):
        self.a=a
        super().__init__(signal_dict,ticker_list)

    def get_order_list(self,stocks_df):
        o1 = orders.BuyMarketOrder(T1,'tick0',1)
        o2 = orders.BuyMarketOrder(T2,'tick1',2)
        o3 = orders.SellMarketOrder(T3,'tick0',3)
        return [o1,o2,o3]

# ----------------------- testing ----------------------------------------------

# to check strategy signal_requests() and run_historical()

class TestBaseStrategy:

    def test_signal_requests(self):
        indi = FakeIndicator(1)
        sig1 = FakeSignal(indi)
        sig2 = FakeSignal(indi)
        strat = FakeStrategy({'s1':sig1,'s2':sig2},['tick0','tick1'])
        sig_reqs_dict = strat.signal_requests(DATA_DF)
        assert len(sig_reqs_dict['tick0'])==2
        assert sig_reqs_dict['tick0'][0].loc[T1]['s1']==1
        assert sig_reqs_dict['tick0'][1].loc[T2]['s2']==-1
        with pytest.raises(KeyError):
            sig_reqs_dict['tick0'][1].loc[T2]['s1']
        with pytest.raises(KeyError):
            sig_reqs_dict['tick0'][1].loc[T1]['s2']
        assert len(sig_reqs_dict['tick1'])==1
        assert sig_reqs_dict['tick1'][0].loc[T2]['s1']==1

    def test_run_historical(self):
        indi = FakeIndicator(1)
        sig1 = FakeSignal(indi)
        strat = FakeStrategy({'s1':sig1},['tick0','tick1'])
        acc = BasicAccount(BROKER,T_START,T_END)
        strat.run_historical(acc)
        assert len(acc.times)==len(acc.t_vals)
        assert all(acc.times==acc.t_vals)
    
