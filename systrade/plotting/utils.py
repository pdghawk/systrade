from matplotlib.ticker import Formatter
from matplotlib.axes import Axes
import matplotlib.axis as maxis
from matplotlib.projections import register_projection

import numpy as np

class MarketHoursFormatter(Formatter):
    """ Custom formatter to allow only plotting market hours only """
    def __init__(self, times):
        self.times=times

    def __call__(self,t_ind,pos=0):
        t_ind = int(round(t_ind))
        if t_ind<0 or t_ind>(len(self.times)-1):
            return ''
        return self.times[t_ind]

class TSeriesAxes(Axes):
    """ A custom axes for projection for market-hour-only plotting """
    name='time_series'

    def set_xaxis_markettime(self,x):
        """ force x axis to follow MarketHoursFormatter """
        self.times = x
        formatter = MarketHoursFormatter(x)
        self.xaxis.set_major_formatter(formatter)

    def plot_tseries(self,x,y,**kwargs):
        """ plot time-series only on market-hours

        x should be a series of times, internally this is converted to indices
        expected by the formatter.

        Note
        -----
        Unlike matplotlib.pyplot.plot args for color cannot be given like 'r',
        they must have keyword declaration : color='r'

        Args:
            - x: time values (Pandas DateTimeIndex, Series, or DateTime)
            - y: time-series y values

        Keyword Args:
            Any Keyword arguments accepted by matplotlib.axes.Axes.plot are
            accepted
        """
        super().plot(np.arange(len(x)), y, **kwargs)

    def format_xaxis_frequency(self, x, frequency='days'):
        if frequency=='days':
            # groupby day maybe preferable
            inds_day_start = list(x.indexer_between_time('09:29','09:31'))
            day_starts = [x.to_series().iloc[i] for i in inds_day_start]
            self.set_xticks(inds_day_start)
        else:
            raise NotImplementedError("frequency keyword `",frequency,"` is not recognized")

    def plot_vert(self,x,ymin,ymax,**kwargs):
        """ plot vertical line

        Args:
            x: time for vertical line - Pandas Datetime
            ymin: low point of line
            ymax: high point of line
        Keyword Args:
            Any Keyword arguments accepted by matplotlib.axes.Axes.plot are
            accepted

        """
        ind = self.times.get_loc(x)
        super().plot([ind,ind],[ymin,ymax],**kwargs)

    def plot_horiz(self,y,xmin,xmax,**kwargs):
        """ plot horizontal line

        Args:
            y: y value for horizontal line
            xmin: initial time of line (Datetime)
            xmax: final time of line (Datetime)
        Keyword Args:
            Any Keyword arguments accepted by matplotlib.axes.Axes.plot are
            accepted

        """
        ind_min = self.times.get_loc(xmin)
        ind_max = self.times.get_loc(xmax)
        super().plot([ind_min,ind_max],[y,y],**kwargs)

register_projection(TSeriesAxes)
