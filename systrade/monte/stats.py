
import numpy as np

def corr_to_cov(rho,sigma):
    """ take correlation and standard deviation and construct covariance """
    sigX,sigY = np.meshgrid(sigma,sigma)
    return rho*sigX*sigY
