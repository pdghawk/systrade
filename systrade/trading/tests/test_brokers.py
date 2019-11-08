import pytest

import numpy as np
import pandas as pd

from systrade.trading.brokers import PaperBroker

T_START = pd.to_datetime('2019/07/10-09:30:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
T_END   = pd.to_datetime('2019/07/10-10:00:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')

TIMEINDEX = pd.date_range(start=T_START,end=T_END,freq='1min')

DATA_DF   = pd.DataFrame(data={'tick0':np.arange(len(TIMEINDEX)) ,
                               'tick1':np.arange(len(TIMEINDEX)-1,-1,-1)},
                               index=TIMEINDEX)

# DATA_DF   = pd.DataFrame(data={'tick0':np.arange(len(TIMEINDEX))},
#                               index=TIMEINDEX)

class TestPaperBroker:
    def test_init(self):
        testseries = pd.Series(np.arange(10))
        with pytest.raises(TypeError):
            broker = PaperBroker(testseries)
        with pytest.raises(TypeError):
            broker = PaperBroker(DATA_DF,slippage_time=1.0)
        with pytest.raises(TypeError):
            broker = PaperBroker(DATA_DF,transaction_cost=lambda x: x**2)
        with pytest.raises(ValueError):
            broker = PaperBroker(DATA_DF,transaction_cost=-0.5)
        with pytest.raises(TypeError):
            broker = PaperBroker(DATA_DF,spread_pct=lambda x: x**2)
        with pytest.raises(ValueError):
            broker = PaperBroker(DATA_DF,spread_pct=-0.5)
        with pytest.raises(ValueError):
            broker = PaperBroker(DATA_DF,spread_pct=200)

    def test_next_extant_time(self):
        broker = PaperBroker(DATA_DF)
        t_get = pd.to_datetime('2019/07/10-09:35:05:000000', format='%Y/%m/%d-%H:%M:%S:%f')
        t_out = broker.next_extant_time(t_get)
        t_expect = pd.to_datetime('2019/07/10-09:36:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
        assert t_out==t_expect
        t_get = pd.to_datetime('2019/07/10-11:35:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
        with pytest.raises(ValueError):
            t_out = broker.next_extant_time(t_get)

    def test_get_timeindex_subset(self):
        broker = PaperBroker(DATA_DF)
        t0 = pd.to_datetime('2019/07/10-09:29:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
        t1 = pd.to_datetime('2019/07/10-09:36:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
        with pytest.raises(ValueError):
            tind = broker.get_timeindex_subset(t0,t1)
        t0 = pd.to_datetime('2019/07/10-09:34:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
        t1 = pd.to_datetime('2019/07/10-11:36:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
        with pytest.raises(ValueError):
            tind = broker.get_timeindex_subset(t0,t1)
        with pytest.raises(TypeError):
            tind = broker.get_timeindex_subset(0,t1)
        with pytest.raises(TypeError):
            tind = broker.get_timeindex_subset(t0,1)
        t1 = pd.to_datetime('2019/07/10-09:36:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
        tind = broker.get_timeindex_subset(t0,t1)
        print(tind)
        print(pd.date_range(t0,t1,freq='1min'))
        assert np.array_equal(tind.values,pd.date_range(t0,t1,freq='1min').values)

    def test_get_firstlast_times(self):
        broker = PaperBroker(DATA_DF)
        t0,t1 = broker.get_firstlast_times()
        assert t0==T_START
        assert t1==T_END

    def test_get_tick_list(self):
        broker = PaperBroker(DATA_DF)
        ticks = broker.get_tick_list()
        assert ticks == ['tick0','tick1']

    def test_get_price_list(self):
        broker = PaperBroker(DATA_DF)
        t0 = T_START
        t1 = T_START + pd.DateOffset(minutes=5)
        with pytest.raises(ValueError):
            prices = broker.get_price_list('badtick',t0,t1)
        with pytest.raises(ValueError):
            prices = broker.get_price_list(['badtick'],t0,t1)
        prices = broker.get_price_list('tick0',t0,t1)
        assert np.array_equal(prices['tick0'].values , np.arange(6) )

        prices = broker.get_price_list(['tick0','tick1'],t0,t1)
        assert np.array_equal(prices['tick0'].values , np.arange(6) )
        assert np.array_equal(prices['tick1'].values ,
                              np.arange(len(TIMEINDEX)-1,len(TIMEINDEX)-7,-1) )

    def test_get_unslipped_price(self):
        broker = PaperBroker(DATA_DF)
        t_get = T_START+pd.DateOffset(minutes=5)
        with pytest.raises(ValueError):
            pp = broker.get_unslipped_price('badtick',t_get)
        price = broker.get_unslipped_price('tick0',t_get)
        assert price == 5

    def test_get_price(self):
        broker = PaperBroker(DATA_DF,
                             slippage_time=pd.DateOffset(seconds=30),
                             transaction_cost = 2.0)
        t_get = T_START+pd.DateOffset(minutes=5)
        with pytest.raises(ValueError):
            p,f,t = broker.get_price('badtick',t_get)
        price,fee,time = broker.get_price('tick0',t_get)
        assert time == t_get+pd.DateOffset(minutes=1)
        assert fee == 2.0
        assert price==6

    def test_get_buy_price(self):
        broker = PaperBroker(DATA_DF,
                             slippage_time=pd.DateOffset(seconds=30),
                             transaction_cost = 2.0,
                             spread_pct = 4)
        t_get = T_START+pd.DateOffset(minutes=5)
        price,fee,time = broker.get_buy_price('tick0',t_get)
        assert time == t_get+pd.DateOffset(minutes=1)
        assert fee == 2.0
        assert price==pytest.approx(6*(1.0+4.0/200.0))

    def test_get_sell_price(self):
        broker = PaperBroker(DATA_DF,
                             slippage_time=pd.DateOffset(seconds=30),
                             transaction_cost = 2.0,
                             spread_pct = 4)
        t_get = T_START+pd.DateOffset(minutes=5)
        price,fee,time = broker.get_sell_price('tick0',t_get)
        assert time == t_get+pd.DateOffset(minutes=1)
        assert fee == 2.0
        assert price==pytest.approx(6*(1.0-4.0/200.0))
