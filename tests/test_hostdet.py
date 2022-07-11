#!/usr/bin/env python
""" Test hostdet code"""

import unittest
from explorer.hostdet import Host


##############################################################################
class TestSolarisHostdet(unittest.TestCase):
    """ test hostdet class """
    def test_hostdet(self):
        """ Test solaris hostdet """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "solaris_host",
                }
        hostdet = Host(config)
        self.assertEqual(hostdet['arch'], 'sun4v')
        self.assertEqual(hostdet['ram'], '49152')
        self.assertEqual(hostdet['virtualmaster'], 'vhcvhaup004')
        self.assertEqual(hostdet['hardware'], 'sun_t8_2')


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
