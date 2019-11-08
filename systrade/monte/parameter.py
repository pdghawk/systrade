""" Module for parameter classes

All classes should have at a minimum methods:
 - integral(time0,time1)
 - square_integral(time0,time1)
 - mean(time0,time1)

"""
import numpy as np
import copy

class SimpleParam:
    """ a constant in time parameter """
    def __init__(self,value):
        self.value = value

    def integral(self,time0,time1):
        """ get integral of parameter between two times
        Args:
            - time0: lower integral bound
            - time1: upper integral bound
        Returns:
            - intgral: \int_{time0}^{time1} parameter(t)
        """
        return self.value*(time1-time0)

    def square_integral(self,time0,time1):
        """ get square integral of parameter between two times
        Args:
            - time0: lower integral bound
            - time1: upper integral bound
        Returns:
            - intgral: \int_{time0}^{time1} parameter^2(t)
        """
        return self.value**2*(time1-time0)

    def mean(self,time0,time1):
        """ get mean of parameter between two times
        Args:
            - time0: lower integral bound
            - time1: upper integral bound
        Returns:
            - intgral: (\int_{time0}^{time1} parameter(t))/(time1-time0)
        """
        return self.value

    def clone(self):
        return copy.deepcopy(self)

class SimpleArrayParam:
    """ a constant in time parameter, initial value a numpy array """
    def __init__(self,value):
        if isinstance(value, np.ndarray):
            self.value = value
        else:
            raise TypeError("SimpleArrayParam must be initialized with numpy array")
        self._shape  = np.shape(self.value)
        if len(np.unique(self._shape))==1:
            self._square = True
        else:
            self._square = False

    @property
    def square(self):
        return copy.deepcopy(self._square)

    @property
    def shape(self):
        return copy.deepcopy(self._shape)

    def integral(self,time0,time1):
        """ get integral of parameter between two times
        Args:
            - time0: lower integral bound
            - time1: upper integral bound
        Returns:
            - intgral: \int_{time0}^{time1} parameter(t)
        """
        return self.value*(time1-time0)

    def square_integral(self,time0,time1):
        """ get square integral of parameter between two times
        Args:
            - time0: lower integral bound
            - time1: upper integral bound
        Returns:
            - intgral: \int_{time0}^{time1} parameter^2(t)
        """
        return self.value**2*(time1-time0)

    def mean(self,time0,time1):
        """ get mean of parameter between two times
        Args:
            - time0: lower integral bound
            - time1: upper integral bound
        Returns:
            - intgral: (\int_{time0}^{time1} parameter(t))/(time1-time0)
        """
        return self.value

    def diag_square_integral(self,time0,time1):
        return np.diag(self.value)**2*(time1-time0)

    def diag_integral(self,time0,time1):
        return np.diag(self.value)*(time1-time0)

    def diag_mean(self,time0,time1):
        return np.diag(self.value)

    def clone(self):
        return copy.deepcopy(self)
