""" module for handling cash and asset holdings """
import copy
import warnings
import numpy as np
import pandas as pd
import time as timer

SECONDS_IN_FULL_YEAR = 3600.0*24.0*365.0


class AssetManager:
    def __init__(self,
                 ticker_list,
                 time0,
                 interest_rate,
                 initial_holdings=None,
                 initial_cash=0,
                 stock_holding=None,
                 cash_holding=None,
                 fee_holding=None):
            if stock_holding is not None:
                self.stock_holding = stock_holding
            else:
                self.stock_holding = self._get_simple_holding(ticker_list,
                                                                time0,
                                                                initial_holdings)
            if cash_holding is not None:
                self.cash_holding = cash_holding
            else:
                self.cash_holding = self._get_simple_cash(interest_rate,
                                                          time0,
                                                          initial_cash)
            if fee_holding is not None:
                self.fee_holding = fee_holding
            else:
                self.fee_holding = self._get_simple_cash(interest_rate,
                                                          time0,
                                                          0.0)

            # self._current_cash  = initial_cash
            # self._current_fees  = 0.0
            if initial_holdings is not None:
                self._current_stock = initial_holdings
            else:
                self._current_stock = dict()
                for t in ticker_list:
                    self._current_stock[t] = 0

            self.asset_history  = []
            #self.asset_history.append({'time': time0,
            #                           'cash': initial_cash,
            #                           'fees': 0.0,
            #                        'stock': self.get_stock_portfolio_value(time0)})
            self.stock_history = []
            #if initial_holdings is not None:
            #    self.stock_history.append(**initial_holdings)

    def _get_simple_holding(self,ticker_list,time0,initial_holdings):
        return Holdings(ticker_list,time0,initial_holdings)

    def _get_simple_cash(self,interest_rate,time0,initial_cash):
        return CashHoldingConstantRate(interest_rate,time0,initial_cash)

    def buy_ticker(self,time,ticker,quantity,price,fee):
        self.stock_holding.add_asset(time,ticker,quantity)
        self.cash_holding.add_asset(-price*quantity,time)
        self.fee_holding.add_asset(-fee,time)

    def sell_ticker(self,time,ticker,quantity,price,fee):
        self.stock_holding.add_asset(time,ticker,-quantity)
        self.cash_holding.add_asset(price*quantity,time)
        self.fee_holding.add_asset(-fee,time)

    def update_to_time(self,time):
        self.update_cash_to_time(time)
        self.update_fee_to_time(time)
        self.update_stock_to_time(time)

    def update_stock_to_time(self,time):
        self._current_stock = self.stock_holding.get_holdings(time)

    def update_cash_to_time(self,time):
        self.cash_holding.set_adjustments_to_now(time)

    def update_fee_to_time(self,time):
        self.fee_holding.set_adjustments_to_now(time)

    def get_stock_portfolio_value(self,broker,time):
        val = 0.0
        if self._current_stock is not None:
            for tick in self._current_stock:
                val += self._current_stock[tick]* \
                       broker.get_unslipped_price(tick,time)
        return val

    def get_cash(self, time):
        return self.cash_holding.get_cash_no_new_vals_check(time)

    def get_fees(self, time):
        return self.fee_holding.get_cash_no_new_vals_check(time)

    def add_to_history(self, broker, time):
        cash_now = self.get_cash(time)
        fees_now = self.get_fees(time)
        stock_val_now = self.get_stock_portfolio_value(broker,time)
        self.asset_history.append({'time':time,
                                   'cash':cash_now,
                                   'fees':fees_now,
                                   'stock':stock_val_now})
        tmp_dict = copy.deepcopy(self._current_stock)
        tmp_dict['time'] = time
        self.stock_history.append(tmp_dict)


class Holdings:
    """ Manage holdings of assets """
    def __init__(self,ticker_list,time0,holdings_dictionary=None):
        """ initialise a set of assets to be held

        Args:
            - ticker_list: a list of tickers that this Holdings will be able to
                           hold
            - time0: the initial time of holdings
            - holdings_dictionary: (dict, optional) keys as tickers, values as
                                   holdings of those tickers at time0.

        """
        self.time0=time0
        if isinstance(ticker_list,str):
            ticker_list = [ticker_list]
        tmp_ticks = copy.deepcopy(ticker_list)

        if holdings_dictionary is None:
            holdings_dictionary = {tick:[0] for tick in tmp_ticks}
            holdings_dictionary['time'] = time0
            #print(holdings_dictionary)
            tmp_ticks.append('time')
            self.adjustments = pd.DataFrame(data=holdings_dictionary,columns=tmp_ticks)
            #self.adjustments.set_index('time',inplace=True)
            self.n = 1
            #print("initialized holdings: \n",self.adjustments)
        else:
            if not isinstance(holdings_dictionary,dict):
                raise TypeError("holdings_dictionary should be a dictionary \
                                  - got a "+str(type(holdings_dictionary)))

            if not set(holdings_dictionary.keys()).issubset(set(ticker_list)):
                raise RuntimeError("all keys in holdings_dictionary should appear \
                                    in ticker_list")
            holdings_dictionary['time'] = time0
            tmp_ticks.append('time')
            print(holdings_dictionary)
            print(tmp_ticks)
            self.adjustments = pd.DataFrame(data=holdings_dictionary,columns=tmp_ticks,index=[0])
            self.adjustments = self.adjustments.fillna(0)
            self.n = 1

    def clone(self):
        return copy.deepcopy(self)

    def add_holdings(self,time,holdings_dict):
        """ add holdings at a given time
        Args:
            - time: a pandas.DateTime object for the time adding the assets
            - holdings_dict: A dictionary keyed by tickers and values as number
                             of those tickers to add. values can be negative.
        """
        cols = set(self.adjustments.columns)
        if not set(holdings_dict.keys()).issubset(cols):
            raise ValueError("trying to add holding for ticker not initialized for this portfolio")

        # for t in cols:
        #     if t not in holdings_dict:
        #         holdings_dict[t] = 0.0
        holdings_dict['time'] = time
        self.adjustments = self.adjustments.append(holdings_dict,
                                                   ignore_index=True,
                                                   sort=False)
        #self.adjustments.loc[self.n+1] = holdings_dict
        self.n+=1

    def add_asset(self,time,ticker,quantity):
        """ add a single holding

        Args:
            - time: a pandas.DateTime object for the time adding the assets
            - ticker: ticker of holding to add
            - quantity: how many of that ticker to add to the Holdings (can be
                        negative)
        """
        if not isinstance(ticker,str):
            raise TypeError("ticker must be a string\n")
        if not isinstance(quantity,(int,np.integer)):
            raise TypeError("quantity must be integer\n")
        if ticker not in self.adjustments.columns.to_list():
            raise ValueError("can't add asset not initialised in the Holding")
        # print("holdings getting a new adjustment of : " , ticker)
        # print(time,quantity)
        newdf = pd.DataFrame({'time':[time],ticker:[quantity]})
        #newdf = newdf.fillna(0)
        self.adjustments = self.adjustments.append(newdf,ignore_index=True,sort=False)
        #self.adjustments[self.n+1] = {'time':[time],ticker:[quantity]}
        self.n+=1
        # it could be that concat is faster here.. have to check


    def get_holdings(self,time_get):
        """ get holdings at a given time

        Args:
            - time_get: pandas.DateTime object at which to get holdings

        Returns:
            - holds_t: dictionary keyed by ticker, values are number of that
                       ticker held at time time_get.
        """
        tmp_df = self.adjustments.loc[self.adjustments['time']<=time_get]
        if len(tmp_df)<1:
            return {tick:0 for tick in self.tick_list}
        else:
            holds_t=tmp_df.drop(columns=['time']).sum().to_dict()
            return holds_t

    def __repr__(self):
        return "Holdings: \n"+str(self._portfolio)

    def __str__(self):
        return "Holdings: \n"+str(self._portfolio)


class CashHoldingConstantRate:
    """ Object to keep track of cash holdings with constant interest rate """
    def __init__(self,r,t0,amt0):
        """ Initialize cash holdings at a given time with given value
        Args:
            - r: interest rate
            - t0: inital time
            - amt0: initial cash holding at t0
        """
        if isinstance(r, (int,float)):
            self._r    = r
        else:
            raise TypeError("interest rate should be a number")
        if isinstance(t0,pd.Timestamp):
            self.t0    = t0
        else:
            raise TypeError("t0 should be a pandas timestamp")
        if isinstance(amt0,(int,float)):
            self.amt0  = amt0
        else:
            raise TypeError("amount should be a number")
        self.adjustments = pd.DataFrame(columns=['time','amount'])
        self.adjustments_to_now = dict()

    def clone(self):
        return copy.deepcopy(self)

    def add_asset(self,amount,time):
        """ add/subract cash at a given time
        Args:
            - amount: amount af cash to add
            - time: time at which adding the cash
        """
        if not isinstance(time,pd.Timestamp):
            raise TypeError("time should be pandas Timestamp")

        if not isinstance(amount, (int,float)):
            raise TypeError("amount should be a number")

        if time<self.t0:
            raise ValueError("adding asset prior to set initial time")

        self.adjustments = self.adjustments.append({'time':time,'amount':amount},ignore_index=True,sort=False)

    def set_adjustments_to_now(self,time):
        """ set value of member adjustments_to_now for given time

        adjustments_to_now keeps track of all cash in/out up to a given time,
        this method can set the given time over which those adjustments are
        considered.

        Args:
            - time: time to set adjustments_to_now to consider
        """
        self.adjustments_to_now = self.adjustments.loc[self.adjustments['time']<=time]

    def get_cash_no_new_vals_check(self,time):
        """ get value of cash at a given time, without checking new transactions

        Use self.adjustments_to_now to get the current value of cash in the
        holding. If need to update adjustements_to_now, that can be done with
        set_adjustments_to_now(time). Or can call get_cash_value(time) if want
        to check through all transactions.

        Args:
            - time: time at which to get cash value held

        Returns:
            - cash value held at time=time
        """
        if not isinstance(time,pd.Timestamp):
            raise TypeError("time should be pandas Timestamp")
        delt0 = (time-self.t0).total_seconds()/SECONDS_IN_FULL_YEAR
        if len(self.adjustments.index)<1:
            return self.amt0*np.exp(self._r*delt0)

        if 'time' in self.adjustments_to_now:
            delt = (time-self.adjustments_to_now['time']).dt.total_seconds()/SECONDS_IN_FULL_YEAR
        else:
            raise RuntimeError("get_cash_no_new_vals_check can only be called \
                                 with times > t0 if set_adjustments_to_now has \
                                 been called on the object ")
        return np.sum(self.adjustments_to_now['amount'].values*np.exp(self._r*delt)) + self.amt0*np.exp(self._r*delt0)

    def get_cash_value(self,time):
        """ Get value of cash held at given time

        Args:
            - time: time at which to get cash value held

        Returns:
            - cash value held at time=time

        """
        delt0 = (time-self.t0).total_seconds()/SECONDS_IN_FULL_YEAR
        if len(self.adjustments.index)<1:
            return self.amt0*np.exp(self._r*delt0)
        tmp_df = self.adjustments.loc[self.adjustments['time']<=time]
        if len(tmp_df.index)==0:
            return self.amt0*np.exp(self._r*delt0)
        delt = (time-tmp_df['time']).dt.total_seconds()/SECONDS_IN_FULL_YEAR
        ams  = tmp_df['amount']
        return np.sum(ams*np.exp(self._r*delt)) + self.amt0*np.exp(self._r*delt0)

    def __repr__(self):
        return "CashHoldings: \n"+str(self._portfolio)

    def __str__(self):
        return "CashHoldings: \n"+str(self._portfolio)
