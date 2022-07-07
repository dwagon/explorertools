#!/usr/bin/env python
""" Test Storage code"""

import unittest
from explorer.zfs import storageZfs


##############################################################################
class test_solaris_zfs(unittest.TestCase):
    """ test zfs class """
    def test_zfs(self):
        """ Test solaris zfs """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "test_host",
                }
        zfs = storageZfs(config, {})
        self.assertEqual(zfs['rpool/ROOT']['properties']['encryption'], 'off')
        self.assertEqual(zfs['zfspools'], {'rpool', 'swappool', 'datapool'})


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
