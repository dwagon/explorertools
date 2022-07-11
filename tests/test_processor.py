#!/usr/bin/env python
""" Test kstat code"""

import unittest
from explorer.processor import Processors


##############################################################################
class TestSolarisProcessors(unittest.TestCase):
    """ test Processors class """
    def test_processors(self):
        """ Test solaris processors """
        config = {
                "explorertype": "solaris",
                "hostname": "testhost",
                "datadir": "test_data",
                "hostpath": "solaris_host",
                }
        procs = Processors(config)
        self.assertEqual(procs[0]['proctype'], 'sparcv9')
        self.assertEqual(procs[7]['speed'], '5067 MHz')


##############################################################################
if __name__ == "__main__":
    unittest.main()

# EOF
