#!/usr/bin/env python
""" Test FMA code"""

import unittest
from explorer.fma import Fma


##############################################################################
class TestSolarisFma(unittest.TestCase):
    """ test Fma class """
    def test_fma(self):
        """ Test solaris fma """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "solaris_host",
                }
        fma = Fma(config)
        print(fma)


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
