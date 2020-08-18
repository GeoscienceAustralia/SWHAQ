#!/usr/bin/env python
# coding: utf-8

"""
:mod: `qdm` -- Quantile Delta Mapping 
=====================================

..:mod: qdm
    :synopsis: Apply quantile delta mapping. 


.. moduleauthor:: Craig Arthur, <craig.arthur@ga.gov.au

Cannon _et al._ (2015) describe a method for bias correction of climate
variables that conserves relative changes in quantiles between current and
future climate regimes. Called Quantile Delta Mapping (QDM), the method ensures
that climate sensitivity of the underlying climate model remains unaffected by
the correction process.

This is a Python wrapper for the QDM function in the `MBC` package for R, see
https://rdrr.io/cran/MBC/man/MBC-package.html for details on the `MBC` package.

Dependencies::

* `rpy2`
* `MBC`
* `numpy`

Cannon, A.J., Sobie, S.R., and Murdock, T.Q. 2015. Bias correction of simulated
precipitation by quantile mapping: How well do methods preserve relative changes
in quantiles and extremes? Journal of Climate, 28: 6938-6959.
doi:10.1175/JCLI-D-14-00754.1

"""

import numpy as np
import rpy2.robjects as ro
from rpy2.robjects.packages import importr

from rpy2.robjects import numpy2ri
numpy2ri.activate()

# Use the R implementation of QDM provided by the MBC package
MBC = importr("MBC")


def qdm(obs, ref, fut, ratio=True, trace=0.1, n=None):
    """
    Calculate the quantile delta mapping for a collection of simulated data. 

    This function is based on the formulation described in Cannon _et al._
    (2015) and Heo _et al._ (2019), where the relative change in quantiles 
    between a reference period and the future period are preserved.

    $\delta_{fut} = \dfrac{Q_{fut}}{F_{ref}^{-1}\left[ F_{fut} ( Q_{fut} ) \right]} $ 

    $Q_{futb} = F_{obs}^{-1} \left[ F_{fut} (Q_{fut}) \right] \times \delta_{fut} $

    $\delta_{fut}$ is the relative change in the quantiles between the simulated
    reference data ('sreftclv') and the simulated future data ('sfuttclv').
    $Q_{fut}$ is the quantile of the simulated future data. $F_{fut}$ and
    $F_{ref}^{-1}$ are a CDF of the simulated future data and an inverse CDF of
    the simulated reference data respectively. Finally, $F_{obs}^{-1}$ is the
    inverse CDF of the observed data, and $Q_{futb}$ are the corrected quantiles
    of the future data.

    In this framework, the algorithm is independent of the selection of
    distribution, which would be data-dependent, and more generally specific to
    the variable that is being corrected. We begin by fitting a lognormal
    distribution to the $\Delta p_c$ values in each of the observed, reference and
    future collections. 

    :param obs: `numpy.array` of observed values 
    :param ref: `numpy.array` of reference period values (simulated) 
    :param fut: `numpy.array` of future period values (simulated) 
    :param bool ratio: True if the variable is a ratio variable. False
    otherwise.
    :param float trace: numeric value indicating the threshold below which
    values of a ratio quantity (e.g., ratio=True) should be considered exact
    zeros.
    :param int n: Number of quantiles used in the quantile mapping; `None`
    equals the length of the `fut` series.


    :returns: `mhatp` a `numpy.array` of bias corrected future values.

    """

    if not isinstance(obs, (list, np.ndarray,)):
        raise TypeError("Incorrect input type for observed values")
    if not isinstance(ref, (list, np.ndarray,)):
        raise TypeError("Incorrect input type for reference period values")
    if not isinstance(fut, (list, np.ndarray,)):
        raise TypeError("Incorrect input type for future period values")

    if any(np.isnan(obs)):
        raise ValueError("Input observation array contains NaN values")
    if any(np.isnan(ref)):
        raise ValueError("Input reference array contains NaN values")
    if any(np.isnan(fut)):
        raise ValueError("Input future array contains NaN values")

    if n:
        n_tau = n
    else:
        n_tau = len(fut)

    mhatc, mhatp = MBC.QDM(obs, ref, fut, ratio, trace, n_tau=n_tau)

    return np.array(mhatc), np.array(mhatp)
