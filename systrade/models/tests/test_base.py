import pytest

import numpy as np
import pandas as pd

from systrade.models.base import BaseParameterizedObject
from systrade.models.base import BaseIndicator
from systrade.models.base import BaseSignal
from systrade.models.base import BaseStrategy

from systrade.models.filters import TickerOneToAnotherFilter

#--------------------- useful classes for testing ------------------------------
class Tmp(BaseParameterizedObject):
    def __init__(self,a,b):
        self.a = a
        self.b = b


class Child(Tmp):
    def __init__(self,a,b,c):
        self.c = c
        super().__init__(a,b)


class BadArgs(BaseParameterizedObject):
    def __init__(self,*args):
        self.z = args[0]


class BadNames(BaseParameterizedObject):
    def __init__(self,z):
        self.a = z


class FakeIndicator(BaseIndicator):
    def __init__(self,a):
        self.a=a
        super().__init__()

    def get_indicator(self,stock_df):
        return None

    def __eq__(self,other):
        return self.a == other.a


class FakeSignal(BaseSignal):
    def __init__(self,indicator,filter=None,a=0):
        self.a=a
        super().__init__(indicator,filter)

    def request_historical(self,stocks_df,signal_name):
        return None

T_START = pd.to_datetime('2019/07/10-09:30:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
T_END   = pd.to_datetime('2019/07/10-10:00:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')

# TIMEINDEX = pd.date_range(start=T_START,end=T_END,freq='1min')
#
# DATA_DF   = pd.DataFrame(data={'tick0':np.arange(len(TIMEINDEX)) ,
#                                'tick1':np.arange(len(TIMEINDEX)-1,-1,-1)},
#                                index=TIMEINDEX)
class FakeStrategy(BaseStrategy):
    def __init__(self,signal_dict,ticker_list,a=0):
        self.a=a
        super().__init__(signal_dict,ticker_list)

    def get_order_list(self,stocks_df,signal_name):
        # t1 = T_START+pd.DateOffset(minutes=4)
        # t2 = T_START+pd.DateOffset(minutes=8)
        # t3 = T_START+pd.DateOffset(minutes=11)
        # o1 = orders.BuyMarketOrder(t1,'tick0',1)
        # o2 = orders.BuyMarketOrder(t2,'tick1',2)
        # o3 = orders.SellMarketOrder(t3,'tick0',3)
        # return [o1,o2,o3]
        return None

#--------------------- testing classes begin -----------------------------------

class TestBaseParameterizedObject:

    def test__get_param_names(self):

        tmp = Tmp(1,2)
        names = tmp._get_param_names()
        assert names == ['a','b']

        ch = Child(1,2,3)
        names = ch._get_param_names()
        assert names==['a','b','c']

        with pytest.raises(RuntimeError):
            mybad = BadArgs(1)
            nn=mybad._get_param_names()

    def test_get_params(self):

        tmp = Tmp(1,2)
        ps  = tmp.get_params()
        assert ps == {'a':1,'b':2}

        ch  = Child(1,2,3)
        ps  = ch.get_params()
        assert ps == {'a':1,'b':2,'c':3}

        nested_ch = Child(1,2,tmp)
        ps = nested_ch.get_params()
        assert ps == {'a':1,'b':2,'c__a':1,'c__b':2,'c':tmp}

        nested_ch = Child(1,ch,tmp)
        ps = nested_ch.get_params()
        assert ps == {'a':1,'b':ch,'b__a':1,'b__b':2,'b__c':3,'c__a':1,'c__b':2,'c':tmp}

        bk = BadNames(1)
        with pytest.raises(RuntimeError):
            ps=bk.get_params()

        # check deep=False keyword option
        ps= nested_ch.get_params(deep=False)
        assert ps == {'a':1,'b':ch,'c':tmp}

    def test_set_params(self):
        tmp = Tmp(1,2)
        tmp.set_params(a=3)
        assert tmp.a == 3
        assert tmp.b == 2
        tmp.set_params(a=5,b=6)
        assert tmp.a==5
        assert tmp.b==6
        nested_ch = Child(1,2,tmp)
        tmp2 = Tmp(3,4)
        nested_ch.set_params(c=tmp2)
        assert nested_ch.c.a==3
        assert nested_ch.c.b==4
        nested_ch.set_params(c__a=5)
        assert nested_ch.c.a==5


class TestBaseSignal:

    def test_init(self):
        indi = FakeIndicator(1)
        sig = FakeSignal(indi)
        assert sig.indicator.a==1
        assert sig.filter is None

        filter = TickerOneToAnotherFilter(['t0'],['t1'])
        sig = FakeSignal(indi, filter)
        assert sig.indicator.a==1
        assert sig.filter.tick_list_in  == ['t0']
        assert sig.filter.tick_list_out == ['t1']


    def test__get_params(self):
        indi = FakeIndicator(1)
        sig = FakeSignal(indi)
        ps = sig._get_params()
        assert ps == {'a':0,'indicator__a':1,'indicator':indi}

        filter = TickerOneToAnotherFilter(['t0'],['t1'])
        sig = FakeSignal(indi,filter=filter)
        ps = sig._get_params()
        assert ps == {'a':0,'indicator__a':1,'indicator':indi}

        ps = sig._get_params(deep=False)
        assert ps == {'a':0,'indicator':indi}


class TestBaseStrategy:

    def test_init(self):
        with pytest.raises(TypeError):
            strat = FakeStrategy(1,['tick0'])

        indi = FakeIndicator(1)
        sig = FakeSignal(indi)

        with pytest.raises(TypeError):
            strat = FakeStrategy({'thesig':sig},1)

        with pytest.raises(TypeError):
            strat = FakeStrategy({'thesig':1},'tick0')

    def test_get_params(self):
        indi = FakeIndicator(1)
        sig = FakeSignal(indi)
        assert issubclass(type(sig),BaseSignal)
        strat = FakeStrategy({'thesig':sig},['tick0','tick1'])
        ps = strat.get_params()
        assert ps=={'a':0,'thesig__a':0, 'thesig__indicator':indi,'thesig__indicator__a':1}
        ps = strat.get_params(deep=False)
        assert ps=={'a':0}

    def test_set_params(self):
        indi = FakeIndicator(1)
        sig = FakeSignal(indi)
        strat = FakeStrategy({'thesig':sig},['tick0','tick1'])
        strat.set_params(a=5)
        ps = strat.get_params()
        assert ps=={'a':5,'thesig__a':0, 'thesig__indicator':indi,'thesig__indicator__a':1}
        strat.set_params(thesig__a=2)
        ps = strat.get_params()
        assert ps=={'a':5,'thesig__a':2, 'thesig__indicator':indi,'thesig__indicator__a':1}
        strat.set_params(thesig__indicator__a=2)
        ps = strat.get_params()
        print("indi a  = ",strat.signal_dict['thesig'].indicator.a)
        print(ps)
        indi_effective = FakeIndicator(2)
        assert ps=={'a':5,'thesig__a':2, 'thesig__indicator':indi_effective,'thesig__indicator__a':2}
        indi2=FakeIndicator(3)
        strat.set_params(thesig__indicator=indi2)
        ps = strat.get_params()
        assert ps=={'a':5,'thesig__a':2, 'thesig__indicator':indi2,'thesig__indicator__a':3}
