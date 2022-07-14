"""
Script to understand swap details
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: swap.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/swap.py $

from explorer import explorerbase
from explorer import storage


##########################################################################
# SwapThing ##############################################################
##########################################################################
class SwapThing(explorerbase.ExplorerBase):
    """ Swap """
    def __init__(self, config, swapvol, data, alldata):
        self.objname = swapvol
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def getNotes(self):
        """ TODO """
        return self["describer"]

    ##########################################################################
    def analyse(self):
        """ TODO """
        if self["devices"] and ("protected" not in self or not self["protected"]):
            self.add_issue("unprotected", obj=self.name(), text="Swap is not redundant")


##########################################################################
# Swap ###################################################################
##########################################################################
class Swap(explorerbase.ExplorerBase):
    """ Swap """
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.st = storage.Storage(config)
        for swp in self.st.keys():
            if "_type" in self.st[swp] and self.st[swp]["_type"] == "swap":
                self[swp] = SwapThing(config, swp, self.st[swp], self.st)
        self.analyse()

    ##########################################################################
    def swap_list(self):
        """ TODO """
        return [self[sw] for sw in sorted(self.keys())]

    ##########################################################################
    def analyse(self):
        """ TODO """
        for swap in self.swap_list():
            swap.analyse()
            self.inherit_issues(swap)


##########################################################################
# storageSwap ############################################################
##########################################################################
class StorageSwap(explorerbase.ExplorerBase):
    """Understand explorer output with respect to swap"""

    ##########################################################################
    def __init__(self, config, data=None):
        if data is None:
            data = {}
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.swapnum = 0
        self["_swap"] = storage.Storage.initial_dict(
            {
                "_type": "allswap",
                "use": set(["_swap"]),
                "description": "Swap",
            }
        )
        self.parse()

    ##########################################################################
    def add_linux_swap(self, device, origin=None):
        """ TODO """
        name = f"swap_{self.swapnum}"
        self.swapnum += 1
        self[name] = storage.Storage.initial_dict(
            {"_type": "swap", "use": set(["_swap"]), "partof": set(["_swap"])}
        )
        self[name]["contains"].add(device)
        self[name]["usepoint"] = device
        self[name]["description"] = "Swap"
        if origin:
            self[name]["_origin"] = origin
        self["swap_devices"].add(name)

    ##########################################################################
    def parse_linux_fstab(self):
        """ TODO """
        infh = self.open("etc/fstab")
        for line in infh:
            if "swap" not in line:
                continue
            bits = line.split()
            if bits[1] == "swap":
                device = self.sanitiseDevice(bits[0])
                self.add_linux_swap(device, origin="etc/fstab")

    ##########################################################################
    def parse_solaris_swap(self):
        """
        Analyse swap output
        """
        infh = self.open("disks/swap-l.out")
        for line in infh:
            line = line.rstrip()
            if line.startswith("swapfile"):
                continue
            if line.startswith("/dev/"):
                name = f"swap_{self.swapnum}"
                self.swapnum += 1
                bits = line.split()
                self["swap_devices"].add(name)
                self["_swap"]["contains"].add(name)
                device = self.sanitiseDevice(bits[0])
                self[name] = storage.Storage.initial_dict(
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
        infh.close()

    ##########################################################################
    def parse_linux_fdisk_chunk(self, lines):
        """ TODO """
        for line in lines:
            if "Linux swap" in line:
                bits = line.split()
                self.add_linux_swap(self.sanitiseDevice(bits[0]), origin="fdisk")

    ##########################################################################
    def parse(self):
        """ TODO """
        self["swap_devices"] = set()
        try:
            if self.config["explorertype"] == "solaris":
                self.parse_solaris_swap()
            elif self.config["explorertype"] == "linux":
                self.parse_linux_fdisk(self.parse_linux_fdisk_chunk)
                if not self["swap_devices"]:
                    self.parse_linux_fstab()
        except UserWarning as err:
            self.warning(err)

    ##########################################################################
    def swap_list(self):
        """ TODO """
        return self["swap_devices"]

    ##########################################################################
    def cross_populate(self, data):
        """ TODO """
        for swap in self.swap_list():
            # Tell all devices that have swap on them that they are used for
            # swap
            for dev in data[swap]["devices"]:
                data[dev]["use"].add(swap)
                if "protected" in data[dev]:
                    data[swap]["protected"] = data[dev]["protected"]
                data[dev]["name"] = "Swap"


# EOF
