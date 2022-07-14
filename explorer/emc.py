#!/usr/bin/env python
"""
Script to understand emc drive details
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: emc.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/emc.py $

from explorer import explorerbase
from explorer import storage


##########################################################################
# EmcSlice ###############################################################
##########################################################################
class EmcSlice(explorerbase.ExplorerBase):
    """ TODO """
    def __init__(self, config, slic, data, alldata):
        """TODO"""
        self.objname = slic
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def is_backup_slice(self):
        """TODO"""
        return False

    ##########################################################################
    def get_sectors(self):
        """TODO"""
        return None, None, None

    ##########################################################################
    def get_notes(self):
        """TODO"""
        return " "
        # return self["describer"]


##########################################################################
# EmcDisk ################################################################
##########################################################################
class EmcDisk(explorerbase.ExplorerBase):
    """EMC Disk"""

    def __init__(self, config, disk, data, alldata):
        """TODO"""
        self.objname = disk
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def unused_disk(self):
        """TODO"""
        return self["unused"]

    ##########################################################################
    def slice_list(self):
        """TODO"""
        slices = sorted(self["slices"])
        return [self[s] for s in slices]


##########################################################################
# EmcDisks ###############################################################
##########################################################################
class EmcDisks(explorerbase.ExplorerBase):
    """EMC Disks"""

    def __init__(self, config):
        """TODO"""
        explorerbase.ExplorerBase.__init__(self, config)
        self.strg = storage.Storage(config)
        for objname, obj in self.strg.items():
            if "_type" in obj and obj["_type"] == "emcdisk":
                emcdisk = objname
                self[emcdisk] = EmcDisk(config, emcdisk, obj, self.strg)
                for emcslice in self[emcdisk]["slices"]:
                    self[emcdisk][emcslice] = EmcSlice(
                        config, emcslice, self.strg[emcslice], self.strg
                    )

    ##########################################################################
    def disk_list(self):
        """TODO"""
        disks = sorted(self.keys())
        return [self[d] for d in disks]


##########################################################################
# storageEmc #############################################################
##########################################################################
class StorageEmc(explorerbase.ExplorerBase):
    """Class to represent all EMC arrays within a system based on data from
    Explorers
    """

    ##########################################################################

    def __init__(self, config, data=None):
        """TODO"""
        explorerbase.ExplorerBase.__init__(self, config)
        if data is None:
            data = {}
        self.data = data
        self.paths = {}
        self.parse()

    ##########################################################################
    def parse(self):
        """TODO"""
        self["emcdisks"] = set()
        try:
            if self.config["explorertype"] == "solaris":
                self.parse_solaris()
            elif self.config["explorertype"] == "linux":
                self.parse_linux()
        except UserWarning as err:
            self.warning(err)
        self.protection_check()

    ##########################################################################
    def calculate_used(self, data):
        """
        Check to see if the disks are actually used
        """
        for disk in self.disk_list():
            # If the entire disk has a use then we don't need to check slices
            if data[disk]["use"]:
                data[disk]["unused"] = False
                continue
            used = False
            for slic in data[disk]["slices"]:
                # Boot Partition always exists
                if data[slic]["slicenum"] in ("8", "i"):
                    continue
                if data[slic]["use"]:
                    used = True
                    break
            if not used:
                data[disk]["unused"] = True
            else:
                data[disk]["unused"] = False

    ##########################################################################
    def parse_linux(self):
        """TODO"""
        self.parse_linux_partitions()
        self.parse_linux_fdisk(self.parse_linux_fdisk_chunk)

    ##########################################################################
    def parse_linux_partitions(self):
        """TODO"""
        filename = "proc/partitions"
        infh = self.open(filename)
        for line in infh:
            if "emcpower" in line:
                emc = line.split()[3]
                if emc[-1].isdigit():
                    self.add_emc_slice(emc, origin=filename)
                else:
                    self.add_emc_disk(emc, origin=filename)
        infh.close()

    ##########################################################################
    def parse_linux_fdisk_chunk(self, lines):
        """TODO"""

    ##########################################################################
    def parse_solaris(self):
        """TODO"""
        self.parse_solaris_emc()
        self.parse_solaris_mnttab()
        self.parse_solaris_swap()
        self.parse_solaris_vxvm()

    ##########################################################################
    def parse_solaris_vxvm(self):
        """TODO"""
        filename = "disks/vxvm/vxdisk-list.out"
        if not self.exists(filename):
            return
        infh = self.open(filename)
        for line in infh:
            bits = line.strip().split()
            if "emcpower" in bits[-1]:
                self.add_emc_slice(bits[-1], origin=filename)
        infh.close()

    ##########################################################################
    def parse_solaris_swap(self):
        """The real details will be found by the swap checker,
        we just need to set up the emc slices that are in use for
        the relationship handling"""

        filename = "disks/swap-l.out"
        if not self.exists(filename):
            return
        infh = self.open(filename)
        for line in infh:
            if "emcpower" in line:
                self.add_emc_slice(line.split()[0], origin=filename)
        infh.close()

    ##########################################################################
    def parse_solaris_mnttab(self):
        """The real details will be found by the filesystem checker,
        we just need to set up the emc slices that are in use for
        the relationship handling"""

        filename = "etc/mnttab"
        if not self.exists(filename):
            return
        infh = self.open(filename)
        for line in infh:
            if "emcpower" in line:
                self.add_emc_slice(line.split()[0], origin=filename)
        infh.close()

    ##########################################################################
    def add_emc_slice(self, device, origin=""):
        """TODO"""
        emcslice = self.sanitiseDevice(device)
        if emcslice not in self or self[emcslice]["_type"] != "emcslice":
            emcdisk = emcslice[:-1]
            if emcdisk not in self:
                self.add_emc_disk(emcdisk, origin)
            if emcslice[-1].isdigit():
                slicenum = int(emcslice[-1])
            else:
                slicenum = ord(emcslice[-1]) - ord("a")
            self[emcslice] = storage.Storage.initial_dict(
                {
                    "_type": "emcslice",
                    "_origin": origin,
                    "description": "EMC Slice",
                    "partof": set([emcdisk]),
                    "slicenum": slicenum,
                }
            )
            self[emcdisk]["slices"].add(emcslice)

    ##########################################################################
    def add_emc_disk(self, disk, origin=""):
        """TODO"""
        self[disk] = storage.Storage.initial_dict(
            {
                "_type": "emcdisk",
                "description": "EMC Drive",
                "slices": set(),
                "paths": set(),
                "_origin": origin,
                "have_cylinders": False,
                "protected": "EMC",
            }
        )
        self["emcdisks"].add(disk)

    ##########################################################################
    def parse_solaris_emc(self):
        """Analyse EMC powerpath config file
        The looks like a series of:

            Pseudo name=emcpower0a
            CLARiiON ID=C10023500010 [Zeus]
            Logical device ID=600601F2F5570000CFD82C659024D911 [LUN 10]
            state=alive; policy=BasicFailover; priority=0; queued-IOs=1
            Owner: default=SP B, current=SP B
            ==============================================================================
            ---------------- Host ---------------   - Stor -   -- I/O Path -  -- Stats ---
            ###  HW Path                I/O Paths    Interf.   Mode    State  Q-IOs Errors
            ==============================================================================
            2304 ssm@0,0/pci@19,700000/lpfc@2 c2t0d0s0  SP A1     active  alive      0      0
            2304 ssm@0,0/pci@19,700000/lpfc@2 c2t1d0s0  SP B1     active  alive      1      0
            2305 ssm@0,0/pci@19,600000/lpfc@1 c3t0d0s0  SP A0     unlic   alive      0      0
            2305 ssm@0,0/pci@19,600000/lpfc@1 c3t1d0s0  SP B0     unlic   alive      0      0

        In this case
        emcpower0a -> c2t0d0s0/c2t1d0s0
        emcpower0b -> c2t0d0s1/c2t1d0s1
        emcpower0h -> c2t0d0s7/c2t1d0s7
        ...
        """
        filename = "emc/powermt_display_dev=all.out"
        if not self.exists(filename):
            return
        infh = self.open(filename)
        emcpower = None

        for line in infh:
            line = line.strip()
            if not line:
                continue
            if emcpower and emcpower not in self:
                self.add_emc_disk(emcpower, origin=filename)

            if line.startswith("Pseudo name"):
                emcpower = line.split("=")[-1][:-1]
                continue

            if line[0].isdigit():
                if not emcpower:
                    self.warning(f"No emcpower device discovered for {line}")
                    continue
                try:
                    dpath = line.split()[2][:-2]  # Strip off slice number
                except IndexError:
                    continue
                if dpath.startswith("c"):
                    self[emcpower]["paths"].add(dpath)
                self.paths[dpath] = emcpower

        infh.close()

    ##########################################################################
    def describer(self, obj, data):
        """TODO"""

    ##########################################################################
    def protection_check(self):
        """If a disk from the drivemap is listed as protected, then
        mark it as such"""
        # TO DO

    ##########################################################################
    def disk_list(self):
        """TODO"""
        return sorted(self["emcdisks"])

    ##########################################################################
    def cross_populate(self, data):
        """TODO"""
        # Look for partitions that live on disks that are EMC Power'd
        for obj in data.copy():
            if isinstance(data[obj], str):
                continue

            if "disk" in data[obj] and data[obj]["disk"] in self.paths:
                disk = data[obj]["disk"]
                data[disk]["emc"] = True
                slic = obj[-1]
                if slic == "8":  # Boot partition - ignorable
                    continue
                emcdisk = self.paths[disk]
                emcslice = emcdisk + chr(int(slic) + ord("a"))
                if emcslice not in self:
                    self[emcslice] = storage.Storage.initial_dict(
                        {
                            "_type": "emcslice",
                            "description": "EMC Slice",
                            "partof": set([emcdisk]),
                            "slicenum": chr(int(slic) + ord("a")),
                        }
                    )
                    self[emcdisk]["slices"].add(emcslice)
                self[emcslice]["contains"].add(obj)
                self[emcslice]["contains"].add(disk)

            if "emcpower" in obj:
                if "emc" not in data[obj]["_type"]:
                    self.debug(f"Missed data[{obj}] {data[obj]}")


# EOF
