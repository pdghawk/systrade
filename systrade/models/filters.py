""" module for filters for tickers to be used for signals """
import copy

class TickerOneToManyFilter:
    " Filter out many tickers for input, and output for single ticker only "
    def __init__(self, tick_in, tick_list_out):
        """ initialise filter

        Args:
            - tick_in: ticker to filter on input
            - tick_list_out: list of tickers to filter on output
        """
        if isinstance(tick_in, str):
            self.tick_in  = tick_in
        else:
            raise TypeError("tick_in should be string name for single ticker")
        if isinstance(tick_list_out,list):
            self.tick_list_out = tick_list_out
        else:
            raise TypeError("tick_list_out should be a list")

    def apply_in(self,data_df):
        """ apply filter on an input dataframe

        use tick_list_in to select only those tickers of the input dataframe

        Args:
            - data_df: the dataframe to be filtered
        Returns:
            - data_df a filtered version of the dataframe
        """
        return data_df[self.tick_in]

    def output_map(self):
        """ get a dictionary mapping input tickers to output tickers

        Returns:
            - Dictionary mapping input tickers to output tickers
        """
        out=dict()
        out[self.tick_in] = self.tick_list_out
        return out

    def clone(self):
        return copy.deepcopy(self)

class TickerOneToAnotherFilter:
    """ filter one set of tickers in, to one set of tickers out

    Filters each ticker in tick_list_in, and will filter for output the ticker at
    same index in tick_list_out for output. i.e can use filter to get indicator
    on tick_list_in[i] and use it to get signal on tick_list_out[i].

    Can also be a OneToOne filter if tick_list_out == tick_list_in.
    """
    def __init__(self, tick_list_in, tick_list_out):
        """ initialise filter

        Args:
            - tick_list_in: list of tickers to filter on input
            - tick_list_out: list of tickers to filter on output
        """
        if(len(tick_list_in)==len(tick_list_out)):
            self.tick_list_in  = tick_list_in
            self.tick_list_out = tick_list_out
        else:
            raise ValueError("tick_list_in and tick_list_out sould be same length")

    def apply_in(self,data_df):
        """ apply filter on an input dataframe

        use tick_list_in to select only those tickers of the input dataframe

        Args:
            - data_df: the dataframe to be filtered
        Returns:
            - data_df a filtered version of the dataframe
        """
        return data_df[self.tick_list_in]

    def output_map(self):
        """ get a dictionary mapping input tickers to output tickers

        Returns:
            - Dictionary mapping input tickers to output tickers
        """
        return {self.tick_list_in[i]:[self.tick_list_out[i]] for i in range(len(self.tick_list_in))}

    def clone(self):
        return copy.deepcopy(self)
