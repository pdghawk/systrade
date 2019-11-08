import pytest

import numpy as np
import pandas as pd

import systrade.models.signals as syssigs
import systrade.models.indicators as sysinds
import systrade.models.filters as sysfilts

T_START = pd.to_datetime('2019/07/10-09:30:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')
T_END   = pd.to_datetime('2019/07/10-09:39:00:000000', format='%Y/%m/%d-%H:%M:%S:%f')

TIMEINDEX = pd.date_range(start=T_START,end=T_END,freq='1min')

DATA_DF   = pd.DataFrame(data={'tick0':[0,1,2,3,4,5,4,3,2,1] ,
                               'tick1':[0,2,4,1,1,5,4,3,2,1]},
                               index=TIMEINDEX)

class TestZeroCrossBuyUpSellDown:

    def test_request_historical(self):
        indi = sysinds.MACrossOver(3,5)
        filt = sysfilts.TickerOneToAnotherFilter(['tick0','tick1'],
                                                 ['tick0','tick1'])
        sig = syssigs.ZeroCrossBuyUpSellDown(indi,filt)
        with pytest.raises(TypeError):
            reqs = sig.request_historical(DATA_DF, 1)
        with pytest.raises(TypeError):
            reqs = sig.request_historical(np.arange(5), 'b')
        reqs = sig.request_historical(DATA_DF, 'sig')
        assert len(reqs['tick0'])==1
        assert reqs['tick0'].index == T_END
        assert reqs['tick0'].values == -1
        expected = pd.DataFrame(data={'sig':[-1.0,1.0]},
                                index=pd.DatetimeIndex(
                                [T_START+pd.DateOffset(minutes=6),
                                 T_START+pd.DateOffset(minutes=7)]))
        assert reqs['tick1'].equals(expected)
