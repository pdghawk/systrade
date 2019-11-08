import pytest

import pandas as pd
import numpy as np

from systrade.models import indicators as sysinds

DF = pd.DataFrame(data={'tick0':np.arange(5),'tick1':np.arange(4,-1,-1)})

class TestMACrossOver:

    def test_init(self):
        with pytest.raises(TypeError):
            indi = sysinds.MACrossOver(1,1,1)
        with pytest.raises(TypeError):
            indi = sysinds.MACrossOver(1,'','')
        with pytest.raises(TypeError):
            indi = sysinds.MACrossOver('',1,'')

    def test_get_indicator(self):
        indi = sysinds.MACrossOver(10,10)
        # period longer than data
        with pytest.raises(ValueError):
            indi.get_indicator(DF)
        indi = sysinds.MACrossOver(2,10)
        with pytest.raises(ValueError):
            indi.get_indicator(DF)
        indi = sysinds.MACrossOver(10,2)
        with pytest.raises(ValueError):
            indi.get_indicator(DF)
        indi = sysinds.MACrossOver(5,2)
        with pytest.raises(ValueError):
            indi.get_indicator(DF)
        indi = sysinds.MACrossOver(1,2)
        vals = indi.get_indicator(DF)
        true_vals = np.ones((5,2))*0.5
        true_vals[:,1]*=-1
        # print(vals)
        assert np.array_equal(vals,true_vals)
