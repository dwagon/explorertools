#!/usr/bin/env python
"""
Script to understand disk details
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: disks.py 3034 2012-10-01 07:15:12Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/disks.py $

import os
import re
import explorerbase
import drivemap
import storage


##########################################################################
# Slice ##################################################################
##########################################################################
class Slice(explorerbase.ExplorerBase):
    """ Slice of a disk """
    def __init__(self, config, slic, data, alldata):
        self.objname = slic
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def __repr__(self):
        """ TODO """
        return "<Slice %s %s>" % (self.name(), self.data)

    ##########################################################################
    def getCylinders(self):
        """ TODO """
        if "first_cylinder" not in self:
            return None, None, None
        return self["first_cylinder"], self["last_cylinder"], self["cylinder_count"]

    ##########################################################################
    def getSectors(self):
        """ TODO """
        if "first_sector" not in self:
            return None, None, None
        return self["first_sector"], self["last_sector"], self["sector_count"]

    ##########################################################################
    def isBackupSlice(self):
        """ TODO """
        return self["backup_slice"]

    ##########################################################################
    def getNotes(self):
        """ TODO """
        return self["describer"]


##########################################################################
# Disk ###################################################################
##########################################################################
class Disk(explorerbase.ExplorerBase):
    """ TODO """
    def __init__(self, config, disk, data, alldata):
        self.objname = disk
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def __repr__(self):
        """ TODO """
        return "<Disk %s %s>" % (self.name(), self.data)

    ##########################################################################
    def unusedDisk(self):
        """ TODO """
        return self["unused"]

    ##########################################################################
    def getSize(self, cylinders):
        """Given a number of cylinders, return the size in Kb"""
        if not cylinders:
            return 0
        if "cylinder_size" in self:
            csize = self["cylinder_size"] / 1024
        else:
            csize = self["sectors/cylinder"] * self["bytes/sector"] / 1024

        return csize * cylinders

    ##########################################################################
    def cylinderMap(self):
        """Work out what all the cylinders on the disk are used for"""
        if not self["have_cylinders"]:
            return []
        cylindermap = []
        diskcylinders = self["accessible cylinders"]
        for slic in self.sliceList():
            if "first_cylinder" not in slic:
                continue
            if slic.isBackupSlice():
                continue
            slicenum = slic["slicenum"]
            fs = int(slic["first_cylinder"])
            ls = int(slic["last_cylinder"])
            sc = int(slic["cylinder_count"])
            cylindermap.append((fs, ls, sc, slicenum))
        cylindermap.sort()
        oldend = self["first_cylinder"] - 1
        lastcylinder = 0
        fullmap = []
        for bits in cylindermap:
            first, last, count, slic = bits
            if first != oldend + 1:
                fullmap.append((oldend + 1, first - 1, first - oldend, "unalloc"))
            oldend = last
            lastcylinder = last
            fullmap.append((first, last, count, slic[-2:]))
        # Work out if there is unallocated space at the end
        if lastcylinder and diskcylinders and lastcylinder != diskcylinders:
            fullmap.append(
                (
                    lastcylinder + 1,
                    diskcylinders,
                    diskcylinders - lastcylinder + 1,
                    "unalloc",
                )
            )
        return fullmap

    ##########################################################################
    def sliceList(self):
        """ TODO """
        slices = sorted(self["slices"])
        return [self[s] for s in slices]

    ##########################################################################
    def analyse(self):
        """ TODO """
        # Check for errors
        if "predfail" in self and self["predfail"] != "0":
            self.addIssue(
                "predfail",
                obj=self.name(),
                text="Disk %s predicted to fail" % self.name(),
            )
        elif "harderrors" in self:
            # Small numbers of hard errors occur too often
            if int(self["harderrors"]) > 50:
                self.addIssue(
                    "harderrors",
                    obj=self.name(),
                    text="Disk %s has %s hard errors"
                    % (self.name(), self["harderrors"]),
                )
            elif int(self["harderrors"]) > 5:
                self.addConcern(
                    "harderrors",
                    obj=self.name(),
                    text="Disk %s has %s hard errors"
                    % (self.name(), self["harderrors"]),
                )

        # Check for cowboy usage of slice 2
        if self.config["explorertype"] == "solaris":
            s2 = "%ss2" % self.name()
            if s2 not in self:
                if "nobackupslice" in self and self["nobackupslice"]:
                    pass
                elif self["use"]:
                    # Disks that have uses (e.g. entire disk is zfs, vxvm)
                    # generally don't need backup slices
                    pass
                elif not self["slices"]:
                    # Disks that have no slices have much more serious problems
                    pass
                else:
                    self.addConcern(
                        "nobackup",
                        obj=self.name(),
                        text="Disk %s has no backup slice" % self.name(),
                    )

            # The only time this isn't true is when the disk/slice is used by
            # vxvm but not in format/prtvtoc
            if s2 in self and "first_sector" in self[s2]:
                if self[s2]["first_sector"] != 0:
                    self.addConcern(
                        "backupslice",
                        obj=self.name(),
                        text="%s is malformed for a backup slice (%s-%s not whole disk)"
                        % (s2, self[s2]["first_sector"], self[s2]["last_sector"]),
                    )

        if self.unusedDisk():
            # self.Debug("%s=%s" % (self.name(), self.data))
            if "nickname" in self:
                self.addConcern(
                    "unuseddisk",
                    obj=self.name(),
                    text="Disk %s (%s) appears not to be used"
                    % (self.name(), self["nickname"]),
                )
            else:
                self.addConcern(
                    "unuseddisk",
                    obj=self.name(),
                    text="Disk %s appears not to be used" % self.name(),
                )

        for slice in self.sliceList():
            self.inheritIssues(slice)


##########################################################################
# Disks ##################################################################
##########################################################################
class Disks(explorerbase.ExplorerBase):
    """ Disks """
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.st = storage.Storage(config)
        for disk in self.st.diskList():
            self[disk] = Disk(config, disk, self.st[disk], self.st)
            for slice in self[disk]["slices"]:
                self[disk][slice] = Slice(config, slice, self.st[slice], self.st)
        self.analyse()

    ##########################################################################
    def diskList(self):
        """ TODO """
        return self.values()

    ##########################################################################
    def analyse(self):
        """ TODO """
        for d in self.diskList():
            d.analyse()
            self.inheritIssues(d)
        self.analyseRaidctl()
        self.analyseLuxadm()

    ##########################################################################
    def analyseRaidctl(self):
        """This is really irritating, the internal raid controller
        hides all the useful details about the physical hardware
        (well it can tell you what they are, but explorer doesn't
        run that flag) and it also makes the unforgivable and
        deliberate  mistake of calling the mirrored disk the same
        name as a real disk - how can you tell which is which?

        Two different formats of raidctl.out:
        First:
            Controller: 3
                    Volume:c3t2d0
                    Disk: 0.2.0
                    Disk: 0.3.0

        Second:
            RAID    Volume  RAID            RAID            Disk
            Volume  Type    Status          Disk            Status
            ------------------------------------------------------
            c1t2d0  IM      OK              c1t2d0          OK
                                            c1t3d0          OK

        """
        filename = "disks/raidctl.out"
        if not self.exists(filename):
            return
        mode = "other"
        buff = []
        badTag = []
        f = self.open(filename)
        for line in f:
            line = line.rstrip()
            buff.append(line)
            if "No RAID volumes found" in line:
                return
            if line.startswith("RAID") or line.startswith("-----") or "Status" in line:
                continue
            if line.startswith("Controller"):
                mode = "controller"
                volume = None
            if mode == "controller":
                if line.startswith("Volume:"):
                    volume = line.split(":")[-1]
                # If no volume, not in use
                if line.startswith("Disk:") and volume:
                    if volume not in self:
                        self[volume] = storage.Storage.initialDict(
                            {
                                "_type": "disk",
                                "description": "Disk Drive",
                                "slices": set(),
                                "product": "unknown",
                                "_origin": filename,
                            }
                        )
#                    numdisks[volume] = numdisks.get(volume, 0) + 1
#                    if numdisks[volume] > 1:
#                        # By default the volume name is the disk name - stupid
#                        self[volume]["protected"] = "Internal HW Raid"
            else:
                bits = line.split()
                if len(bits) == 5:
                    volume = bits[0]
                    disk = bits[3]
                    badTag.append(
                        (self.raidCheck(line, 2, "Raid Volume %s" % volume), volume)
                    )
                    badTag.append(
                        (self.raidCheck(line, 4, "Raid Disk %s" % disk), disk)
                    )
                elif len(bits) == 4:
                    volume = bits[0]
                    disk = bits[2]
                    badTag.append(
                        (self.raidCheck(line, 1, "Raid Volume %s" % volume), volume)
                    )
                    badTag.append(
                        (self.raidCheck(line, 3, "Raid Disk %s" % disk), disk)
                    )
                elif len(bits) == 2:
                    disk = bits[1]
                    badTag.append(
                        (self.raidCheck(line, 1, "Raid Disk %s" % disk), disk)
                    )
                else:
                    self.Warning("Unhandled output of raidctl.out: %s" % line)
        f.close()
        for tag, obj in badTag:
            if tag:
                self.addIssue(tag, obj=obj, text=buff)
                break

    ##########################################################################
    def raidCheck(self, line, spot, label):
        """ TODO """
        if line.split()[spot] != "OK":
            return label
        return ""

    ##########################################################################
    def analyseLuxadm(self):
        """Parse the luxadm inq output to work out what arrays are plugged into
        the host; and hopefully what disks are then on which arrays
        """
        # self.arrays={}
        for luxf in self.glob("disks/luxadm_display_*"):
            self.analyseLuxDisplay(luxf)

    ##########################################################################
    def analyseLuxDisplay(self, luxf):
        """ TODO """
        f = self.open(luxf)
        for line in f:
            line = line.strip()
            if line.startswith("/dev/r"):
                path = line.replace("/dev/rdsk/", "")[:-2]
            if line.startswith("Path status") or line.startswith("State"):
                if ":" in line:
                    status = line.split(":")[-1].strip()
                else:
                    status = line.split()[-1].strip()
                if status not in ("O.K.", "ONLINE", "STANDBY"):
                    self.addIssue(
                        "channel",
                        obj=path,
                        text="Channel path %s has bad status '%s'" % (path, status),
                    )
        f.close()


##########################################################################
# storageDisks ###########################################################
##########################################################################
class storageDisks(explorerbase.ExplorerBase):
    """Class to represent all disks within a system based on data from
    Explorers
    """

    ##########################################################################
    def __init__(self, config, data={}):
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.channelmap = {}
        self.parse()
        self.selfPopulate()

    ##########################################################################
    def parse(self):
        """ TODO """
        self["disks"] = set()
        try:
            if self.config["explorertype"] == "solaris":
                self.parse_Solaris()
            elif self.config["explorertype"] == "linux":
                self.parse_Linux()
        except UserWarning as err:
            self.Warning(err)
        self.protectionCheck()

    ##########################################################################
    def parse_Linux(self):
        """ TODO """
        self["_uuidmap"] = {}
        self["_labelmap"] = {}
        self.parseLinux_blkid()
        self.parseLinux_partitions()
        self.parseLinux_fdisk(self.parseLinux_fdisk_chunk)
        self.parseLinux_multipath()
        self.parseLinux_pvs()
        self.parseLinux_hardwarepy(self.parseLinux_hardwarepy_chunk)
        for disk in self.diskList():
            self.postProcess(disk)

    ##########################################################################
    def parseLinux_pvs(self):
        """
        PV                  VG    Fmt  Attr PSize   PFree   DevSize PV UUID
        /dev/cciss/c0d0p1              --        0       0    2.00G
        /dev/cciss/c0d0p2   vgsys lvm2 a-   556.72G 467.72G 556.73G bjO0hi-kxyl-xXv0-ev2p-FzZG-Vav0-ANaLZY
        /dev/ram                       --        0       0   16.00M
        """

        fname = "sos_commands/devicemapper/pvs_-a_-v"
        if not self.exists(fname):
            return
        f = self.open(fname)
        for line in f:
            line = line.strip()
            bits = line.split()
            device = self.sanitiseDevice(bits[0])
            for i in (-1, -2):
                matchobj = re.match(r"(?P<size>\d+\.\d\d)(?P<sizeunits>[GM])", bits[i])
                if matchobj:
                    size = float(matchobj.group("size"))
                    if matchobj.group("sizeunits") == "M":
                        size *= 1024
                    elif matchobj.group("sizeunits") == "G":
                        size *= 1024 * 1024
                    if device in self:
                        self[device]["size"] = size
                    break
        f.close()

    ##########################################################################
    def parseLinux_multipath(self):
        """ TODO """
        # This looks like it was explicitly designed to be unparseable by a computer
        # databases (360a9800057396d4e4a5a623454317175) dm-5 NETAPP,LUN
        # [size=200G][features=1 queue_if_no_path][hwhandler=0][rw]
        # \_ round-robin 0 [prio=8][active]
        #  \_ 0:0:0:0 sda 8:0   [active][ready]
        #  \_ 1:0:0:0 sde 8:64  [active][ready]
        # \_ round-robin 0 [prio=2][enabled]
        #  \_ 0:0:1:0 sdc 8:32  [active][ready]
        #  \_ 1:0:1:0 sdg 8:96  [active][ready]
        #
        data = ""
        fname = "sos_commands/devicemapper/multipath_-v4_-ll"
        if not self.exists(fname):
            return
        f = self.open(fname)
        oldline = None
        mode = False
        for line in f:
            if line.startswith("["):
                mode = True
                data = oldline + line
                continue
            if mode:
                data += line
            if mode and line[0] not in r"\ ":
                mode = False
                self.parseLinux_multipath_stanza(data)
                data = ""
            oldline = line
        f.close()
        if data:
            self.parseLinux_multipath_stanza(data)

    ##########################################################################
    def parseLinux_multipath_stanza(self, buffer):
        """ TODO """
        name = "mpath_%s" % buffer.splitlines()[0].split()[0]
        if name not in self:
            self[name] = storage.Storage.initialDict(
                {
                    "_type": "mpath",
                    "description": "Multipath",
                    "subdisks": set(),
                    "_origin": "sos_commands/devicemapper/multipath_-v4_-ll",
                }
            )
        subdisks = set()
        for line in buffer.splitlines():
            if line[0] == " ":
                m = re.search(
                    r".*_ \d+:\d+:\d+:\d+\s+(?P<disk>\S+)\s+\d+:\d+\s+.*", line
                )
                if m:
                    subdisks.add(m.group("disk"))
                    self[name]["contains"].add(m.group("disk"))
                else:
                    self.Warning("Couldn't match %s" % line)
        self[name]["subdisks"] = subdisks

    ##########################################################################
    def parseLinux_hardwarepy_chunk(self, buff, class_):
        """ TODO """
        if class_ == "HD":
            if buff.get("bus", "none") == "USB":
                return
            model = buff.get("desc", "unknown desc")
            device = self.sanitiseDevice(buff.get("device", "unknown device"))
            if device not in self:
                self[device] = storage.Storage.initialDict(
                    {
                        "_type": "disk",
                        "description": "Disk Drive",
                        "slices": set(),
                        "_origin": "hardware.py",
                        "have_cylinders": False,
                    }
                )
                self["disks"].add(device)
            self[device]["product"] = model

    ##########################################################################
    def parseLinux_blkid(self):
        """Parse the linux dump outputs"""
        if not self.exists("sos_commands/filesys/blkid"):
            return
        f = self.open("sos_commands/filesys/blkid")
        for line in f:
            bits = line.split()
            dev = self.sanitiseDevice(bits[0][:-1])
            if dev.startswith('"') and dev.endswith('"'):  # Trim quotes
                dev = dev[1:-1]
            for bit in bits[1:]:
                if bit.startswith("LABEL"):
                    self["_labelmap"][bit.split("=")[1].replace('"', "")] = dev
                if bit.startswith("UUID"):
                    self["_uuidmap"][bit.split("=")[1].replace('"', "")] = dev
        f.close()

    ##########################################################################
    def parse_Solaris(self):
        """ TODO """
        self.parseSolaris_format()
        if not self["disks"]:
            self.alternativeParseFormat()
        self.parsePathToInst()
        self.parseLuxadm()
        for disk in self["disks"]:
            self.parseDisk(disk)
        datadev = self.parseIostatE()
        for dev in datadev:
            self.matchDiskToPath(datadev[dev])
        for disk in self.diskList():
            self.postProcess(disk)
        self.parseRaidctl()

    ##########################################################################
    def parseDisk(self, disk):
        """ TODO """
        self.parsePrtvtoc(disk)

    ##########################################################################
    def parsePrtvtoc(self, disk):
        """Examine the prtvtoc output for each disk
        You can't guarantee which slice will be used to generate the
        prtvtoc - so try them all
        """
        files = self.glob("disks/prtvtoc/%ss*" % disk)
        if not files:
            return
        filename = files[0]
        self[disk]["have_cylinders"] = False
        self[disk]["first_cylinder"] = 0
        unalloc = False
        f = self.open(filename)
        for line in f:
            if line.startswith("*"):
                if line.find("bytes/sector") >= 0:
                    self[disk]["bytes/sector"] = int(line.split()[1])
                elif line.find("sectors/cylinder") >= 0:
                    self[disk]["sectors/cylinder"] = int(line.split()[1])
                    self[disk]["have_cylinders"] = True
                elif line.find("accessible cylinders") >= 0:
                    self[disk]["accessible cylinders"] = int(line.split()[1]) - 1
                elif line.find("cylinders") >= 0:
                    self[disk]["cylinders"] = int(line.split()[1])
                elif line.find("Unallocated") >= 0:
                    self[disk]["unallocated_space"] = []
                    unalloc = True
                if unalloc:
                    if len(line.split()) != 1:
                        self[disk]["unallocated_space"].append(line[1:].strip())
                    else:
                        unalloc = False
            else:
                bits = line.strip().split()
                slicenum = bits[0]
                slicename = "%ss%s" % (disk, slicenum)
                self[disk]["slices"].add(slicename)
                self[slicename] = storage.Storage.initialDict(
                    {
                        "_type": "slice",
                        "description": "Disk Slice",
                        "slicenum": slicenum,
                        "disk": disk,
                        "tag": bits[1],
                        "flags": bits[2],
                        "first_sector": int(bits[3]),
                        "sector_count": int(bits[4]),
                        "last_sector": int(bits[5]),
                        "_origin": filename,
                    }
                )
                if slicenum == "8":
                    self[slicename]["use"].add("Boot Partition")
                    self[slicename]["partof"].add("Boot Partition")
                    self["Boot Partition"] = storage.Storage.initialDict(
                        {"_type": "boot_partition"}
                    )
                if self[disk]["have_cylinders"]:
                    sl = self[slicename]
                    sl["first_cylinder"] = (
                        sl["first_sector"] / self[disk]["sectors/cylinder"]
                    )
                    sl["last_cylinder"] = (
                        sl["last_sector"] / self[disk]["sectors/cylinder"]
                    )
                    sl["cylinder_count"] = (
                        sl["sector_count"] / self[disk]["sectors/cylinder"]
                    )
                try:
                    self[slicename]["mountpoint"] = bits[6]
                except IndexError:
                    pass
        f.close()

    ##########################################################################
    def mergeDrivemap(self, disk):
        """Take the options listed in drivemap for this device and merge them in"""
        d = self[disk]
        if "product" in d and d["product"] in drivemap.drivemap:
            dr = drivemap.drivemap[d["product"]]
            for k, v in dr.items():
                d[k] = v

    ##########################################################################
    def protectionCheck(self):
        """If a disk from the drivemap is listed as protected, then
        mark it as such"""

        for disk in self.diskList():
            d = self[disk]
            if "product" in d and d["product"] in drivemap.drivemap:
                if "protected" in drivemap.drivemap[d["product"]]:
                    d["protected"] = drivemap.drivemap[d["product"]]["protected"]

    ##########################################################################
    def parseRaidctl(self):
        """This is really irritating, the internal raid controller
        hides all the useful details about the physical hardware
        (well it can tell you what they are, but explorer doesn't
        run that flag) and it also makes the unforgivable and
        deliberate  mistake of calling the mirrored disk the same
        name as a real disk - how can you tell which is which?

        Two different formats of raidctl.out:
        First:
            Controller: 3
                    Volume:c3t2d0
                    Disk: 0.2.0
                    Disk: 0.3.0

        Second:
            RAID    Volume  RAID            RAID            Disk
            Volume  Type    Status          Disk            Status
            ------------------------------------------------------
            c1t2d0  IM      OK              c1t2d0          OK
                                            c1t3d0          OK

        """
        filename = "disks/raidctl.out"
        if not self.exists(filename):
            return
        mode = "other"
        numdisks = {}
        f = self.open(filename)
        for line in f:
            line = line.strip()
            if "No RAID volumes found" in line:
                return
            if line.startswith("RAID") or line.startswith("-----") or "Status" in line:
                continue
            if line.startswith("Controller"):
                mode = "controller"
                volume = None
            if mode == "controller":
                if line.startswith("Volume:"):
                    volume = line.split(":")[-1]
                # If no volume, not in use
                if line.startswith("Disk:") and volume:
                    if volume not in self:
                        self[volume] = storage.Storage.initialDict(
                            {
                                "_type": "disk",
                                "description": "Disk Drive",
                                "slices": set(),
                                "product": "unknown",
                                "_origin": filename,
                            }
                        )
                        self["disks"].add(volume)
                    self[volume]["raidctl"] = True
                    numdisks[volume] = numdisks.get(volume, 0) + 1
                    if numdisks[volume] > 1:
                        # By default the volume name is the disk name - stupid
                        self[volume]["protected"] = "Internal HW Raid"
            else:
                bits = line.split()
                if len(bits) == 5:
                    volume = bits[0]
                    disk = bits[3]
                    if disk in self:
                        self[disk]["raidctl"] = True
                        self[disk]["product"] = "Part of hw raid"
                        self[disk]["protected"] = "Internal HW Raid"
                        self[disk]["description"] = "Hardware Raid"
                    else:
                        self.Warning("Disk %s found in raidctl not format" % disk)
                elif len(bits) == 4:
                    volume = bits[0]
                    disk = bits[2]
                    if disk in self:
                        self[disk]["raidctl"] = True
                        self[disk]["protected"] = "Internal HW Raid"
                        self[disk]["product"] = "Part of hw raid"
                        self[disk]["description"] = "Hardware Raid"
                    else:
                        self.Warning("Disk %s found in raidctl not format" % disk)
                elif len(bits) == 2:
                    disk = bits[0]
                else:
                    self.Warning("Unhandled output of raidctl.out: %s" % line)
        f.close()

    ##########################################################################
    def postProcess(self, disk):
        """Do the little clean up tasks"""
        if (
            "product" not in self[disk] or self[disk]["product"] == "unknown"
        ) and "model" in self[disk]:
            self[disk]["product"] = self[disk]["model"]

        # Remove not 'real' disks
        self.mergeDrivemap(disk)
        if self.isRemovable(disk):
            self["disks"].remove(disk)
            del self.data[disk]
            return

        # Handle multipathed disks
        if disk in self.channelmap:
            self[disk]["aliases"] = set([d for d in self.channelmap[disk] if d != disk])

    ##########################################################################
    def isRemovable(self, disk):
        removables = (
            "CD-224E",
            "SUN32XCD",
            "DVD-ROM",
            "ODD-DVD",
            "DV-28E",
            "CD-RW",
            "CD-ROM",
            "DV-28SL",
            "FD-05PUB",
            "CD/DVDW",
            "DW-",
        )
        if "product" not in self[disk]:
            return False
        if "fake" in self[disk] and self[disk]["fake"]:
            return True
        for rem in removables:
            if rem in self[disk]["product"]:
                return True
        return False

    ##########################################################################
    def parseLuxadm(self):
        """Parse the luxadm inq output to work out what arrays are plugged into
        the host; and hopefully what disks are then on which arrays
        """
        self.arrays = {}
        for luxf in self.glob("disks/luxadm_inq_*"):
            self.parseLuxInq(luxf)
        for luxf in self.glob("disks/luxadm_display_*"):
            self.parseLuxDisplay(luxf)

    ##########################################################################
    def parseLuxDisplay(self, luxf):
        f = self.open(luxf)
        paths = []
        buff = []
        for line in f:
            line = line.strip()
            if line.startswith("DEVICE PROPERTIES"):
                if buff:
                    self.parseLuxStanza(buff)
                buff = [line]
                for disk in paths:
                    self.channelmap[disk] = paths[:]
                paths = []
            else:
                buff.append(line)
            if line.startswith("/dev/r"):
                path = line.replace("/dev/rdsk/", "")[:-2]
                paths.append(path)
        for disk in paths:
            self.channelmap[disk] = paths[:]
        f.close()
        if buff:
            self.parseLuxStanza(buff)

    ##########################################################################
    def parseLuxStanza(self, input):
        serial = "Unknown"
        for line in input:
            if line.startswith("Serial Num:"):
                serial = line.split(":")[1].strip()
            if line.startswith("/dev/rdsk"):
                drive = line.replace("/dev/rdsk/", "")[:-2]
                try:
                    self[drive]["serial"] = serial
                except KeyError:
                    self.Warning("Unknown disk %s in luxadm display" % drive)

    ##########################################################################
    def parseLuxInq(self, luxf):
        path = ""
        product = "lux-unknown"
        vendor = ""
        ctrl = ""
        f = self.open(luxf)
        for line in f:
            line = line.strip()
            if line.startswith("/devices"):
                path = line
                matchobj = re.search(r"/devices(?P<ctrl>.*)/([^/]*)", path)
                ctrl = matchobj.group("ctrl")
            if line.startswith("Vendor:"):
                vendor = line.split(":")[1].strip()
            if line.startswith("Product:"):
                product = line.split(":")[1].strip()
        f.close()
        self.arrays[self.cmdfilename(luxf)] = {
            "path": path,
            "product": product,
            "vendor": vendor,
            "ctrl": ctrl,
            "name": self.cmdfilename(luxf).replace("luxadm_inq_dev_es_", ""),
        }

    ##########################################################################
    def parsePathToInst(self):
        f = self.open("etc/path_to_inst")
        self.devlist = {}
        for line in f:
            matchobj = re.search(r'"(?P<path>.*)" (?P<devnum>\S+) "(?P<devtype>.*)"', line)
            if matchobj:
                self.devlist[
                    "%s%s" % (matchobj.group("devtype"), matchobj.group("devnum"))
                ] = matchobj.group("path")
        f.close()

    ##########################################################################
    def matchDiskToPath(self, d):
        """Match the disk to the path found in path_to_inst
        so we can tie a disk in c0t0d0 format to one in sd0 format
        """
        try:
            path = self.devlist[d["device"]]
        except KeyError:  # device doesn't appear in path_to_inst
            self.Warning("Disk %s isn't in /etc/path_to_inst" % d["device"])
            return

        for disk in self.diskList():
            if "path" not in self[disk]:
                continue

            # Try and fit the disk into any arrays that we know about
            for arr in self.arrays:
                if path.startswith(self.arrays[arr]["ctrl"]):
                    self[disk]["array"] = "%s %s %s" % (
                        self.arrays[arr]["name"],
                        self.arrays[arr]["vendor"],
                        self.arrays[arr]["product"],
                    )

            # Match the device in sd0 format to c0t0d0 by the path_to_inst
            if path.endswith(self[disk]["path"]):
                for k, v in d.items():
                    self[disk][k] = v
                return
        # This won't match removable media
        # self.Warning("Couldn't match %s %s %s" % (d['device'], path, `d`))

    ##########################################################################
    def alternativeParseFormat(self):
        """Something has gone wrong with the format analysis
        Try an alternative approach
        """
        self.addConcern("format", text="Couldn't get format data")
        disklist = self.glob("disks/prtvtoc/*")
        for diskfile in disklist:
            # Strip s2 off the end of the filename
            disk = os.path.split(diskfile)[-1][:-2]
            self[disk] = storage.Storage.initialDict(
                {
                    "_type": "disk",
                    "description": "Disk Drive",
                    "slices": set(),
                    "product": "unknown",
                    "_origin": diskfile,
                }
            )
            self[disk]["format_details"] = "Broken format command"
            self["disks"].add(disk)

    ##########################################################################
    def parseLinux_partitions(self):
        """Analyse the proc/partitions file to determine disk partitions
        As always there are a number of different formats

        Format 1
            major minor  #blocks  name

               8     0   71577608 sda

        Format 2
            major minor  #blocks  name     rio rmerge rsect ruse wio wmerge wsect wuse running use aveq

             104     0   35559877 cciss/c0d0 593417934 3143644600 3929862432 22290308 341597851 709675064 4130779488 42186393 0 21975721 21523989

        Partitions have different numbering systems as well:
            Disk sda has sda1, sda2, sda3, ...
            Disk c0d0 has c0d0p1, c0d0p2, c0d0p3, ...
        """
        f = self.open("proc/partitions")
        for line in f:
            line = line.strip()
            if self.lineSkipper(line, start=["major"], middle=["emcpower"]):
                continue
            bits = line.split()
            part = bits[3]

            diskname = ""
            for diskfmt in [
                r"(?P<disk>[hs]d[a-z]{1,2})$",
                r"cciss/(?P<disk>c\dd\d)$",
                r"ida/(?P<disk>c\dd\d)$",
            ]:
                rm = re.match(diskfmt, part)
                if rm:
                    diskname = rm.group("disk")
                    break
            if diskname:
                self[diskname] = storage.Storage.initialDict(
                    {
                        "_type": "disk",
                        "description": "Disk Drive",
                        "slices": set(),
                        "product": "unknown",
                        "_origin": "proc/partitions",
                        "have_cylinders": False,
                    }
                )
                self["disks"].add(diskname)
                continue

            # Check to see if it matches known virtual disks
            isVirt = False
            for virtfmt in [r"md\d", r"dm-\d", "lvm.", r"loop\d"]:
                if re.match(virtfmt, part):
                    isVirt = True
                    break
            if isVirt:
                continue

            matchob = None
            for partfmt in [
                r"(?P<slicehandle>(?P<disk>[hs]d[a-z]{1,2})(?P<slice>\d))",
                r"cciss/(?P<slicehandle>(?P<disk>c\dd\d)(?P<slice>p\d))",
                r"(?P<slicehandle>(?P<disk>emcpower)(?P<slice>\S))",
                r"ida/(?P<slicehandle>(?P<disk>c\dd\d)(?P<slice>p\d))",
            ]:
                matchob = re.match(partfmt, part)
                if matchob:
                    break

            if not matchob:
                self.Fatal("Unhandled disk partition: %s" % part)
            disk = matchob.group("disk")
            slice = matchob.group("slice")
            slicehandle = matchob.group("slicehandle")
            self.addSlice(slicehandle, slice, disk)
        f.close()

    ##########################################################################
    def addSlice(self, slicehandle, slice, disk):
        """Add a new disk slice
        slicehandle is what the slice is known as - generally diskpartition
        slice is just the slice component
        disk is the name of the disk
        """
        self[slicehandle] = storage.Storage.initialDict(
            {
                "_type": "slice",
                "description": "Disk Slice",
                "slicenum": slice,
                "disk": disk,
            }
        )
        self[disk]["slices"].add(slicehandle)

    ##########################################################################
    def parseLinux_fdisk_chunk(self, lines):
        disk = None
        for line in lines:
            line = line.strip()
            if "emcpower" in line:
                return
            if self.lineSkipper(
                line,
                start=["<---", "Device"],
                middle=["DOS and BSD magic", "BSD mode", "does not end on"],
            ):
                continue
            if line.startswith("Disk"):
                matchobj = re.search(
                    r"Disk (?P<device>/dev/.*): (?P<size>.*), (?P<bytes>\d+) bytes", line
                )
                if matchobj:
                    disk = self.sanitiseDevice(matchobj.group("device"))
                    if disk not in self:
                        self[disk] = storage.Storage.initialDict(
                            {
                                "_type": "disk",
                                "description": "Disk Drive",
                                "slices": set(),
                                "product": "unknown",
                                "_origin": "fdisk_-l",
                                "have_cylinders": False,
                            }
                        )
                        self["disks"].add(disk)
                    self[disk]["size"] = matchobj.group("size")
                    self[disk]["bytes"] = matchobj.group("bytes")
                    continue
                n = re.search(
                    r"Disk (?P<device>/dev/.*): (?P<heads>\d+) heads, (?P<sectors>\d+) sectors, (?P<cylinders>\d+) cylinders",
                    line,
                )
                if n:
                    disk = self.sanitiseDevice(n.group("device"))
                    self[disk]["heads"] = n.group("heads")
                    self[disk]["first_cylinder"] = 1
                    self[disk]["cylinders"] = int(n.group("cylinders"))
                    self[disk]["have_cylinders"] = True
                    self[disk]["accessible cylinders"] = int(n.group("cylinders"))
                    continue
                if "doesn't contain a valid partition table" in line:
                    # TODO - disk needs to raise an issue
                    continue

            m = re.search(
                r"(?P<heads>\d+) heads, (?P<sectors>\d+) sectors/track, (?P<cylinders>\d+) cylinders",
                line,
            )
            if m:
                self[disk]["heads"] = m.group("heads")
                self[disk]["first_cylinder"] = 1
                self[disk]["sectors/track"] = m.group("sectors")
                self[disk]["have_cylinders"] = True
                self[disk]["cylinders"] = int(m.group("cylinders"))
                self[disk]["accessible cylinders"] = int(m.group("cylinders"))
                continue

            m = re.search(
                r"Units = cylinders of (?P<facta>\d+) \* (?P<factb>\d+) = (?P<cylinder_size>\d+) bytes",
                line,
            )
            if m:
                self[disk]["cylinder_size"] = int(m.group("cylinder_size"))
                continue

            m = re.search(r"Units = cylinders of (?P<facta>\d+) \* (?P<factb>\d+)", line)
            if m:
                self[disk]["cylinder_size"] = int(m.group("facta")) * int(
                    m.group("factb")
                )
                continue

            m = re.search(
                r"(?P<device>/dev/.*?)\s+(?P<boot>\*?)\s+(?P<start>\d+)\s+(?P<end>\d+)\s+(?P<blocks>\d+)\+?\s+(?P<id>..)\s+(?P<system>.*)",
                line,
            )
            if m:
                part = self.sanitiseDevice(m.group("device"))

                # Don't know why this happens (not in /proc/partitions) - disk
                # not used?
                if part not in self:
                    self.addConcern(
                        "unuseddisk",
                        obj=self.name(),
                        text="Disk %s potentially unused" % part,
                    )
                    continue

                # Not a real partition
                if m.group("system") in ("Extended", "Win95 Ext'd (LBA)"):
                    del self[part]
                    self[disk]["slices"].remove(part)
                    continue
                if m.group("boot"):
                    self[part]["bootable"] = True
                else:
                    self[part]["bootable"] = False
                self[part]["first_cylinder"] = int(m.group("start"))
                self[part]["last_cylinder"] = int(m.group("end"))
                self[part]["cylinder_count"] = (
                    self[part]["last_cylinder"] - self[part]["first_cylinder"]
                )
                self[part]["blocks"] = m.group("blocks")
                self[part]["id"] = m.group("id")
                self[part]["system"] = m.group("system")
                continue

            self.Warning("Unhandled fdisk line >%s<" % line)

    ##########################################################################
    def parseSolaris_format(self):
        f = self.open("disks/format.out")
        for line in f:
            line = line.strip()
            m = re.search(r"\d+. (?P<disk>\S+) <(?P<details>.*)>", line)
            if m:
                disk = m.group("disk")
                if "emcpower" in disk:
                    continue
                self[disk] = storage.Storage.initialDict(
                    {
                        "_type": "disk",
                        "description": "Disk Drive",
                        "slices": set(),
                        "product": "unknown",
                        "_origin": "disks/format.out",
                    }
                )
                self[disk]["format_details"] = m.group("details")
                self["disks"].add(disk)
                continue
            if line.startswith("/") and not line.startswith("/pseudo"):
                self[disk]["path"] = line.strip()
        f.close()

    ##########################################################################
    def selfPopulate(self):
        for d in self.diskList():
            # If a disk is raid protected then its slices are also
            if "protected" in self[d]:
                for s in self[d]["slices"]:
                    if self[d]["protected"]:
                        self[s]["protected"] = self[d]["protected"]
                        self[s]["description"] = "Hardware Raid Slice"

    ##########################################################################
    def isBackupSliceCriteria(self, slice):
        """Return true if the slice is the backup slice
        It is considered not the backup slice if it is used
        """
        if "first_sector" not in self[slice]:
            return False
        if self[slice]["first_sector"] != 0:
            return False
        if not slice.endswith("s2"):
            return False
        # If only one slice exists on this disk, and it is s2 then
        # it isn't really the backup slice
        if len(self[self[slice]["disk"]]["slices"]) == 1:
            return False
        return True

    ##########################################################################
    def crossPopulate(self, data):
        for disk in self.diskList():
            try:
                self.crossPopulateDisk(data, disk)
            except Exception:
                self.Warning("Failed to crossPopulateDisk: %s" % disk)
                raise

    ##########################################################################
    def crossPopulateDisk(self, data, disk):
        # Check to see if the slice is used as the backup slice
        for slice in data[disk]["slices"]:
            data[slice]["backup_slice"] = False
            if self.isBackupSliceCriteria(slice):
                if not data[slice]["use"]:
                    data[slice]["backup_slice"] = True

        # Remove unused slices that overlap used backup slice
        bs = "%ss2" % disk  # Backup slice
        if bs in data and data[bs]["use"]:
            for ns in list(data[disk]["slices"]):
                # Skip the backup slice itself
                if ns == bs:
                    continue
                if (
                    "use" in self[ns]
                    and self[ns]["use"]
                    and self[ns]["slicenum"] != "8"
                ):
                    self.Warning(
                        "Overlap problem between %s %s and %s %s"
                        % (ns, list(data[ns]["use"]), bs, list(data[bs]["use"]))
                    )
                else:
                    if ns in data:
                        # self.Debug("Removing slice %s as it overlaps with a used backup slice" % ns)
                        # If we are the boot partition - we can be used and not
                        # used at the same time
                        if (
                            data[ns]["slicenum"] == "8"
                            and ns in data["Boot Partition"]["contains"]
                        ):
                            data["Boot Partition"]["contains"].remove(ns)
                        del data[ns]
                        data[disk]["slices"].remove(ns)

        self.crossPopulateProtection(disk, data)

    ##########################################################################
    def crossPopulateProtection(self, disk, data):
        # If a disk slice has protection then the use/filesystem on it also has
        # protection
        for slice in data[disk]["slices"]:
            if "protected" in data[disk] and data[disk]["protected"]:
                protect = data[disk]["protected"]
            elif "protected" in data[slice] and data[slice]["protected"]:
                protect = data[slice]["protected"]
            else:
                protect = False

            for use in data[slice]["use"]:
                if protect:
                    if use in data:
                        data[use]["protected"] = protect
                    elif "Quorum" not in "use":
                        # Quorums aren't part of the whole 'storage family' but
                        # they still use a disk
                        pass
                    else:
                        self.Debug("Protected with no device use=%s" % use)

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
            for slice in data[disk]["slices"]:
                # Boot Partition always exists
                if data[slice]["slicenum"] == "8":
                    continue
                if data[slice]["use"]:
                    used = True
                    break
            if not used:
                data[disk]["unused"] = True
            else:
                data[disk]["unused"] = False

        # If the disk is a multipath'd one then if we are used then
        # the other disks are used
        for disk in self.diskList():
            if not data[disk]["unused"] and "aliases" in data[disk]:
                for d in data[disk]["aliases"]:
                    data[d]["unused"] = False

    ##########################################################################
    def parseIostatE(self, filename="disks/iostat_-E.out"):
        """Parse iostat -E output"""
        f = self.open(filename)
        datadev = {}
        dev = ""
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = re.match(
                r"(?P<device>\S+)\s*Soft Errors: (?P<softerrors>\d+) Hard Errors: (?P<harderrors>\d+) Transport Errors: (?P<transerrors>\d+)",
                line,
            )
            if m:
                dev = m.group("device")
                datadev[dev] = {}
                datadev[dev].update(m.groupdict())
                continue
            m = re.match(
                r"Vendor: (?P<vendor>.*?)\s+Product: (?P<product>.*?)\s+Revision: (?P<revision>.*) Serial No:\s*(?P<serial>.+?)",
                line,
            )
            if m:
                datadev[dev].update(m.groupdict())
                continue
            # Same as above but with no serial to prevent overwriting a serial
            # from elserwhere
            m = re.match(
                r"Vendor: (?P<vendor>.*?)\s+Product: (?P<product>.*?)\s+Revision: (?P<revision>.*) Serial No:\s*",
                line,
            )
            if m:
                datadev[dev].update(m.groupdict())
                continue
            m = re.match(
                r"Model: (?P<model>.*) Revision: (?P<revision>.*) Serial No: (?P<serial>.*)",
                line,
            )
            if m:
                datadev[dev].update(m.groupdict())
                continue
            m = re.match(r"Size: (?P<size>\S+) <(?P<bytes>-?\d+) bytes>", line)
            if m:
                datadev[dev].update(m.groupdict())
                continue
            m = re.match(
                r"Media Error: (?P<mediaerror>\d+) Device Not Ready: (?P<devnotready>\d+)\s+No Device: (?P<nodev>\d+) Recoverable: (?P<recoverable>\d+)",
                line,
            )
            if m:
                datadev[dev].update(m.groupdict())
                continue
            m = re.match(
                r"Illegal Request: (?P<illreq>\d+) Predictive Failure Analysis: (?P<predfail>\d+)",
                line,
            )
            if m:
                datadev[dev].update(m.groupdict())
                continue
            m = re.match(r"Illegal Request: (?P<illreq>\d+)", line)
            if m:
                datadev[dev].update(m.groupdict())
                continue
            m = re.match(
                r"RPM: (?P<rpm>\d+) Heads: (?P<heads>\d+) Size: (?P<size>\S+) <(?P<bytes>-?\d+) bytes>",
                line,
            )
            if m:
                datadev[dev].update(m.groupdict())
                continue
        f.close()
        return datadev

    ##########################################################################
    def describer(self, obj, data):
        if data[obj]["_type"] == "slice":
            return self.sliceDescriber(obj, data)
        elif data[obj]["_type"] == "disk":
            return self.diskDescriber(obj, data)
        else:
            self.Fatal("describer passed object of type %s" % data[obj]["_type"])

    ##########################################################################
    def sliceDescriber(self, slice, data):
        # Work out from the partof which is the next level up
        tmp = []
        if "partof" not in data[slice]:
            return "unused slice?"
        for obj in data[slice]["partof"]:
            if "partof" in data[obj]:
                tmp.append((len(data[obj]["partof"]), obj))
        if not tmp:  # Mounted directly onto slice
            return ""
        tmp.sort()
        tmp.reverse()

        str = ""
        debugstr = ""
        if "emcpowerpath" in data[slice]:
            str += "EMC PowerPath %s" % data[slice]["emcpowerpath"]
        metadbcount = 0
        softparcount = 0
        for lev, partof in tmp:
            if partof in data:
                if data[partof]["_type"] == "metadb_copy":
                    metadbcount += 1
                    continue
                if data[partof]["_type"] == "metadb":
                    if "diskset" in data[partof]:
                        str += "Diskset %s " % data[partof]["diskset"]
                    if metadbcount == 1:
                        str += "MetaDB (1 copy)"
                    else:
                        str += "MetaDB (%d copies)" % metadbcount
                    continue
                if data[partof]["_type"] == "zfs_pool":
                    str += "ZFS Pool: %s" % partof
                    break
                if data[partof]["_type"] == "allswap":
                    continue
                if data[partof]["_type"] == "swap":
                    continue
                if data[partof]["_type"] == "logvol":
                    continue
                if data[partof]["_type"] == "disksuite":
                    if data[partof]["type"] == "softpar":
                        softparcount += 1
                        continue
                    str += "%s (%s) of " % (data[partof]["description"], partof)
                    continue
                if data[partof]["_type"] == "boot_partition":
                    break
                # This should be 'use' so dont report it
                if data[partof]["_type"] == "filesystem":
                    continue
                # This should be 'use' so dont report it
                if data[partof]["_type"] == "did_slice":
                    continue

                # Default describer
                debugstr += "&lt;%s-%s&gt;" % (partof, data[partof]["_type"])
                if "description" in data[partof] and data[partof]["description"]:
                    debugstr += "%s (description:)%s of " % (
                        partof,
                        data[partof]["description"],
                    )
                    str += "%s %s of " % (partof, data[partof]["description"])
                else:
                    str += "%s (?)" % partof
            else:
                str += "(unknown %s)" % partof
        # You can get hundreds of these which makes it unreadable
        if softparcount:
            str += " %d soft partitions" % softparcount
        if str.endswith(" of "):  # Trim last ' of ' off
            str = str[:-4]
        debugstr += "%s" % tmp
        return str
        # return "%s <font color=blue>[%s]</font>" % (str, debugstr)     #
        # Debugging

    ##########################################################################
    def diskDescriber(self, disk, data):
        """Generate the description used if the entire disk is used as
        a single unit
        """
        if "use" not in data[disk] or not data[disk]["use"]:
            return "%s.describer(%s)" % (self.__class__.__name__, disk)
        str = ""
        mounts = []
        for su in data[disk]["use"]:
            if su not in data:
                continue
            if data[su]["_type"] == "filesystem":
                mounts.append(su)

        if not data[disk]["partof"]:
            return ", ".join(list(self[disk]["use"]))

        for po in data[disk]["partof"]:
            if po not in data or "_type" not in data[po]:
                continue
            # ZFS pools
            if data[po]["_type"] == "zfs_pool":
                str = "ZFS Pool %s: %s" % (po, ", ".join(mounts))
                break
            # Linux metadevices
            if data[po]["_type"] == "metadev":
                str = "Metadev %s: %s" % (po, ", ".join(mounts))
                break
            # EMC PowerPath
            if data[po]["_type"] == "emcpower":
                str = "EMC PowerPath %s:" % po
                if mounts:
                    str += " %s" % (", ".join(mounts))
                else:
                    str += " No apparent use"
                    self.addConcern(
                        "unused emcpower",
                        obj=po,
                        text="EMC PowerPath %s has no obvious use" % po,
                    )
                break

            str += "[%s %s]" % (data[po]["_type"], po)
        return str

    ##########################################################################
    def diskList(self):
        """Return a list of disks defined on this server
        In the storage class this returns a list of keys, in Disks
        class it returns a list of instances of Disk.
        """
        return sorted(self["disks"])


# EOF
