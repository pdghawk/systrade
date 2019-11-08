""" Module for indicators on stocks

Notes
-------

All indicator classes should inherit from base/BaseIndicator, and provide a
get_indicator method. For details of this method see docstring of
base/BaseIndicator or the get_indicator method in MACrossOver in this module.
"""

#from abc import ABC,abstractmethod
import numpy as np
import pandas as pd
import copy
import warnings
from pandas.tseries.offsets import DateOffset

from .base import BaseIndicator

class MACrossOver(BaseIndicator):
    """ Indicator for moving average crossover"""
    def __init__(self,period1,period2,win_type=None):
        """
        Args:
            - period1: number of previous points to average over
            - period2: number of previous points to average over
            - win_type: type of window, see https://docs.scipy.org/doc/scipy/reference/signal.windows.html#module-scipy.signal.windows
        """
        if isinstance(period1, (float, int)):
            self.period1 = int(period1)
        else:
            raise TypeError("MACrossOver: periods should be a number")
        if isinstance(period2, (float, int)):
            self.period2 = int(period2)
        else:
            raise TypeError("MACrossOver: periods should be a number")
        if isinstance(win_type,(str)) or win_type is None:
            self.win_type = win_type
        else:
            raise TypeError("MACrossover win_type should be a string")

    def get_indicator(self,stock_df):
        """ apply moving average indicator to stock(s)

        indicator is applied to each ticker individually. A moving average of
        period1 is subratracted from a moving average of period2.

        The first p points of each column in stock_df data are set to
        stock_df[col].iloc[p], where p is max(period1, period2)

        Args:
            - stock_df: dataframe of stock(s), indexed by time

        Returns:
            - indi: indicator over timeframe of stock_df
        """
        max_p = max(self.period1,self.period2)
        if max_p>=len(stock_df.index):
            raise ValueError("MACrossOver period(s) are longer than the data")
        indi = stock_df.rolling(self.period1,self.win_type).mean().shift() \
              - stock_df.rolling(self.period2,self.win_type).mean().shift()
        # get the values at the time longest period first met
        tmp_val = indi.iloc[max_p].values
        #print(tmp_val)
        tmp_vals = np.tile(tmp_val,(max_p,1))
        # repeat the values at time max_p for all times up to then (prevents a fake crossover)
        indi.iloc[0:max_p] = tmp_vals
        return indi

# -------------------- useful functions  ---------------------------------------

def moving_average(x,period):
    """ get the moving average of x, with period p
    Args:
        - x: numpy array to calculate moving average of (over axis 0)
        - p: period to use for moving average (units: number of elements)
    Returns:
        -ma: moving average of x with period p, of shape(x)
    """
    if len(np.shape(x))==1:
        np.expand_dims(x,axis=1)
    cs=np.cumsum(x,axis=0)
    ma=np.zeros_like(cs)
    ma[period+1:] = (cs[period:-1]-cs[1:-period])/float(period)
    ma[:period] = ma[period+1]
    return ma
