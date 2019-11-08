""" Module for creating random pathways
"""
import numpy as np
from scipy import linalg
from . import parameter
import warnings
import copy


class GeometricDiffusionSingleAsset:
    def __init__(self,generator,r_param,vol_param):
        self.generator = generator.clone()
        self.r_param = r_param.clone()
        self.vol_param = vol_param.clone()

    def get_path_constants(self,time0,time1):
        """ get path constants within a time-window
        Args:
            - time0: beginning of time window
            - time1: end of time window
            - r_param: (of optionpricer.parameter type) interest rate parameter
            - vol_param: (of optionpricer.parameter type) volatility parameter
        Returns:
             - (r,var,mu,discount), where:
                 - r: interest rate in this time region
                 - var: variance in this time region
                 - mu: r-0.5*var in this time region
                 - discount: discount factor for time-vlaue of money in this time region
        """
        r = self.r_param.integral(time0,time1)
        # variance
        var = self.vol_param.square_integral(time0,time1)
        # risk neutral movement position
        mu = r - 0.5*var
        # discount to be applied due to time-value of money
        discount = np.exp(-r)
        return r,var,mu,discount

    def get_single_path(self,spot0,time0,time1):
        """ calculate a future spot value at a later time

        Args:
            - spot0: current spot
            - time0: initial time
            - time1: time at which to get future_spot
        Returns:
            - future_spot: value for spot at time1
        """
        r,var,mu,discount = self.get_path_constants(time0, time1)
        rand_val = self.generator.get_samples(1)
        future_spot = spot0*np.exp(mu)
        future_spot *= np.exp(np.sqrt(var)*rand_val)
        return future_spot

    def get_single_timed_path(self,spot0,times):
        """ calculate a future spot value on a list of futre times

        Args:
            - spot: current spot
            - times: times at which to get spot (from initial time to a final time)
        Returns:
            - future_spots: value for spot at times in 'times'
        """
        future_spots    = np.zeros_like(times)
        future_spots[0] = spot
        if isinstance(generator, Antithetic):
            print("Warning ( optionpricer.path.single_timed_path() ): generating a \
                   timed sequence with antithetic generator")
        for i in range(1,len(times)):
            r,var,mu,discount = self.get_path_constants(times[i-1], times[i])
            rand_vals = self.generator.get_samples(1)
            future_spots[i] = future_spots[i-1]*np.exp(mu)
            future_spots[i] *= np.exp(np.sqrt(var)*rand_vals)
        #future_spots *= discount
        return future_spots

    def get_many_paths(self,n_paths,spot0,time0, time1):
        """ calculate many future spot value at a later time

        Args:
            - n_paths: number of paths to calculate
            - spot0: current spot
            - time0: initial time
            - time1: time at which to get future_spot
        Returns:
            - future_spots: values for spot at time1
        """
        assert(n_paths>0)
        if n_paths==1:
            return self.get_single_path(spot0, time0, time1)
        r,var,mu,discount = self.get_path_constants(time0, time1)
        rand_vals = self.generator.get_samples(n_paths)
        #print("rands = ", rand_vals)
        future_spots = spot*np.exp(mu)
        future_spots *= np.exp(np.sqrt(var)*rand_vals)
        #future_spots *= discount
        return future_spots

    def get_many_timed_paths(self,n_paths,spot0,times):
        """ calculate many future spot value at a later time

        Args:
            - n_paths: number of paths to calculate
            - spot0: current spot
            - times: 1d array of times

        Returns:
            - future_spots: values for spot at time1
        """
        assert(n_paths>0)
        if n_paths==1:
            return self.get_single_timed_path(spot0, time0, time1)
        rand_vals    = self.generator.get_samples(n_samples=n_paths, sample_dimension=len(times))
        future_spots = np.zeros_like(rand_vals)
        future_spots[0,:] = spot0
        for i in range(1,len(times)):
            r,var,mu,discount = self.get_path_constants(times[i-1], times[i])
            #rand_vals = generator.get_samples(1)
            future_spots[i,:] = future_spots[i-1,:]*np.exp(mu)
            future_spots[i,:] *= np.exp(np.sqrt(var)*rand_vals[i-1,:])
        return future_spots

    def clone(self):
        return copy.deepcopy(self)


class GeometricDiffusionManyAsset:
    def __init__(self,generator,r_param,covariance_param,cholesky_param=None):
        self.generator = generator.clone()
        self.r_param = r_param.clone()
        self.covariance_param = covariance_param.clone()
        self.cholesky_param = cholesky_param.clone()
        if not self.cholesky_param.square:
            raise ValueError("cholesky_param should be square")
        self._n_assets = cholesky_param.shape[0]

    def get_path_constants(self,time0,time1):
        """ get path constants within a time-window
        Args:
            - time0: beginning of time window
            - time1: end of time window
        Returns:
             - (r,var,mu,discount), where:
                 - r: interest rate in this time region
                 - var: variance in this time region
                 - mu: r-0.5*var in this time region
                 - discount: discount factor for time-vlaue of money in this time region
        """
        r = self.r_param.integral(time0,time1)
        # variance
        vars = self.covariance_param.diag_integral(time0,time1)
        # risk neutral movement position
        mu = r - 0.5*vars
        # discount to be applied due to time-value of money
        discount = np.exp(-r)
        return r,vars,mu,discount

    def get_single_path(self,spots0,time0,time1):
        r,vars,mu,discount = self.get_path_constants(time0, time1)
        # get samples that are not antithetic or decorated
        rand_vals_standard = self.generator.get_simple_samples(len(spots0))
        if self.cholesky_param is None:
            chol = linalg.cholesky(self.covariance_param.mean(time0,time1),lower=True)
            self.cholesky_param = parameter.SimpleArrayParam(chol)
        rand_vals = np.dot(np.sqrt(self.cholesky_param.square_integral(time0,time1)),rand_vals_standard)
        #print(rand_vals, vars, np.exp(mu))
        future_spots = spots0*np.exp(mu)
        future_spots *= np.exp(rand_vals)
        return future_spots

    def get_single_timed_path(self,spots0,times):
        if (self.cholesky_param is not None and not isinstance(self.covariance_param,parameter.SimpleArrayParam)):
            warnings.warn("cholesky parameter has been set although covariance is time dependent - time dependence will be ignored")
        future_spots = np.zeros((len(times),len(spots0)))
        future_spots[0,:] = spots0
        for i in range(1,len(times)):
            future_spots[i,:] = self.get_single_path(future_spots[i-1,:],times[i-1],times[i])
        return future_spots

    def get_many_paths(self,n_paths,spots0,time0,time1):
        """

        returns size (len(spots), n_paths)
        """
        assert(n_paths>0)

        if self.cholesky_param is None:
            chol = linalg.cholesky(covariance_param.mean(time0,time1),lower=True)
            self.cholesky_param = parameter.SimpleArrayParam(chol)

        if n_paths==1:
            return self.get_single_path(spots,time0,time1)

        r,vars,mu,discount = self.get_path_constants(time0, time1)
        rand_vals0 = self.generator.get_samples(n_samples=n_paths,sample_dimension=len(spots))
        rand_vals = np.dot(np.sqrt(self.cholesky_param.square_integral(time0,time1)),rand_vals0)
        future_spots = spots0*np.exp(mu)
        future_spots = np.tile(future_spots[:,np.newaxis],(1,n_paths))
        future_spots *= np.exp(rand_vals)
        return future_spots

    def clone(self):
        return copy.deepcopy(self)


class JumpDiffusionSingleAsset:
    def __init__(self):
        raise NotImplementedError("JumpDiffusionSingleAsset in production")
