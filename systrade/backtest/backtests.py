""" backtests module provides utilities for backtesting of strategies """
from systrade.trading import accounts
from systrade.models.base import ParamGrid

import numpy as np
from random import shuffle
import copy

from itertools import product

import matplotlib.pyplot as plt

import pandas as pd

# extensions required here:
# * alternative history testing - from the data - get mu,covariance - use
#   to build new monte carlo pathways for the stocks. run strategy on those
#   alternative histories - how is the performance of the strategy. Must
#   consider what p-value should be in this case
#        - note that extraction of mu from data is not a trivial excersize
#        - also note that this is not very throrough as no guarantee on market
#          following a statistical process of our choice (Guassian, Jumps etc)
#
# * testing machine-learning type models. purged test-train split &
#   cross-validation.
#
# sensitivity to conditions - how mcuh does profit/max drawdown ect vary as
# one changes the parameters of a model that has already been optimized. if
# response is fairly flat in that region - less likely to be overfit
# exact statistical nature of this type of test would presumably need to
# be honed.

class TestData:
    """ class to store results of a single backtest"""
    def __init__(self):
        self.p_value=None
        self.adjusted_p_value=None
        self.max_drawdown=None
        self.avg_trades_per_day=None
        self.total_trades=0
        self.null_rejected=False
        self.mean_excess_return = None


class SingleStrategyBackTest:
    """ Backtester for a single strategy test """
    def __init__(self,broker,account_factory,strategy):
        """ initialize
        Args:
            - broker: a systrade,trading.broker object
            - strategy: a systrade.models.strategy object
        """
        self._strategy = strategy.clone()
        self._broker   = broker
        self.testdata  = TestData()
        self.account_factory = account_factory

    def _make_times_valid(self,t0,t1):
        start, end = self._broker.get_firstlast_times()

        if(t0 is None and t1 is None):
            t0,t1=start,end
        elif(t0 is None):
            t0,_=start,end
        elif(t1 is None):
            _,t1=start,end

        if t0<start:
            raise ValueError("t0 too early")
        if t1>end:
            raise ValueError("t1 too late")

        return t0,t1

    def _create_account(self,t0,t1):
        #account = accounts.BasicAccount(self._broker,t0,t1)
        account = self.account_factory.make_account(self._broker,t0,t1)
        return account

    def _run_strategy(self,t0,t1):
        t0,t1 = self._make_times_valid(t0,t1)
        # create an account with which to trade
        account = self._create_account(t0,t1)
        # apply strategy over historical trading through account
        self._strategy.run_historical(account)
        return account

    def portfolio_to_returns(self,portfolio_df):
        # sum portfolio over portfolio, cash, and fees (axis=1)
        running_valuation = portfolio_df.sum(axis=1).values
        pf_returns = running_valuation[1:]-running_valuation[:-1]
        return pf_returns

    def benchmark_returns(self,benchmark_df):
        bm_returns = benchmark_df.values[1:]-benchmark_df.values[:-1]
        return bm_returns

    def test_statistic_from_returns_arr(self,portfolio_returns,benchmark_returns):
        test_stat = portfolio_returns - benchmark_returns
        return test_stat

    def test_statistic_from_values_df(self,portfolio_df,benchmark_df):
        pf_returns = self.portfolio_to_returns(portfolio_df)
        bm_returns = self.benchmark_returns(benchmark_df)
        test_stat = self.test_statistic_from_returns_arr(pf_returns,bm_returns)
        return test_stat

    def mean_excess_return(self,portfolio_df):
        return np.mean(self.portfolio_to_returns(portfolio_df))

    def get_mean_adjusted_test_stat(self,test_stat):
        return test_stat-np.mean(test_stat)

    def _get_sample_means(self,test_size,adjusted_test_stat):
        adj_stat = adjusted_test_stat
        sampling_means=np.zeros((test_size,))
        for i in range(test_size):
            tmp_stat = np.random.choice(adj_stat,size=len(adj_stat))
            sampling_means[i] = np.mean(tmp_stat)
        return sampling_means

    def _get_pval(self,sample_means,test_mean):
        test_size = len(sample_means)
        pval = len(sample_means[sample_means>test_mean])/test_size
        return pval

    def run_bootstrap(self,benchmark,significance=0.05,test_size=5000,t0=None,t1=None):
        """ run a bootstrap evaluation of mean test statistic and its p-value

        The backtesters strategy is used to trade on historical data, provided
        vy the backtesters broker, via a temporary systrade.models.account.

        results of the test will be stored in self.testdata, a TestData object.

        Args:
            - benchmark: a time-series of the price of the benchmark

        Keyword Args:
            - significance: statistical significance required to reject Null
                            hypothesis. between 0-1, defaults to 0.05.
            - test_size: the number of bootstrap tests to run to form the
                         distribution of the sample mean.
            - t0: (pandas datetime) time to begin trading the strategy. If None,
                   will use the brokers first available time. defaults to None.
            - t1: (pandas datetime) time to finish trading the strategy. If None,
                   will use the brokers last available time. defaults to None.

        Returns:
            - pval: The p-value of the backtest
        """
        #run the strategy, and get back the account that it ran on
        account = self._run_strategy(t0,t1)
        self.testdata.total_trades = account.total_trades
        # get the portfolio dataframe from the accocunt after trading historically
        portfolio_df = account.get_portfolio_df()
        # get the test statistic
        test_stat = self.test_statistic_from_values_df(portfolio_df,benchmark)

        # plt.plot(running_valuation+benchmark.values[0],'r')
        # plt.plot(benchmark.values,'k')
        # plt.show()
        self.testdata.mean_excess_return = np.mean(test_stat)

        adj_stat = self.get_mean_adjusted_test_stat(test_stat)

        sampling_means=self._get_sample_means(test_size,adj_stat)
        pval = self._get_pval(sampling_means,np.mean(test_stat))
        self.testdata.p_value = pval
        if(pval<significance):
            self.testdata.null_rejected = True

        # mean_test_stat = np.mean(test_stat)
        # n,bins,patches = plt.hist(sampling_means,bins=100, density=True, facecolor='b')
        # plt.plot([mean_test_stat,mean_test_stat],[0,1.2*np.max(n)],'k')
        # plt.ylim([0, 1.2*np.max(n)])
        # print("{p:.4f}".format(p=pval))
        # plt.text(1.4*mean_test_stat,0.7*np.max(n),"p = {p:.4f}".format(p=pval))
        # plt.show()

        return pval


class MultiStrategyBackTest:
    """ Object for backtesting multiple strategies at once """
    def __init__(self,broker,account_factory,strategies):
        """ initialize
        Args:
            - broker: a systrade,trading.broker object
            - strategies: a list of systrade.models.strategy objects
        """
        self.strategies = strategies
        self._broker = broker
        self.test_data_list = []
        self.account_factory = account_factory

    def adjust_pvalues(self,p_values,fwer_alpha,method='Holm'):
        if method=='Holm':
            inds_reject,adj_p = holm_adjust(p_values,fwer_alpha)
        elif method=='Bonferroni':
            inds_reject,adj_p = bonferroni_adjust(p_values,fwer_alpha)
        else:
            raise ValueError("method chosen: \"",method,"\" ,is not an available option")
        return inds_reject, adj_p

    def adjust_pvals_and_null_rejection(self,pvals,fwer_alpha,method='Holm'):
        inds_reject, adj_p = self.adjust_pvalues(pvals,fwer_alpha,method)
        for idx,t_dat in enumerate(self.test_data_list):
            t_dat.adjusted_p_value = adj_p[idx]
            if (idx in inds_reject):
                t_dat.null_rejected = True
            else:
                t_dat.null_rejected = False
        return adj_p

    def run_bootstrap_all(self,benchmark,fwer_alpha=0.05,method='Holm',test_size_each=5000,t0=None,t1=None):
        """ bootstrap evaluation of p-value for all strategies

        All the backtesters strategies are used to trade on historical data,
        provided by the backtesters broker, via a temporary systrade.models.account.

        results of the test of each strategy will be stored in self.testdata, a
        list of TestData objects.

        Args:
            - benchmark: a time-series of the price of the benchmark

        Keyword Args:
            - fwer_alpha: The probability of >= 1 Type I errors in the family of
                          strategies tested will be controlled at this level.
                          between 0-1, defaults to 0.05.
            - method: The method for p-value correction to control the FWER at
                      required level. Default is 'Holm'. Options are:
                      * 'Holm' (default): Holm-Bonferroni Procedure
                      * 'Bonferroni': Bonferroni Procedure
            - test_size: the number of bootstrap tests to run to form the
                         distribution of the sample mean.
            - t0: (pandas datetime) time to begin trading the strategy. If None,
                   will use the brokers first available time. defaults to None.
            - t1: (pandas datetime) time to finish trading the strategy. If None,
                   will use the brokers last available time. defaults to None.

        Returns:
            - adj_p: array of the adjusted p-values for each strategy
        """
        p_values = np.zeros((len(self.strategies),))
        for i,s in enumerate(self.strategies):
            print("running backtest on strategy ",i+1," of ",len(self.strategies))
            tester = SingleStrategyBackTest(self._broker,self.account_factory,s)
            _ = tester.run_bootstrap(benchmark,test_size=test_size_each,t0=t0,t1=t1)
            #self.test_data_list.append(copy.deepcopy(tester.testdata))
            self.test_data_list.append(tester.testdata)
            p_values[i]=tester.testdata.p_value

        adj_p = self.adjust_pvals_and_null_rejection(p_values,fwer_alpha,method)
        return adj_p

    @property
    def results_df(self):
        rows_as_list = []
        for td in self.test_data_list:
            rows_as_list.append(vars(td))
        df = pd.DataFrame(rows_as_list)
        return df


class ParameterScanBackTest:
    """ Object for backtesting a strategy with many different parameters"""
    def __init__(self,broker,account_factory,strategy,param_dict):
        """ Initialize

        Args:
            - broker: a systrade,trading.broker object
            - strategy: a systrade.models.strategy object
            - param_dict: a dictionary of parameters with the follwing key,value
                          properties:
                          * keys: should be names of parameters of the strategy,
                                  note that valid names can be found with
                                  strategy.get_parameters().keys()
                          * values: should be a python list of values that the
                                    named parameter should take in backtesting
                          all combinations of values will be tested.
        """
        self.broker     = broker
        self.strategy   = strategy.clone()
        self.param_grid = ParamGrid.check_and_create(param_dict,strategy)
        self.account_factory = account_factory

        self.test_data_list = []
        self.strategy_list  = []
        self.test_stat_list = []

        self.succesful_strategies = []

        self._best_strategy  = None
        self._best_test_data = None

    def run_bootstrap_all(self,benchmark,fwer_alpha=0.05,method='Holm',test_size_each=5000,t0=None,t1=None):
        """ bootstrap p-value for strategy backtested with all parameter values

        All possible version of the strategy determined by param_dict are used
        to trade on historical data, provided by the backtesters broker, via a
        temporary systrade.models.account.

        results of the test of each strategy will be stored in self.testdata, a
        list of TestData objects, and each of these strategies will be stored in
        strategy_list.

        Args:
            - benchmark: a time-series of the price of the benchmark

        Keyword Args:
            - fwer_alpha: The probability of >= 1 Type I errors in the family of
                          strategies tested will be controlled at this level.
                          between 0-1, defaults to 0.05.
            - method: The method for p-value correction to control the FWER at
                      required level. Default is 'Holm'. Options are:
                      * 'Holm' (default): Holm-Bonferroni Procedure
                      * 'Bonferroni': Bonferroni Procedure
            - test_size: the number of bootstrap tests to run to form the
                         distribution of the sample mean.
            - t0: (pandas datetime) time to begin trading the strategy. If None,
                   will use the brokers first available time. defaults to None.
            - t1: (pandas datetime) time to finish trading the strategy. If None,
                   will use the brokers last available time. defaults to None.

        Returns:
            - adj_p: array of the adjusted p-values for each strategy
        """
        param_list = list(self.param_grid)
        num_params = len(param_list)
        self.strategy_list = []
        for p in param_list:
            #print("trying params: ",p)
            tmp_strat = self.strategy.clone()
            tmp_strat.set_params(**p)
            #print(tmp_strat.get_params())
            self.strategy_list.append(tmp_strat)
        multi_strat_backtester = MultiStrategyBackTest(self.broker,self.account_factory,self.strategy_list)
        adj_p = multi_strat_backtester.run_bootstrap_all(benchmark,
                                                        fwer_alpha=fwer_alpha,
                                                        method=method,
                                                        test_size_each=test_size_each,
                                                        t0=t0,
                                                        t1=t1)
        self.test_data_list = multi_strat_backtester.test_data_list
        #self.test_stat_list = [t.adjusted_p_value for t in self.test_data_list]
        return adj_p

    # def get_best_strategy_and_testdata(self):
    #     lowest_p = 5e10
    #     #best_ind = 0
    #     for i in range(len(self.test_data_list)):
    #         if self.test_data_list[i] < lowest_p:
    #             best_ind=i
    #     if best_ind:
    #         return self.strategy_list[best_ind],self.test_data_list[best_ind]
    #     else:
    #         return None

    def get_successful_strategies(self):
        """ get list of profitable (and statistically significant) strategies """
        good_strats=[self.strategy_list[i] for i in range(len(self.test_data_list))
                   if self.test_data_list[i].mean_excess_return>0.0
                   if self.test_data_list[i].null_rejected]
        return good_strats

    def get_successful_strategies_and_data(self):
        """ get list of profitable (and statistically significant) strategies

        get a list of bothe the strategies but also the test data of historical
        trading, for each of these strategies.

        Returns:
            - good_strats: a list of tuples. Each tuple has:
                           (strategy object, TestData object)
                           each strategy is a statistically significant profitable
                           strategy.

        """
        good_strats=[(self.strategy_list[i],self.test_data_list[i])
                     for i in range(len(self.test_data_list))
                     if self.test_data_list[i].mean_excess_return>0.0
                     if self.test_data_list[i].null_rejected]
        return good_strats

    def get_results_df(self,include_params=False):
        """ get a pandas dataframe of results of the backtest

        Keyword Args:
            - include_params: (bool) if True, include parameters used as a
                              column in the dataframe
        Returns:
            - df: pandas dataframe, each row for a strategy tested, columns provide
                  info on the backtest performance.
        """
        # TODO: all params in a seperate df with a different df for params
        # can then join the df's in seperate code to extract whatever the user
        # wants to get out...?
        param_list = list(self.param_grid)
        rows_as_list = []

        if not include_params:
            for td in self.test_data_list:
                rows_as_list.append(vars(td))
        else:
            param_list = list(self.param_grid)
            for i in range(len(self.test_data_list)):
                this_dict = vars(self.test_data_list[i])
                this_dict['params'] = param_list[i]
                rows_as_list.append(this_dict)
        df = pd.DataFrame(rows_as_list)
        return df





# ------------------------------------------------------------------------------

def bonferroni_adjust(p_vals,fwer_alpha):
    """ Apply Bonferroni adjustment to list of p-values

    Args:
        - p_vals: numpy array of p values of individual tests
        - fwer_alpha: Family Wise Error Rate significance required
    Returns:
        - (indices, adjusted p_values): where indices are indices of p_vals where
                                        one can reject the null hypothesis. and
                                        adjusted p_values are p_values after
                                        adjustment for the FWER
    """
    N=len(p_vals)
    test_condition = fwer_alpha/N
    inds_reject_null = np.where(p_vals<test_condition)
    return inds_reject_null[0],p_vals*N

def holm_adjust(p_vals,fwer_alpha):
    """ Apply Bonferrino-Holm adjustment to list of p-values

    Args:
        - p_vals: numpy array of p values of individual tests
        - fwer_alpha: Family Wise Error Rate significance required
    Returns:
        - (indices, adjusted p_values): where indices are indices of p_vals where
                                        one can reject the null hypothesis. and
                                        adjusted p_values are p_values after
                                        adjustment for the FWER
    """
    N=len(p_vals)
    sort_inds = np.argsort(p_vals)
    sorted_p = p_vals[sort_inds]
    adjusted_p=sorted_p*np.arange(N,0,-1)
    unsort_inds=np.argsort(sort_inds)
    adjusted_p=adjusted_p[unsort_inds]
    inds_reject_null = np.where(adjusted_p<fwer_alpha)
    inds_reject_null = inds_reject_null[0]
    return inds_reject_null,adjusted_p

# ------------------------------------------------------------------------------
