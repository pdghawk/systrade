# New BSD License
#
# Copyright (c) 2007–2019 The scikit-learn developers.
# Copyright (c) 2019 Peter Hawkins
# All rights reserved.
#
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   a. Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#   b. Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#   c. Neither the name of the Scikit-learn Developers  nor the names of
#      its contributors may be used to endorse or promote products
#      derived from this software without specific prior written
#      permission.
#
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
""" base module for defining Base Classes of modelling objects

The implementation of base indicators, signals, and strategies all inheirit from
a base paramterized object. Parameters of models can be easily
adjusted for backtesting a model with many variations of its parameters. Ideas
and code from scikit-learn was used in developing the code in this module, the
BSD license and copyright of the sci-kit learn software applies to this code,
as written in this module's source code. Further, we here cite scikit-learn's design:

API design for machine learning software: experiences from the scikit-learn project, Buitinck et al., 2013.
which can be found on the arXiv: https://arxiv.org/abs/1309.0238

BaseParameterizedObject is a modified version of scikit-learn's sklearn.base.BaseEstimator.
ParamGrid is a modified verison of scikit-learns's sklearn.model_selection.ParameterGrid.

This module is in no way endorsed by scikit-learn.
"""

import inspect
import copy
from collections import defaultdict
from itertools import product

from abc import ABC,abstractmethod

class BaseParameterizedObject:
    """ Base object for parametrized objects in models """
    @classmethod
    def _get_param_names(cls):
        """ get names of parameters of the object """
        init_signature = inspect.signature(cls.__init__)
        parameters = [p for p in init_signature.parameters.values()
                      if p.name != 'self' and p.kind != p.VAR_KEYWORD]
        # n.b VAR_KEYWORD meaansL A dict of keyword arguments that aren’t bound
        # to any other parameter. This corresponds to a **kwargs parameter in a
        # Python function definition.
        for p in parameters:
            # check if parameter kinds was of *args type (VAR_POSITIONAL)
            if p.kind == p.VAR_POSITIONAL:
                raise RuntimeError("systrade.models parametrized objects should"
                                    "not use *args, or **kwargs in their init")
        return sorted([p.name for p in parameters])

    def get_params(self,deep=True):
        """ get parameters of the object

        Args:
            - deep: (bool,optional) if True, get nested parameters

        Returns:
            - out_dict: dictionary with keys as parameter names, and values as
                        parameter values.
        """
        out_dict = dict()
        for key in self._get_param_names():
            try:
                value = getattr(self, key)
            except AttributeError:
                print(key)
                raise RuntimeError("Parameters of model objects should be \
                                    received as instance attributes: \n \
                                    e.g names of class members should appear \
                                    as they do in class __init__")
            if deep and hasattr(value, 'get_params'):
                deep_items = value.get_params().items()
                out_dict.update((key + '__' + k, val) for k, val in deep_items)
            out_dict[key] = value
        return out_dict

    def set_params(self,**params):
        """ set values of parameters

        valid parameter names can be retrieved with get_params()

        Args:
            - **params: keyword parameter name, value pairs.
        """
        valid_params=self.get_params(deep=True)
        nested_params=defaultdict(dict)
        for key,value in params.items():
            if key not in valid_params:
                raise ValueError("Cannot set a parameter that does not exist")
            key,delim,subkey = key.partition('__')
            if delim: #i.e string was able to be split be the delimiter
                    nested_params[key][subkey]=value
            else:
                setattr(self,key,value)

        for key, sub_params in nested_params.items():
            valid_params[key].set_params(**sub_params)

    def clone(self):
        """ clone (deep copy) the object"""
        return copy.deepcopy(self)


class BaseIndicator(BaseParameterizedObject,ABC):
    """ Abstract base class for indicators """
    def __init__(self):
        pass

    @abstractmethod
    def get_indicator(self,stock_df):
        """ apply indicator to stock(s)

        Args:
            - stock_df: dataframe of stock(s), indexed by time

        Returns:
            - indi: indicator over timeframe of stock_df, on all tickers therein
                    individually
        """
        pass


class BaseSignal(BaseParameterizedObject,ABC):
    """ Abstract Base Class  for signal objects

    Note that inherited classes must initialise all other parameters as keyword
    arguments in order for get_params to work as expected.

    """
    def __init__(self,indicator,filter=None):
        """ Signal initialised with an indicator and a filter
        Args:
            - indicator: a models.indicator object to collect indicator for
                         signal to base its decisions on
            - filter: a models.filter object for ticker selection
        """
        self.indicator=indicator
        if filter is None:
            self.filter  = filter
        else:
            self.filter  = filter.clone()
        param_dict=self.get_params()
        print("signal: ",param_dict)

    @abstractmethod
    def request_historical(self,stocks_df,signal_name):
        """ use historical data to get a dictionary of signals

        Args:
            - stocks_df: pandas dataframe of stock prices, indexed by time
            - signal_name: a name to give this signals output
        Returns:
            - signal_dict: a dictionary witb keys being the tickers that the
                           signal considers (selected by this signal's filter),
                           and values being dataframes, indexed by times at which
                           signals are seen, and a column named by argument
                           'signal_name', with +/-1 for a buy/sell signal.
        """
        pass

    def _get_params(self,deep=True):
        """ get parameters of this signal """
        out_dict = super().get_params(deep)
        try:
            del out_dict['filter']
        except KeyError:
            print("'filter' key of strategy not found")
        return out_dict

    def get_params(self,deep=True):
        """ get parameters of this signal

        Args:
            - deep: (bool) True will also return nested parameters of class members

        Returns:
            - out_dict: dictionary of parameters, keys are parameter names,
                        values are parameter values. Keys for nested parameters
                        have '__' between nested object names.

        """
        return self._get_params(deep)


class BaseStrategy(BaseParameterizedObject,ABC):
    """ Abstract Base Class for trading stratgies """

    def __init__(self,signal_dict,ticker_list):
        """ create strategy object
        Args:
            - signal_dict: A dictionary if signals, keys are names for those
                           signals, and values are models.signal objects
            - ticker_list: A list of tickers that the strategy will consider, or
                           a single ticker as a string
        """
        if isinstance(signal_dict,dict):
            if all([issubclass(type(s),BaseSignal) for s in signal_dict.values()]):
                self.signal_dict = copy.deepcopy(signal_dict)
            else:
                raise TypeError("signal_dict should have values that are systrade"+
                                " signal objects - i.e inherit models.base.BaseSignal")
        else:
            raise TypeError("signal_dict should be a dictionary")

        if isinstance(ticker_list,str):
            ticker_list=[ticker_list]

        if isinstance(ticker_list,list):
            self.ticker_list = copy.deepcopy(ticker_list)
        else:
            raise TypeError("ticker_list should be a list, or a single ticker \
                             as a string")

        #pdict = self.get_params()
        #print("strat : ",pdict)

    def _get_params(self,attr,deep=True):
        """ get parameters of strategy and its signals """
        out_dict = super().get_params(deep=False)
        try:
            del out_dict['signal_dict']
        except KeyError:
            print("'signal_dict' key of strategy not found")
        try:
            del out_dict['ticker_list']
        except KeyError:
            print("'ticker_list' key of strategy not found")
        if deep:
            sig_dict = getattr(self,attr)
            for sig_name,sig_obj in sig_dict.items():
                if hasattr(sig_obj,'get_params'):
                    for param_name,param_value in sig_obj.get_params().items():
                        out_dict["%s__%s" % (sig_name,param_name)] = param_value
        return out_dict

    def get_params(self,deep=True):
        """ get parameters of strategy and its signals
        Args:
            - deep: (bool, optional) if True, get nested parameters of each signal
        Returns:
            - out_dict: dictionary of parameters, keys are parameter names,
                        values are parameter values. Keys for nested parameters
                        have '__' between nested object names. Signal names are
                        those provided in the signal_dict
        """
        return self._get_params('signal_dict',deep)

    def set_params(self,**params):
        """ set parameters of strategy and its signals (and nested objects)
        Args:
            - **params: keyword arguments for any parameters of the strategy,
                        see valid options by calling strategy.get_params()
        Returns:
            - self
        """
        valid_signal_names = list(self.signal_dict.keys())
        for param_name in list(params.keys()):
            if "__" not in param_name:
                value = params.pop(param_name)
                super().set_params(**{param_name:value})
            else:
                key,delim,subkey = param_name.partition('__')
                #print("k,d,s : ", key,delim,subkey)
                if key in self.signal_dict:
                    value = params.pop(param_name)
                    self.signal_dict[key].set_params(**{subkey:value})
                else:
                    raise RuntimeError("Cannot set signal named: ", key,
                                       " in strategy as it does not exist")
        return self


    def signal_requests(self,stocks_df):
        """ returns dictionary with a list of requests for each ticker (key)

        For each signal in the strategy, get the signals for all the tickers
        they consider. Combine all signals into a dictionary, with keys being
        the tickers. Each ticker key, than has as a value a list of dataframes,
        containing any signals found.

        Args:
            - stocks_df: dataframe of tickers value over time

        Returns:
            - requests_dict: a dictionary with keys=tickers, and values=list of
            dataframes, containing any signals found - i,e each dataframe is
            indexed by time, and has a column named by signal_dict key with +/-1
            where a signal is found.
        """
        requests_dict = dict()
        for tick in self.ticker_list:
            requests_dict[tick] = []
        # collect signals over time-period of the stock data in stocks_df, for
        # each signal in the signal dictionary oif this strategy
        for sig_name,sig in self.signal_dict.items():
            these_reqs = sig.request_historical(stocks_df,signal_name=sig_name)
            for ticker in these_reqs:
                requests_dict[ticker].append(these_reqs[ticker])
        return requests_dict

    @abstractmethod
    def get_order_list(self,stocks_df):
        """ compulsory method for inherited classes to get a list of orders
        Returns:
            - order_list: a list of order requests, as dictionaries, fields
                          available are type,ticker,time,quantity,limit
        """
        pass

    def risk_check_cancellations(self,account):
        """ cancel orders that are active but no longer wanted """
        pass

    def risk_check_new_orders(self,account):
        """ place new orders due to changing circumstances """
        pass

    def portfolio_adjust(self,account):
        """ place/cancel orders to optimize portfolio """
        pass

    def run_historical(self,account):
        """ run historical trading

        Args:
            - account: A tradings.account object that handles order placement
        """
        stocks_df = account.get_data(self.ticker_list)
        order_list = self.get_order_list(stocks_df)
        # placed_orders = dict()
        for o in order_list:
            account.place_historical_order(**o)
        #     placed_orders[id] = o

        alltimes = copy.deepcopy(account.times)
        for t_idx,t_val in alltimes.iteritems():
            #check if want to place or cancel orders to optimize portfolio
            self.portfolio_adjust(account)
            # check if want to place any new orders for risk purposes
            self.risk_check_new_orders(account)
            #check if we need to cancel any orders for risk avoidance
            self.risk_check_cancellations(account)
            # update account to next time step
            account.update_to_t(t_val)
        return None

    def __repr__(self):
        return "Strategy with params : " + str(self.get_params())


class ParamGrid:
    """ class to store a grid of parameters """
    def __init__(self,param_dict):
        """ initialize

        Args:
            - param_dict: a dictionary of parameters, keys as their names, with
                          values being lists of values the parameter should take
        """
        if isinstance(param_dict,dict):
            self.param_dict = param_dict
        else:
            raise TypeError("param_dict should be a dictionary")

    @classmethod
    def check_and_create(cls,param_dict,strategy):
        """ check if pd is a dictionary with allowed parameters """
        for key,value in param_dict.items():
            if not isinstance(value,list):
                raise TypeError("param_dict", key, " should have a list as"
                                 " value in the dictionary")
        valid_params = strategy.get_params()
        for p in param_dict.keys():
            if p not in valid_params:
                raise ValueError(p," is not a valid parameter of strategy to be set")
        return cls(param_dict)

    def __iter__(self):
        items = sorted(self.param_dict.items())
        if not items:
            yield {} # n.b truth value is False
        else:
            keys, values = zip(*items)
            # iterate over all possible combinations of the values
            # but n.b iterate as a generator with yield statement
            for v in product(*values):
                params = dict(zip(keys, v))
                yield params

    def __len__(self):
        """ total number of paramter sets to try """
        keys, vals = zip(*self.param_dict.items())
        length = 1
        for v in vals:
            length *= len(v)
        return length
