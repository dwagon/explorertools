#!/usr/bin/env python
""" Test NIC code"""

import unittest
from explorer.nic import Nics


##############################################################################
class TestNics(unittest.TestCase):
    """test Nics class"""

    def test_parse_solaris_ifconfig(self):
        """Test parse_solaris_ifconfig"""
        config = {
            "explorertype": "solaris",
            "hostname": "testhost",
            "datadir": "test_data",
            "hostpath": "solaris_host",
        }
        nics = Nics(config)
        nics.prettyPrint()
        self.assertEqual(nics.data["lo0"].data["interfaces"]["lo0"]["mtu"], "8252")
        self.assertEqual(
            nics.data["net0"].data["interfaces"]["net0"]["ether"], "0:21:f6:79:89:aa"
        )


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
