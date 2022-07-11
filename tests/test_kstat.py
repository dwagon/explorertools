#!/usr/bin/env python
""" Test kstat code"""

import unittest
from explorer.kstat import Kstat


##############################################################################
class TestSolarisKstat(unittest.TestCase):
    """ test Kstat class """
    def test_kstat(self):
        """ Test solaris kstat """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "solaris_host",
                }
        kst = Kstat(config)
        self.assertEqual(kst['cpu']['sys']['0']['cpu_ticks_kernel'], '31644646')


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
