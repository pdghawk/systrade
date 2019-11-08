""" The signals module provides classes to build buy/sell signals

Notes
------
All strategies should inherit from BaseSignal, and provide a request_historical
method. For details of this method see docstring of base/BaseSignal or the
request_historical method in ZeroCrossBuyUpSellDown in this module.
"""
#from abc import ABC,abstractmethod
import copy
import numpy as np
import pandas as pd

from .base import BaseSignal



class ZeroCrossBuyUpSellDown(BaseSignal):
    """ Signal that checks for indicator crossing zero

    This signal goves a buy signal for positive gradient crossing, and sell for
    a negative gradient crossing
    """
    def __init__(self,indicator,filter,extra_param=0.0):
        """ Signal initialised with an indicator and a filter, and other params
        Args:
            - indicator: a models.indicator object to collect indicator for
                         signal to base its decisions on
            - filter: a models.filter object for ticker selection
            - extra_param: an extra parameter of this signal
        """
        self.extra_param=extra_param
        super().__init__(indicator,filter)


    def request_historical(self,stocks_df,signal_name='signal'):
        """ use historical data to get a dictionary of signals

        Args:
            - stocks_df: pandas dataframe of tickers over time
            - signal_name: a name to give this signal as output column

        Returns:
            - signal_dict: a dictionary with keys being the tickers that the
                           signal considers (selected by this signal's filter),
                           and values being dataframes, indexed by times at which
                           signals are seen, and a column named by argument
                           'signal_name', with +/-1 for a buy/sell signal.
        """
        if not isinstance(signal_name,str):
            raise TypeError("singal_name must be a string")
        if not isinstance(stocks_df,pd.DataFrame):
            raise TypeError("singal_name must be a string")
        if self.filter is not None:
            stock_df = self.filter.apply_in(stocks_df) # new df, not overwritten
        else:
            stock_df = stocks_df

        indi = self.indicator.get_indicator(stock_df)
        signal_dict = dict()
        in_to_out_dict = self.filter.output_map()
        # loop over tickers
        for c in stock_df.columns.to_list():
            indi_comp_0 = indi[c].values*indi[c].shift().values # <zero at cross
            indi_comp_0[0] = 1.0 # instead of NaN - make >0 - supresses warnings
            indi_comp_g = np.sign(indi[c].values-indi[c].shift().values) #grad - up or down
            cross_inds  = np.where(indi_comp_0<0.0) # indices of crossing
            # for this ticker, dataframe of all crossing times, and whether indicator
            # was growing or falling
            mydf = pd.DataFrame(index=stock_df.iloc[cross_inds].index,
                                data={signal_name:indi_comp_g[cross_inds]})
            # append dataframe into dict of signals
            for tick_out in in_to_out_dict[c]:
                signal_dict[tick_out] = mydf
        return signal_dict
