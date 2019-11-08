import pytest

import numpy as np
import pandas as pd

from systrade.trading import orders

import systrade.models.signals as syssigs
import systrade.models.indicators as sysinds
import systrade.models.filters as sysfilts
import systrade.models.strategies as sysstrats

T_START = pd.to_datetime('2019/07/10-09:30:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
T_END   = pd.to_datetime('2019/07/10-09:39:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')

T_36 = pd.to_datetime('2019/07/10-09:36:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
T_38 = pd.to_datetime('2019/07/10-09:38:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
T_40 = pd.to_datetime('2019/07/10-09:40:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')


TIMEINDEX = pd.date_range(start=T_START,end=T_END,freq='1min')

DATA_DF   = pd.DataFrame(data={'tick0':[0,1,2,3,4,5,4,3,2,1] ,
                               'tick1':[0,2,4,1,1,5,4,3,2,1]},
                               index=TIMEINDEX)

class TestSimpleStrategy:
    def test_get_order_list(self):
        indi = sysinds.MACrossOver(3,5)
        filt = sysfilts.TickerOneToAnotherFilter(['tick0','tick1'],
                                                 ['tick0','tick1'])
        sig0 = syssigs.ZeroCrossBuyUpSellDown(indi,filt)
        # switch filter order to create a new signal with
        filt = sysfilts.TickerOneToAnotherFilter(['tick0','tick1'],
                                                 ['tick1','tick0'])
        sig1 = syssigs.ZeroCrossBuyUpSellDown(indi,filt)

        strat = sysstrats.SimpleStrategy({'sig0':sig0, 'sig1':sig1},
                                         ['tick0','tick1'],
                                         2)
        order_list = strat.get_order_list(DATA_DF)

        expected = [orders.SellMarketOrder(T_36,'tick0',1),
                    orders.BuyMarketOrder(T_38,'tick0',1),
                    orders.SellMarketOrder(T_40,'tick0',1),
                    orders.SellMarketOrder(T_36,'tick1',1),
                    orders.BuyMarketOrder(T_38,'tick1',1),
                    orders.SellMarketOrder(T_40,'tick1',1)]
        #print(order_list)
        assert len(order_list)==len(expected)
        assert [o.time_placed for o in order_list]==[o.time_placed for o in expected]
        assert [o.ticker for o in order_list]==[o.ticker for o in expected]

        # with a different resampling period
        strat = sysstrats.SimpleStrategy({'sig0':sig0, 'sig1':sig1},
                                         ['tick0','tick1'],
                                         3)
        order_list = strat.get_order_list(DATA_DF)

        expected = [orders.SellMarketOrder(T_36,'tick0',1),
                    orders.SellMarketOrder(T_36,'tick1',1)]
        #print(order_list)
        assert len(order_list)==len(expected)
        assert [o.time_placed for o in order_list]==[o.time_placed for o in expected]
        assert [o.ticker for o in order_list]==[o.ticker for o in expected]
