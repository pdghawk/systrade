""" Module for Brokers

Brokers hold data, and provide it or subsets of it on request

when requesting price for buying and selling, prices will likely differ
"""

import copy

import pandas as pd
from pandas.tseries.offsets import DateOffset

class PaperBroker:
    def __init__(self,
                 data_df,
                 slippage_time=DateOffset(seconds=0),
                 transaction_cost=0.0,
                 spread_pct=0.0):
        """ create a homemade paper trading brokerage account

        Args:
            - data_df: pandas dataframe, indexed by time, columns as ticker names

        Keyword Args:
            - slippage_time: pandas DateOffset object, specifying delay broker
                             has between request and real-time info
                             (default 0 seconds)
            - transcation_cost: cost to perform a transaction (default 0)
            - spread_pct: the spread percentage between buy/sell price,
                          defaults to 0%.

        """
        if isinstance(data_df, pd.DataFrame):
            self._historical_data = data_df
        else:
            raise TypeError("data_df supplied to PaperBroker should be a \
                             pandas DataFrame ")
        if isinstance(slippage_time, pd.DateOffset):
            self._slippage_time = slippage_time
        else:
            raise TypeError("splippage time should be a pandas DateOffset")
        if isinstance(transaction_cost,(float,int)):
            if transaction_cost>=0:
                self.transaction_cost = transaction_cost
            else:
                raise ValueError("transcation fee cannot be < 0")
        else:
            raise TypeError("transcation_cost should be a number")
        if isinstance(spread_pct,(float,int)):
            if (spread_pct <= 100.0) and spread_pct >=0.0:
                self.spread_pct = spread_pct
            else:
                raise ValueError("spread_pct should be a percentage: on [0,1]")
        else:
            raise TypeError("spread_pct should be  a number")


    def clone(self):
        return copy.deepcopy(self)

    def next_extant_time(self,time):
        if time<=self._historical_data.index.max():
            t_ind = self._historical_data.index.get_loc(time, 'backfill')
            time  = self._historical_data.index[t_ind]
            return time
        else:
            raise ValueError("requesting a time later than available in data")

    # ---------- information requests ------------------------------------------

    def get_timeindex_subset(self,t0,t1):
        if not isinstance(t0,pd.Timestamp):
            raise TypeError("t0 should be a pandas timestamp")
        if not isinstance(t1,pd.Timestamp):
            raise TypeError("t1 should be a pandas timestamp")
        if t0<self._historical_data.index.min():
            raise ValueError("requesting data prior to earliest time")
        if t1>self._historical_data.index.max():
            raise ValueError("requesting data after latest time")
        return copy.deepcopy(self._historical_data.loc[t0:t1].index)

    def get_firstlast_times(self):
        t0 = self._historical_data.index.min()
        t1 = self._historical_data.index.max()
        return t0,t1

    def get_tick_list(self):
        return self._historical_data.columns.to_list()

    def get_price_list(self,ticker_list,time0,time1):
        if isinstance(ticker_list,str):
            ticker_list=[ticker_list]
        if set(ticker_list).issubset(self._historical_data.columns):
            return self._historical_data.loc[time0:time1][ticker_list]
        else:
            raise ValueError("ticker_list contained tickers that do not exist in historical data")

    def get_data_subset(self,ticker,time):
        max_time = self._historical_data.index.max()
        return self.get_price_list(ticker,time,max_time)

    def get_unslipped_price(self,ticker,time):
        #time = time+self.broker._slippage_time
        time = self.next_extant_time(time)

        if ticker in self._historical_data:
            return self._historical_data.loc[time][ticker]
        else:
            raise ValueError("ticker:",ticker," not available in historical_data")

    def get_price(self,ticker,time):
        time = time+self._slippage_time
        time = self.next_extant_time(time)

        if ticker in self._historical_data:
            return self._historical_data.loc[time][ticker], self.transaction_cost,time
        else:
            raise ValueError("ticker:",ticker," not available in historical_data")

    def get_buy_price(self,ticker,time):
        p,f,t = self.get_price(ticker,time)
        return p*(1.0+self.spread_pct/200.0),f,t

    def get_sell_price(self,ticker,time):
        p,f,t = self.get_price(ticker,time)
        return p*(1.0-self.spread_pct/200.0),f,t
