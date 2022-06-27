#!/usr/local/bin/python
#
# Script to analyse prtconf -vD from explorers
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: prtconf.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/prtconf.py $

import os
import sys
import getopt
import re
import explorerbase
import kstat

verbflag = 0

##########################################################################


class Driver(explorerbase.ExplorerBase):
    def __init__(self, config, drivername):
        explorerbase.ExplorerBase.__init__(self, config)
        self.objname = drivername
        self.children = []
        self.parent = None
        self.lines = {}

    ##########################################################################
    def analyseLines(self):
        for mode in self.lines.keys():
            self.analyse(mode)
        self["vendor"] = ""
        if "hardware:inquiry-vendor-id" in self:
            self["vendor"] += "%s " % self["hardware:inquiry-vendor-id"]
        if "hardware:inquiry-product-id" in self:
            self["vendor"] += self["hardware:inquiry-product-id"]
        if self["vendor"] == "SUNW SUNWGS INT FCBPL":
            self["vendor"] = "Internal FibreChannel Backplane"

    ##########################################################################
    def getName(self, line):
        for reg in (
            "name='(?P<name>.*)'",
            "name=(?P<name>.*)",
            "name \<(?P<name>.*?)\>",
        ):
            m = re.search(reg, line)
            if m:
                return m.group("name")
        if "driver name" in line:
            return None
        self.Warning("No match for name: %s" % line)

    ##########################################################################
    def getValue(self, line):
        for reg in (
            "value='(?P<value>.*)'",
            "value=(?P<value>.*)",
            "value <(?P<value>.*?)>",
            "value '(?P<value>.*?)'",
        ):
            m = re.search(reg, line)
            if m:
                return m.group("value")
        self.Warning("No match for value:%s" % line)

    ##########################################################################
    def analyse(self, mode):
        name = ""
        value = ""
        for line in self.lines[mode]:
            if "name" in line:
                name = self.getName(line)
                value = ""
            elif "value" in line:
                value = self.getValue(line)

            if name and value:
                self["%s:%s" % (mode, name)] = value
                name = ""
                value = ""

    ##########################################################################
    def addParent(self, blob):
        self.parent = blob

    ##########################################################################
    def removeChild(self, blob):
        self.children.remove(blob)

    ##########################################################################
    def addChild(self, blob):
        self.children.append(blob)
        blob.addParent(self)

    ##########################################################################
    def isTape(self):
        if self.name().startswith("st"):
            return True
        return False

    ##########################################################################
    def isDisk(self):
        if self.name().startswith("sd"):
            return True
        if self.name().startswith("ssd"):
            return True
        return False

    ##########################################################################
    def isNull(self):
        """return True if there is no info in the blob, meaning that it is
        probably a null blob
        """
        if len(self.data) == 0:
            return True
        return False

    ##########################################################################
    def addLine(self, line, mode):
        if mode not in self.lines:
            self.lines[mode] = []
        self.lines[mode].append(line.strip())


##########################################################################
# Prtconf ################################################################
##########################################################################


class Prtconf(explorerbase.ExplorerBase):
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self["_rootblob"] = None
        self["_enclosures"] = []
        if self.exists("sysconfig/prtconf-vD.out"):
            self["_kstat_disks"] = []
            self["_kstat_tapes"] = []
            self.getKstats()
            self.parsePrtconf_vd()
            for devname, blob in self.items():
                if devname.startswith("_"):
                    continue
                blob.analyseLines()
                if self.isNullBlobs(blob):
                    blob.parent.removeChild(blob)
                    del self[devname]
                    continue
            self.analyseEnclosures()
        self["boot_aliases"] = {}
        self.parsePrtconf_vp()

    ##########################################################################
    def parsePrtconf_vp(self):
        filename = "sysconfig/prtconf-vp.out"
        if not self.exists(filename):
            return
        f = self.open(filename)
        buff = []
        for line in f:
            line = line.strip()
            if not line:
                buff = []
                continue
            if "'aliases'" in line:
                self.parseAliases(buff)
            buff.append(line)
        f.close()

    ##########################################################################
    def parseAliases(self, buff):
        for line in buff:
            if "Node" in line:
                continue
            bits = line.split(":")
            self["boot_aliases"][bits[0]] = bits[1].strip()[1:-1]

    ##########################################################################
    def analyse(self):
        pass

    ##########################################################################
    def isNullBlobs(self, blob):
        """Sometimes there are lots of basically empty blobs in prtdiag
        Try and detect them
        They generally won't have a presence in kstat because they aren't real
        """
        if self["_kstat_disks"]:
            if blob.isDisk() and blob.name() not in self["_kstat_disks"]:
                return True
            if blob.isTape() and blob.name() not in self["_kstat_tapes"]:
                return True
        if blob.isNull():
            print("Removing %s as a null blob" % blob)
            return True
        return False

    ##########################################################################
    def getKstats(self):
        k = kstat.Kstat(self.config)
        for link in k.classChains("disk"):
            self["_kstat_disks"].append(link.name())
        for link in k.classChains("tape"):
            self["_kstat_tapes"].append(link.name())

    ##########################################################################
    def analyseEnclosures(self):
        tmpdrivers = self.values()
        for devname, blob in self.items():
            if devname.startswith("_"):
                continue
            if blob.name().startswith("ses"):
                kidlist = []
                for b in blob.parent.children:
                    if b not in tmpdrivers:  # A driver can only appear once
                        continue
                    if b.name().startswith("sgen"):
                        tmpdrivers.remove(b)
                        continue
                    if b.name().startswith("ses"):
                        tmpdrivers.remove(b)
                        continue
                    kidlist.append(b)
                    tmpdrivers.remove(b)
                if kidlist:
                    self["_enclosures"].append([blob, kidlist])

    ##########################################################################
    def display(self, blob=None, indent=0):
        if not blob:
            blob = self["_rootblob"]
        print("%s%s" % (" " * indent * 4, blob.name()))
        for k, v in blob.data.items():
            print("    %s%s=%s" % (" " * indent * 4, k, v))
        for c in blob.children:
            self.display(c, indent + 1)

    ##########################################################################
    def addDriver(self, name):
        d = Driver(self.config, name)
        self[name] = d
        return d

    ##########################################################################
    def parsePrtconf_vd(self):
        f = self.open("sysconfig/prtconf-vD.out")
        self["_rootblob"] = self.addDriver("root")
        indentblob = {0: self["_rootblob"]}
        oldindent = 0
        currblob = self["_rootblob"]
        mode = ""

        for line in f:
            m = re.match(
                "(?P<indent>\s*)(?P<module>\S+), instance #(?P<instance>\d+) \(driver name: (?P<driver>\S+)\)",
                line,
            )
            if m:
                mode = ""
                indent = len(m.group("indent")) / 4

                currblob = self.addDriver(
                    "%s%s" % (m.group("module"), m.group("instance"))
                )
                indentblob[indent - 1].addChild(currblob)
                indentblob[indent] = currblob
                oldindent = indent
                continue
            if "System software properties" in line:
                mode = "system"
                continue
            if "Range Specifications" in line:
                mode = "range"
                continue
            if "Register Specifications" in line:
                mode = "register"
                continue
            if "System properties" in line:
                mode = "system"
                continue
            if "Driver properties" in line:
                mode = "driver"
                continue
            if "Hardware properties" in line:
                mode = "hardware"
                continue
            if "Device Minor Nodes" in line:
                mode = "device"
                continue
            if mode in ("hardware", "driver", "system"):
                currblob.addLine(line, mode)
                continue
            if mode in ("device", "range", "register", "system"):
                continue

        f.close()


# EOF
