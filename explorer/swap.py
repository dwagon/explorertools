#!/usr/local/bin/python
#
# Script to understand swap details
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: swap.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/swap.py $

import os
import sys
import getopt
import re
import explorerbase
import storage

##########################################################################
# SwapThing ##############################################################
##########################################################################


class SwapThing(explorerbase.ExplorerBase):
    def __init__(self, config, swapvol, data, alldata):
        self.objname = swapvol
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def getNotes(self):
        return self["describer"]

    ##########################################################################
    def analyse(self):
        if self["devices"] and ("protected" not in self or not self["protected"]):
            self.addIssue("unprotected", obj=self.name(), text="Swap is not redundant")


##########################################################################
# Swap ###################################################################
##########################################################################


class Swap(explorerbase.ExplorerBase):
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.st = storage.Storage(config)
        for swp in self.st.keys():
            if "_type" in self.st[swp] and self.st[swp]["_type"] == "swap":
                self[swp] = SwapThing(config, swp, self.st[swp], self.st)
        self.analyse()

    ##########################################################################
    def swapList(self):
        return [self[sw] for sw in sorted(self.keys())]

    ##########################################################################
    def analyse(self):
        for swap in self.swapList():
            swap.analyse()
            self.inheritIssues(swap)


##########################################################################
# storageSwap ############################################################
##########################################################################


class storageSwap(explorerbase.ExplorerBase):

    """Understand explorer output with respect to swap"""

    ##########################################################################

    def __init__(self, config, data={}):
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.swapnum = 0
        self["_swap"] = storage.Storage.initialDict(
            {
                "_type": "allswap",
                "use": set(["_swap"]),
                "description": "Swap",
            }
        )
        self.parse()

    ##########################################################################
    def addLinux_swap(self, device, origin=None):
        name = "swap_%d" % self.swapnum
        self.swapnum += 1
        self[name] = storage.Storage.initialDict(
            {"_type": "swap", "use": set(["_swap"]), "partof": set(["_swap"])}
        )
        self[name]["contains"].add(device)
        self[name]["usepoint"] = device
        self[name]["description"] = "Swap"
        if origin:
            self[name]["_origin"] = origin
        self["swap_devices"].add(name)

    ##########################################################################
    def parseLinux_fstab(self):
        f = self.open("etc/fstab")
        for line in f:
            if "swap" not in line:
                continue
            bits = line.split()
            if bits[1] == "swap":
                device = self.sanitiseDevice(bits[0])
                self.addLinux_swap(device, origin="etc/fstab")

    ##########################################################################
    def parseSolaris_swap(self):
        """
        Analyse swap output
        """
        f = self.open("disks/swap-l.out")
        for line in f:
            line = line.rstrip()
            if line.startswith("swapfile"):
                continue
            if line.startswith("/dev/"):
                name = "swap_%d" % self.swapnum
                self.swapnum += 1
                bits = line.split()
                self["swap_devices"].add(name)
                self["_swap"]["contains"].add(name)
                device = self.sanitiseDevice(bits[0])
                self[name] = storage.Storage.initialDict(
                    {
                        "_type": "swap",
                        "_origin": "disks/swap-l.out",
                        "description": "Swap",
                        "contains": set([device]),
                        "partof": set(["_swap"]),
                        "usepoint": device,
                        "size": int(bits[3]) / 2,
                        "free": int(bits[4]) / 2,
                        "use": set(["_swap"]),
                    }
                )
        f.close()

    ##########################################################################
    def parseLinux_fdisk_chunk(self, lines):
        for line in lines:
            if "Linux swap" in line:
                bits = line.split()
                self.addLinux_swap(self.sanitiseDevice(bits[0]), origin="fdisk")

    ##########################################################################
    def parse(self):
        self["swap_devices"] = set()
        try:
            if self.config["explorertype"] == "solaris":
                self.parseSolaris_swap()
            elif self.config["explorertype"] == "linux":
                self.parseLinux_fdisk(self.parseLinux_fdisk_chunk)
                if not self["swap_devices"]:
                    self.parseLinux_fstab()
        except UserWarning as err:
            self.Warning(err)

    ##########################################################################
    def swapList(self):
        return self["swap_devices"]

    ##########################################################################
    def crossPopulate(self, data):
        for swap in self.swapList():
            # Tell all devices that have swap on them that they are used for
            # swap
            for dev in data[swap]["devices"]:
                data[dev]["use"].add(swap)
                if "protected" in data[dev]:
                    data[swap]["protected"] = data[dev]["protected"]
                data[dev]["name"] = "Swap"


# EOF
