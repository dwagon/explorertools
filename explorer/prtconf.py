"""
Script to analyse prtconf -vD from explorers
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: prtconf.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/prtconf.py $

import re
import explorerbase
import kstat


##########################################################################
class Driver(explorerbase.ExplorerBase):
    """ TODO """
    def __init__(self, config, drivername):
        explorerbase.ExplorerBase.__init__(self, config)
        self.objname = drivername
        self.children = []
        self.parent = None
        self.lines = {}

    ##########################################################################
    def analyse_lines(self):
        """ TODO """
        for mode in self.lines:
            self.analyse(mode)
        self["vendor"] = ""
        if "hardware:inquiry-vendor-id" in self:
            self["vendor"] += f"{self['hardware:inquiry-vendor-id']}"
        if "hardware:inquiry-product-id" in self:
            self["vendor"] += self["hardware:inquiry-product-id"]
        if self["vendor"] == "SUNW SUNWGS INT FCBPL":
            self["vendor"] = "Internal FibreChannel Backplane"

    ##########################################################################
    def get_name(self, line):
        """ TODO """
        for reg in (
            r"name='(?P<name>.*)'",
            r"name=(?P<name>.*)",
            r"name \<(?P<name>.*?)\>",
        ):
            matchobj = re.search(reg, line)
            if matchobj:
                return matchobj.group("name")
        if "driver name" in line:
            return None
        self.Warning(f"No match for name: {line}")
        return None

    ##########################################################################
    def get_value(self, line):
        """ TODO """
        for reg in (
            "value='(?P<value>.*)'",
            "value=(?P<value>.*)",
            "value <(?P<value>.*?)>",
            "value '(?P<value>.*?)'",
        ):
            matchobj = re.search(reg, line)
            if matchobj:
                return matchobj.group("value")
        self.Warning(f"No match for value:{line}")
        return None

    ##########################################################################
    def analyse(self, mode):
        """ TODO """
        name = ""
        value = ""
        for line in self.lines[mode]:
            if "name" in line:
                name = self.get_name(line)
                value = ""
            elif "value" in line:
                value = self.get_value(line)

            if name and value:
                self[f"{mode}:{name}"] = value
                name = ""
                value = ""

    ##########################################################################
    def add_parent(self, blob):
        """ TODO """
        self.parent = blob

    ##########################################################################
    def remove_child(self, blob):
        """ TODO """
        self.children.remove(blob)

    ##########################################################################
    def add_child(self, blob):
        """ TODO """
        self.children.append(blob)
        blob.add_parent(self)

    ##########################################################################
    def is_tape(self):
        """ TODO """
        if self.name().startswith("st"):
            return True
        return False

    ##########################################################################
    def is_disk(self):
        """ TODO """
        if self.name().startswith("sd"):
            return True
        if self.name().startswith("ssd"):
            return True
        return False

    ##########################################################################
    def is_null(self):
        """return True if there is no info in the blob, meaning that it is
        probably a null blob
        """
        if len(self.data) == 0:
            return True
        return False

    ##########################################################################
    def add_line(self, line, mode):
        """ TODO """
        if mode not in self.lines:
            self.lines[mode] = []
        self.lines[mode].append(line.strip())


##########################################################################
# Prtconf ################################################################
##########################################################################
class Prtconf(explorerbase.ExplorerBase):
    """ TODO """
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self["_rootblob"] = None
        self["_enclosures"] = []
        if self.exists("sysconfig/prtconf-vD.out"):
            self["_kstat_disks"] = []
            self["_kstat_tapes"] = []
            self.get_kstats()
            self.parse_prtconf_vd()
            for devname, blob in self.items():
                if devname.startswith("_"):
                    continue
                blob.analyse_lines()
                if self.is_null_blobs(blob):
                    blob.parent.remove_child(blob)
                    del self[devname]
                    continue
            self.analyse_enclosures()
        self["boot_aliases"] = {}
        self.parse_prtconf_vp()

    ##########################################################################
    def parse_prtconf_vp(self):
        """ TODO """
        filename = "sysconfig/prtconf-vp.out"
        if not self.exists(filename):
            return
        infh = self.open(filename)
        buff = []
        for line in infh:
            line = line.strip()
            if not line:
                buff = []
                continue
            if "'aliases'" in line:
                self.parse_aliases(buff)
            buff.append(line)
        infh.close()

    ##########################################################################
    def parse_aliases(self, buff):
        """ TODO """
        for line in buff:
            if "Node" in line:
                continue
            bits = line.split(":")
            self["boot_aliases"][bits[0]] = bits[1].strip()[1:-1]

    ##########################################################################
    def analyse(self, mode):
        """ TODO """

    ##########################################################################
    def is_null_blobs(self, blob):
        """Sometimes there are lots of basically empty blobs in prtdiag
        Try and detect them
        They generally won't have a presence in kstat because they aren't real
        """
        if self["_kstat_disks"]:
            if blob.is_disk() and blob.name() not in self["_kstat_disks"]:
                return True
            if blob.is_tape() and blob.name() not in self["_kstat_tapes"]:
                return True
        if blob.is_null():
            print(f"Removing {blob} as a null blob")
            return True
        return False

    ##########################################################################
    def get_kstats(self):
        """ TODO """
        k = kstat.Kstat(self.config)
        for link in k.classChains("disk"):
            self["_kstat_disks"].append(link.name())
        for link in k.classChains("tape"):
            self["_kstat_tapes"].append(link.name())

    ##########################################################################
    def analyse_enclosures(self):
        """ TODO """
        tmpdrivers = self.values()
        for devname, blob in self.items():
            if devname.startswith("_"):
                continue
            if blob.name().startswith("ses"):
                kidlist = []
                for blb in blob.parent.children:
                    if blb not in tmpdrivers:  # A driver can only appear once
                        continue
                    if blb.name().startswith("sgen"):
                        tmpdrivers.remove(blb)
                        continue
                    if blb.name().startswith("ses"):
                        tmpdrivers.remove(blb)
                        continue
                    kidlist.append(blb)
                    tmpdrivers.remove(blb)
                if kidlist:
                    self["_enclosures"].append([blob, kidlist])

    ##########################################################################
    def display(self, blob=None, indent=0):
        """ TODO """
        if not blob:
            blob = self["_rootblob"]
        print("%s%s" % (" " * indent * 4, blob.name()))
        for k, v in blob.data.items():
            print("    %s%s=%s" % (" " * indent * 4, k, v))
        for chld in blob.children:
            self.display(chld, indent + 1)

    ##########################################################################
    def add_driver(self, name):
        """ TODO """
        drvr = Driver(self.config, name)
        self[name] = drvr
        return drvr

    ##########################################################################
    def parse_prtconf_vd(self):
        """ TODO """
        infh = self.open("sysconfig/prtconf-vD.out")
        self["_rootblob"] = self.add_driver("root")
        indentblob = {0: self["_rootblob"]}
        currblob = self["_rootblob"]
        mode = ""

        for line in infh:
            matchobj = re.match(
                r"(?P<indent>\s*)(?P<module>\S+), instance #(?P<instance>\d+) \(driver name: (?P<driver>\S+)\)",
                line,
            )
            if matchobj:
                mode = ""
                indent = len(matchobj.group("indent")) / 4

                currblob = self.add_driver("{matchobj.group('module')}{matchobj.group('instance')}")
                indentblob[indent - 1].add_child(currblob)
                indentblob[indent] = currblob
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
                currblob.add_line(line, mode)
                continue
            if mode in ("device", "range", "register", "system"):
                continue

        infh.close()


# EOF
