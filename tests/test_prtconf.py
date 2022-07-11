#!/usr/bin/env python
""" Test prtconf code"""

import unittest
from explorer.prtconf import Prtconf


##############################################################################
class TestSolarisPrtconf(unittest.TestCase):
    """ test Prtconf class """
    def test_prtconf(self):
        """ Test solaris prtconf """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "solaris_host",
                }
        prtconf = Prtconf(config)
        self.assertEqual(prtconf['boot_aliases']['disk'], '/virtual-devices@100/channel-devices@200/disk@0')


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
