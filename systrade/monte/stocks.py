
from . import parameter as param
from . import path
from . import stats

from scipy import linalg
import numpy as np
import pandas as pd

from pandas.tseries.holiday import USFederalHolidayCalendar

MARKET_SECONDS_PER_YEAR = 252.0*6.5*60.0*60.0

class MultiStockPath:
    def __init__(self,
                 generator,
                 correlation_matrix,
                 sigmas,
                 stock_names):
        self.generator = generator.clone()
        # check dimensions of matrix and sigmas etc all work out
        self.correlation_matrix = correlation_matrix
        self.sigmas = sigmas
        self.stock_names = stock_names

    def get_path(self, initial_values, t_start, t_end, freq, interest_rate, seed=None):
        # check initial value os the right size and dimension
        #print("getting path " , freq.)
        # set up parameters of the pathway model
        covar = stats.corr_to_cov(self.correlation_matrix,self.sigmas)
        covar_param = param.SimpleArrayParam(covar)

        chol = linalg.cholesky(covar,lower=True)
        chol[chol<1.0e-9]=0.0
        cholesky_param = param.SimpleArrayParam(chol)

        r_param = param.SimpleParam(interest_rate)

        # create the index of times that are in market hours between
        # requested times
        timeindex = pd.date_range(start=t_start,end=t_end,freq=freq)
        # get the frequency (in seconds) now before removing non-market times
        freq_in_secs = pd.to_timedelta(timeindex.freq,unit='s').total_seconds()
        # only trading hours
        timeindex = timeindex[timeindex.indexer_between_time('09:30','16:00')]
        # only weekdays
        timeindex = timeindex[~(timeindex.dayofweek > 4)]
        # remove fed holidays
        cal = USFederalHolidayCalendar()
        hols = cal.holidays(start=timeindex.min(), end=timeindex.max())
        timeindex=timeindex[~timeindex.isin(hols)]

        # get array of time in yearly units and get stock pathways
        times = np.arange(0,len(timeindex))*freq_in_secs/MARKET_SECONDS_PER_YEAR

        # seed and create the pathway generator object
        np.random.seed(seed=seed)
        path_maker = path.GeometricDiffusionManyAsset(self.generator,
                                                      r_param,
                                                      covar_param,
                                                      cholesky_param)

        if len(times)>0:
            s_paths = path_maker.get_single_timed_path(initial_values,times)
        else:
            raise RunTimeError('Trying to generate stocks on empty time list')

        # put all data into a pandas Dataframe
        stocks_df = pd.DataFrame(index=timeindex,data=s_paths,columns=self.stock_names)
        print("internal : ",stocks_df.groupby(stocks_df.index.dayofweek).sum())
        np.random.seed(seed=None)
        return stocks_df

def time_index_to_seconds_elapsed(time_index):
    t_elapsed_s = pd.to_timedelta(time_index - time_index[0]).total_seconds()
    return t_elapsed_s.values
