#!/usr/bin/env python
""" Test NIC code"""

import unittest
from explorer.nic import Nics


##############################################################################
class Test_nics(unittest.TestCase):
    """ test Nics class """
    def test_parse_solaris_ifconfig(self):
        """ Test parse_solaris_ifconfig """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "test_host",
                }
        nics = Nics(config)
        self.assertEqual(
            nics.data['vsw0'].data['interfaces']['vsw0']['ether'],
            '0:14:4f:fb:4c:82'
        )
        self.assertEqual(
            nics.data['aggr1'].data['interfaces']['aggr1']['ipaddr'],
            '10.64.51.12'
        )


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
