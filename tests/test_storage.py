#!/usr/bin/env python
""" Test Storage code"""

import unittest
from explorer.storage import Storage


##############################################################################
class TestSolarisStorage(unittest.TestCase):
    """ test storage class """
    def test_storage(self):
        """ Test solaris storage """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "solaris_host",
                }
        stor = Storage(config)
        stor.prettyPrint()
        self.assertEqual(
                stor, ''
        )


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
