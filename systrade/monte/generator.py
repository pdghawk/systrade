""" Module for statistal/random number generators
"""
import numpy as np
import copy

class Normal:
    """ object for generating random normally distributed numbers"""
    def __init__(self,mean=0.0,var=1.0):
        self.mean = mean
        self.var  = var

    def get_samples(self,n_samples=1):
        """ get samples from normally distributed samples
        Keyword Args:
            - n_samples: number of samples to get (defaults to 1)
        Returns:
            normally distributed samples, n_samples in number
        """
        return np.random.normal(self.mean,self.var,n_samples)

    def clone(self):
        return copy.deepcopy(self)

    get_simple_samples = get_samples


class Antithetic:
    """ generate antithetic distributions

    Uses another generator class to get the statistical distribution type, but
    outputs the results so that the samples are antithetic
    """
    def __init__(self,gen):
        self._negate     = False
        self._generator  = gen.clone()
        self.last_sample = None

    def get_samples(self,n_samples=1,sample_dimension=1):
        """ get samples from the distribution

        Keyword Args:
            - n_samples: number of samples to get (defaults to 1)
            - sample_dimension: number of random variables per sample to get (defaults to 1)
        Returns:
            antithetic samples according to self._generators distribution, n_samples in number
        """
        assert(n_samples>0)
        assert(sample_dimension>=1)
        if sample_dimension==1:
            if (n_samples == 1 and not self._negate):
                samples = self.generator.get_samples(n_samples)
                self._negate = not self._negate
                self.last_sample = samples
                return samples
            elif (n_samples == 1 and self._negate):
                samples = -self.last_sample
                self._negate = not self._negate
                self.last_sample = samples
                return samples
            else:
                # get a certain number, and then repeat them, but negative
                # negate parameter should be swapped depending on n_sampeles even/odd
                samples = np.zeros((n_samples,))
                if n_samples%2==0:
                    n_get    = n_samples//2
                else:
                    n_get    = n_samples//2+1

                samples[:n_get] = self._generator.get_samples(n_get)
                samples[n_get:] = -samples[:(n_samples-n_get)]

                self.last_sample = None
                self._negate = False

                return samples
        else:
            if (n_samples == 1 and not self._negate):
                samples = self.generator.get_samples(sample_dimension)
                self._negate = not self._negate
                self.last_sample = samples
                return samples
            elif (n_samples == 1 and self._negate):
                samples = -self.last_sample
                self._negate = not self._negate
                self.last_sample = samples
                return samples
            else:
                # get a certain number, and then repeat them, but negative
                # negate parameter should be swapped depending on n_sampeles even/odd
                samples = np.zeros((sample_dimension,n_samples))
                if n_samples%2==0:
                    n_get    = n_samples//2
                else:
                    n_get    = n_samples//2+1

                samples[:,:n_get] = np.reshape(self._generator.get_samples(n_get*sample_dimension),(sample_dimension,n_get))
                samples[:,n_get:] = -samples[:,:(n_samples-n_get)]

                self.last_sample = None
                self._negate = False

                return samples



    def get_simple_samples(self,n_samples=1):
        return self._generator.get_samples(n_samples)

    def clone(self):
        return copy.deepcopy(self)
