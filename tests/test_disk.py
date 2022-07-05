#!/usr/bin/env python
""" Test NIC code"""

import unittest
from explorer.disks import Disks


##############################################################################
class Test_disks_solaris(unittest.TestCase):
    """ test Disks class """
    def test_disks(self):
        """ Test solaris disks """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "test_host",
                }
        disks = Disks(config)
        print(list(disks.diskList())[0])
        self.assertEqual(
                disks, ''
        )


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
