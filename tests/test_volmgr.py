#!/usr/bin/env python
""" Test Storage code"""

import unittest
from explorer.volmanager import storageVolmanager


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
        stor = storageVolmanager(config)
        self.assertEqual(stor['d10']['_type'], 'disksuite')
        self.assertEqual(stor['d10']['type'], 'mirror')
        self.assertEqual(stor['d10']['devdesc'], 'Submirrors: /dev/md/rdsk/d116')


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
