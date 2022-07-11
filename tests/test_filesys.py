#!/usr/bin/env python
""" Test Filesystem code"""

import unittest
from explorer.filesys import storageFilesystems


##############################################################################
class TestSolarisFilesys(unittest.TestCase):
    """ test filesys class """
    def test_storagefilesys(self):
        """ Test solaris storage """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "solaris_host",
                }
        filesys = storageFilesystems(config)
        self.assertEqual(filesys['/var']['device'], 'rpool/ROOT/11.4.35.94.4/var')


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
