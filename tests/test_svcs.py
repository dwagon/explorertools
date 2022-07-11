#!/usr/bin/env python
""" Test svcs code"""

import unittest
from explorer.svcs import Svcs


##############################################################################
class TestSolarisSvcs(unittest.TestCase):
    """ test Svcs class """
    def test_svcs(self):
        """ Test solaris svcs """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "solaris_host",
                }
        svc = Svcs(config)
        svc.prettyPrint()


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
