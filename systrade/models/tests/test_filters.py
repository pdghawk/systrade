import pytest

import pandas as pd
import numpy as np

from systrade.models.filters import TickerOneToManyFilter
from systrade.models.filters import TickerOneToAnotherFilter

DF = pd.DataFrame(data={'tick0':np.arange(5),'tick1':np.arange(4,-1,-1)})

class TestTickerOneToManyFilter:

    def test_init(self):
        with pytest.raises(TypeError):
            f = TickerOneToManyFilter('t','t')
        with pytest.raises(TypeError):
            f = TickerOneToManyFilter(['t'],['t'])

    def test_apply_in(self):
        f = TickerOneToManyFilter('tick0',['tick0','tick1'])
        input = f.apply_in(DF)
        assert np.array_equal(input, np.arange(5))

    def test_output_map(self):
        f = TickerOneToManyFilter('tick0',['tick0','tick1'])
        out_map = f.output_map()
        assert out_map['tick0'] == ['tick0','tick1']
        assert len(out_map)==1

class TestTickerOneToAnotherFilter:

    def test_init(self):
        with pytest.raises(ValueError):
            f = TickerOneToAnotherFilter(['t','t2'],['t1'])

    def test_apply_in(self):
        f = TickerOneToAnotherFilter(['tick0','tick1'],['tick0','tick1'])
        input=f.apply_in(DF)
        assert np.array_equal(input,np.concatenate((np.expand_dims(np.arange(5),1),np.expand_dims(np.arange(4,-1,-1),1)),axis=1))

    def test_output_map(self):
        f = TickerOneToAnotherFilter(['tick0','tick1'],['tick1','tick0'])
        out_map = f.output_map()
        assert out_map['tick0'] == ['tick1']
        assert out_map['tick1'] == ['tick0']
