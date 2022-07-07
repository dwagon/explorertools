#!/usr/bin/env python
""" Test Storage code"""

import unittest
from explorer.swap import storageSwap


##############################################################################
class test_solaris_swap(unittest.TestCase):
    """ test storage class """
    def test_swap(self):
        """ Test solaris storage """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "test_host",
                }
        swap = storageSwap(config)
        self.assertEqual(swap['swap_devices'], {'swap_0', 'swap_1'})
        self.assertEqual(swap['_swap']['contains'], {'swap_0', 'swap_1'})


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
