#!/usr/bin/env python
""" Test Zone code"""

import unittest
from explorer.zones import Zones


##############################################################################
class TestSolarisZones(unittest.TestCase):
    """ test zone class """
    def test_zone(self):
        """ Test solaris zone """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "solaris_host",
                }
        zon = Zones(config)
        zon.prettyPrint()
        # self.assertEqual(zon['d10']['_type'], 'disksuite')
        # self.assertEqual(zon['d10']['type'], 'mirror')
        # self.assertEqual(zon['d10']['devdesc'], 'Submirrors: /dev/md/rdsk/d116')


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
