#!/usr/bin/env python
""" Test Disks code"""

import unittest
from explorer.disks import storageDisks


##############################################################################
class test_solaris_storage(unittest.TestCase):
    """ test storage class """
    def test_storage(self):
        """ Test solaris storage """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "test_host",
                }
        stor = storageDisks(config)
        self.assertEqual(stor['c1d0s0']['disk'], 'c1d0')
        self.assertEqual(stor['c1d0s0']['first_sector'], 256)
        self.assertEqual(stor['c1d0']['slices'], {'c1d0s0', 'c1d0s8'})


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
