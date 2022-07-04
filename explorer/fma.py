#!/usr/bin/env python3
"""
Script to understand fma output for explorer analysis
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: fma.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/fma.py $

import explorerbase

##########################################################################
# Fma ####################################################################
##########################################################################


class Fma(explorerbase.ExplorerBase):
    """Understand explorer output with respect to fma"""

    ##########################################################################
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        if not self.exists("fma/fmadm-config.out"):
            return
        self.parseFmadm()

    ##########################################################################
    def analyse(self):
        """TODO"""

    ##########################################################################
    # --------------- ------------------------------------  -------------- ---
    # TIME            EVENT-ID                              MSG-ID         SEVERITY
    # --------------- ------------------------------------  -------------- ---
    # Jan 29 13:14:19 f4f4fac3-529d-430f-c480-e4cd41f60e19  AMD-8000-7U    Major
    #
    # or
    #
    #   STATE RESOURCE / UUID
    #   -------- -------------------------------------------------------------
    #   degraded mem:///motherboard=0/chip=0/memory-controller=0/dimm=3/rank=0
    ##########################################################################
    def parseFmadm(self):
        """TODO"""
        f = self.open("fma/fmadm-faulty-a.out")
        buff = []  # Error excluding headers
        mode = None

        for line in f:
            line = line.rstrip()
            if line.startswith("TIME"):
                mode = "TIME"
                continue
            elif "RESOURCE" in line:
                mode = "RESOURCE"
                continue

            if "--------" in line:
                if buff:
                    self.addFma(buff, mode)
                    buff = []
            else:
                buff.append(line.strip())
        f.close()
        if buff:
            self.addFma(buff, mode)

    ##########################################################################
    def addFma(self, buff, mode):
        """TODO"""
        if mode == "TIME":
            subcat = buff[0].split()[-1].strip()
        if mode == "RESOURCE":
            subcat = buff[0].split()[0].strip()
        self.addIssue(subcat, obj=buff[0], text=buff)


# EOF
