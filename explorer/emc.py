#!/usr/bin/env python
"""
Script to understand emc drive details
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: emc.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/emc.py $

import explorerbase
import storage


##########################################################################
# EmcSlice ###############################################################
##########################################################################
class EmcSlice(explorerbase.ExplorerBase):
    def __init__(self, config, slic, data, alldata):
        """ TODO """
        self.objname = slic
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def isBackupSlice(self):
        """ TODO """
        return False

    ##########################################################################
    def getSectors(self):
        """ TODO """
        return None, None, None

    ##########################################################################
    def getNotes(self):
        """ TODO """
        return " "
        # return self["describer"]


##########################################################################
# EmcDisk ################################################################
##########################################################################
class EmcDisk(explorerbase.ExplorerBase):
    """ EMC Disk """
    def __init__(self, config, disk, data, alldata):
        """ TODO """
        self.objname = disk
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def unusedDisk(self):
        """ TODO """
        return self["unused"]

    ##########################################################################
    def sliceList(self):
        """ TODO """
        slices = sorted(self["slices"])
        return [self[s] for s in slices]


##########################################################################
# EmcDisks ###############################################################
##########################################################################
class EmcDisks(explorerbase.ExplorerBase):
    """ EMC Disks """
    def __init__(self, config):
        """ TODO """
        explorerbase.ExplorerBase.__init__(self, config)
        self.st = storage.Storage(config)
        for objname, obj in self.st.items():
            if "_type" in obj and obj["_type"] == "emcdisk":
                emcdisk = objname
                self[emcdisk] = EmcDisk(config, emcdisk, obj, self.st)
                for emcslice in self[emcdisk]["slices"]:
                    self[emcdisk][emcslice] = EmcSlice(
                        config, emcslice, self.st[emcslice], self.st
                    )

    ##########################################################################
    def diskList(self):
        """ TODO """
        disks = sorted(self.keys())
        return [self[d] for d in disks]


##########################################################################
# storageEmc #############################################################
##########################################################################
class storageEmc(explorerbase.ExplorerBase):
    """Class to represent all EMC arrays within a system based on data from
    Explorers
    """

    ##########################################################################

    def __init__(self, config, data={}):
        """ TODO """
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.paths = {}
        self.parse()

    ##########################################################################
    def parse(self):
        """ TODO """
        self["emcdisks"] = set()
        try:
            if self.config["explorertype"] == "solaris":
                self.parse_Solaris()
            elif self.config["explorertype"] == "linux":
                self.parse_Linux()
        except UserWarning as err:
            self.Warning(err)
        self.protectionCheck()

    ##########################################################################
    def calculateUsed(self, data):
        """
        Check to see if the disks are actually used
        """
        for disk in self.diskList():
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
    def parse_Linux(self):
        """ TODO """
        self.parse_Linux_partitions()
        self.parseLinux_fdisk(self.parse_Linux_fdisk_chunk)

    ##########################################################################
    def parse_Linux_partitions(self):
        """ TODO """
        filename = "proc/partitions"
        f = self.open(filename)
        for line in f:
            if "emcpower" in line:
                emc = line.split()[3]
                if emc[-1].isdigit():
                    self.addEmcSlice(emc, origin=filename)
                else:
                    self.addEmcDisk(emc, origin=filename)
        f.close()

    ##########################################################################
    def parse_Linux_fdisk_chunk(self, lines):
        """ TODO """
        pass

    ##########################################################################
    def parse_Solaris(self):
        """ TODO """
        self.parse_Solaris_emc()
        self.parse_Solaris_mnttab()
        self.parse_Solaris_swap()
        self.parse_Solaris_vxvm()

    ##########################################################################
    def parse_Solaris_vxvm(self):
        """ TODO """
        filename = "disks/vxvm/vxdisk-list.out"
        if not self.exists(filename):
            return
        f = self.open(filename)
        for line in f:
            bits = line.strip().split()
            if "emcpower" in bits[-1]:
                self.addEmcSlice(bits[-1], origin=filename)
        f.close()

    ##########################################################################
    def parse_Solaris_swap(self):
        """The real details will be found by the swap checker,
        we just need to set up the emc slices that are in use for
        the relationship handling"""

        filename = "disks/swap-l.out"
        if not self.exists(filename):
            return
        f = self.open(filename)
        for line in f:
            if "emcpower" in line:
                self.addEmcSlice(line.split()[0], origin=filename)
        f.close()

    ##########################################################################
    def parse_Solaris_mnttab(self):
        """The real details will be found by the filesystem checker,
        we just need to set up the emc slices that are in use for
        the relationship handling"""

        filename = "etc/mnttab"
        if not self.exists(filename):
            return
        f = self.open(filename)
        for line in f:
            if "emcpower" in line:
                self.addEmcSlice(line.split()[0], origin=filename)
        f.close()

    ##########################################################################
    def addEmcSlice(self, device, origin=""):
        """ TODO """
        emcslice = self.sanitiseDevice(device)
        if emcslice not in self or self[emcslice]["_type"] != "emcslice":
            emcdisk = emcslice[:-1]
            if emcdisk not in self:
                self.addEmcDisk(emcdisk, origin)
            if emcslice[-1].isdigit():
                slicenum = int(emcslice[-1])
            else:
                slicenum = ord(emcslice[-1]) - ord("a")
            self[emcslice] = storage.Storage.initialDict(
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
    def addEmcDisk(self, disk, origin=""):
        """ TODO """
        self[disk] = storage.Storage.initialDict(
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
    def parse_Solaris_emc(self):
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
        f = self.open(filename)
        emcpower = None

        for line in f:
            line = line.strip()
            if not line:
                continue
            if emcpower and emcpower not in self:
                self.addEmcDisk(emcpower, origin=filename)

            if line.startswith("Pseudo name"):
                emcpower = line.split("=")[-1][:-1]
                continue

            if line[0].isdigit():
                if not emcpower:
                    self.Warning("No emcpower device discovered for %s" % line)
                    continue
                try:
                    dpath = line.split()[2][:-2]  # Strip off slice number
                except IndexError:
                    continue
                if dpath.startswith("c"):
                    self[emcpower]["paths"].add(dpath)
                self.paths[dpath] = emcpower

        f.close()

    ##########################################################################
    def describer(self, obj, data):
        """ TODO """
        pass

    ##########################################################################
    def protectionCheck(self):
        """If a disk from the drivemap is listed as protected, then
        mark it as such"""
        # TODO

    ##########################################################################
    def diskList(self):
        """ TODO """
        return sorted(self["emcdisks"])

    ##########################################################################
    def cross_populate(self, data):
        """ TODO """
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
                    self[emcslice] = storage.Storage.initialDict(
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
                    self.Debug("Missed data[%s] %s" % (obj, data[obj]))


# EOF
