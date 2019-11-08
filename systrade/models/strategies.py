""" The strategies module provides utilities for designing trading strategies

Notes
------
All strategies should inherit from BaseStrategy, and provide a get_order_list
method. For details of the requirements of this method, see its docstring in
base/BaseStrategy, or in the method within SimpleStrategy in this module.
"""
import copy
import pandas as pd
import numpy as np
import time as timer
import matplotlib.pyplot as plt

from .base import BaseStrategy

# TODO: extend strategy types
 # examples - how the signals are combined - could be done in many ways
 # should check whether indivdual positions should be exited (been held at a loss too long)
 # eg buy and simultaneously do a sell_limit for same_quantity or something
 # portfolio re-optimization movements (modern portfolio theory) n.b maximise
 # expected returns whilst minimising the portoflio variance

class SimpleStrategy(BaseStrategy):
    """ A simple strategy that sums signals in 5 minute intervals

    Combines all signals provided, and sums over 5 minute intervals to generate
    a meta-signal on which to place orders.

    A list of orders can be geberated with get_order_list(), and that list of
    orders can be historically traded with run_historical().
    """
    def __init__(self,signal_dict,ticker_list,resampling=5):
        # initialise the members of the BaseStrategy
        if isinstance(resampling,(int,float)):
            self.resampling = int(resampling)
        else:
            raise TypeError("resampling should be a number")
        super().__init__(signal_dict,ticker_list)

    def get_order_list(self,stocks_df):
        """ generate a list of orders based on historical data
            Args:
                - stocks_df: dataframe of tickers values indexed by time
            Returns:
                - order_list: a list of trading.orders objects
        """

        requests_dict = self.signal_requests(stocks_df)
        order_list = []
        for ticker in requests_dict:
            # concat all the dataframes for this ticker into single dataframe
            # where each signal will have a column
            tmp_df = pd.concat(requests_dict[ticker],sort=False)
            # now collate over time periods to get a 'master signal' from the
            # various input signals
            #resample into 5 min intervals
            tmp_df = tmp_df.resample(str(self.resampling)+'T',
                                     closed='right',
                                     label='right').sum()
            # sum over all signals
            tmp_df['sum'] = tmp_df.sum(axis=1)
            # drop the original signal columns
            tmp_df = tmp_df.drop(columns=list(self.signal_dict.keys()))
            # this is a simple selection - anywhere the sum over signals gave
            # a positive or negative overall signal in that 5 minute period
            tmp_df = tmp_df.loc[~(tmp_df==0).all(axis=1)]

            for idx,row in tmp_df.iterrows():
                if row['sum']>0:
                    # signals sum to positive request - buy
                    #order_list.append(orders.BuyMarketOrder(idx,ticker,1))
                    order_list.append({'type': 'buy_market',
                                       'time': idx,
                                       'ticker': ticker,
                                       'quantity': 1})
                elif row['sum']<0:
                    # signals sum to negative request - sell
                    #order_list.append(orders.SellMarketOrder(idx,ticker,1))
                    order_list.append({'type': 'sell_market',
                                       'time': idx,
                                       'ticker': ticker,
                                       'quantity': 1})
                else:
                    # zeros should have been removed above- error for safety
                    raise RuntimeError("0 encountered in collated signals")
        return order_list

    def __repr__(self):
        return "Simple"+super().__repr__()
