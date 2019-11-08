""" accounts module provides ultilities for handling an account for transactions """
from . import holdings
from . import orders
import pandas as pd
import time
import copy
import warnings

import matplotlib.pyplot as plt

class BasicAccount:
    """ Basic account for equites trading and cash holding for historical trading """
    def __init__(self, broker, time0, time1,
                 order_manager=orders.OrderManager(),
                 asset_manager=None,
                 interest_rate=0.0):
        """ initialize account with broker and time-period

        Args:
            - broker: A trading.brokers object from which to retrieve market data
            - time0: earliest time account able to trade from
            - time1: latest time account able to trade to
        Keyword Args:
            - interest_rate: interest_rate affecting cash holdings (defaults to 0)
        """
        self.broker = broker # not cloned to save memory of data
        self.order_manager = order_manager
        if asset_manager is not None:
            self.asset_manager = asset_manager
        else:
            self.asset_manager = holdings.AssetManager(
                                        self.broker.get_tick_list(),
                                        time0,
                                        interest_rate)

        if isinstance(time0,pd.Timestamp):
            self._time0  = time0
        else:
            raise TypeError("time0 should be a pnadas timestamp")
        if isinstance(time0,pd.Timestamp):
            self._time1  = time1
        else:
            raise TypeError("time1 should be a pandas timestamp")

        bt0,bt1 = self.broker.get_firstlast_times()
        if time1>bt1:
            raise ValueError("cannot set account with final time later than \
                              brokers latest time")
        if time0<bt0:
            raise ValueError("cannot set account with initial time earlier than \
                              brokers earliest time")

        # time-series the account will consider
        self.times = pd.Series(self.broker.get_timeindex_subset(self._time0,self._time1))
        # total trades account has processed
        self.total_trades = 0
        self.last_time_checked = self._time0 + pd.DateOffset(minutes=-1)

    # ----------------- broker interaction methods -----------------------------
    def get_data(self,ticker_list):
        """ get data from broker for given tickers

        Args:
            - ticker_list: list of tickers to get data for

        Returns:
            - dataframe of prices between times account considers on tickers in
              ticker_list
        """
        return self.broker.get_price_list(ticker_list,self._time0,self._time1)

    def get_data_subset(self,ticker_list,time0,time1=None):
        """ get data on tickers in a certain timeframe

        Args:
            - ticker_list: list of tickers to get data for
            - time0: initial time to get data from
            - time1: (optional) time to get dat until, default is self._time1

        Returns:
            - dataframe of prices between time0 and time1 on tickers in
              ticker_list
        """
        if isinstance(ticker_list,str):
            ticker_list = [ticker_list]
        if time1 is None:
            time1=self._time1
        if time0<self._time0:
            raise ValueError("requesting time prior to accounts allowed time range")
        if time1>self._time1:
            raise ValueError("requesting time after the accounts allowed time range")
        return self.broker.get_price_list(ticker_list,time0,time1)

    def get_unslipped_price(self,ticker,time):
        """ get price from broker without slippage

        Args:
            - ticker: ticker to get price for
            - time: time at which to get price
        """
        return self.broker.get_unslipped_price(ticker,time)

    def get_buy_price(self,ticker,time):
        """ get buy price form broker

        Args:
            - ticker: ticker to get price for
            - time: time at which to get price
        """
        return self.broker.get_buy_price(ticker,time)

    def get_sell_price(self,ticker,time):
        """ get sell price from broker

        Args:
            - ticker: ticker to get price for
            - time: time at which to get price
        """
        return self.broker.get_sell_price(ticker,time)

    # -------------------- AssetManagement methods -----------------------------
    def get_portfolio_df(self):
        """ Get the portoflio dataframe

        The dataframe is indexed by time, and has columns for the value of the
        portfolio of assets, as well columns for cash and fees - allowing them
        to be seperately evaluated.

        Keyword Args:
            - construct: (bool) If True then portforlio datframe will be
                         reconstructed regardless of whether already performed.
                         (defaults to True)
        Returns:
            - portfolio_df: dataframe of the portfolio
        """
        df = pd.DataFrame(data=self.asset_manager.asset_history)
        return df.set_index('time')

    def get_holdings_df(self):
        """ get dataframe of holdings over time """
        #return pd.DataFrame(index=self.t_vals, data=self.holdings_list)
        df = pd.DataFrame(data=self.asset_manager.stock_history)
        return df.set_index('time')

    # -----------  OrderManager interaction ------------------------------------

    def place_historical_order(self,type,time,ticker,quantity,limit=0):
        """ add an order to be historically traded

        Args:
            - order: trading.orders object to be added

        Keyword Args:
            - reorder: if True will reorder the entire order list (default False)

        Returns:
            - id: id of the order added
        """
        info = {'type': type,
                'time': time,
                'ticker': ticker,
                'quantity':quantity,
                'limit':limit}
        id   = self.order_manager.place_order(info,self.broker)
        return id

    def cancel_order(self,id):
        """ cancel an order that has been added to the order list

        If the requested order has already been fulfilled, cancellation will fail
        silently

        Args:
            - id: is of the order to be cancelled
        """
        try:
            self.order_manager.cancel_order(id)
        except KeyError:
            warnings.warn("cannot cancel order with id: " + str(id) +
                          " as that id is not a valid order")

    def get_unfulfilled_orders(self):
        return self.order_manager.get_open_orders_info()

    def check_order_fulfilled(self,id):
        return self.order_manager.check_order_fulfilled(id)

    # ----------------- running historical interactions ------------------------

    def update_to_t(self,time):
        """ Update the account to a given time

        Calling this method lets the account check which unfulfilled orders need
        to be executed and updates the portfolio, cash, and fees holdings.

        Args:
            - time: time to update to

        Keyword Args:
            - collect_holdings: (bool) If True keep track of holdings at each
                                time this method is called. (defaults to True)
        """
        if not isinstance(time, pd.Timestamp):
            raise TypeError("time supplied to aupdate_to_t should be \
                             a pandas timestamp")
        if time>self.last_time_checked:
            tmp_orders = self.order_manager.get_open_orders_info()
            for id, o in tmp_orders.items():
                if time>=o['time_executed']:
                    self.order_manager.execute_order(id,self.asset_manager)
                    self.asset_manager.update_to_time(time)
                    self.total_trades += 1

            self.last_time_checked = time
            self.asset_manager.add_to_history(self.broker,time)

class BasicAccountFactory:
    def make_account(self,broker,t0,t1):
        return BasicAccount(broker,t0,t1)
