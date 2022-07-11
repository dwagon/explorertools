#!/usr/bin/env python
""" Test kstat code"""

import unittest
from explorer.misc import miscDetails


##############################################################################
class TestSolarisMisc(unittest.TestCase):
    """ test Misc class """
    def test_misc(self):
        """ Test solaris misc """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "solaris_host",
                }
        misc = miscDetails(config)
        self.assertEqual(misc['explorerversion'], '20.4')
        self.assertEqual(misc['eeprom']['boot-device'], 'disk0')
        self.assertEqual(misc['packages']['SUNWlibC'], "5.11,REV=2011.04.11")
        self.assertEqual(misc['processes']['21187']['cmd'], "/usr/lib/ssh/sshd")


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
