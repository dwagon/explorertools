#!/usr/bin/env python
""" Test prtdiag code"""

import unittest
from explorer.prtdiag import Prtdiag


##############################################################################
class TestSolarisPrtdiag(unittest.TestCase):
    """ test Prtdiag class """
    def test_prtdiag(self):
        """ Test solaris prtdiag """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "solaris_host",
                }
        prtdiag = Prtdiag(config)
        prtdiag.prettyPrint()
        # Needs more work


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
