import unittest
import numpy as np
from scipy.stats import lognorm
import NumpyTestCase
from quantileMapping import qdm

np.random.seed(seed=233423)

class TestQDM(NumpyTestCase.NumpyTestCase):
    badinput = 0.5
    nanarray = np.array([1,2,3,4,np.nan])
    
    obsdist = lognorm.rvs(0.57, size=100)
    obsp = lognorm.fit(obsdist)
    refdist = lognorm.rvs(0.45, size=100)
    refp = lognorm.fit(refdist)
    futdist = lognorm.rvs(0.55, size=100)
    futp = lognorm.fit(futdist)
    x = np.linspace(0, 1, 101)
    qobs = np.quantile(obsdist, x)
    qref = np.quantile(refdist, x)
    qfut = np.quantile(futdist, x)

    def testQDMInput(self):
        """Test input is array-like"""
        self.assertRaises(TypeError, qdm, 0.5, 0.5, 0.5)

    def testQDMNanInput(self):
        """Test input array has no nan values"""
        self.assertRaises(ValueError, qdm, self.nanarray,
                          self.nanarray, self.nanarray)
    
    def testRefInput(self):
        """Test using reference data as future returns obs dist params"""
        testqfut = qdm(self.obsdist, self.refdist, self.refdist)
        testp = lognorm.fit(testqfut)
        self.assertAlmostEqual(self.obsp[0], testp[0], places=2)
        self.assertAlmostEqual(self.obsp[1], testp[1], places=2)
        self.assertAlmostEqual(self.obsp[2], testp[2], places=2)


if __name__ == "__main__":
    #flStartLog('', 'CRITICAL', False)
    testSuite = unittest.makeSuite(TestQDM,'test')
    unittest.TextTestRunner(verbosity=2).run(testSuite)
