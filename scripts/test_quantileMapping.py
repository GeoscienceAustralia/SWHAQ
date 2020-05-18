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
    refdist = lognorm.rvs(0.45, size=100)
    futdist = lognorm.rvs(0.55, size=100)
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
        """Test using reference data as future returns obs"""
        testqfut = qdm(self.obsdist, self.refdist, self.refdist)
        print(np.sort(testqfut))
        print(np.sort(self.obsdist))
        print(np.sort(self.obsdist) - np.sort(testqfut))
        self.numpyAssertAlmostEqual(self.qobs, np.quantile(testqfut, self.x))

if __name__ == "__main__":
    #flStartLog('', 'CRITICAL', False)
    testSuite = unittest.makeSuite(TestQDM,'test')
    unittest.TextTestRunner(verbosity=2).run(testSuite)
